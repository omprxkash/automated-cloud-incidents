"""Two-pass code generator: AST → bytecode file bytes."""
from __future__ import annotations
import struct
from .parser import Program, Instruction, LabelDef, StringDef
from ..vm.opcodes import OpCode
from ..vm.cpu import MAGIC
from ..vm.exceptions import AssemblerError

_MNEMONIC_TO_OPCODE: dict[str, OpCode] = {op.name: op for op in OpCode}


def _pack_int(value: int) -> bytes:
    return struct.pack(">i", value)


class CodeGen:
    def __init__(self, program: Program) -> None:
        self._program = program
        # Data segment: maps label name → heap address (offset within data blob)
        self._data_labels: dict[str, int] = {}
        self._data_blob: bytes = b""
        # Code: maps label name → byte offset within code blob
        self._code_labels: dict[str, int] = {}
        # symbol table: addr → name
        self._symbols: dict[int, str] = {}

    def generate(self) -> bytes:
        """Return the complete .bc file bytes."""
        self._build_data_segment()
        code_bytes = self._emit_code()
        return self._pack_file(code_bytes)

    # ------------------------------------------------------------------
    # Pass 1: data segment
    # ------------------------------------------------------------------

    def _build_data_segment(self) -> None:
        blob = bytearray()
        for sdef in self._program.data.defs:
            self._data_labels[sdef.name] = len(blob)
            encoded = sdef.value.encode("utf-8") + b"\x00"
            blob.extend(encoded)
        self._data_blob = bytes(blob)

    # ------------------------------------------------------------------
    # Pass 1: collect code labels (first pass)
    # ------------------------------------------------------------------

    def _collect_code_labels(self) -> bytes:
        """First pass: sizes without resolving labels → get label addresses."""
        offset = 0
        for item in self._program.code.items:
            if isinstance(item, LabelDef):
                self._code_labels[item.name] = offset
                self._symbols[offset] = item.name
            elif isinstance(item, Instruction):
                offset += self._instruction_size(item)
        return b""

    def _instruction_size(self, instr: Instruction) -> int:
        op = _MNEMONIC_TO_OPCODE[instr.mnemonic]
        # 1 byte opcode + 4 byte operand for those that carry one
        from ..vm.opcodes import OPERAND_OPCODES
        return 1 + (4 if op in OPERAND_OPCODES else 0)

    # ------------------------------------------------------------------
    # Pass 2: emit code
    # ------------------------------------------------------------------

    def _emit_code(self) -> bytes:
        self._collect_code_labels()
        buf = bytearray()
        for item in self._program.code.items:
            if isinstance(item, LabelDef):
                continue
            assert isinstance(item, Instruction)
            op = _MNEMONIC_TO_OPCODE[instr := item.mnemonic]
            buf.append(op.value)

            from ..vm.opcodes import OPERAND_OPCODES
            if op in OPERAND_OPCODES:
                buf.extend(self._resolve_operand(item))

        return bytes(buf)

    def _resolve_operand(self, instr: Instruction) -> bytes:
        operand = instr.operand
        if operand is None:
            raise AssemblerError(f"{instr.mnemonic} requires an operand", instr.line)

        if isinstance(operand, int):
            return _pack_int(operand)

        # It's a string — look up as code label or data label
        if operand in self._code_labels:
            return _pack_int(self._code_labels[operand])
        if operand in self._data_labels:
            return _pack_int(self._data_labels[operand])
        raise AssemblerError(
            f"Undefined label {operand!r}", instr.line
        )

    # ------------------------------------------------------------------
    # File packing
    # ------------------------------------------------------------------

    def _pack_file(self, code_bytes: bytes) -> bytes:
        sym_bytes = "\n".join(
            f"{name}={addr}" for addr, name in self._symbols.items()
        ).encode("utf-8")
        header = (
            MAGIC
            + len(self._data_blob).to_bytes(4, "big")
            + len(code_bytes).to_bytes(4, "big")
            + len(sym_bytes).to_bytes(4, "big")
        )
        return header + self._data_blob + code_bytes + sym_bytes


def assemble(source: str) -> bytes:
    """Assemble *source* text and return .bc file bytes."""
    from .lexer import tokenize
    from .parser import parse
    tokens = tokenize(source)
    program = parse(tokens)
    return CodeGen(program).generate()
