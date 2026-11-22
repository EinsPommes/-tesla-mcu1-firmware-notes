# 03 — `/usr/bin/autopilot-api`

## Identification

| | |
|---|---|
| Size | 4,885,128 bytes |
| Format | ELF32 ARM, EABI5 hard-float, `EXEC`, entry `0x6b384` |
| sha256 | `7cb8e7619a7eb2e22fdc8131e0ed0941d52f42510235c5e2105090b4f6f8900f` |
| Language | **Go 1.13.5** (GOPATH-mode build) |
| Linking | dynamic: `libpthread.so.0`, `libc.so.6` (cgo) |
| Symbols | `.symtab` stripped; names recovered from `.gopclntab` (5619 funcs) |
| Build path | `/firmware/os/output/mcu-cid/build/autopilot-api-0/src/` |

Identity and sha256 from REA `open_binary`; Go version / build-info from REA
`inspect_go_binary`. Deep decompilation was not available (see `docs/01`), so
function recovery and ARM disassembly used the `tools/` scripts.

## Purpose

Despite the name this is **not** driving/autopilot logic. It is the
**network egress gateway for the Autopilot computer (APE)**: a TLS **SNI proxy**
that lets the AP ECU reach the internet through the MCU's modem/WiFi, while an
**SNI allowlist** restricts which destinations the AP may reach.

## Section map (for tooling)

```
.text        vaddr 0x00011000  foff 0x001000  size 0x227de0
.rodata      vaddr 0x00240000  foff 0x230000  size 0x0dfbee
.gopclntab   vaddr 0x00322cc0  foff 0x312cc0  size 0x15a3bf
.noptrdata   vaddr 0x00480150  foff 0x470150
.data        vaddr 0x004b2cf0  foff 0x4a2cf0
```

Uniform `vaddr − foff = 0x10000` for all load sections (used by `tools/csdis.py`).

## Structure (recovered)

```
main.main                 # starts 2x sniproxy.NewServer goroutines + multiproxy.New + http
main.logRequest

internal/app/sniproxy
  .NewServer              0x235d64  builds SNI->backend map; local binds 192.168.90.100:8443 / :8444
  .(*Server).Run          0x23604c
  .(*Server).runfrontend  0x236318  accept loop, 1 goroutine per connection
  .getWifiAddr            0x23660c  source address of the vehicle WiFi interface
  .(*Server).proxyConnection 0x2368a0  dial backend (WiFi-bound) + splice
  .(*Server).joinConnections 0x236bf0  bidirectional copy
  .init                   0x237360  builds the allowlist (SNI + backend host:443 pairs)
  .frontend, .defaultFrontend

internal/app/httpproxy        (reverse HTTP proxy, New/init)
internal/pkg/multiproxy       New / splitPath / newDirector / newDirector.func1
internal/app/simpletime
```

## Data path (from disassembly)

### `runfrontend` (accept loop)
Logs `"Handling connections to %v"`, `"Accepted new connection for %v from %v"`,
spawns a goroutine (→ `proxyConnection`) per accepted connection; on error
`"Failed to accept new connection for '%v': %v"`.

### `NewServer`
Builds a `map[string]string` (SNI hostname → backend `host:443`) via
`runtime.makemap_small` + `mapassign_faststr`. Local listener bind addresses are
**`192.168.90.100:8443`** and **`192.168.90.100:8444`** — Tesla's internal
MCU↔Autopilot Ethernet link. `main.main` starts two servers (one per port).

### `proxyConnection` (core, 0x2368a0)
```
getWifiAddr()                              ; source IP = vehicle WiFi interface
net.DialTimeout / Dialer.DialContext(...)  ; dial backend, source-bound to WiFi
  on error -> log "Failed to dial backend connection, wifi: %v %v: %v"
  on ok    -> log "Initiated new connection to backend: %v %v"
             joinConnections(front, back)  ; splice both directions
unmatched SNI -> defaultFrontend
```

TLS is terminated end-to-end by the AP computer and the real backend; this proxy
only reads the **cleartext SNI** from the ClientHello, enforces the allowlist,
and binds egress to the WiFi interface. It does not MITM.

Annotated disassembly excerpt of `proxyConnection`:

```
2368d4  bl   getWifiAddr
236988  ldr  r3, ="Failed to dial backend connection, wifi: %v %v: %v"
2369ac  bl   log.(*Logger).Printf
236a6c  ldr  r2, ="Initiated new connection to backend: %v %v"
236a90  bl   log.(*Logger).Printf
236abc  bl   sniproxy.(*Server).joinConnections
236b40  bl   net.(*Dialer).DialContext
236b98  bl   net.DialTimeout
```

## Allowlist

The complete SNI allowlist and backend mapping is in
[`autopilot-api-allowlist.md`](autopilot-api-allowlist.md) (and `.csv`).

## Open threads

- `multiproxy.newDirector.func1` — the HTTP path-based routing of the
  `ServeMux` side (`splitPath`), not yet disassembled.
- How the two servers (`:8443` vs `:8444`) partition the allowlist, and the
  exact `defaultFrontend` behavior for an unlisted SNI (reject vs default dial).
- `httpproxy` (the `internal/app` one) role vs the TLS/SNI path.
