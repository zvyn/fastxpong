from typing import TypedDict


class BatDict(TypedDict):
    score: int
    pos: int
    len: int
    up_key: str
    down_key: str


class BallDict(TypedDict):
    position: tuple[float, float]
    velocity: tuple[float, float]


class SessionDict(TypedDict):
    count: int


class StateDict(TypedDict):
    left: BatDict
    right: BatDict
    ball: BallDict
    session: SessionDict
