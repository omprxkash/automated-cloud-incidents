"""Tests for the assembler pipeline: lexer → parser → codegen."""
import struct
import pytest
from src.assembler.lexer import tokenize, TT
from src.assembler.parser import parse, Instruction, LabelDef, StringDef
from src.assembler.codegen import assemble
from src.vm.cpu import load_bytecode, MAGIC
from src.vm.opcodes import OpCode
from src.vm.exceptions import AssemblerError


# ------------------------------------------------------------------
# Lexer
# ------------------------------------------------------------------

def test_lex_mnemonic():
    tokens = tokenize("PUSH 42")
    assert tokens[0].type == TT.MNEMONIC
    assert tokens[0].value == "PUSH"
    assert tokens[1].type == TT.INTEGER
    assert tokens[1].value == 42


def test_lex_label_def():
    tokens = tokenize("loop:")
    assert tokens[0].type == TT.LABEL_DEF
    assert tokens[0].value == "loop"


def test_lex_comment_stripped():
    tokens = tokenize("HALT  ; this is ignored")
    assert tokens[0].type == TT.MNEMONIC
    assert tokens[0].value == "HALT"
    assert tokens[1].type == TT.EOF


def test_lex_string():
    tokens = tokenize('"hello world"')
    assert tokens[0].type == TT.STRING
    assert tokens[0].value == "hello world"


def test_lex_negative_int():
    tokens = tokenize("PUSH -7")
    assert tokens[1].type == TT.INTEGER
    assert tokens[1].value == -7


def test_lex_hex_int():
    tokens = tokenize("PUSH 0xFF")
    assert tokens[1].type == TT.INTEGER
    assert tokens[1].value == 255


def test_lex_directive():
    tokens = tokenize(".data")
    assert tokens[0].type == TT.DIRECTIVE
    assert tokens[0].value == ".data"


# ------------------------------------------------------------------
# Parser
# ------------------------------------------------------------------

def test_parse_simple_code():
    tokens = tokenize(".code\nmain:\n  PUSH 1\n  HALT")
    prog = parse(tokens)
    items = prog.code.items
    assert isinstance(items[0], LabelDef)
    assert items[0].name == "main"
    assert isinstance(items[1], Instruction)
    assert items[1].mnemonic == "PUSH"
    assert items[1].operand == 1
    assert isinstance(items[2], Instruction)
    assert items[2].mnemonic == "HALT"


def test_parse_data_section():
    tokens = tokenize('.data\n  greeting "Hello"')
    prog = parse(tokens)
    assert len(prog.data.defs) == 1
    assert prog.data.defs[0].name == "greeting"
    assert prog.data.defs[0].value == "Hello"


def test_parse_label_operand():
    src = ".code\nmain:\n  JUMP main"
    tokens = tokenize(src)
    prog = parse(tokens)
    instr = prog.code.items[-1]
    assert isinstance(instr, Instruction)
    assert instr.operand == "main"


# ------------------------------------------------------------------
# Codegen / roundtrip
# ------------------------------------------------------------------

def test_assemble_halt():
    bc = assemble(".code\nHALT")
    heap_data, code, symbols = load_bytecode(bc)
    assert code == bytes([OpCode.HALT.value])


def test_assemble_push_print_halt():
    bc = assemble(".code\nPUSH 99\nPRINT\nHALT")
    heap_data, code, symbols = load_bytecode(bc)
    expected = (
        bytes([OpCode.PUSH.value])
        + struct.pack(">i", 99)
        + bytes([OpCode.PRINT.value, OpCode.HALT.value])
    )
    assert code == expected


def test_assemble_data_label():
    bc = assemble('.data\n  msg "hi"\n.code\nPUSH msg\nPRINTS\nHALT')
    heap_data, code, symbols = load_bytecode(bc)
    # msg is at heap offset 0
    push_operand = struct.unpack(">i", code[1:5])[0]
    assert push_operand == 0
    assert heap_data[:3] == b"hi\x00"


def test_assemble_label_jump():
    src = ".code\nmain:\n  PUSH 1\n  JUMP main"
    bc = assemble(src)
    heap_data, code, symbols = load_bytecode(bc)
    # JUMP target should be 0 (main is at offset 0)
    jump_target = struct.unpack(">i", code[-4:])[0]
    assert jump_target == 0


def test_undefined_label_raises():
    with pytest.raises(AssemblerError):
        assemble(".code\nJUMP nowhere")


def test_magic_header():
    bc = assemble(".code\nHALT")
    assert bc[:4] == MAGIC
