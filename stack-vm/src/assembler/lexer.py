"""Lexer for Oracle VM assembly source."""
from __future__ import annotations
import re
from dataclasses import dataclass
from enum import auto, Enum
from ..vm.exceptions import AssemblerError


class TT(Enum):
    DIRECTIVE   = auto()   # .data  .code
    LABEL_DEF   = auto()   # name:
    MNEMONIC    = auto()   # PUSH IADD ...
    IDENT       = auto()   # label reference used as operand
    INTEGER     = auto()   # 42  -7  0xFF
    STRING      = auto()   # "hello"
    EOF         = auto()


@dataclass
class Token:
    type: TT
    value: object  # str | int
    line: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, line={self.line})"


_DIRECTIVES = {".data", ".code"}

_MNEMONICS = {
    "PUSH", "POP", "DUP", "SWAP",
    "IADD", "ISUB", "IMUL", "IDIV", "IMOD", "INEG",
    "ICMP", "IEQ", "ILT", "IGT",
    "LOAD", "STORE", "ALOAD", "ASTORE",
    "JUMP", "JTRUE", "JFALSE", "CALL", "RET",
    "PRINT", "PRINTS", "READ",
    "ALLOC", "FREE",
    "HALT",
}

_INT_RE = re.compile(r"^-?(?:0[xX][0-9a-fA-F]+|\d+)$")


def tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    for lineno, raw_line in enumerate(source.splitlines(), start=1):
        line = raw_line.split(";", 1)[0].strip()  # strip comments
        if not line:
            continue
        pos = 0
        while pos < len(line):
            # Skip whitespace
            m = re.match(r"\s+", line[pos:])
            if m:
                pos += m.end()
                continue

            # String literal
            if line[pos] == '"':
                end = line.find('"', pos + 1)
                if end == -1:
                    raise AssemblerError("Unterminated string literal", lineno)
                raw = line[pos + 1:end]
                # Handle simple escape sequences
                raw = raw.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
                tokens.append(Token(TT.STRING, raw, lineno))
                pos = end + 1
                continue

            # Word token
            m = re.match(r"[A-Za-z_][A-Za-z0-9_]*:?|[.\-]?[A-Za-z_][A-Za-z0-9_]*:?|-?\d[\dxXa-fA-F]*", line[pos:])
            if not m:
                # Try standalone minus-number
                m = re.match(r"-\d+", line[pos:])
            if m:
                word = m.group(0)
                pos += m.end()

                if word in _DIRECTIVES:
                    tokens.append(Token(TT.DIRECTIVE, word, lineno))
                elif word.endswith(":"):
                    tokens.append(Token(TT.LABEL_DEF, word[:-1], lineno))
                elif word.upper() in _MNEMONICS:
                    tokens.append(Token(TT.MNEMONIC, word.upper(), lineno))
                elif _INT_RE.match(word):
                    base = 16 if word.lstrip("-").startswith(("0x", "0X")) else 10
                    tokens.append(Token(TT.INTEGER, int(word, base), lineno))
                else:
                    tokens.append(Token(TT.IDENT, word, lineno))
                continue

            raise AssemblerError(f"Unexpected character: {line[pos]!r}", lineno)

    tokens.append(Token(TT.EOF, None, 0))
    return tokens
