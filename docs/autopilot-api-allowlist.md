# `autopilot-api` — SNI allowlist

Extracted from `internal/app/sniproxy.init` (0x237360). Each entry is a pair of
`.rodata` strings: the bare hostname is the **SNI match key**, the `host:443`
form is the **backend dial target**. Mapping is (almost entirely) identity —
i.e. TLS passthrough to the same host on 443; the proxy's job is allowlisting +
binding egress to the vehicle WiFi interface, not rewriting.

Local listeners: `192.168.90.100:8443` and `192.168.90.100:8444`
(internal MCU↔Autopilot Ethernet).

## Tesla global (`*.ap.tesla.services`)

| SNI | Backend |
|---|---|
| `apmv3.go.tesla.services` | `apmv3.go.tesla.services:443` |
| `api-eng.ap.tesla.services` | `api-eng.ap.tesla.services:443` |
| `api-prd.ap.tesla.services` | `api-prd.ap.tesla.services:443` |
| `telemetry-eng.ap.tesla.services` | `telemetry-eng.ap.tesla.services:443` |
| `telemetry-prd.ap.tesla.services` | `telemetry-prd.ap.tesla.services:443` |
| `hermes-eng.ap.tesla.services` | `hermes-eng.ap.tesla.services:443` |
| `hermes-prd.ap.tesla.services` | `hermes-prd.ap.tesla.services:443` |
| `x1.ap.tesla.services` | `x1.ap.tesla.services:443` |
| `s3.ap.tesla.services` | `s3.ap.tesla.services:443` |
| `*.s3.ap.tesla.services` (wildcard) | — |
| `api-ap-prd.i.tslans.net` | `api-ap-prd.i.tslans.net:443` (internal alias) |

## AWS S3 — Hermes snapshots (US-West-2)

| SNI |
|---|
| `tesla-hermes-snapshot.s3-us-west-2.amazonaws.com` |
| `tesla-hermes-snapshot.s3.us-west-2.amazonaws.com` |
| `tesla-hermes-snapshot-eng.s3-us-west-2.amazonaws.com` |
| `tesla-hermes-snapshot-eng.s3.us-west-2.amazonaws.com` |

## China region

| SNI | Note |
|---|---|
| `api-ap-eng.vn.cloud.tesla.cn` | Autopilot API (eng) |
| `api-ap-prd.vn.cloud.tesla.cn` | Autopilot API (prod) |
| `hermes-ap-eng.vn.cloud.tesla.cn` | Hermes (eng) |
| `hermes-ap-prd.vn.cloud.tesla.cn` | Hermes (prod) |
| `firehose.cn-north-1.amazonaws.com.cn` | AWS Kinesis Firehose |
| `tesla-hermes-clips-cn.s3.cn-north-1.amazonaws.com.cn` | S3 dashcam/clips (CN) |
| `intelligentmap-api.baidu.com` | Baidu maps / navigation |

The binary ships **both** the global `.services` and the China `.cn` endpoint
sets; environment/market selection happens at runtime.
