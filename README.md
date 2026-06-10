# GreenIOT — Greenhouse Monitoring Server v5

> **Genius Olympiad 2026** — Simon Onderisin  
> Centralized IoT server for three greenhouse environments using Raspberry Pi Pico W devices.

---

## Overview

GreenIOT collects real-time sensor data from three Raspberry Pi Pico W devices, forwards readings to the ThingSpeak cloud platform, maintains a local CSV backup, and serves a live JSON API for the web dashboard and mobile app.

Two operating modes are supported:

| Mode | Transport | Use case |
|------|-----------|----------|
| **WiFi Network** | TCP :9991 over LAN | Full production deployment |
| **USB Serial** | USB-C cable (COM port) | Demo / presentation without WiFi |

---

## Repository Structure

```
├── server/
│   ├── server.py           # WiFi mode — asyncio TCP, HTTP API, ThingSpeak, CSV
│   ├── serial_server.py    # Serial mode — same features, reads from COM port
│   └── requirements.txt    # aiohttp, pyserial
├── pico/
│   ├── main.py             # Pico W firmware — WiFi mode (TCP send)
│   ├── serial_main.py      # Pico W firmware — Serial mode (USB print)
│   ├── servo.py            # Servo motor driver
│   ├── scd4x.py            # SCD4X CO2/temperature sensor driver
│   └── ...                 # Test scripts
├── site/
│   ├── index.html          # Web dashboard + documentation
│   ├── css/style.css
│   └── js/app.js
├── mobile/                 # React Native app (Android + iOS)
│   ├── App.js
│   ├── app.json            # Expo SDK 51 config
│   ├── eas.json            # EAS build profiles
│   └── src/...
├── windows/
│   ├── greeniot_launcher.py  # Windows GUI launcher (WiFi + Serial mode)
│   ├── build_exe.bat         # PyInstaller .exe builder
│   └── README.md
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

### WiFi Mode
```
Pico 1 ──┐
Pico 2 ──┼──► server.py (TCP :9991) ──► ThingSpeak  (every 2 min)
Pico 3 ──┘        │                 ├──► CSV Backup  (every 10 min)
                   └──► HTTP API (:8080) ──► Web Dashboard / Mobile App
```

### Serial / Demo Mode
```
Pico (USB-C) ──► serial_server.py (COM port) ──► ThingSpeak  (every 2 min)
                        │                     ├──► CSV Backup  (every 10 min)
                        └──► HTTP API (:8080) ──► Web Dashboard / Mobile App
```

> **Demo tip:** connect the phone to the laptop's WiFi hotspot, then open the web dashboard or mobile app pointing at the laptop's IP — everything works the same as WiFi mode.

---

## Data Protocol

Both modes use the same plain-text key:value format, one field per line:

```
HM1:65.5
TP1:22.3
DRRS1:1
PS1:0
RAM1:45.2
---
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

All endpoints are on port `8080`. CORS is fully enabled.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/data` | Live sensor readings for all 3 Picos |
| POST | `/door` | Set door override `{pico, value}` |
| GET | `/cmd/{pico_id}` | Current door override for a Pico |
| GET | `/alerts` | Last 100 ThingSpeak failure events |
| GET | `/status` | Server uptime, start time, mode |
| GET | `/ports` | Available COM ports *(serial mode only)* |

### Door control values

| `value` | Action |
|---------|--------|
| `1` | Force open |
| `0` | Force close |
| `null` | Auto (sensor-driven) |

---

## Running

### Install dependencies

```bash
pip install aiohttp pyserial
```

### WiFi mode

```bash
python3 server/server.py
```

### Serial / demo mode

```bash
# Auto-detect Pico COM port
python3 server/serial_server.py

# Or specify port manually
python3 server/serial_server.py COM3        # Windows
python3 server/serial_server.py /dev/ttyACM0  # Linux
```

### Windows GUI launcher

```bash
python windows/greeniot_launcher.py
```

Toggle between **WiFi Network** and **USB Serial** mode with the radio buttons. In serial mode, select the COM port from the dropdown and click **Start Server**.

### Build a standalone Windows .exe

```bash
cd windows
build_exe.bat
```

---

## Web Dashboard

Open `site/index.html` in any browser or deploy to Netlify:

1. Enter the server IP in the **Server IP** field
2. Click **Connect**
3. The dashboard polls every 5 seconds — shows live temperature, humidity, door/pump status, RAM bars, door controls, server uptime, and alert log

---

## Mobile App (Android + iOS)

Source in `mobile/`. Built with React Native / Expo SDK 51.

```bash
cd mobile && npm install

# Development
npx expo start

# Build Android APK
export EXPO_TOKEN=your_token
eas build -p android --profile preview

# Build iOS (TestFlight)
eas build -p ios --profile preview
```

---

## Pico W Firmware

### WiFi mode — `pico/main.py`
- Connects to WiFi on boot, resets if connection fails
- Sends data over TCP to the server every 40 seconds
- Polls `GET /cmd/{id}` every 5 seconds for door override commands

### Serial mode — `pico/serial_main.py`
- No WiFi required — data sent via `print()` over USB serial
- Same sensors, same door logic, same data format
- Flash as `main.py` on the Pico, plug in via USB-C

**Sensors (both modes):**
- SCD4X (I2C) — temperature, GP16 SDA / GP17 SCL
- Analog humidity sensor — ADC on GP27
- Door servo — PWM on GP1
- Pump relay — GP15

**SCD4X fault tolerance:** if the sensor is missing or fails I2C detection, the Pico boots normally and skips temperature/door — all other tasks continue.

---

## Async Tasks

| Task | Interval | Description |
|------|----------|-------------|
| `api_server()` | Continuous | HTTP API on `:8080` |
| `data_recv()` / `serial_recv()` | Continuous | Receives sensor data |
| `data_send()` | 120 s | Pushes to ThingSpeak (4 channels) |
| `backup_data()` | 600 s | Appends to CSV backup |
| `ping_pico()` | 3600 s | Pings each Pico *(WiFi mode only)* |

---

## ThingSpeak Channels

| Channel | Field 1 | Field 2 | Field 3 | Field 4 |
|---------|---------|---------|---------|---------|
| Semi-Closed GH | Humidity | Temperature | Door | Pump |
| Fully-Closed GH | Humidity | Temperature | Door | Pump |
| Free Planting | Humidity | Temperature | Door | Pump |
| Device Health | RAM1 % | RAM2 % | RAM3 % | — |

---

## CSV Backup

File: `backup_data_server.csv` / `backup_data_serial.csv` — written every 10 minutes, capped at 1440 rows (~10 days).

```
Time | Humidity SC | TP SC | DRRS SC | PS SC | HM C | TP C | DRRS C | PS C | HM FREE | TP FREE | DRRS FREE | PS FREE
```

> **Restart-safe:** existing CSV rows are loaded back into memory on startup so history is never lost.

---

© 2026 Simon Onderisin. All rights reserved. — GreenIOT
