from __future__ import annotations
from .exceptions import HeapError


class SimpleHeap:
    """Flat byte-array heap with a simple free-list allocator.

    The first ``reserved`` bytes (set via ``init_allocator``) are treated as
    a static data section — the allocator never touches them.  Each dynamic
    block carries an 8-byte header: [size: 4 bytes big-endian][in_use: 4 bytes].
    """

    HEADER = 8

    def __init__(self, size: int = 65536) -> None:
        self._mem: bytearray = bytearray(size)
        self._size = size
        self._free: list[tuple[int, int]] = []
        # Allocator not active until init_allocator() is called
        self._initialized = False

    def init_allocator(self, after: int = 0) -> None:
        """Start the dynamic allocator at the first 4-byte-aligned offset after ``after``."""
        start = (after + 3) & ~3
        capacity = self._size - start - self.HEADER
        if capacity <= 0:
            raise HeapError("Heap too small to initialise allocator")
        self._free = [(start, capacity)]
        self._initialized = True

    # ------------------------------------------------------------------
    # Allocation
    # ------------------------------------------------------------------

    def alloc(self, n: int) -> int:
        if not self._initialized:
            raise HeapError("Allocator not initialised — call init_allocator() first")
        if n <= 0:
            raise HeapError("Allocation size must be positive")
        aligned = (n + 3) & ~3
        for i, (hdr, blk_size) in enumerate(self._free):
            if blk_size >= aligned:
                self._free.pop(i)
                remaining = blk_size - aligned - self.HEADER
                if remaining >= 4:
                    next_hdr = hdr + self.HEADER + aligned
                    self._free.insert(i, (next_hdr, remaining))
                self._write_header(hdr, aligned, 1)
                return hdr + self.HEADER
        raise HeapError(f"Out of heap memory (requested {n} bytes)")

    def free(self, addr: int) -> None:
        hdr = addr - self.HEADER
        if hdr < 0:
            raise HeapError(f"Invalid heap address: {addr}")
        size = self._read_uint(hdr)
        in_use = self._read_uint(hdr + 4)
        if not in_use:
            raise HeapError(f"Double-free at address {addr}")
        self._write_header(hdr, size, 0)
        self._free.append((hdr, size))
        self._free.sort(key=lambda x: x[0])
        self._coalesce()

    # ------------------------------------------------------------------
    # Byte / integer / string access
    # ------------------------------------------------------------------

    def read_byte(self, addr: int) -> int:
        self._check(addr, 1)
        return self._mem[addr]

    def write_byte(self, addr: int, value: int) -> None:
        self._check(addr, 1)
        self._mem[addr] = value & 0xFF

    def read_int(self, addr: int) -> int:
        self._check(addr, 4)
        return int.from_bytes(self._mem[addr : addr + 4], "big", signed=True)

    def write_int(self, addr: int, value: int) -> None:
        self._check(addr, 4)
        self._mem[addr : addr + 4] = value.to_bytes(4, "big", signed=True)

    def read_string(self, addr: int) -> str:
        end = addr
        while end < self._size and self._mem[end] != 0:
            end += 1
        return self._mem[addr:end].decode("utf-8", errors="replace")

    def write_string(self, addr: int, s: str) -> None:
        encoded = s.encode("utf-8") + b"\x00"
        if addr + len(encoded) > self._size:
            raise HeapError("String write exceeds heap bounds")
        self._mem[addr : addr + len(encoded)] = encoded

    def write_bytes_raw(self, addr: int, data: bytes) -> None:
        if addr + len(data) > self._size:
            raise HeapError("Raw write exceeds heap bounds")
        self._mem[addr : addr + len(data)] = data

    # ------------------------------------------------------------------
    # Hex dump
    # ------------------------------------------------------------------

    def dump(self, start: int = 0, length: int = 256) -> str:
        lines = []
        for offset in range(0, length, 16):
            addr = start + offset
            if addr >= self._size:
                break
            chunk = self._mem[addr : addr + 16]
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            asc_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            lines.append(f"{addr:04x}  {hex_part:<47}  {asc_part}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check(self, addr: int, size: int) -> None:
        if addr < 0 or addr + size > self._size:
            raise HeapError(f"Heap address out of bounds: {addr}")

    def _read_uint(self, addr: int) -> int:
        return int.from_bytes(self._mem[addr : addr + 4], "big")

    def _write_header(self, hdr: int, size: int, in_use: int) -> None:
        self._mem[hdr : hdr + 4] = size.to_bytes(4, "big")
        self._mem[hdr + 4 : hdr + 8] = in_use.to_bytes(4, "big")

    def _coalesce(self) -> None:
        merged = True
        while merged:
            merged = False
            for i in range(len(self._free) - 1):
                hdr1, sz1 = self._free[i]
                hdr2, sz2 = self._free[i + 1]
                if hdr1 + self.HEADER + sz1 == hdr2:
                    self._free[i] = (hdr1, sz1 + self.HEADER + sz2)
                    self._free.pop(i + 1)
                    merged = True
                    break
