"""Oracle VM — command-line interface."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path


def cmd_assemble(args: argparse.Namespace) -> int:
    from .assembler.codegen import assemble
    src = Path(args.source)
    if not src.exists():
        print(f"Error: file not found: {src}", file=sys.stderr)
        return 1
    bytecode = assemble(src.read_text(encoding="utf-8"))
    out = Path(args.output) if args.output else src.with_suffix(".bc")
    out.write_bytes(bytecode)
    print(f"Assembled {src} -> {out}  ({len(bytecode)} bytes)")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from .vm.cpu import CPU, load_bytecode
    bc_path = Path(args.bytecode)
    if not bc_path.exists():
        print(f"Error: file not found: {bc_path}", file=sys.stderr)
        return 1
    raw = bc_path.read_bytes()
    heap_data, code, symbols = load_bytecode(raw)
    cpu = CPU(code=code, heap_data=heap_data, symbols=symbols)
    cpu.run()
    return 0


def cmd_debug(args: argparse.Namespace) -> int:
    from .assembler.codegen import assemble
    from .vm.cpu import CPU, load_bytecode
    from .debugger.repl import DebuggerREPL
    src = Path(args.source)
    if not src.exists():
        print(f"Error: file not found: {src}", file=sys.stderr)
        return 1
    raw = assemble(src.read_text(encoding="utf-8"))
    heap_data, code, symbols = load_bytecode(raw)
    cpu = CPU(code=code, heap_data=heap_data, symbols=symbols)
    DebuggerREPL(cpu).start()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m src.main",
        description="Oracle VM — assemble, run, or debug .asm programs",
    )
    sub = p.add_subparsers(dest="command", required=True)

    asm = sub.add_parser("assemble", aliases=["asm"], help="Assemble a .asm file to bytecode")
    asm.add_argument("source", help="Path to the .asm source file")
    asm.add_argument("-o", "--output", help="Output .bc file path (default: same name)")
    asm.set_defaults(func=cmd_assemble)

    run = sub.add_parser("run", help="Run a compiled .bc bytecode file")
    run.add_argument("bytecode", help="Path to the .bc bytecode file")
    run.set_defaults(func=cmd_run)

    dbg = sub.add_parser("debug", aliases=["dbg"], help="Assemble and debug interactively")
    dbg.add_argument("source", help="Path to the .asm source file")
    dbg.set_defaults(func=cmd_debug)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
