import pytest
from src.vm.stack import OperandStack
from src.vm.exceptions import StackOverflowError, StackUnderflowError


def test_push_pop():
    s = OperandStack()
    s.push(42)
    assert s.pop() == 42


def test_push_multiple():
    s = OperandStack()
    for v in [1, 2, 3]:
        s.push(v)
    assert s.pop() == 3
    assert s.pop() == 2
    assert s.pop() == 1


def test_peek_does_not_remove():
    s = OperandStack()
    s.push(99)
    assert s.peek() == 99
    assert s.peek() == 99
    assert len(s) == 1


def test_dup():
    s = OperandStack()
    s.push(7)
    s.dup()
    assert s.pop() == 7
    assert s.pop() == 7


def test_swap():
    s = OperandStack()
    s.push(10)
    s.push(20)
    s.swap()
    assert s.pop() == 10
    assert s.pop() == 20


def test_overflow():
    s = OperandStack(max_size=3)
    s.push(1)
    s.push(2)
    s.push(3)
    with pytest.raises(StackOverflowError):
        s.push(4)


def test_underflow_pop():
    s = OperandStack()
    with pytest.raises(StackUnderflowError):
        s.pop()


def test_underflow_peek():
    s = OperandStack()
    with pytest.raises(StackUnderflowError):
        s.peek()


def test_underflow_swap():
    s = OperandStack()
    s.push(1)
    with pytest.raises(StackUnderflowError):
        s.swap()


def test_snapshot():
    s = OperandStack()
    s.push(1)
    s.push(2)
    snap = s.snapshot()
    assert snap == [1, 2]
    s.push(3)
    assert snap == [1, 2]  # snapshot is a copy


def test_negative_values():
    s = OperandStack()
    s.push(-100)
    assert s.pop() == -100


def test_len():
    s = OperandStack()
    assert len(s) == 0
    s.push(0)
    assert len(s) == 1
    s.pop()
    assert len(s) == 0
