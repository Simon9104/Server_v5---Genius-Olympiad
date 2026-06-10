import asyncio
import csv
import datetime
import json
import os
import socket
from collections import deque

import aiohttp
from aiohttp import web

print('System is starting right now!!!!')
print('All rights reserved by Simon Onderisin ® 2026')
print('Any way of copying this code is strictly prohibited!!!!')

# ── Network ───────────────────────────────────────────────────────────────────
SERVER_HOST = '0.0.0.0'
SERVER_PORT  = 9991
API_PORT     = 8080          # HTTP API for the live dashboard
RECV_BUFFER  = 2048

PICO_IPS = {
    1: '192.168.1.59',
    2: '192.168.1.118',
    3: '192.168.1.118',
}

# ── ThingSpeak ────────────────────────────────────────────────────────────────
THINGSPEAK_URL = 'https://api.thingspeak.com/update'
TS_KEYS = {
    'semi_closed':  'XRHM95UX4K3FVX0J',
    'fully_closed': 'VT7JT0U9KSCCYMTG',
    'free_planting':'KK2CRU2B3CKZW40C',
    'ram':          'ENMLII2NCVO8DNZM',
}

# ── Netlify cloud sync ────────────────────────────────────────────────────────
NETLIFY_URL   = os.environ.get('GREENIOT_NETLIFY_URL', '')   # e.g. https://yoursite.netlify.app
NETLIFY_TOKEN = os.environ.get('GREENIOT_TOKEN', '')
NETLIFY_HEADERS = {'x-greeniot-token': NETLIFY_TOKEN, 'Content-Type': 'application/json'}

# ── Intervals (seconds) ───────────────────────────────────────────────────────
INTERVAL_THINGSPEAK = 120
INTERVAL_BACKUP     = 600
INTERVAL_PING       = 3600

# ── Network resilience ────────────────────────────────────────────────────────
HTTP_TIMEOUT    = aiohttp.ClientTimeout(total=10)
MAX_RETRIES     = 3
RETRY_BACKOFF   = (2, 4, 8)   # seconds between retry attempts

# ── Sensor state (arrays indexed 0=Pico1, 1=Pico2, 2=Pico3) ──────────────────
state = {
    'hm':   [0.0, 0.0, 0.0],
    'temp': [0.0, 0.0, 0.0],
    'door': [0.0, 0.0, 0.0],
    'pump': [0.0, 0.0, 0.0],
    'ram':  [None, None, None],
}
seq = {k: [0, 0, 0] for k in state}

# ── Door override — persistent per Pico (null=auto, 0=close, 1=open) ─────────
door_override = [None, None, None]

SERVER_START_TIME = datetime.datetime.now()

# ── Alert log — recent ThingSpeak failure events ──────────────────────────────
alert_log: deque = deque(maxlen=100)

# ── CSV backup — rolling window, never holds more than MAX_ROWS in RAM ────────
MAX_BACKUP_ROWS = 1440          # ~10 days at 10-min intervals
backup_rows: deque = deque(maxlen=MAX_BACKUP_ROWS)
if os.path.exists('backup_data_server.csv'):
    with open('backup_data_server.csv', 'r', newline='') as _f:
        _reader = csv.reader(_f)
        next(_reader, None)
        for _row in _reader:
            backup_rows.append(_row)
CSV_COLUMNS = [
    'Time',
    'Humidity SC', 'TP SC', 'DRRS SC', 'PS SC',
    'HM C',        'TP C',  'DRRS C',  'PS C',
    'HM FREE',     'TP FREE','DRRS FREE','PS FREE',
]

# ── TCP server ────────────────────────────────────────────────────────────────
tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcp_server.bind((SERVER_HOST, SERVER_PORT))
tcp_server.listen(5)
tcp_server.setblocking(False)

# ── Parse incoming line ───────────────────────────────────────────────────────
_PREFIX_MAP = {
    'HM1':   ('hm',   0), 'HM2':   ('hm',   1), 'HM3':   ('hm',   2),
    'TP1':   ('temp', 0), 'TP2':   ('temp', 1), 'TP3':   ('temp', 2),
    'DRRS1': ('door', 0), 'DRRS2': ('door', 1), 'DRRS3': ('door', 2),
    'PS1':   ('pump', 0), 'PS2':   ('pump', 1), 'PS3':   ('pump', 2),
    'RAM1':  ('ram',  0), 'RAM2':  ('ram',  1), 'RAM3':  ('ram',  2),
}
_LABEL = {
    'hm': 'Humidity', 'temp': 'Temperature',
    'door': 'Door status', 'pump': 'Pump status', 'ram': 'RAM usage',
}
_PICO_NAME = ['First', 'Second', 'Third']

def parse_line(line: str) -> None:
    if ':' not in line:
        return
    key, _, raw = line.partition(':')
    entry = _PREFIX_MAP.get(key.strip())
    if entry is None:
        return
    field, idx = entry
    try:
        value = float(raw.strip())
    except ValueError:
        return
    state[field][idx] = value
    seq[field][idx]  += 1
    print(f"{seq[field][idx]}. {_LABEL[field]} — {_PICO_NAME[idx]} Pico: {value}")
    print('-' * 33)

# ── Async HTTP helpers (non-blocking, with retry + backoff) ───────────────────
async def http_get(session: aiohttp.ClientSession, url: str, params: dict) -> bool:
    for attempt, delay in enumerate(RETRY_BACKOFF, 1):
        try:
            async with session.get(url, params=params, timeout=HTTP_TIMEOUT) as resp:
                return resp.status == 200
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            print(f'HTTP GET attempt {attempt}/{MAX_RETRIES} failed: {e}')
            if attempt < MAX_RETRIES:
                await asyncio.sleep(delay)
    return False

# ── Tasks ─────────────────────────────────────────────────────────────────────
async def data_recv() -> None:
    loop = asyncio.get_event_loop()
    while True:
        try:
            client, _addr = await loop.sock_accept(tcp_server)
            try:
                data = await asyncio.wait_for(
                    loop.sock_recv(client, RECV_BUFFER), timeout=5
                )
            finally:
                client.close()
            for line in data.decode(errors='ignore').strip().split('\n'):
                parse_line(line)
        except asyncio.TimeoutError:
            print('data_recv: client timed out, dropped.')
        except Exception as e:
            print(f'data_recv error: {e}')
        await asyncio.sleep(0)


async def data_send(session: aiohttp.ClientSession) -> None:
    await asyncio.sleep(INTERVAL_THINGSPEAK)
    channels = [
        ('semi_closed',   0, 'Semi-Closed'),
        ('fully_closed',  1, 'Fully-Closed'),
        ('free_planting', 2, 'Free Planting'),
    ]
    while True:
        for ch_key, i, name in channels:
            ok = await http_get(session, THINGSPEAK_URL, {
                'api_key': TS_KEYS[ch_key],
                'field1':  state['hm'][i],
                'field2':  state['temp'][i],
                'field3':  state['door'][i],
                'field4':  state['pump'][i],
            })
            if ok:
                print(f'ThingSpeak [{name}]: sent.')
            else:
                print(f'ThingSpeak [{name}]: FAILED after {MAX_RETRIES} retries.')
                alert_log.append({'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'msg': f'ThingSpeak FAILED — {name}'})

        ok_ram = await http_get(session, THINGSPEAK_URL, {
            'api_key': TS_KEYS['ram'],
            'field1':  state['ram'][0] if state['ram'][0] is not None else 0,
            'field2':  state['ram'][1] if state['ram'][1] is not None else 0,
            'field3':  state['ram'][2] if state['ram'][2] is not None else 0,
        })
        if not ok_ram:
            print(f'ThingSpeak [RAM]: FAILED after {MAX_RETRIES} retries.')
            alert_log.append({'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'msg': 'ThingSpeak FAILED — RAM'})

        await asyncio.sleep(INTERVAL_THINGSPEAK)


async def netlify_sync(session: aiohttp.ClientSession) -> None:
    if not NETLIFY_URL or not NETLIFY_TOKEN:
        print('Netlify sync disabled — set GREENIOT_NETLIFY_URL and GREENIOT_TOKEN env vars.')
        return
    await asyncio.sleep(INTERVAL_THINGSPEAK)
    while True:
        try:
            payload = {
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'picos': [
                    {
                        'id': i + 1,
                        'name': name,
                        'humidity':    state['hm'][i],
                        'temperature': state['temp'][i],
                        'door':        state['door'][i],
                        'pump':        state['pump'][i],
                        'ram':         state['ram'][i],
                    }
                    for i, name in enumerate(['Semi-Closed', 'Fully-Closed', 'Free Planting'])
                ],
            }
            async with session.post(
                f'{NETLIFY_URL}/api/update',
                json=payload,
                headers=NETLIFY_HEADERS,
                timeout=HTTP_TIMEOUT,
            ) as resp:
                if resp.status == 200:
                    print('Netlify sync: OK')
                else:
                    print(f'Netlify sync: failed ({resp.status})')
                    alert_log.append({'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                      'msg': f'Netlify sync FAILED — HTTP {resp.status}'})
        except Exception as e:
            print(f'Netlify sync error: {e}')
        await asyncio.sleep(INTERVAL_THINGSPEAK)


async def backup_data() -> None:
    await asyncio.sleep(INTERVAL_BACKUP)
    while True:
        s = state
        row = [
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            s['hm'][0],   s['temp'][0], s['door'][0], s['pump'][0],
            s['hm'][1],   s['temp'][1], s['door'][1], s['pump'][1],
            s['hm'][2],   s['temp'][2], s['door'][2], s['pump'][2],
        ]
        backup_rows.append(row)
        # Write incrementally — no DataFrame allocation
        with open('backup_data_server.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_COLUMNS)
            writer.writerows(backup_rows)
        print('Backup saved.')
        print('-' * 33)
        await asyncio.sleep(INTERVAL_BACKUP)


# ── HTTP API ──────────────────────────────────────────────────────────────────
async def api_data(_req: web.Request) -> web.Response:
    payload = {
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'picos': [
            {
                'id': i + 1,
                'name': name,
                'humidity':    state['hm'][i],
                'temperature': state['temp'][i],
                'door':        state['door'][i],
                'pump':        state['pump'][i],
                'ram':         state['ram'][i],
            }
            for i, name in enumerate(['Semi-Closed', 'Fully-Closed', 'Free Planting'])
        ],
    }
    return web.Response(
        text=json.dumps(payload),
        content_type='application/json',
        headers={'Access-Control-Allow-Origin': '*'},
    )

async def api_door(req: web.Request) -> web.Response:
    cors = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Content-Type'}
    if req.method == 'OPTIONS':
        return web.Response(headers=cors)
    try:
        body  = await req.json()
        pico  = int(body['pico']) - 1           # 1-based → 0-based
        value = body.get('value')               # null = auto, 0 = close, 1 = open
        if pico not in (0, 1, 2):
            raise ValueError
        if value is not None:
            value = int(value)
            if value not in (0, 1):
                raise ValueError
    except Exception:
        return web.Response(status=400, text='Bad request', headers=cors)
    door_override[pico] = value              # persist until changed again
    action = 'AUTO' if value is None else ('OPEN' if value == 1 else 'CLOSE')
    print(f'Door override: Pico {pico+1} → {action}')
    print('-' * 33)
    return web.Response(text=json.dumps({'ok': True}), content_type='application/json', headers=cors)

async def api_cmd(req: web.Request) -> web.Response:
    cors = {'Access-Control-Allow-Origin': '*'}
    pico_id = int(req.match_info['pico_id']) - 1
    # Return current override — persistent, not cleared after read
    return web.Response(
        text=json.dumps({'door': door_override[pico_id]}),
        content_type='application/json',
        headers=cors,
    )

async def api_alerts(_req: web.Request) -> web.Response:
    return web.Response(
        text=json.dumps(list(alert_log)),
        content_type='application/json',
        headers={'Access-Control-Allow-Origin': '*'},
    )

async def api_status(_req: web.Request) -> web.Response:
    uptime = datetime.datetime.now() - SERVER_START_TIME
    hours, rem = divmod(int(uptime.total_seconds()), 3600)
    minutes = rem // 60
    return web.Response(
        text=json.dumps({
            'started': SERVER_START_TIME.strftime('%Y-%m-%d %H:%M:%S'),
            'uptime': f'{hours}h {minutes}m',
        }),
        content_type='application/json',
        headers={'Access-Control-Allow-Origin': '*'},
    )

async def api_server() -> None:
    app = web.Application()
    app.router.add_get('/data', api_data)
    app.router.add_get('/alerts', api_alerts)
    app.router.add_get('/status', api_status)
    app.router.add_post('/door', api_door)
    app.router.add_options('/door', api_door)
    app.router.add_get('/cmd/{pico_id}', api_cmd)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, SERVER_HOST, API_PORT)
    await site.start()
    print(f'API server running on http://{SERVER_HOST}:{API_PORT}/data')
    print('-' * 33)

async def ping_pico(index: int) -> None:
    ip   = PICO_IPS[index + 1]
    name = _PICO_NAME[index]
    while True:
        proc = await asyncio.create_subprocess_shell(
            f'ping -c 1 -W 2 {ip}',
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        status = 'ONLINE' if proc.returncode == 0 else 'OFFLINE — check connection!'
        print(f'{name} Pico ({ip}): {status}')
        print('-' * 33)
        await asyncio.sleep(INTERVAL_PING)


def print_banner() -> None:
    os.system('clear')
    GREEN  = '\033[92m'
    CYAN   = '\033[96m'
    YELLOW = '\033[93m'
    WHITE  = '\033[97m'
    DIM    = '\033[2m'
    RESET  = '\033[0m'
    BOLD   = '\033[1m'

    banner = f"""
{GREEN}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  {CYAN}{BOLD} ██████╗ ██████╗ ███████╗███████╗███╗   ██╗{GREEN}                ║
║  {CYAN}{BOLD}██╔════╝ ██╔══██╗██╔════╝██╔════╝████╗  ██║{GREEN}                ║
║  {CYAN}{BOLD}██║  ███╗██████╔╝█████╗  █████╗  ██╔██╗ ██║{GREEN}                ║
║  {CYAN}{BOLD}██║   ██║██╔══██╗██╔══╝  ██╔══╝  ██║╚██╗██║{GREEN}                ║
║  {CYAN}{BOLD}╚██████╔╝██║  ██║███████╗███████╗██║ ╚████║{GREEN}                ║
║  {CYAN}{BOLD} ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝{GREEN}                ║
║  {CYAN}{BOLD}██╗ ██████╗ ████████╗{GREEN}                                       ║
║  {CYAN}{BOLD}██║██╔═══██╗╚══██╔══╝{GREEN}                                       ║
║  {CYAN}{BOLD}██║██║   ██║   ██║   {GREEN}                                       ║
║  {CYAN}{BOLD}██║██║   ██║   ██║   {GREEN}                                       ║
║  {CYAN}{BOLD}██║╚██████╔╝   ██║   {GREEN}                                       ║
║  {CYAN}{BOLD}╚═╝ ╚═════╝    ╚═╝   {GREEN}                                       ║
║                                                              ║
║   {YELLOW}{BOLD}              GreenIOT  v6.0{GREEN}                            ║
║   {WHITE}{DIM}         Genius Olympiad 2026 — Simon Onderisin{GREEN}           ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  {WHITE}  TCP  {GREEN}│{WHITE} 0.0.0.0:{CYAN}9991{GREEN}          Pico data intake             ║
║  {WHITE}  API  {GREEN}│{WHITE} 0.0.0.0:{CYAN}8080{GREEN}          Live dashboard API            ║
║  {WHITE}  CSV  {GREEN}│{WHITE} backup_data_server.csv{GREEN}   Rolling 10-day log         ║
║  {WHITE} PICOS {GREEN}│{WHITE} Pico 1 · Pico 2 · Pico 3{GREEN}                            ║
║                                                              ║
║  {DIM}{WHITE}All rights reserved © 2026 Simon Onderisin{GREEN}                  ║
║  {DIM}{WHITE}Any copying of this code is strictly prohibited.{GREEN}            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{RESET}
"""
    print(banner)
    rows_loaded = len(backup_rows)
    if rows_loaded:
        print(f'{YELLOW}  ↺  Loaded {rows_loaded} backup rows from previous session.{RESET}')
    netlify_status = NETLIFY_URL if NETLIFY_URL else 'disabled (set GREENIOT_NETLIFY_URL)'
    print(f'  NETLIFY │ {netlify_status}')
    print(f'{GREEN}  ✔  System starting…{RESET}\n')


async def main() -> None:
    print_banner()

    connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(api_server())
            tg.create_task(data_recv())
            tg.create_task(data_send(session))
            tg.create_task(netlify_sync(session))
            tg.create_task(backup_data())
            for i in range(3):
                tg.create_task(ping_pico(i))


asyncio.run(main())
