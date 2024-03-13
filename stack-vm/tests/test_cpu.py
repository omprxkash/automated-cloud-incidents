"""Unit tests for the CPU instruction set."""
import io
import struct
import pytest
from src.vm.cpu import CPU, MAGIC
from src.vm.opcodes import OpCode
from src.vm.exceptions import VMError, StackUnderflowError


def _pack(*ops) -> bytes:
    """Build bytecode from (opcode, optional_int_operand) tuples."""
    buf = bytearray()
    for item in ops:
        if isinstance(item, OpCode):
            buf.append(item.value)
        elif isinstance(item, int):
            buf.extend(struct.pack(">i", item))
        elif isinstance(item, bytes):
            buf.extend(item)
    return bytes(buf)


def run_code(ops, stdin_data="", heap_data=b"") -> str:
    """Assemble ops list into bytecode, run, return captured stdout."""
    code = _pack(*ops)
    out = io.StringIO()
    inp = io.StringIO(stdin_data)
    cpu = CPU(code=code, heap_data=heap_data, stdout=out, stdin=inp)
    cpu.run()
    return out.getvalue()


# ------------------------------------------------------------------
# Stack ops
# ------------------------------------------------------------------

def test_push_halt():
    code = _pack(OpCode.PUSH, 42, OpCode.HALT)
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 42


def test_pop():
    code = _pack(OpCode.PUSH, 5, OpCode.PUSH, 99, OpCode.POP, OpCode.HALT)
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 5


def test_dup():
    code = _pack(OpCode.PUSH, 7, OpCode.DUP, OpCode.HALT)
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 7
    assert cpu.stack.pop() == 7


def test_swap():
    code = _pack(OpCode.PUSH, 1, OpCode.PUSH, 2, OpCode.SWAP, OpCode.HALT)
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 1
    assert cpu.stack.pop() == 2


# ------------------------------------------------------------------
# Arithmetic
# ------------------------------------------------------------------

def test_iadd():
    code = _pack(OpCode.PUSH, 3, OpCode.PUSH, 4, OpCode.IADD, OpCode.HALT)
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 7


def test_isub():
    code = _pack(OpCode.PUSH, 10, OpCode.PUSH, 3, OpCode.ISUB, OpCode.HALT)
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 7


def test_imul():
    code = _pack(OpCode.PUSH, 6, OpCode.PUSH, 7, OpCode.IMUL, OpCode.HALT)
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 42


def test_idiv():
    code = _pack(OpCode.PUSH, 10, OpCode.PUSH, 3, OpCode.IDIV, OpCode.HALT)
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 3


def test_imod():
    code = _pack(OpCode.PUSH, 10, OpCode.PUSH, 3, OpCode.IMOD, OpCode.HALT)
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 1


def test_ineg():
    code = _pack(OpCode.PUSH, 5, OpCode.INEG, OpCode.HALT)
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == -5


def test_div_by_zero():
    code = _pack(OpCode.PUSH, 5, OpCode.PUSH, 0, OpCode.IDIV, OpCode.HALT)
    cpu = CPU(code)
    with pytest.raises(VMError, match="Division by zero"):
        cpu.run()


# ------------------------------------------------------------------
# Comparison
# ------------------------------------------------------------------

def test_icmp_less():
    code = _pack(OpCode.PUSH, 3, OpCode.PUSH, 5, OpCode.ICMP, OpCode.HALT)
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == -1


def test_icmp_equal():
    code = _pack(OpCode.PUSH, 5, OpCode.PUSH, 5, OpCode.ICMP, OpCode.HALT)
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 0


def test_icmp_greater():
    code = _pack(OpCode.PUSH, 7, OpCode.PUSH, 3, OpCode.ICMP, OpCode.HALT)
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 1


def test_ieq_true():
    code = _pack(OpCode.PUSH, 4, OpCode.PUSH, 4, OpCode.IEQ, OpCode.HALT)
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 1


def test_ieq_false():
    code = _pack(OpCode.PUSH, 4, OpCode.PUSH, 5, OpCode.IEQ, OpCode.HALT)
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 0


def test_ilt():
    code = _pack(OpCode.PUSH, 2, OpCode.PUSH, 5, OpCode.ILT, OpCode.HALT)
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 1


def test_igt():
    code = _pack(OpCode.PUSH, 9, OpCode.PUSH, 3, OpCode.IGT, OpCode.HALT)
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 1


# ------------------------------------------------------------------
# Control flow
# ------------------------------------------------------------------

def test_jump():
    # Layout: PUSH(5) JUMP(5) PUSH(5) HALT(1) — HALT is at byte 15
    halt_addr = 5 + 5 + 5
    code = _pack(
        OpCode.PUSH, 1,
        OpCode.JUMP, halt_addr,
        OpCode.PUSH, 2,
        OpCode.HALT,
    )
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 1
    assert len(cpu.stack) == 0


def test_jtrue_taken():
    # Layout: PUSH(5) PUSH(5) JTRUE(5) PUSH(5) HALT(1) — HALT is at byte 20
    halt_addr = 5 + 5 + 5 + 5
    code = _pack(
        OpCode.PUSH, 1,
        OpCode.PUSH, 1,
        OpCode.JTRUE, halt_addr,
        OpCode.PUSH, 99,
        OpCode.HALT,
    )
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 1
    assert len(cpu.stack) == 0


def test_jfalse_taken():
    # Layout: PUSH(5) PUSH(5) JFALSE(5) PUSH(5) HALT(1) — HALT is at byte 20
    halt_addr = 5 + 5 + 5 + 5
    code = _pack(
        OpCode.PUSH, 1,
        OpCode.PUSH, 0,
        OpCode.JFALSE, halt_addr,
        OpCode.PUSH, 99,
        OpCode.HALT,
    )
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 1
    assert len(cpu.stack) == 0


# ------------------------------------------------------------------
# Local variables
# ------------------------------------------------------------------

def test_store_load():
    code = _pack(
        OpCode.PUSH, 123,
        OpCode.STORE, 0,
        OpCode.LOAD, 0,
        OpCode.HALT,
    )
    cpu = CPU(code)
    cpu.run()
    assert cpu.stack.pop() == 123


# ------------------------------------------------------------------
# I/O
# ------------------------------------------------------------------

def test_print():
    out = run_code([OpCode.PUSH, 42, OpCode.PRINT, OpCode.HALT])
    assert out.strip() == "42"


def test_prints():
    msg = b"Hi\x00"
    out = run_code([OpCode.PUSH, 0, OpCode.PRINTS, OpCode.HALT], heap_data=msg)
    assert out.strip() == "Hi"


def test_read():
    code = _pack(OpCode.READ, OpCode.HALT)
    inp = io.StringIO("7\n")
    cpu = CPU(code, stdin=inp)
    cpu.run()
    assert cpu.stack.pop() == 7


# ------------------------------------------------------------------
# Factorial via CALL / RET
# ------------------------------------------------------------------

def test_factorial_10():
    from src.assembler.codegen import assemble
    from src.vm.cpu import load_bytecode
    from pathlib import Path
    src = Path("programs/factorial.asm").read_text()
    bc = assemble(src)
    heap_data, code, symbols = load_bytecode(bc)
    out = io.StringIO()
    cpu = CPU(code=code, heap_data=heap_data, symbols=symbols, stdout=out)
    cpu.run()
    assert out.getvalue().strip() == "3628800"


def test_fibonacci_10():
    from src.assembler.codegen import assemble
    from src.vm.cpu import load_bytecode
    from pathlib import Path
    src = Path("programs/fibonacci.asm").read_text()
    bc = assemble(src)
    heap_data, code, symbols = load_bytecode(bc)
    out = io.StringIO()
    cpu = CPU(code=code, heap_data=heap_data, symbols=symbols, stdout=out)
    cpu.run()
    assert out.getvalue().strip() == "55"
