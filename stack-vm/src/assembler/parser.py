"""Parser for Oracle VM assembly — turns a token list into an AST."""
from __future__ import annotations
from dataclasses import dataclass, field
from .lexer import Token, TT
from ..vm.exceptions import AssemblerError


@dataclass
class StringDef:
    name: str
    value: str
    line: int


@dataclass
class LabelDef:
    name: str
    line: int


@dataclass
class Instruction:
    mnemonic: str
    operand: int | str | None  # int literal, label name, or nothing
    line: int


@dataclass
class DataSection:
    defs: list[StringDef] = field(default_factory=list)


@dataclass
class CodeSection:
    items: list[LabelDef | Instruction] = field(default_factory=list)


@dataclass
class Program:
    data: DataSection
    code: CodeSection


# Mnemonics that require exactly one operand
_NEEDS_OPERAND = {
    "PUSH", "LOAD", "STORE",
    "JUMP", "JTRUE", "JFALSE", "CALL",
}

# Mnemonics that take NO operand
_NO_OPERAND = {
    "POP", "DUP", "SWAP",
    "IADD", "ISUB", "IMUL", "IDIV", "IMOD", "INEG",
    "ICMP", "IEQ", "ILT", "IGT",
    "ALOAD", "ASTORE",
    "RET", "PRINT", "PRINTS", "READ",
    "ALLOC", "FREE",
    "HALT",
}


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _consume(self, tt: TT | None = None) -> Token:
        tok = self._tokens[self._pos]
        if tt is not None and tok.type != tt:
            raise AssemblerError(
                f"Expected {tt.name}, got {tok.type.name} ({tok.value!r})",
                tok.line,
            )
        self._pos += 1
        return tok

    def parse(self) -> Program:
        data = DataSection()
        code = CodeSection()

        while self._peek().type != TT.EOF:
            tok = self._peek()
            if tok.type == TT.DIRECTIVE:
                self._consume()
                if tok.value == ".data":
                    self._parse_data_section(data)
                elif tok.value == ".code":
                    self._parse_code_section(code)
                else:
                    raise AssemblerError(f"Unknown directive {tok.value!r}", tok.line)
            else:
                # Bare code without a .code directive — treat as implicit .code
                self._parse_code_section(code)

        return Program(data=data, code=code)

    def _parse_data_section(self, data: DataSection) -> None:
        while self._peek().type not in (TT.DIRECTIVE, TT.EOF):
            tok = self._peek()
            if tok.type == TT.IDENT:
                name_tok = self._consume(TT.IDENT)
                str_tok = self._consume(TT.STRING)
                data.defs.append(StringDef(name_tok.value, str_tok.value, name_tok.line))
            elif tok.type == TT.LABEL_DEF:
                # A label defined inside .data — unusual but harmless; skip
                self._consume()
            else:
                break

    def _parse_code_section(self, code: CodeSection) -> None:
        while self._peek().type not in (TT.DIRECTIVE, TT.EOF):
            tok = self._peek()
            if tok.type == TT.LABEL_DEF:
                self._consume()
                code.items.append(LabelDef(tok.value, tok.line))
            elif tok.type == TT.MNEMONIC:
                self._consume()
                mnemonic = tok.value
                operand = None
                if mnemonic in _NEEDS_OPERAND:
                    op_tok = self._peek()
                    if op_tok.type == TT.INTEGER:
                        operand = self._consume().value
                    elif op_tok.type == TT.IDENT:
                        operand = self._consume().value
                    else:
                        raise AssemblerError(
                            f"{mnemonic} requires an operand", tok.line
                        )
                code.items.append(Instruction(mnemonic, operand, tok.line))
            else:
                raise AssemblerError(
                    f"Unexpected token in .code: {tok.type.name} ({tok.value!r})",
                    tok.line,
                )


def parse(tokens: list[Token]) -> Program:
    return Parser(tokens).parse()
