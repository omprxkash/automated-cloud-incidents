class VMError(Exception):
    """Base for all Oracle VM runtime errors."""


class StackOverflowError(VMError):
    """Operand stack exceeded its maximum depth."""


class StackUnderflowError(VMError):
    """Pop or peek on an empty operand stack."""


class HeapError(VMError):
    """Invalid heap access or allocation failure."""


class AssemblerError(Exception):
    """Raised when the assembler cannot parse or compile source."""

    def __init__(self, message: str, line: int = 0):
        super().__init__(f"line {line}: {message}" if line else message)
        self.line = line
