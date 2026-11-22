# Tesla MCU1 Firmware RE — `2022.8.10.5`

Reverse-engineering notes for a Tesla **MCU1 / CID** firmware image
(`2022.8.10.5.mcu1`). Work-in-progress; documents the file format, the root
filesystem layout, and per-binary analysis.

> **Scope / legal:** Research and documentation of firmware for interoperability
> and security study. This repo contains **no** Tesla binaries, firmware, or
> proprietary code — only original analysis notes and tooling. The image itself
> is excluded via `.gitignore` and must be supplied by the user.

## Target

| | |
|---|---|
| File | `2022.8.10.5.mcu1` (940,724,288 bytes) |
| Container | SquashFS 4.0, **LZ4**, 128 KiB blocks, 5091 inodes, ~925 MB used |
| Platform | Tesla **MCU1 / CID** (Center Information Display, Tegra, ARM `armhf`) |
| Release | `feature-2022.8.10.5-75`, commit `b94e08b2c3…`, scope **PROD** |
| Base OS | Buildroot 2019.02.9, glibc, `ld-linux-armhf.so.3` |
| Build tree | `/firmware/os/output/mcu-cid/` |

See [`docs/01-firmware-overview.md`](docs/01-firmware-overview.md).

## Analyzed components

| Binary | Type | Summary | Notes |
|---|---|---|---|
| `/usr/bin/toolbox-api` | Go 1.13.5 (ARM) | Localhost HTTP API exposing vehicle **data values** via D-Bus `com.tesla.Debug` | [docs/02](docs/02-toolbox-api.md) |
| `/usr/bin/autopilot-api` | Go 1.13.5 (ARM) | **SNI egress proxy**: gives the Autopilot ECU internet access through the MCU, with an SNI allowlist | [docs/03](docs/03-autopilot-api.md), [allowlist](docs/autopilot-api-allowlist.md) |

## Reproducing

Host used: Windows 11 + Python 3.12; WSL Debian for `readelf`/`strings`
(its `objdump` lacked an ARM disassembler, so ARM disassembly is done with
Capstone — see `tools/`).

```powershell
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r tools\requirements.txt
# 1. list the squashfs tree
python tools\sqfs_tree.py <path>\2022.8.10.5.mcu1
# 2. cat identity/config files
python tools\sqfs_cat.py <path>\2022.8.10.5.mcu1 /etc/swver /etc/build-info
# 3. extract a binary
python tools\sqfs_extract.py <path>\2022.8.10.5.mcu1 .\bins /usr/bin/autopilot-api
# 4. recover Go function addresses from .gopclntab
python tools\parse_pclntab.py .\bins\autopilot-api funcs.json sniproxy
# 5. disassemble a function (ARM, with call + rodata annotation)
python tools\csdis.py .\bins\autopilot-api funcs.json 0x2368a0 848
```

See [`tools/README.md`](tools/README.md) for details and the per-binary offset
constants (they differ per binary; derive them with `readelf -S`).

## Toolchain note

Driven through **REA** (reverse-engineering MCP toolkit). REA was used for:

- `open_binary` — format / architecture / sha256 identification of each binary.
- `inspect_go_binary` — confirmed **Go 1.13.5**, GOPATH-mode build, and the
  build-info offsets for both `toolbox-api` and `autopilot-api`.
- `extract_firmware` (Unblob) — attempted whole-image extraction; revealed the
  512 MiB staging cap that made it unsuitable for the ~925 MB rootfs.

REA's **deep decompiler was unavailable on this host**: on Windows its Ghidra
provider accepts only native PE and raw-6502, so the ARM ELF binaries were
rejected (Hopper is macOS-only, IDA/Kuna not configured). The WSL `objdump` was
also built without ARM support. So REA handled identification and Go metadata,
and the ARM disassembly / symbol recovery was done with the companion scripts in
`tools/` (custom `.gopclntab` parser + Capstone). See `docs/01` for the full
rationale.
