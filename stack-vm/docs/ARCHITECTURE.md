# Oracle VM — Architecture

## Overview

Oracle VM is a stack-based virtual machine inspired by the JVM.  Source code written in a simple assembly language is compiled to compact bytecode, then executed by a software CPU that manages its own operand stack, call frames, and heap.

## Pipeline

```
  .asm source
      │
      ▼
  ┌─────────┐
  │  Lexer  │  tokenise: directives, mnemonics, labels, literals
  └────┬────┘
       │ token list
       ▼
  ┌─────────┐
  │  Parser │  produce AST: DataSection + CodeSection
  └────┬────┘
       │ Program AST
       ▼
  ┌──────────┐
  │  CodeGen │  two-pass: collect labels → emit bytecode
  └────┬─────┘
       │ .bc file bytes
       ▼
  ┌────────────────────────────────┐
  │             CPU                │
  │  ┌──────────┐  ┌────────────┐ │
  │  │  Operand │  │ Call Stack │ │
  │  │  Stack   │  │ (frames)   │ │
  │  └──────────┘  └────────────┘ │
  │  ┌──────────────────────────┐ │
  │  │          Heap            │ │
  │  │  static data │ allocator │ │
  │  └──────────────────────────┘ │
  └────────────────────────────────┘
```

## Components

### Assembler (`src/assembler/`)

**Lexer** (`lexer.py`) — scans source text character by character and produces a flat list of typed tokens.  Comments (`;`) are stripped.  Recognises directives (`.data`, `.code`), label definitions (`name:`), mnemonics (`PUSH`, `IADD`, …), integer literals (decimal and hex), and string literals.

**Parser** (`parser.py`) — consumes the token list and builds a two-section AST.  The `.data` section holds named string definitions; the `.code` section holds label markers and instructions with optional operands.  Validates that operand-bearing mnemonics actually have an operand.

**CodeGen** (`codegen.py`) — two-pass compilation.

- *Pass 1*: lay out the `.data` section as a flat byte blob, assign each string label a heap offset.  Walk the `.code` section to record each label's byte offset.
- *Pass 2*: emit bytecode, resolving label operands to their recorded offsets.

Output is a `.bc` file: 16-byte header + static data + code bytes + symbol table.

### Virtual Machine (`src/vm/`)

**OpCode** (`opcodes.py`) — `IntEnum` of all 25+ opcodes.

**OperandStack** (`stack.py`) — fixed-capacity integer stack with overflow/underflow detection.

**SimpleHeap** (`heap.py`) — flat `bytearray` divided into a static region (strings) and a dynamic region managed by a first-fit free-list allocator.  Each dynamic block carries an 8-byte header (size + in-use flag).

**CallFrame** (`frame.py`) — activation record holding a local-variable table (dict of int → int) and the return address.

**CPU** (`cpu.py`) — fetch–decode–execute loop.  Reads bytecode bytes sequentially (`ip` register), dispatches each opcode, manipulates the stack, heap, and call frame.  Supports `run()` (to HALT or breakpoint) and `step()` (one instruction, for the debugger).

### Debugger (`src/debugger/`)

**Inspector** (`inspector.py`) — reads live CPU state and provides a `disassemble()` function that walks bytecode and formats each instruction with its mnemonic, operand, and resolved label name.

**DebuggerREPL** (`repl.py`) — interactive command loop built on `rich`.  Presents the disassembly, operand stack, heap dump, and register state in formatted panels and tables.

## Memory layout at runtime

```
Heap (65 536 bytes)
┌────────────────────────────────────────┐
│  0x0000  Static data (.data strings)   │
│          null-terminated, packed       │
├────────────────────────────────────────┤
│  aligned  Dynamic allocations         │
│           [8-byte header | user data]  │
│           ...                          │
└────────────────────────────────────────┘
```

## Call convention

Arguments are pushed onto the operand stack before `CALL`.  The first instruction of a function typically uses `STORE` to move arguments into local variables.  Return values are left on the operand stack when `RET` executes.  There is no separate argument-passing register.
