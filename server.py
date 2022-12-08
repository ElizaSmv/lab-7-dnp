import argparse
import sys
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
from random import randint
import time
from threading import Timer
import grpc
import raft_pb2_grpc
import raft_pb2_grpc as pb2_grpc
import raft_pb2 as pb2


class Handler(raft_pb2_grpc.RaftServicer):

    def RequestVote(self, request: pb2.RVArgs, context) -> pb2.Check:
        if d[given_id].sleeping:
            return None

        term = request.term  # candidate term
        candidateid = request.candidateId
        lastIndex = request.lastLogIndex
        lastTerm = request.lastLogTerm
        # print('incoming vote req', candidateid, term, lastIndex)

        my_term = d[given_id].term  # my term
        k = len(d[given_id].logs)
        my_last_log = d[given_id].logs[k]

        if term > my_term:
            d[given_id].term = term
        if term < my_term:
            d[given_id].last_update = time.time()
            print("low term")
            return pb2.Check(term=my_term, success=False)

        if d[given_id].vote[0] and d[given_id].vote[1] != given_id:
            print(f"Not Voted for node {candidateid}")
            return pb2.Check(term=my_term, success=False)

        if lastIndex < my_last_log[0]:
            d[given_id].last_update = time.time()
            print("low log index")
            return pb2.Check(term=my_term, success=False)

        if lastIndex == my_last_log[0] and lastTerm != my_last_log[1]:
            d[given_id].last_update = time.time()
            print("low log term ")
            return pb2.Check(term=my_term, success=False)

        d[given_id].vote = (True, candidateid)
        d[candidateid].votes += 1
        print(f"Voted for node {candidateid}")
        return pb2.Check(term=my_term, success=True)

    def AppendEntries(self, request: pb2.AEArgs, context) -> pb2.Check:
        global id_leader
        if d[given_id].sleeping:
            return None
        # print("got heartbeat")
        term = request.term
        id_leader = request.leaderId
        prev_index = request.prevLogIndex
        prev_term = request.prevLogTerm
        ent = request.entries
        lead_commit = request.leaderCommit
        d[given_id].last_update = time.time()
        if term >= d[given_id].term:
            d[given_id].term = term
            return pb2.Check(term=d[given_id].term, success=True)

        if term < d[given_id].term: # FIXME
            d[given_id].last_update = time.time()
            d[given_id].state = "Follower"
            print(f"I'm a {d[given_id].state}. Term: {d[given_id].term}")
            return pb2.Check(term=d[given_id].term, success=False)





    def GetLeader(self, request, context) -> pb2.Leader:
        if d[given_id].sleeping:
            return None
        print("Command from client: getleader")
        for k, v in d.items():
            if v.state == "Leader":
                mes = f"{v.addr}:{v.port}"
                print(f"the leader {k} mes")
                return pb2.Leader(id=k, addr=mes)
        if d[given_id].vote[0] is False and d[given_id].vote[1] != -1:
            temp_id = d[given_id].vote[1]
            mes = d[temp_id].addr
            print(f"election now {temp_id} {mes}")
            return pb2.Leader(id=temp_id, addr=mes)
        if d[given_id].vote[0] is False:
            print("has not voted yet")
            return pb2.Leader(addr=' ')
        m = f"{d[id_leader].addr}:{d[id_leader].port}"
        return pb2.Leader(id=id_leader, addr=m)

    def Suspend(self, request: pb2.Per, context) -> pb2.Null:
        if d[given_id].sleeping:
            return None
        y = request.period
        print(f"Command from client: suspend {y}")
        d[given_id].sleeping = True
        print(f"Sleeping for {y} seconds")
        t = Timer(y, sleep_callback, (d[given_id], ))
        t.start()
        return pb2.Null()

    def SetVal(self, request, context) -> pb2.SetReturn:
        if d[given_id].sleeping:
            return None
        global id_leader
        key = request.key
        value = request.value
        print(f"Command from client: setval {key} {value}")
        if d[given_id].state == "Candidate":
            return pb2.SetReturn(success=False)
        d[id_leader].last_applied += 1 # TODO: That won't update the value of leader
        temp = (t, d[id_leader].last_applied, f"{key}={value}")
        # d[id_leader].new_entries.append()




        return pb2.SetReturn()

    def GetVal(self, request, context) -> pb2.GetReturn:
        if d[given_id].sleeping:
            return None
        global id_leader
        key = request.key
        print(f"Command from client: getval {key}")

        return pb2.GetReturn()


def sleep_callback(x):
    x.sleeping = False
    x.last_update = time.time()


class Node:

    def __init__(self, state, timer, term, addr, port) -> None:
        self.state = state
        self.timer = timer
        self.term = term
        self.addr = addr
        self.port = port
        self.vote = (False, -1)
        self.votes = 0
        self.last_update = 0
        self.sleeping = False
        self.commit_index = 0
        self.last_applied = 0
        self.logs = [(0, 0, " ")]
        self.commands = {}
        self.new_entries = []
        self.nextIndex = {} # only for leader
        self.matchIndex = {} # only for leader
        self.channel = grpc.insecure_channel(f'{addr}:{port}')
        self.stub = pb2_grpc.RaftStub(self.channel)

    def start_election(self):
        # print('Running as Candidate')

        self.vote = (True, given_id)
        self.votes = 1  # votes for yourself
        print(f"Voted for node {given_id}")
        for k, v in d.items():
            if k != given_id:
                try:
                    last_log_index = self.last_applied
                    last_log_term = self.logs[last_log_index][1]
                    aaa = pb2.RVArgs(term=self.term,
                                     candidateId=given_id,
                                     lastLogIndex=last_log_index,
                                     lastLogTerm=last_log_term)
                    r = v.stub.RequestVote(aaa)
                except grpc.RpcError as e:
                    continue
                # print(f'recieved vote from {k}, ', r.success, r.term)
                ans = r.term
                flag = r.success
                if ans > self.term:
                    self.term = ans
                    self.state = "Follower"
                    print(f"I'm a {self.state}. Term: {self.term}")
                    self.votes = 0
                    return None
                if flag is True:
                    self.votes += 1
                    # print("yay")
        print("Votes received")

        if 0.5 < (self.votes / len(d)):
            d[given_id].state = "Leader"
            print(f"I'm a {self.state}. Term: {self.term}")
        else:
            d[given_id].state = "Follower"
            print(f"I'm a {self.state}. Term: {self.term}")
            self.last_update = time.time()
            self.term += 1
        self.vote = (False, -1)

    def follower(self):
        # print('Running as a follower')
        self.last_update = time.time()
        while time.time() - self.last_update <= self.timer:
            # print(time.time() - self.last_update, self.timer)
            pass
        self.state = "Candidate"
        print(f"I'm a {self.state}. Term: {self.term}")
        self.term = self.term + 1
        print('term', self.term)

    def leader(self):
        print(f"I'm a {self.state}. Term: {self.term}")
        for k, v in d.items():
            if k != given_id:
                if len(self.new_entries) == 0:
                    print("Heart beat")
                    t.submit(v.heartbeat, self.term, given_id, (), self.commit_index)
                else:
                    for e in self.new_entries:
                        print("Append entries")
                        t.submit(v.heartbeat, self.term, given_id, e, self.commit_index)
        time.sleep(0.05)

    def start_server(self):
        # print(f"I'm a {self.state}. Term: {self.term}")
        while True:
            if self.sleeping:
                continue
            if self.state == "Follower":
                self.follower()
            if self.state == "Candidate":
                self.start_election()
            if self.state == "Leader":
                self.leader()

    def heartbeat(self, term, leader_id, entries, commit): # FIXME
        try:
            # print(f"send hb to {self.port}")
            # append = self.stub.AppendEntries(pb2.AEArgs(term=term,
                                                        leaderId=leader_id,
                                                        prevLogIndex=,
                                                        prevLogTerm=,
                                                        entries=entries,
                                                        leaderCommit=commit))
            # print("Delivered heartbeat")
            # return append
        except grpc.RpcError as e:
            # print("heartbeat error", e)
            return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Server receive data')
    parser.add_argument('id', type=int, help="Server id")
    given_id = parser.parse_args().id
    d = {}

    with open("config.conf") as f:
        for line in f:
            id, addr, port = line.split()
            id = int(id)
            rand_timer = (randint(150, 300)) / 1000
            d[id] = Node("Follower", rand_timer, 0, addr, port)

    if given_id in d.keys():
        my_node = d[given_id]
    else:
        print("This node does not exist")
        sys.exit(0)

    t = ThreadPoolExecutor(max_workers=len(d))
    id_leader = -1

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    pb2_grpc.add_RaftServicer_to_server(Handler(), server)
    server.add_insecure_port(f"{my_node.addr}:{my_node.port}")
    server.start()
    print(f"The server starts at {my_node.addr}:{my_node.port}")
    print(f"I am a {my_node.state}. Term: {my_node.term}")
    time.sleep(5)
    try:
        my_node.start_server()
    except KeyboardInterrupt:
        work = False
        print("Shutting down")
