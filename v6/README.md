# GreenIOT v6 — Netlify Cloud Sync

v6 builds on all v5 features and adds **Netlify cloud sync**, enabling the dashboard to be accessed publicly from any device — not just on the local network.

## What's new in v6

- Every 120 seconds the Python server POSTs sensor data to a Netlify Function (`/api/update`)
- Netlify Functions store data in **Netlify Blobs** (key: `"latest"`)
- A public Netlify dashboard reads live data from `/api/data`
- The local dashboard at `:8080` continues to work exactly as before
- Door control works both ways: local `POST /door` and Netlify `POST /api/door`
- Dashboard has a **Local / Cloud toggle** — enter your Netlify URL and click "Use Cloud"

## Running the server

### 1. Set environment variables

```bash
export GREENIOT_NETLIFY_URL=https://yoursite.netlify.app
export GREENIOT_TOKEN=your-secret-token
```

If these are not set, Netlify sync is disabled and the server runs in local-only mode (all v5 behaviour).

### 2. Start the server

```bash
cd v6/server
pip install aiohttp
python server.py
```

The banner will show the Netlify URL status. Local TCP (:9991) and HTTP API (:8080) work as normal.

## Deploying to Netlify

1. Push the `v6/` directory to a GitHub repo (or point Netlify at this repo with base directory `v6/`)
2. In the Netlify dashboard → **Site settings → Environment variables**, add:
   - `GREENIOT_TOKEN` — the same secret token you set on the server
3. Deploy. Netlify will detect `netlify.toml`, build the static site from `v6/site/`, and deploy the functions from `v6/netlify/functions/`.

## Dashboard Local/Cloud toggle

Open `index.html` (local `:8080` or deployed Netlify URL):

- **Local mode** (default): enter your server's LAN IP and click "Connect"
- **Cloud mode**: enter your Netlify URL (e.g. `https://yoursite.netlify.app`) and click "Use Cloud"

In cloud mode all data fetches go to Netlify Functions (`/api/data`, `/api/alerts`, `/api/status`). Door commands go to `/api/door` — note these require the `x-greeniot-token` header, so door control from the public dashboard will only work if you add token support to the frontend or proxy through a trusted backend.

## API endpoints (Netlify Functions)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/update` | Receives sensor payload from server (token required) |
| GET | `/api/data` | Returns latest sensor data (public) |
| GET | `/api/status` | Returns last sync time and data availability (public) |
| GET | `/api/alerts` | Returns alert log (public) |
| POST | `/api/alerts` | Appends an alert (token required) |
| GET | `/api/door?pico=1` | Returns current door override for a Pico (public) |
| POST | `/api/door` | Sets door override (token required) |

## Project structure

```
v6/
├── netlify.toml               # Netlify build config
├── package.json               # @netlify/blobs dependency
├── netlify/
│   └── functions/
│       ├── update.js          # Receives data from server
│       ├── data.js            # Serves latest data to dashboard
│       ├── door.js            # Door override read/write
│       ├── alerts.js          # Alert log read/write
│       └── status.js          # Sync status
├── server/
│   └── server.py              # Python asyncio server (v5 + Netlify sync)
└── site/
    ├── index.html             # Dashboard (Local/Cloud toggle added)
    ├── _redirects
    ├── css/style.css
    └── js/app.js              # Cloud mode fetch logic added
```

---
All rights reserved © 2026 Simon Onderisin. Any copying of this code is strictly prohibited.
