# tools

Analysis scripts used for this RE. Pure Python; no ARM toolchain required.
Install into a virtualenv:

```bash
python -m venv .venv
. .venv/Scripts/activate      # Windows ; or: source .venv/bin/activate
pip install -r requirements.txt
```

## SquashFS (read / extract the firmware image)

`sqfs_patch.py` — monkeypatches `PySquashfsImage` to decompress SquashFS **raw
LZ4 blocks** (the library otherwise wrongly uses the LZ4 *frame* format).
Imported by the three scripts below; not run directly.

| Script | Usage |
|---|---|
| `sqfs_tree.py` | `python sqfs_tree.py <image.mcu1>` — totals, top-level entries, largest files |
| `sqfs_cat.py` | `python sqfs_cat.py <image.mcu1> /etc/swver /etc/build-info …` — print files |
| `sqfs_extract.py` | `python sqfs_extract.py <image.mcu1> <outdir> /usr/bin/autopilot-api …` — extract to disk |

## Go ELF analysis (ARM, stripped `.symtab`)

| Script | Usage |
|---|---|
| `elf32.py` | helper: ELF32 section map + uniform `vaddr-foff` delta (imported) |
| `parse_pclntab.py` | `python parse_pclntab.py <binary> <out.json> [name-filter]` — recover func name→addr from `.gopclntab` |
| `csdis.py` | `python csdis.py <binary> <funcs.json> <start-hex> <size-bytes>` — Capstone ARM disasm, annotated with call targets + `.rodata` strings |

Section offsets are read from the ELF automatically, so the Go tools work on any
of the firmware's Go ARM binaries, not just `autopilot-api`. Example:

```bash
python sqfs_extract.py 2022.8.10.5.mcu1 ./bins /usr/bin/autopilot-api
python parse_pclntab.py ./bins/autopilot-api funcs.json sniproxy
python csdis.py ./bins/autopilot-api funcs.json 0x2368a0 848   # proxyConnection
```

## Notes

- `parse_pclntab.py` targets the Go 1.2–1.15 pclntab layout (magic
  `0xfffffffb`), 32-bit. Newer Go (1.16+ / `0xfffffff0`+) has a different header.
- `csdis.py` disassembles in ARM mode (Go emits ARM, not Thumb, for `.text`).
- The environment that produced these results: Windows 11 + Python 3.12;
  WSL Debian only for `readelf`/`nm`/`strings` (its `objdump` had no ARM
  support). None of this touches the vehicle; it is static file analysis.
