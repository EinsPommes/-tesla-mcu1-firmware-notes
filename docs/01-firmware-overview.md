# 01 — Firmware Overview

## File identification

`2022.8.10.5.mcu1` — 940,724,288 bytes. Despite the `.mcu1` extension it is not
a raw MCU binary but a **SquashFS filesystem image** (the whole device root
filesystem). Magic bytes `68 73 71 73` = `hsqs` (SquashFS, little-endian).

### SquashFS superblock (parsed)

| Field | Offset | Value |
|---|---|---|
| magic | 0x00 | `hsqs` |
| inode_count | 0x04 | 5091 |
| mkfs_time | 0x08 | `0x62FEC25B` = 2022-08-18 UTC |
| block_size | 0x0C | 131072 (128 KiB) |
| frag_count | 0x10 | 452 |
| compression | 0x14 | **5 = LZ4** |
| block_log | 0x16 | 17 (2^17 = 128 KiB) |
| id_count | 0x1A | 30 |
| version | 0x1C | **4.0** |
| bytes_used | 0x28 | `0x373237EF` = 925,528,559 (rest of file is padding) |

Extracted size: **4619 files / 472 dirs / ~1.32 GB** uncompressed.

> **LZ4 gotcha:** SquashFS uses the **raw LZ4 block** format, not the LZ4 frame
> format. `PySquashfsImage` 0.9.0 wrongly calls `lz4.frame` and fails with
> `LZ4F_getFrameInfo failed`. `tools/sqfs_patch.py` monkeypatches it to
> `lz4.block.decompress(src, uncompressed_size=outsize)`.

## Identity (from `/etc`)

| File | Value |
|---|---|
| `/etc/product` | `mcu` |
| `/etc/product-platform` | `cid` |
| `/etc/swver`, `/etc/product-release` | `feature-2022.8.10.5-75-b94e08b2c3` |
| `/etc/commit`, `/etc/linux-release` | `b94e08b2c3be7e6f42eeab442cf219982202e50e` |
| `/etc/release-scope`, `/etc/ui-build` | `PROD` (`TESLA_RELEASE_SCOPE=PROD`) |
| `/etc/build-info` | `…/firmware-repo-feature-2022-8-10-5/…/ui-artifacts/cid-ic.models` |
| `/usr/lib/os-release` | `Buildroot 2019.02.9` |

Platform = **CID** (the Tegra-based MCU1 center display). Architecture: ELF32
ARM, EABI5, hard-float; dynamic loader `ld-linux-armhf.so.3`.

## Top-level layout

```
.overlay  bin  cid-etc  cid-root  deploy  dev  etc  home  ic-etc  ic-root
lib  libexec  mnt  newusr  opt  proc  root  run  sbin  service  sys  tmp
usr  var
```

Notable:

- **`/usr/tesla/UI/`** — Qt-based car GUI: `QtCarServer`, `QtCarCluster`,
  `QtCarSpeechRecognizer`, `QtCarNetManager`, `QtCarAudiod`, `libQtCarGUI.so`, …
- **`/opt/hermes/`** — Tesla connectivity/telemetry stack (`hermes_client`,
  `hermes_proxy`, `hermes_eventlogs`, `hermes_teleforce`, …).
- **`/usr/bin/`** — `autopilot-api`, `toolbox-api`, `mametesla`, `webrtc-comms`,
  `architect`, `compositor`, `dashcamd`, standard Buildroot userland.
- **`/deploy/`** — `cid-kernel.img`, `ic-kernel.img`, `ic-recovery-kernel.img`,
  and `.plf` updater/installer payloads (`fc6050_lucie_128_*`).
- **Nested `*.dirsquashed`** — SquashFS-in-SquashFS blobs for large trees
  (`usr.tesla.UI.assets` 342 MB, `deploy.seed_artifacts_v2` 113 MB,
  `usr.share`, `usr.lib.python3.6`, `usr.lib.perl5`, pinyin/chewing IME data).

The presence of `cid-*` and `ic-*` trees (etc/root/lib/kernel) shows this image
provisions **both** the CID (center display) and the IC (instrument cluster).

## Largest files (top 20)

```
342,532,096  /usr.tesla.UI.assets.dirsquashed
112,893,952  /deploy.seed_artifacts_v2.dirsquashed
 47,370,240  /usr.share.dirsquashed
 36,975,432  /deploy/fc6050_lucie_128_installer_payload.plf
 36,971,732  /deploy/fc6050_lucie_128_updater_usbd_payload.plf
 29,471,844  /usr/lib/libicudata.so.70.1
 27,045,016  /usr/bin/mametesla
 25,521,128  /usr/lib/libWebKit.so.1.0.0
 23,724,516  /usr/tesla/UI/lib/libQtCarGUI.so.1.0.0
 18,722,816  /usr.tesla.UI.lib.sunpinyin.dirsquashed
 14,862,344  /usr/lib/libQtWebKit.so.4.9.4
 14,355,384  /opt/hermes/hermes_client
 14,033,644  /usr/tesla/UI/bin/QtCarSpeechRecognizer
 13,475,020  /usr/tesla/UI/bin/QtCarServer
 12,887,508  /usr/tesla/UI/lib/libQtCarMediaV2.so.1.0.0
 12,849,152  /deploy/cid-kernel.img
 11,942,856  /usr/lib/libavcodec.so.58.91.100
  9,955,128  /opt/hermes/hermes_eventlogs
  9,823,520  /opt/hermes/hermes_proxy
  9,739,100  /usr/lib/libvalhalla.so.0.0.0
```

(`libvalhalla` = the Mapbox Valhalla routing engine; `libWebKit`/`libQtWebKit`
back the browser; `mametesla` is the arcade-emulator easter egg.)

## Toolchain rationale

The work was driven through **REA** (reverse-engineering MCP toolkit); where REA
could not help on this host, companion scripts filled the gap.

**What REA did:**

- `open_binary` — identified each target (ELF32 / ARM / sha256).
- `inspect_go_binary` — confirmed **Go 1.13.5**, GOPATH-mode builds, build-info
  location, for both Go binaries.
- `extract_firmware` (Unblob) — attempted; surfaced the 512 MiB staging cap.

**Where REA stopped on this host:**

- Its **deep decompiler was unavailable for ARM ELF**: the Windows Ghidra
  provider accepts only native PE and raw-6502 (`target_format_unsupported`);
  Hopper is macOS-only; IDA/Kuna not configured. So `binary_overview` /
  `list_strings` / decompilation could not run on these binaries.
- `inspect_with_objdump` needs a local GNU objdump (none on the Windows PATH).
- `extract_firmware` caps staging at 512 MiB — too small for the ~925 MB rootfs.

**Where companion tooling took over:**

- **WSL Debian** `readelf` / `nm` / `strings` for ELF headers and string recon
  (its `objdump` was built without ARM — `can't disassemble for architecture
  UNKNOWN!`).
- Read/extract the SquashFS with `PySquashfsImage` + patched LZ4.
- Recover Go function names from `.gopclntab` (custom parser; `.symtab` stripped)
  and disassemble ARM with **Capstone**.
