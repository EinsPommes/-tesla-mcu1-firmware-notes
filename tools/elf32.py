"""Minimal ELF32 section-header reader (no external deps).

Returns, for a little-endian ELF32 image, a map of section name -> dict with
vaddr, foff and size, so the Go-analysis tools can locate .gopclntab/.rodata/
.text without hardcoded offsets.
"""
import struct
from pathlib import Path


def sections(path: str | Path) -> dict[str, dict[str, int]]:
    data = Path(path).read_bytes()
    if data[:4] != b"\x7fELF" or data[4] != 1:
        raise ValueError("not an ELF32 image")
    # ELF32 header fields we need
    e_shoff = struct.unpack_from("<I", data, 0x20)[0]
    e_shentsize = struct.unpack_from("<H", data, 0x2e)[0]
    e_shnum = struct.unpack_from("<H", data, 0x30)[0]
    e_shstrndx = struct.unpack_from("<H", data, 0x32)[0]

    def shdr(i: int) -> dict[str, int]:
        off = e_shoff + i * e_shentsize
        name, _type, _flags, addr, offset, size = struct.unpack_from("<IIIIII", data, off)
        return {"name_off": name, "vaddr": addr, "foff": offset, "size": size}

    strtab = shdr(e_shstrndx)
    strbase = strtab["foff"]

    def nm(name_off: int) -> str:
        end = data.index(b"\x00", strbase + name_off)
        return data[strbase + name_off:end].decode("ascii", "replace")

    out = {}
    for i in range(e_shnum):
        s = shdr(i)
        out[nm(s["name_off"])] = {"vaddr": s["vaddr"], "foff": s["foff"], "size": s["size"]}
    return out


def load_delta(secs: dict[str, dict[str, int]]) -> int:
    """Uniform vaddr - foff for load sections (Go/ARM images use one value)."""
    t = secs[".text"]
    return t["vaddr"] - t["foff"]
