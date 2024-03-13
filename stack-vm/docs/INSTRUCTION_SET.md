# Oracle VM — Instruction Set Reference

All integers are 32-bit signed big-endian.  The operand stack grows upward; "top" means the most recently pushed value.

## Notation

| Symbol | Meaning |
|--------|---------|
| `a`, `b` | Values popped from the operand stack (b = top, a = second) |
| `→` | Stack effect (left side = before, right side = after) |
| `[idx]` | Local variable at index *idx* in the current frame |
| `H[addr]` | 32-bit integer at heap address *addr* |

---

## Stack operations

| Hex | Mnemonic | Operand | Stack effect | Notes |
|-----|----------|---------|--------------|-------|
| 0x01 | `PUSH` | int32 | `→ n` | Push literal integer |
| 0x02 | `POP` | — | `a →` | Discard top |
| 0x03 | `DUP` | — | `a → a a` | Duplicate top |
| 0x04 | `SWAP` | — | `a b → b a` | Swap top two values |

---

## Integer arithmetic

All arithmetic operations pop two values (b = top, a = second) and push one result.

| Hex | Mnemonic | Stack effect | Notes |
|-----|----------|--------------|-------|
| 0x10 | `IADD` | `a b → a+b` | |
| 0x11 | `ISUB` | `a b → a−b` | subtracts top from second |
| 0x12 | `IMUL` | `a b → a×b` | |
| 0x13 | `IDIV` | `a b → a÷b` | truncates toward zero; raises on div-by-zero |
| 0x14 | `IMOD` | `a b → a mod b` | raises on mod-by-zero |
| 0x15 | `INEG` | `a → −a` | unary negation; pops one |

---

## Comparison

Pop two values (b = top, a = second), push result.

| Hex | Mnemonic | Stack effect | Notes |
|-----|----------|--------------|-------|
| 0x20 | `ICMP` | `a b → r` | r = −1 if a<b, 0 if a==b, 1 if a>b |
| 0x21 | `IEQ` | `a b → r` | r = 1 if a==b, else 0 |
| 0x22 | `ILT` | `a b → r` | r = 1 if a<b, else 0 |
| 0x23 | `IGT` | `a b → r` | r = 1 if a>b, else 0 |

---

## Local variables

Each call frame has its own local variable table, indexed by a non-negative integer.  Uninitialized locals default to 0.

| Hex | Mnemonic | Operand | Stack effect | Notes |
|-----|----------|---------|--------------|-------|
| 0x30 | `LOAD` | int32 idx | `→ [idx]` | Push local variable |
| 0x31 | `STORE` | int32 idx | `a →` | Pop into local variable |
| 0x32 | `ALOAD` | — | `base idx → H[base + idx×4]` | Array element read |
| 0x33 | `ASTORE` | — | `base idx val →` | Array element write |

> **ASTORE pops order:** value first (top), then index, then base.

---

## Control flow

| Hex | Mnemonic | Operand | Stack effect | Notes |
|-----|----------|---------|--------------|-------|
| 0x40 | `JUMP` | int32 addr | — | Unconditional jump |
| 0x41 | `JTRUE` | int32 addr | `a →` | Jump if a ≠ 0 |
| 0x42 | `JFALSE` | int32 addr | `a →` | Jump if a == 0 |
| 0x43 | `CALL` | int32 addr | — | Push call frame, jump to addr |
| 0x44 | `RET` | — | — | Pop call frame, return to caller |

> Arguments are passed on the operand stack and must be consumed by the callee (typically with `STORE`).  Return values are left on the operand stack.

---

## I/O

| Hex | Mnemonic | Stack effect | Notes |
|-----|----------|--------------|-------|
| 0x50 | `PRINT` | `a →` | Print integer followed by newline |
| 0x51 | `PRINTS` | `addr →` | Print null-terminated UTF-8 string from heap |
| 0x52 | `READ` | `→ n` | Read one integer from stdin |

---

## Heap management

| Hex | Mnemonic | Stack effect | Notes |
|-----|----------|--------------|-------|
| 0x60 | `ALLOC` | `size → addr` | Allocate *size* bytes; return base address |
| 0x61 | `FREE` | `addr →` | Free previously allocated block |

---

## Halt

| Hex | Mnemonic | Notes |
|-----|----------|-------|
| 0xFF | `HALT` | Stop execution |

---

## Bytecode file format (`.bc`)

```
Offset  Size  Field
0       4     Magic: 0x4F 0x56 0x4D 0x01  ("OVM\x01")
4       4     data_size  — bytes of static heap data
8       4     code_size  — bytes of executable code
12      4     sym_size   — bytes of symbol table (UTF-8 text)
16      *     static heap data (strings from .data section)
16+d    *     bytecode instructions
16+d+c  *     symbol table: "name=addr\nname=addr\n..."
```
