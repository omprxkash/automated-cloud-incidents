from enum import IntEnum


class OpCode(IntEnum):
    # Stack operations
    PUSH   = 0x01
    POP    = 0x02
    DUP    = 0x03
    SWAP   = 0x04

    # Integer arithmetic
    IADD   = 0x10
    ISUB   = 0x11
    IMUL   = 0x12
    IDIV   = 0x13
    IMOD   = 0x14
    INEG   = 0x15

    # Comparison
    ICMP   = 0x20
    IEQ    = 0x21
    ILT    = 0x22
    IGT    = 0x23

    # Local variable memory
    LOAD   = 0x30
    STORE  = 0x31
    ALOAD  = 0x32
    ASTORE = 0x33

    # Control flow
    JUMP   = 0x40
    JTRUE  = 0x41
    JFALSE = 0x42
    CALL   = 0x43
    RET    = 0x44

    # I/O
    PRINT  = 0x50
    PRINTS = 0x51
    READ   = 0x52

    # Heap management
    ALLOC  = 0x60
    FREE   = 0x61

    # Halt
    HALT   = 0xFF


# Opcodes that carry a 4-byte integer operand in the bytecode stream
OPERAND_OPCODES = frozenset({
    OpCode.PUSH,
    OpCode.LOAD,
    OpCode.STORE,
    OpCode.JUMP,
    OpCode.JTRUE,
    OpCode.JFALSE,
    OpCode.CALL,
})
