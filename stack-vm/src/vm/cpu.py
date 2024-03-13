from __future__ import annotations
import sys
from .opcodes import OpCode
from .stack import OperandStack
from .heap import SimpleHeap
from .frame import CallFrame
from .exceptions import VMError

MAGIC = b"OVM\x01"


def load_bytecode(raw: bytes) -> tuple[bytes, bytes, dict[int, str]]:
    """Parse a .bc file into (heap_data, code, symbol_table)."""
    if raw[:4] != MAGIC:
        raise VMError("Not a valid Oracle VM bytecode file")
    data_size = int.from_bytes(raw[4:8], "big")
    code_size = int.from_bytes(raw[8:12], "big")
    sym_size  = int.from_bytes(raw[12:16], "big")
    offset = 16
    heap_data = raw[offset:offset + data_size]
    offset += data_size
    code = raw[offset:offset + code_size]
    offset += code_size
    symbols: dict[int, str] = {}
    sym_raw = raw[offset:offset + sym_size].decode("utf-8")
    if sym_raw:
        for entry in sym_raw.split("\n"):
            if "=" in entry:
                name, addr = entry.split("=", 1)
                symbols[int(addr)] = name
    return heap_data, code, symbols


class CPU:
    """Oracle VM stack-based CPU."""

    def __init__(
        self,
        code: bytes,
        heap_data: bytes = b"",
        symbols: dict[int, str] | None = None,
        heap_size: int = 65536,
        stdin=None,
        stdout=None,
    ) -> None:
        self.bytecode = code
        self.ip = 0
        self.stack = OperandStack(max_size=1024)
        # Seed call stack with a global frame so LOAD/STORE work anywhere
        self.call_stack: list[CallFrame] = [CallFrame("__main__", -1)]
        self.heap = SimpleHeap(size=heap_size)
        self.running = False
        self._breakpoints: set[int] = set()
        self.symbols = symbols or {}
        self._stdin = stdin or sys.stdin
        self._stdout = stdout or sys.stdout

        # Write static data into heap then start the allocator after it
        if heap_data:
            self.heap.write_bytes_raw(0, heap_data)
        self.heap.init_allocator(after=len(heap_data))

    # ------------------------------------------------------------------
    # Public execution interface
    # ------------------------------------------------------------------

    def run(self) -> None:
        self.running = True
        while self.running and self.ip < len(self.bytecode):
            if self.ip in self._breakpoints:
                break
            self.step()

    def step(self) -> None:
        if not self.running and self.ip == 0:
            self.running = True
        if self.ip >= len(self.bytecode):
            self.running = False
            return
        op = OpCode(self._fetch_byte())
        self._execute(op)

    def add_breakpoint(self, addr: int) -> None:
        self._breakpoints.add(addr)

    def remove_breakpoint(self, addr: int) -> None:
        self._breakpoints.discard(addr)

    @property
    def current_frame(self) -> CallFrame:
        return self.call_stack[-1]

    # ------------------------------------------------------------------
    # Fetch helpers
    # ------------------------------------------------------------------

    def _fetch_byte(self) -> int:
        if self.ip >= len(self.bytecode):
            raise VMError("Unexpected end of bytecode")
        b = self.bytecode[self.ip]
        self.ip += 1
        return b

    def _fetch_int(self) -> int:
        if self.ip + 4 > len(self.bytecode):
            raise VMError("Unexpected end of bytecode while reading int")
        val = int.from_bytes(self.bytecode[self.ip : self.ip + 4], "big", signed=True)
        self.ip += 4
        return val

    # ------------------------------------------------------------------
    # Instruction dispatch
    # ------------------------------------------------------------------

    def _execute(self, op: OpCode) -> None:  # noqa: C901 (long dispatch is fine)
        s = self.stack
        h = self.heap

        # ---- Stack ----
        if op == OpCode.PUSH:
            s.push(self._fetch_int())

        elif op == OpCode.POP:
            s.pop()

        elif op == OpCode.DUP:
            s.dup()

        elif op == OpCode.SWAP:
            s.swap()

        # ---- Arithmetic ----
        elif op == OpCode.IADD:
            b, a = s.pop(), s.pop()
            s.push(a + b)

        elif op == OpCode.ISUB:
            b, a = s.pop(), s.pop()
            s.push(a - b)

        elif op == OpCode.IMUL:
            b, a = s.pop(), s.pop()
            s.push(a * b)

        elif op == OpCode.IDIV:
            b, a = s.pop(), s.pop()
            if b == 0:
                raise VMError("Division by zero")
            s.push(int(a / b))  # truncate toward zero

        elif op == OpCode.IMOD:
            b, a = s.pop(), s.pop()
            if b == 0:
                raise VMError("Modulo by zero")
            s.push(a % b)

        elif op == OpCode.INEG:
            s.push(-s.pop())

        # ---- Comparison ----
        elif op == OpCode.ICMP:
            b, a = s.pop(), s.pop()
            s.push(0 if a == b else (-1 if a < b else 1))

        elif op == OpCode.IEQ:
            b, a = s.pop(), s.pop()
            s.push(1 if a == b else 0)

        elif op == OpCode.ILT:
            b, a = s.pop(), s.pop()
            s.push(1 if a < b else 0)

        elif op == OpCode.IGT:
            b, a = s.pop(), s.pop()
            s.push(1 if a > b else 0)

        # ---- Local variables ----
        elif op == OpCode.LOAD:
            idx = self._fetch_int()
            s.push(self.current_frame.load(idx))

        elif op == OpCode.STORE:
            idx = self._fetch_int()
            self.current_frame.store(idx, s.pop())

        # ---- Heap array access ----
        elif op == OpCode.ALOAD:
            index = s.pop()
            base = s.pop()
            s.push(h.read_int(base + index * 4))

        elif op == OpCode.ASTORE:
            value = s.pop()
            index = s.pop()
            base = s.pop()
            h.write_int(base + index * 4, value)

        # ---- Control flow ----
        elif op == OpCode.JUMP:
            self.ip = self._fetch_int()

        elif op == OpCode.JTRUE:
            addr = self._fetch_int()
            if s.pop() != 0:
                self.ip = addr

        elif op == OpCode.JFALSE:
            addr = self._fetch_int()
            if s.pop() == 0:
                self.ip = addr

        elif op == OpCode.CALL:
            addr = self._fetch_int()
            name = self.symbols.get(addr, f"fn@{addr:#x}")
            frame = CallFrame(name=name, return_addr=self.ip)
            self.call_stack.append(frame)
            self.ip = addr

        elif op == OpCode.RET:
            if len(self.call_stack) <= 1:
                # Returning from __main__ — treat as HALT
                self.running = False
                return
            frame = self.call_stack.pop()
            self.ip = frame.return_addr

        # ---- I/O ----
        elif op == OpCode.PRINT:
            print(s.pop(), file=self._stdout)

        elif op == OpCode.PRINTS:
            addr = s.pop()
            print(h.read_string(addr), file=self._stdout)

        elif op == OpCode.READ:
            line = self._stdin.readline().strip()
            try:
                s.push(int(line))
            except ValueError:
                raise VMError(f"READ: expected integer, got {line!r}")

        # ---- Heap management ----
        elif op == OpCode.ALLOC:
            size = s.pop()
            s.push(h.alloc(size))

        elif op == OpCode.FREE:
            h.free(s.pop())

        # ---- Halt ----
        elif op == OpCode.HALT:
            self.running = False

        else:
            raise VMError(f"Unknown opcode: {op:#x}")
