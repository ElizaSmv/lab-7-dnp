from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Check(_message.Message):
    __slots__ = ["success", "term"]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    TERM_FIELD_NUMBER: _ClassVar[int]
    success: bool
    term: int
    def __init__(self, term: _Optional[int] = ..., success: bool = ...) -> None: ...

class Leader(_message.Message):
    __slots__ = ["addr", "id"]
    ADDR_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    addr: str
    id: int
    def __init__(self, id: _Optional[int] = ..., addr: _Optional[str] = ...) -> None: ...

class Null(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class Per(_message.Message):
    __slots__ = ["period"]
    PERIOD_FIELD_NUMBER: _ClassVar[int]
    period: int
    def __init__(self, period: _Optional[int] = ...) -> None: ...

class TeId(_message.Message):
    __slots__ = ["id", "term"]
    ID_FIELD_NUMBER: _ClassVar[int]
    TERM_FIELD_NUMBER: _ClassVar[int]
    id: int
    term: int
    def __init__(self, term: _Optional[int] = ..., id: _Optional[int] = ...) -> None: ...
