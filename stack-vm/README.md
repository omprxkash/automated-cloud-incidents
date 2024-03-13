# Oracle VM

A learning-grade stack-based virtual machine — complete with its own bytecode instruction set, an assembler that turns `.asm` source into bytecode, an interpreter that runs it, and an interactive debugger you can step through.  Think of it as a tiny JVM you can read in an afternoon.

---

## What it does

I built this to understand how virtual machines actually work underneath all the abstraction.  Oracle VM gives you:

- **25+ opcodes** covering arithmetic, comparison, local variables, heap arrays, control flow, I/O, and heap management
- **A two-pass assembler** — lexer → parser → codegen — that compiles `.asm` text to compact bytecode files
- **A stack-based CPU** with an operand stack, a call stack of activation frames, and a 64 KB heap with a free-list allocator
- **An interactive debugger REPL** (powered by `rich`) with step, breakpoints, stack/heap/register inspection, and live disassembly
- **Four sample programs** — hello world, iterative factorial, recursive Fibonacci, and bubble sort on a heap array

---

## Quick start

```bash
pip install -r requirements.txt

# Assemble a program
python -m src.main assemble programs/factorial.asm -o factorial.bc

# Run it
python -m src.main run factorial.bc
# → 3628800

# Debug it interactively
python -m src.main debug programs/fibonacci.asm
```

---

## Usage

```
python -m src.main assemble <file.asm> [-o <file.bc>]
python -m src.main run <file.bc>
python -m src.main debug <file.asm>
```

### Debugger commands

| Command | What it does |
|---------|-------------|
| `s` / `step` | Execute one instruction |
| `r` / `run` | Run until a breakpoint or HALT |
| `b <addr>` | Set a breakpoint at an address (hex or decimal) |
| `st` / `stack` | Print the operand stack |
| `h` / `heap` | Hex dump of the first 128 heap bytes |
| `reg` | Print IP and call stack depth |
| `l` / `list` | Disassemble the next 10 instructions |
| `q` / `quit` | Exit |

---

## Writing assembly

Source files use a two-section format:

```asm
.data
  greeting "Hello, Oracle VM!"   ; null-terminated string

.code
main:
  PUSH greeting   ; push the heap address of the string
  PRINTS          ; print it
  HALT
```

Labels work as jump targets and as data references.  Comments start with `;`.

### A real example — iterative factorial

```asm
.code
main:
  PUSH 10
  CALL factorial
  PRINT
  HALT

factorial:
  STORE 0        ; local[0] = n
  PUSH 1
  STORE 1        ; local[1] = result = 1
loop:
  LOAD 0
  PUSH 1
  IGT            ; n > 1?
  JFALSE done
  LOAD 1
  LOAD 0
  IMUL
  STORE 1        ; result *= n
  LOAD 0
  PUSH 1
  ISUB
  STORE 0        ; n -= 1
  JUMP loop
done:
  LOAD 1
  RET
```

---

## How it works

```
  .asm source
      │
      ▼
  ┌─────────┐     ┌─────────┐     ┌──────────┐
  │  Lexer  │ ──▶ │  Parser │ ──▶ │  CodeGen │
  └─────────┘     └─────────┘     └──────────┘
                                       │ .bc file
                                       ▼
                              ┌─────────────────┐
                              │       CPU        │
                              │  operand stack   │
                              │  call frames     │
                              │  heap            │
                              └─────────────────┘
```

The assembler runs in two passes: first it collects all label addresses, then it emits bytecode with forward references resolved.  The `.bc` file has a small header (magic, sizes), a static data blob for strings, the instruction bytes, and a symbol table so the debugger can show label names.

The CPU executes one instruction per `step()` call.  Each call frame has its own local variable table, so recursive calls get independent state.  The heap starts with a static region for `.data` strings and grows dynamically through ALLOC/FREE.

Full architecture details are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Instruction set summary

| Group | Opcodes |
|-------|---------|
| Stack | `PUSH` `POP` `DUP` `SWAP` |
| Arithmetic | `IADD` `ISUB` `IMUL` `IDIV` `IMOD` `INEG` |
| Comparison | `ICMP` `IEQ` `ILT` `IGT` |
| Local vars | `LOAD` `STORE` |
| Heap arrays | `ALOAD` `ASTORE` |
| Control | `JUMP` `JTRUE` `JFALSE` `CALL` `RET` |
| I/O | `PRINT` `PRINTS` `READ` |
| Heap | `ALLOC` `FREE` |
| System | `HALT` |

Full stack-effect documentation: [docs/INSTRUCTION_SET.md](docs/INSTRUCTION_SET.md)

---

## Project structure

```
orcale-virtual-machine/
├── src/
│   ├── vm/
│   │   ├── opcodes.py      OpCode enum
│   │   ├── cpu.py          fetch–decode–execute loop
│   │   ├── stack.py        operand stack
│   │   ├── heap.py         heap + allocator
│   │   ├── frame.py        call frame / local variables
│   │   └── exceptions.py   VMError, StackOverflowError, …
│   ├── assembler/
│   │   ├── lexer.py        tokeniser
│   │   ├── parser.py       AST builder
│   │   └── codegen.py      two-pass bytecode emitter
│   ├── debugger/
│   │   ├── inspector.py    state reader + disassembler
│   │   └── repl.py         rich interactive REPL
│   └── main.py             CLI entry point
├── programs/
│   ├── hello.asm
│   ├── factorial.asm
│   ├── fibonacci.asm
│   └── bubble_sort.asm
├── tests/
│   ├── test_stack.py
│   ├── test_cpu.py
│   ├── test_assembler.py
│   └── test_programs.py
└── docs/
    ├── INSTRUCTION_SET.md
    └── ARCHITECTURE.md
```

---

## Testing

```bash
pytest --tb=short -q
# or with coverage
pytest --cov=src --cov-report=term-missing
```

The test suite covers individual opcodes, the full assembler pipeline, and all four sample programs end-to-end (including recursive Fibonacci and 10! = 3 628 800).

---

## Known limitations

- Integers are Python's arbitrary-precision ints — there's no real 32-bit overflow behaviour
- The heap allocator uses first-fit and can fragment under heavy churn
- No garbage collection — everything allocated must be manually `FREE`d
- No type system — the stack holds raw integers; strings live only on the heap
- `READ` expects well-formed integer input; bad input raises a `VMError`
