# 02 — `/usr/bin/toolbox-api`

## Identification

| | |
|---|---|
| Size | 6,201,984 bytes |
| Format | ELF32 ARM, EABI5 hard-float, `EXEC` |
| sha256 | `b825b1d296b65d7d31cf77d016f0e98e644ba6f9fea94dd6061c0c91f5300190` |
| Language | **Go 1.13.5** (`.note.go.buildid`, GOPATH-mode build) |
| Linking | dynamic: `libpthread.so.0`, `libc.so.6` (cgo) |
| Symbols | `.symtab` stripped; names recovered from `.gopclntab` |
| Build path | `/firmware/os/output/mcu-cid/build/toolbox-api-0/src/` |

Identity and sha256 from REA `open_binary`; Go version / build-info from REA
`inspect_go_binary`.

## Purpose

A **localhost HTTP service that exposes vehicle "data values" (signals)**,
bridging HTTP ↔ the car's data-value system over **D-Bus** (`com.tesla.Debug`,
`unix:path=/var/run/dbus/system_bus_socket`). It is the backend that Tesla's
service **Toolbox** diagnostic tool talks to.

## Structure (recovered)

`main.*`:

```
main.main
main.runHTTPServer          # HTTP listener (binds 127.0.0.1:<port>)
main.runDVServer            # data-value server
main.logRequest
main.(*DVServer).addVehicleSpecificDataValues
```

Internal application package `internal/app/dvproxy`:

```
dvproxy.(*Proxy).GetDataValue   / getDataValue
dvproxy.(*Proxy).GetDataValues  / getDataValues
dvproxy.(*Proxy).SetDataValue   / setDataValue
```

Tesla internal library: `stash.teslamotors.com/gol/go-datavalue`
(`datavalue.DataValueClient`). Vendored deps include `github.com/godbus/dbus/v5`.

D-Bus / method names seen in `.rodata`:

```
com.tesla.Debug
/get_data_value   /get_data_values   /set_data_value
AsyncGetDataValue AsyncGetDataValues AsyncSetDataValue
get_data_values
```

## Example data-value signals (from `.rodata`)

GUI / vehicle-API signal identifiers the proxy can read/write:

```
GUI_audioVolume          GUI_lockRequest         GUI_factoryMode
GUI_targetVizFps         GUI_useAutopark2        GUI_mirrorFoldRequest
GUI_dasAutoparkStatus    GUI_activeTouchPoints   GUI_seatHeaterRequestLeftRear
GUI_frontDoorPassengerRequest   GUI_easyEntryRequestRightRear
GUI_autopilotCamBlockedNotification   VAPI_navigation
```

## Open threads

- Exact HTTP routes and listen port of `runHTTPServer` (localhost only).
- Access control: what, if anything, gates `SetDataValue` (write path).
- `addVehicleSpecificDataValues` — how the signal set is assembled per vehicle.
