import sys
import grpc
import raft_pb2_grpc as pb2_grpc
import raft_pb2 as pb2

if __name__ == "__main__":

    print("The client starts")

    channel = None
    stub = None
    res = None

    while True:
        line = input("> ")
        try:
            com, arg = line.split(maxsplit=1)
        except ValueError as e:
            com = line
            arg = ''

        try:
            if "connect" == com:
                ipaddr, port = arg.split()
                print(port)
                try:
                    channel = grpc.insecure_channel(f"{ipaddr}:{port}")
                    stub = pb2_grpc.RaftStub(channel)
                    print("Connected")
                except grpc.RpcError as e:
                    print(f"Can't connect to {arg} server")
            elif "getleader" == com:
                r = stub.GetLeader(pb2.Null())
                print(r)

            elif "suspend" == com:
                arg = int(arg)
                r = stub.Suspend(pb2.Per(period=arg))
                print(f"Sleeping for {arg} seconds")
                # print(r)
            elif "setval" == com:
                key, value = arg.split()
                r = stub.SetVal(pb2.Set(key=key, value=value))
                print(r.success)
            elif "getval" == com:
                r = stub.GetVal(pb2.Set(value=arg))
                print(r.key)
            elif "quit" == com:
                print("The client ends")
                sys.exit(0)
            else:
                print("Invalid input")
        except KeyboardInterrupt:
            print("Shutting down")
            sys.exit(0)
