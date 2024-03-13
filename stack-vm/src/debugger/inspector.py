"""Read CPU state and disassemble bytecode for the debugger."""
from __future__ import annotations
from ..vm.opcodes import OpCode, OPERAND_OPCODES
from ..vm.cpu import CPU


def disassemble(bytecode: bytes, start: int = 0, count: int = 10, symbols: dict[int, str] | None = None) -> list[str]:
    """Return up to *count* disassembled instruction strings starting at *start*."""
    lines = []
    ip = start
    sym = symbols or {}
    while ip < len(bytecode) and len(lines) < count:
        label = sym.get(ip, "")
        label_prefix = f"{label}:\n  " if label else "  "
        try:
            op = OpCode(bytecode[ip])
        except ValueError:
            lines.append(f"{ip:04x}: {label_prefix}?? {bytecode[ip]:02x}")
            ip += 1
            continue
        if op in OPERAND_OPCODES:
            if ip + 5 > len(bytecode):
                lines.append(f"{ip:04x}: {label_prefix}{op.name} <truncated>")
                break
            operand = int.from_bytes(bytecode[ip + 1 : ip + 5], "big", signed=True)
            operand_label = sym.get(operand, "")
            operand_str = f"{operand_label}  ({operand:#010x})" if operand_label else f"{operand}"
            lines.append(f"{ip:04x}: {label_prefix}{op.name:<8} {operand_str}")
            ip += 5
        else:
            lines.append(f"{ip:04x}: {label_prefix}{op.name}")
            ip += 1
    return lines


class Inspector:
    """Snapshot helper -- pulls state from a live CPU for display."""

    def __init__(self, cpu: CPU) -> None:
        self._cpu = cpu

    def stack_snapshot(self) -> list[int]:
        return self._cpu.stack.snapshot()

    def ip(self) -> int:
        return self._cpu.ip

    def call_depth(self) -> int:
        return len(self._cpu.call_stack)

    def call_stack_names(self) -> list[str]:
        return [f.name for f in self._cpu.call_stack]

    def current_locals(self) -> dict[int, int]:
        return dict(self._cpu.current_frame.locals)

    def is_running(self) -> bool:
        return self._cpu.running

    def next_instructions(self, count: int = 10) -> list[str]:
        return disassemble(
            self._cpu.bytecode,
            start=self._cpu.ip,
            count=count,
            symbols=self._cpu.symbols,
        )

    def heap_dump(self, start: int = 0, length: int = 128) -> str:
        return self._cpu.heap.dump(start=start, length=length)
