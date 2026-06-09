# GreenIOT — Windows Server Launcher

A desktop GUI app for running the GreenIOT server on Windows.

## Run directly (no build needed)

```
pip install aiohttp
python greeniot_launcher.py
```

## Build a standalone .exe

```
build_exe.bat
```

Requires Python + pip. The `.exe` will appear in `windows/dist/`.  
No Python installation needed on the target machine after building.

## Features

- **Start / Stop** the server with one click
- **Live log output** with colour-coded lines (green = OK, yellow = warning, red = error)
- **Local IP** shown at the top so you know what to enter in the mobile app
- **Dashboard link** — shows the direct URL to the live JSON feed
- Detects if the server crashes and updates the status indicator

## Requirements

- Python 3.11+
- `aiohttp` (`pip install aiohttp`)
- `server/server.py` present in the repository (the launcher finds it automatically)
