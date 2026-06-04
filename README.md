# Greenhouse IoT Monitoring Server v5

> **Genius Olympiad 2025** — Simon Onderisin  
> Centralized IoT server for three greenhouse environments using Raspberry Pi Pico devices.

---

## Overview

This server collects real-time sensor data from three Raspberry Pi Pico devices over TCP, forwards readings to the ThingSpeak cloud platform, sends alerts to Discord, maintains a local CSV backup, and serves a live JSON API for the web dashboard.

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

The server exposes a live JSON endpoint for the web dashboard.

**Endpoint:** `GET http://<server-ip>:8080/data`

**Response:**
```json
{
  "timestamp": "2025-06-04 14:23:01",
  "picos": [
    { "id": 1, "name": "Semi-Closed",   "humidity": 65.5, "temperature": 22.3, "door": 1, "pump": 0, "ram": 45.2 },
    { "id": 2, "name": "Fully-Closed",  "humidity": 78.1, "temperature": 27.8, "door": 0, "pump": 1, "ram": 38.7 },
    { "id": 3, "name": "Free Planting", "humidity": 54.2, "temperature": 19.4, "door": 0, "pump": 0, "ram": 71.3 }
  ]
}
```

CORS is enabled — the dashboard can be opened from any browser on the network.

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
| `control_RPI()` | 3600 s | Pings Pico 1, 2, and 3 — logs online/offline |

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

---

## Requirements

```
aiohttp
```

> `pandas` and `requests` are no longer required — replaced by `csv.writer` and `aiohttp`.

## Running

```bash
pip install aiohttp
python3 server/server.py
```

The server starts 6 async tasks and listens on:
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

© 2025 Simon Onderisin. All rights reserved.
