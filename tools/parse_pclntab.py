"""Recover Go function name -> entry address from a stripped ELF's .gopclntab.

Works on Go 1.2-1.15 pclntab (magic 0xfffffffb / 0xfffffffa), which is what the
Tesla MCU1 Go 1.13.5 ARM binaries use. `.symtab` is stripped in these images,
but the pclntab still holds every function name.

Usage:
    python parse_pclntab.py <binary> <out.json> [name-substring-filter]
"""
import json
import struct
import sys
from pathlib import Path

import elf32


def parse(path: str | Path) -> list[dict[str, object]]:
    secs = elf32.sections(path)
    pcln = secs[".gopclntab"]
    data = Path(path).read_bytes()
    base = data[pcln["foff"]:pcln["foff"] + pcln["size"]]

    magic = struct.unpack_from("<I", base, 0)[0]
    ptrsize = base[7]
    if magic not in (0xFFFFFFFB, 0xFFFFFFFA):
        raise ValueError(f"unexpected pclntab magic {magic:#x}")
    if ptrsize != 4:
        raise ValueError(f"only 32-bit pclntab supported, got ptrsize={ptrsize}")

    def u32(off: int) -> int:
        return struct.unpack_from("<I", base, off)[0]

    def cstr(off: int) -> str:
        end = base.index(b"\x00", off)
        return base[off:end].decode("utf8", "replace")

    nfunc = u32(8)
    ftab = 12
    funcs: list[tuple[int, str]] = []
    for i in range(nfunc):
        entry = u32(ftab + i * 8)
        funcoff = u32(ftab + i * 8 + 4)
        nameoff = u32(funcoff + 4)  # _func.nameoff at +ptrsize
        funcs.append((entry, cstr(nameoff)))

    maxpc = u32(ftab + nfunc * 8)
    funcs.sort()
    result: list[dict[str, object]] = []
    for i, (entry, name) in enumerate(funcs):
        nxt = funcs[i + 1][0] if i + 1 < len(funcs) else maxpc
        result.append({"addr": entry, "size": nxt - entry, "name": name})
    return result


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit("usage: parse_pclntab.py <binary> <out.json> [name-filter]")
    binary, out_json = sys.argv[1], sys.argv[2]
    funcs = parse(binary)
    Path(out_json).write_text(json.dumps(funcs), encoding="utf8")
    print(f"nfunc={len(funcs)} -> {out_json}")
    if len(sys.argv) > 3:
        needle = sys.argv[3].lower()
        for e in funcs:
            if needle in str(e["name"]).lower():
                print(f"0x{e['addr']:08x}  size={e['size']:>6}  {e['name']}")


if __name__ == "__main__":
    main()
