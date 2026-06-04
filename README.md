# Greenhouse IoT Monitoring Server v5

> **Genius Olympiad 2026** — Simon Onderisin  
> Centralized IoT server for three greenhouse environments using Raspberry Pi Pico W devices.

---

## Overview

This server collects real-time sensor data from three Raspberry Pi Pico W devices over TCP, forwards readings to the ThingSpeak cloud platform, sends alerts to Discord, maintains a local CSV backup, and serves a live JSON API for the web dashboard.

---

## Repository Structure

```
├── server/
│   ├── server.py       # Main server — asyncio, TCP, HTTP API, ThingSpeak, Discord
│   └── config.py       # Discord tokens (not tracked by git — create locally)
├── pico/
│   ├── main.py         # Pico W main program — sensors, servo, pump, TCP send
│   ├── servo.py        # Servo motor driver
│   ├── scd4x.py        # SCD4X CO2/temperature/humidity sensor driver
│   ├── skuska_rele_BIO.py  # Relay test script
│   ├── server.py       # Early Pico socket test
│   └── try.py          # Early Pico socket test
├── index.html          # Documentation website + live dashboard
├── .gitignore
└── README.md
```

---

## Devices

| Device | IP Address | Environment |
|--------|-----------|-------------|
| Pico 1 | `192.168.1.59` | Semi-Closed Greenhouse |
| Pico 2 | `192.168.1.118` | Fully-Closed Greenhouse |
| Pico 3 | `192.168.1.118` | Free Planting Area |

---

## Data Flow

```
Pico 1 ──┐
Pico 2 ──┼──► Python Server (TCP :9991) ──► ThingSpeak  (every 2 min)
Pico 3 ──┘        │                     ├──► Discord     (every 2 hr)
                   │                     ├──► CSV Backup  (every 10 min)
                   └──► HTTP API (:8080) ──► Live Dashboard (browser)
```

---

## TCP Protocol

Each Pico connects to port `9991` and sends plain-text key-value pairs, one per line:

```
HM1:65.5
TP1:22.3
DRRS1:1
PS1:0
RAM1:45.2
```

| Prefix | Sensor | Unit |
|--------|--------|------|
| `HM1/2/3:` | Humidity | % |
| `TP1/2/3:` | Temperature | °C |
| `DRRS1/2/3:` | Door / Relay Status | 0 or 1 |
| `PS1/2/3:` | Pump Status | 0 or 1 |
| `RAM1/2/3:` | Device RAM Usage | % |

---

## HTTP API

The server exposes a live JSON API for the web dashboard and door control.

### `GET /data`

**Endpoint:** `GET http://<server-ip>:8080/data`

**Response:**
```json
{
  "timestamp": "2026-06-04 14:23:01",
  "picos": [
    { "id": 1, "name": "Semi-Closed",   "humidity": 65.5, "temperature": 22.3, "door": 1, "pump": 0, "ram": 45.2 },
    { "id": 2, "name": "Fully-Closed",  "humidity": 78.1, "temperature": 27.8, "door": 0, "pump": 1, "ram": 38.7 },
    { "id": 3, "name": "Free Planting", "humidity": 54.2, "temperature": 19.4, "door": 0, "pump": 0, "ram": 71.3 }
  ]
}
```

CORS is enabled — the dashboard can be opened from any browser on the network.

### `POST /door`

Control a Pico's door servo remotely.

```json
{ "pico": 1, "value": 1 }
```

| `value` | Action |
|---------|--------|
| `1` | Force open |
| `0` | Force close |
| `null` | Auto (sensor-driven) |

### `GET /cmd/{pico_id}`

Picos poll this endpoint every 5 seconds to receive the current door override.

```json
{ "door": 1 }
```

The override persists until explicitly changed — it is not cleared after the Pico reads it.

---

## Live Dashboard

Open `index.html` in any browser on the same network:

1. Enter the server IP in the **Server IP** field
2. Click **Connect**
3. The dashboard polls the API every 5 seconds and shows live readings for all 3 Picos — temperature, humidity, door/pump status, and RAM usage with colour-coded bars

---

## Async Tasks

| Task | Interval | Description |
|------|----------|-------------|
| `api_server()` | Continuous | Serves live JSON on `http://0.0.0.0:8080/data` |
| `data_recv()` | Continuous | Listens for incoming TCP data from all Picos |
| `data_send()` | 120 s | Pushes sensor data to ThingSpeak (4 channels) |
| `transfer_discord()` | 7200 s | Posts RAM usage summary to Discord |
| `backup_data()` | 600 s | Appends snapshot to `backup_data_server.csv` |
| `ping_pico()` | 3600 s | Pings Pico 1, 2, and 3 — logs online/offline |

---

## ThingSpeak Channels

| Variable | Channel | Field 1 | Field 2 | Field 3 | Field 4 |
|----------|---------|---------|---------|---------|---------|
| `API1` | Semi-Closed GH | Humidity | Temperature | Door | Pump |
| `API2` | Fully-Closed GH | Humidity | Temperature | Door | Pump |
| `API3` | Free Planting | Humidity | Temperature | Door | Pump |
| `API_RAM` | Device Health | RAM1 % | RAM2 % | RAM3 % | — |

---

## CSV Backup Schema

File: `backup_data_server.csv` — written every 10 minutes, capped at 1440 rows (~10 days).

```
Time | Humidity SC | TP SC | DRRS SC | PS SC | HM C | TP C | DRRS C | PS C | HM FREE | TP FREE | DRRS FREE | PS FREE
```

**Legend:** SC = Semi-Closed · C = Fully-Closed · FREE = Free Planting  
**Columns:** HM = Humidity · TP = Temperature · DRRS = Door/Relay · PS = Pump

> **Restart-safe:** on startup the server loads existing CSV rows back into memory before writing, so history is never lost across restarts.

---

## Pico W — `pico/main.py`

The Pico W program reads sensors and sends data to the server every 40 seconds.

**Sensors used:**
- SCD4X (I2C) — temperature (GP16 SDA, GP17 SCL)
- Analog humidity sensor — ADC on GP27
- Door servo — PWM on GP1
- Pump relay — GP15

**SCD4X fault tolerance:** if the sensor is not connected or fails I2C detection, the Pico boots normally — temperature and door control are skipped, all other tasks keep running.

**WiFi:** connects on boot with a 15-second timeout. Calls `machine.reset()` if connection fails.

---

## Requirements

```
aiohttp
```

> `pandas` and `requests` are no longer required — replaced by `csv.writer` and `aiohttp`.

## Running

1. Install dependencies and start:

```bash
pip install aiohttp
python3 server/server.py
```

On startup the terminal displays a colour ASCII banner with system info, port assignments, and how many backup rows were restored from the previous session.

The server listens on:
- **TCP `:9991`** — receives sensor data from Picos
- **HTTP `:8080`** — serves live JSON for the dashboard

---

## Documentation Website

Open `index.html` in any browser for the full visual overview including:
- System architecture and data flow diagram
- TCP protocol reference
- ThingSpeak channel mapping
- Async task schedule
- CSV schema
- MicroPython sender code for each Pico
- **Live sensor dashboard** (requires server running)

---

© 2026 Simon Onderisin. All rights reserved.
