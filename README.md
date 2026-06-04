# Greenhouse IoT Monitoring Server v5

> **Genius Olympiad 2025** — Simon Onderisin  
> Centralized IoT server for three greenhouse environments using Raspberry Pi Pico devices.

---

## Overview

This server collects real-time sensor data from three Raspberry Pi Pico devices over TCP, forwards readings to the ThingSpeak cloud platform, sends alerts to Discord, and maintains a local CSV backup.

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
Pico 3 ──┘                              ├──► Discord     (every 2 hr)
                                         └──► CSV Backup  (every 10 min)
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

## Async Tasks

| Task | Interval | Description |
|------|----------|-------------|
| `data_recv()` | Continuous | Listens for incoming TCP data from all Picos |
| `data_send()` | 120 s | Pushes sensor data to ThingSpeak (4 channels) |
| `transfer_discord()` | 7200 s | Posts RAM usage summary to Discord |
| `backup_data()` | 600 s | Appends snapshot to `backup_data_server.csv` |
| `control_RPI()` | 3600 s | Pings Pico 1 and logs online/offline status |
| `control_RPI2()` | 3600 s | Pings Pico 2 |
| `control_RPI3()` | 3600 s | Pings Pico 3 |

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

File: `backup_data_server.csv`

```
Time | Humidity SC | TP SC | DRRS SC | PS SC | HM C | TP C | DRRS C | PS C | HM FREE | TP FREE | DRRS FREE | PS FREE
```

**Legend:** SC = Semi-Closed · C = Fully-Closed · FREE = Free Planting  
**Columns:** HM = Humidity · TP = Temperature · DRRS = Door/Relay · PS = Pump

---

## Requirements

```
python3
requests
pandas
```

## Running

```bash
python3 server.py
```

The server binds to `0.0.0.0:9991` and starts all 7 async tasks automatically.

---

## Documentation Website

Open `index.html` in any browser for a full visual overview of the system architecture, data flow, and protocol reference.

---

© 2025 Simon Onderisin. All rights reserved.
