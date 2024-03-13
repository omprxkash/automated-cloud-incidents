"""Interactive debugger REPL for Oracle VM -- powered by rich."""
from __future__ import annotations
from ..vm.cpu import CPU
from .inspector import Inspector

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
    _RICH = True
except ImportError:
    _RICH = False

_HELP = """\
  s / step        -- step one instruction
  r / run         -- run until breakpoint or HALT
  b <addr>        -- set breakpoint at address (hex or decimal)
  st / stack      -- print the operand stack
  h / heap        -- hex dump of heap (first 128 bytes)
  reg             -- print IP and call stack depth
  l / list        -- disassemble next 10 instructions
  q / quit        -- exit the debugger
  ? / help        -- show this help
"""


class DebuggerREPL:
    def __init__(self, cpu: CPU) -> None:
        self._cpu = cpu
        self._inspector = Inspector(cpu)
        self._console = Console() if _RICH else None

    def start(self) -> None:
        self._print_banner()
        self._show_listing()
        while True:
            try:
                raw = input("(ovm-dbg) ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not raw:
                continue
            parts = raw.split()
            cmd = parts[0].lower()
            args = parts[1:]
            if cmd in ("q", "quit"):
                break
            elif cmd in ("s", "step"):
                self._cmd_step()
            elif cmd in ("r", "run"):
                self._cmd_run()
            elif cmd == "b":
                self._cmd_break(args)
            elif cmd in ("st", "stack"):
                self._cmd_stack()
            elif cmd in ("h", "heap"):
                self._cmd_heap()
            elif cmd == "reg":
                self._cmd_reg()
            elif cmd in ("l", "list"):
                self._cmd_list()
            elif cmd in ("?", "help"):
                print(_HELP)
            else:
                print(f"Unknown command {cmd!r}. Type ? for help.")

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def _cmd_step(self) -> None:
        if not self._cpu.running and self._cpu.ip >= len(self._cpu.bytecode):
            print("Program has halted.")
            return
        ip_before = self._cpu.ip
        self._cpu.step()
        self._print_state(ip_before)

    def _cmd_run(self) -> None:
        self._cpu.run()
        if not self._cpu.running:
            print("Program halted.")
        else:
            print(f"Stopped at breakpoint: IP={self._cpu.ip:#x}")
        self._show_listing()

    def _cmd_break(self, args: list[str]) -> None:
        if not args:
            bps = sorted(self._cpu._breakpoints)
            if bps:
                print("Breakpoints:", ", ".join(f"{a:#x}" for a in bps))
            else:
                print("No breakpoints set.")
            return
        try:
            addr = int(args[0], 0)
            self._cpu.add_breakpoint(addr)
            print(f"Breakpoint set at {addr:#x}")
        except ValueError:
            print(f"Invalid address: {args[0]!r}")

    def _cmd_stack(self) -> None:
        snap = self._inspector.stack_snapshot()
        if not snap:
            print("Stack is empty.")
            return
        if _RICH and self._console:
            t = Table(title="Operand Stack (top to bottom)", show_header=True)
            t.add_column("Depth", style="dim")
            t.add_column("Value", style="bold cyan")
            for i, v in enumerate(reversed(snap)):
                t.add_row(str(i), str(v))
            self._console.print(t)
        else:
            print("Stack (top to bottom):", list(reversed(snap)))

    def _cmd_heap(self) -> None:
        dump = self._inspector.heap_dump(0, 128)
        if _RICH and self._console:
            self._console.print(Panel(dump, title="Heap dump (0x0000-0x007f)"))
        else:
            print(dump)

    def _cmd_reg(self) -> None:
        ip = self._inspector.ip()
        depth = self._inspector.call_depth()
        names = " -> ".join(self._inspector.call_stack_names())
        print(f"IP={ip:#06x}  call_depth={depth}  frames=[{names}]")

    def _cmd_list(self) -> None:
        self._show_listing()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _show_listing(self) -> None:
        lines = self._inspector.next_instructions(10)
        if _RICH and self._console:
            body = "\n".join(lines) if lines else "<end of bytecode>"
            self._console.print(Panel(body, title=f"Disassembly @ IP={self._cpu.ip:#x}"))
        else:
            for line in lines:
                print(line)

    def _print_state(self, ip_before: int) -> None:
        snap = self._inspector.stack_snapshot()
        ip_now = self._inspector.ip()
        stack_str = str(list(reversed(snap))) if snap else "[]"
        if _RICH and self._console:
            self._console.print(
                f"[dim]{ip_before:#06x}[/dim] -> [bold]{ip_now:#06x}[/bold]  "
                f"stack={stack_str}"
            )
        else:
            print(f"{ip_before:#06x} -> {ip_now:#06x}  stack={stack_str}")
        if not self._cpu.running:
            print("Program halted.")
        else:
            self._show_listing()

    def _print_banner(self) -> None:
        if _RICH and self._console:
            self._console.print(
                Panel(
                    "[bold green]Oracle VM Debugger[/bold green]\n"
                    "Type [bold]?[/bold] for help, [bold]q[/bold] to quit.",
                    title="ovm-dbg",
                )
            )
        else:
            print("Oracle VM Debugger -- type ? for help, q to quit")
