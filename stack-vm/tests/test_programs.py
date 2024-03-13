"""End-to-end tests: assemble each sample program and verify its output."""
import io
from pathlib import Path
import pytest
from src.assembler.codegen import assemble
from src.vm.cpu import CPU, load_bytecode


def _run_asm(name: str) -> str:
    src = (Path("programs") / name).read_text(encoding="utf-8")
    bc = assemble(src)
    heap_data, code, symbols = load_bytecode(bc)
    out = io.StringIO()
    cpu = CPU(code=code, heap_data=heap_data, symbols=symbols, stdout=out)
    cpu.run()
    return out.getvalue().strip()


def test_hello():
    result = _run_asm("hello.asm")
    assert result == "Hello, Oracle VM!"


def test_factorial():
    result = _run_asm("factorial.asm")
    assert result == "3628800"


def test_fibonacci():
    result = _run_asm("fibonacci.asm")
    assert result == "55"


def test_bubble_sort():
    result = _run_asm("bubble_sort.asm")
    lines = result.splitlines()
    assert lines == ["1", "2", "3", "5", "8", "9"]
