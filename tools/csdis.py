"""Annotated ARM disassembly of a Go function from a stripped ELF.

Uses Capstone (no ARM objdump needed). Annotates branch/call targets with the
function names recovered by parse_pclntab.py, and resolves PC-relative literal
loads that point into .rodata to the string they reference.

Usage:
    python csdis.py <binary> <funcs.json> <start-hex> <size-bytes>
"""
import bisect
import json
import struct
import sys
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN, Cs

import elf32


class Image:
    def __init__(self, path: str | Path, funcs_json: str | Path) -> None:
        self.data = Path(path).read_bytes()
        secs = elf32.sections(path)
        self.delta = elf32.load_delta(secs)
        ro = secs[".rodata"]
        self.ro_lo = ro["vaddr"]
        self.ro_hi = ro["vaddr"] + ro["size"]
        funcs = json.loads(Path(funcs_json).read_text(encoding="utf8"))
        self.byaddr: dict[int, str] = {int(f["addr"]): str(f["name"]) for f in funcs}
        self.faddrs: list[int] = sorted(self.byaddr)

    def word(self, vaddr: int) -> int | None:
        off = vaddr - self.delta
        if 0 <= off <= len(self.data) - 4:
            return struct.unpack_from("<I", self.data, off)[0]
        return None

    def rostr(self, vaddr: int, maxlen: int = 80) -> str | None:
        off = vaddr - self.delta
        if not 0 <= off < len(self.data):
            return None
        out = bytearray()
        for b in self.data[off:off + maxlen]:
            if 32 <= b < 127:
                out.append(b)
            else:
                break
        return out.decode("ascii", "replace") if out else None

    def name_for(self, addr: int) -> str | None:
        if addr in self.byaddr:
            return self.byaddr[addr]
        i = bisect.bisect_right(self.faddrs, addr) - 1
        if i >= 0 and addr - self.faddrs[i] < 0x4000:
            return f"{self.byaddr[self.faddrs[i]]}+0x{addr - self.faddrs[i]:x}"
        return None


def disassemble(img: Image, start: int, size: int) -> None:
    code = img.data[start - img.delta:start - img.delta + size]
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
    for ins in md.disasm(code, start):
        note = ""
        mn, op = ins.mnemonic, ins.op_str
        if (mn in ("bl", "blx", "b", "bx") or mn.startswith("b.")) and "#0x" in op:
            try:
                target = int(op.split("#")[-1], 16)
            except ValueError:
                target = None
            if target is not None and (name := img.name_for(target)):
                note = f"   ; -> {name}"
        if mn == "ldr" and "[pc, #" in op:
            try:
                imm = int(op.split("[pc, #")[1].rstrip("]!"), 0)
            except (ValueError, IndexError):
                imm = None
            if imm is not None:
                pool = (ins.address & ~3) + 8 + imm
                w = img.word(pool)
                if w is not None:
                    if img.ro_lo <= w < img.ro_hi and (s := img.rostr(w)):
                        note = f'   ; =0x{w:x} "{s}"'
                    elif name := img.name_for(w):
                        note = f"   ; =0x{w:x} &{name}"
                    else:
                        note = f"   ; =0x{w:x}"
        print(f"  {ins.address:08x}:  {mn:<7} {op}{note}")


def main() -> None:
    if len(sys.argv) != 5:
        sys.exit("usage: csdis.py <binary> <funcs.json> <start-hex> <size-bytes>")
    img = Image(sys.argv[1], sys.argv[2])
    disassemble(img, int(sys.argv[3], 16), int(sys.argv[4]))


if __name__ == "__main__":
    main()
