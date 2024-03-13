from __future__ import annotations
from .exceptions import StackOverflowError, StackUnderflowError


class OperandStack:
    """Fixed-capacity integer stack for the Oracle VM CPU."""

    def __init__(self, max_size: int = 1024) -> None:
        self.max_size = max_size
        self._data: list[int] = []

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def push(self, value: int) -> None:
        if len(self._data) >= self.max_size:
            raise StackOverflowError(
                f"Stack overflow: max depth {self.max_size} exceeded"
            )
        self._data.append(value)

    def pop(self) -> int:
        if not self._data:
            raise StackUnderflowError("Stack underflow: pop from empty stack")
        return self._data.pop()

    def peek(self) -> int:
        if not self._data:
            raise StackUnderflowError("Stack underflow: peek on empty stack")
        return self._data[-1]

    def dup(self) -> None:
        self.push(self.peek())

    def swap(self) -> None:
        if len(self._data) < 2:
            raise StackUnderflowError("Stack underflow: swap needs at least 2 values")
        self._data[-1], self._data[-2] = self._data[-2], self._data[-1]

    # ------------------------------------------------------------------
    # Inspection helpers
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"OperandStack({self._data!r})"

    def snapshot(self) -> list[int]:
        return list(self._data)

    def clear(self) -> None:
        self._data.clear()
