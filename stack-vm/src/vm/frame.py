from __future__ import annotations


class CallFrame:
    """Activation record pushed onto the call stack when CALL is executed."""

    def __init__(self, name: str, return_addr: int) -> None:
        self.name = name
        self.return_addr = return_addr
        self.locals: dict[int, int] = {}

    def load(self, index: int) -> int:
        if index not in self.locals:
            return 0
        return self.locals[index]

    def store(self, index: int, value: int) -> None:
        self.locals[index] = value

    def __repr__(self) -> str:
        return f"CallFrame(name={self.name!r}, ret={self.return_addr}, locals={self.locals})"
