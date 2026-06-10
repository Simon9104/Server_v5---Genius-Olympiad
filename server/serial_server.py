import asyncio
import csv
import datetime
import json
import os
import sys
from collections import deque

import aiohttp
from aiohttp import web
import serial
import serial.tools.list_ports

print('GreenIOT Serial Server starting…')
print('All rights reserved by Simon Onderisin ® 2026')

# ── Config ────────────────────────────────────────────────────────────────────
API_PORT    = 8080
RECV_BUFFER = 2048

# COM port can be overridden by first CLI argument: python serial_server.py COM3
SERIAL_PORT = sys.argv[1] if len(sys.argv) > 1 else None
BAUD_RATE   = 115200

# ── ThingSpeak ────────────────────────────────────────────────────────────────
THINGSPEAK_URL = 'https://api.thingspeak.com/update'
TS_KEYS = {
    'semi_closed':  'XRHM95UX4K3FVX0J',
    'fully_closed': 'VT7JT0U9KSCCYMTG',
    'free_planting':'KK2CRU2B3CKZW40C',
    'ram':          'ENMLII2NCVO8DNZM',
}

# ── Intervals (seconds) ───────────────────────────────────────────────────────
INTERVAL_THINGSPEAK = 120
INTERVAL_BACKUP     = 600

# ── Network resilience ────────────────────────────────────────────────────────
HTTP_TIMEOUT  = aiohttp.ClientTimeout(total=10)
MAX_RETRIES   = 3
RETRY_BACKOFF = (2, 4, 8)

# ── Sensor state ─────────────────────────────────────────────────────────────
state = {
    'hm':   [0.0, 0.0, 0.0],
    'temp': [0.0, 0.0, 0.0],
    'door': [0.0, 0.0, 0.0],
    'pump': [0.0, 0.0, 0.0],
    'ram':  [None, None, None],
}
seq = {k: [0, 0, 0] for k in state}

door_override   = [None, None, None]
SERVER_START_TIME = datetime.datetime.now()
alert_log: deque = deque(maxlen=100)

# ── CSV backup ────────────────────────────────────────────────────────────────
MAX_BACKUP_ROWS = 1440
backup_rows: deque = deque(maxlen=MAX_BACKUP_ROWS)
if os.path.exists('backup_data_serial.csv'):
    with open('backup_data_serial.csv', 'r', newline='') as _f:
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

# ── Parse incoming line ───────────────────────────────────────────────────────
_PREFIX_MAP = {
    'HM1':   ('hm',   0), 'HM2':   ('hm',   1), 'HM3':   ('hm',   2),
    'TP1':   ('temp', 0), 'TP2':   ('temp', 1), 'TP3':   ('temp', 2),
    'DRRS1': ('door', 0), 'DRRS2': ('door', 1), 'DRRS3': ('door', 2),
    'PS1':   ('pump', 0), 'PS2':   ('pump', 1), 'PS3':   ('pump', 2),
    'RAM1':  ('ram',  0), 'RAM2':  ('ram',  1), 'RAM3':  ('ram',  2),
}
_LABEL     = {'hm':'Humidity','temp':'Temperature','door':'Door','pump':'Pump','ram':'RAM'}
_PICO_NAME = ['First','Second','Third']

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

# ── Active serial connection (shared so door API can write back) ──────────────
_serial_conn: serial.Serial | None = None

# ── Auto-detect Pico COM port ─────────────────────────────────────────────────
def detect_pico_port() -> str | None:
    for port in serial.tools.list_ports.comports():
        desc = (port.description or '').lower()
        if any(k in desc for k in ('pico', 'rp2040', 'micropython', 'cdc')):
            return port.device
    ports = serial.tools.list_ports.comports()
    return ports[0].device if ports else None

def serial_write(cmd: str) -> None:
    global _serial_conn
    if _serial_conn and _serial_conn.is_open:
        try:
            _serial_conn.write((cmd + '\n').encode())
            print(f'Serial TX: {cmd}')
        except Exception as e:
            print(f'Serial write error: {e}')
    else:
        print(f'Serial TX skipped (not connected): {cmd}')

# ── Serial reader task ────────────────────────────────────────────────────────
async def serial_recv() -> None:
    global _serial_conn
    port = SERIAL_PORT or detect_pico_port()
    if not port:
        print('ERROR: No COM port found. Plug in the Pico and restart.')
        return

    print(f'Opening serial port {port} @ {BAUD_RATE} baud…')
    loop = asyncio.get_event_loop()

    while True:
        try:
            _serial_conn = serial.Serial(port, BAUD_RATE, timeout=1)
            print(f'Serial connected on {port}')
            print('-' * 33)
            while True:
                def _read():
                    return _serial_conn.readline()
                raw = await loop.run_in_executor(None, _read)
                if raw:
                    line = raw.decode(errors='ignore').strip()
                    if line and line != '---':
                        parse_line(line)
                await asyncio.sleep(0)
        except serial.SerialException as e:
            _serial_conn = None
            print(f'Serial error: {e} — retrying in 5s…')
            await asyncio.sleep(5)
        except Exception as e:
            _serial_conn = None
            print(f'serial_recv error: {e}')
            await asyncio.sleep(2)

# ── HTTP helpers ──────────────────────────────────────────────────────────────
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

# ── ThingSpeak task ───────────────────────────────────────────────────────────
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
                print(f'ThingSpeak [{name}]: FAILED.')
                alert_log.append({'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                   'msg': f'ThingSpeak FAILED — {name}'})
        ok_ram = await http_get(session, THINGSPEAK_URL, {
            'api_key': TS_KEYS['ram'],
            'field1':  state['ram'][0] or 0,
            'field2':  state['ram'][1] or 0,
            'field3':  state['ram'][2] or 0,
        })
        if not ok_ram:
            alert_log.append({'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                               'msg': 'ThingSpeak FAILED — RAM'})
        await asyncio.sleep(INTERVAL_THINGSPEAK)

# ── CSV backup task ───────────────────────────────────────────────────────────
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
        with open('backup_data_serial.csv', 'w', newline='') as f:
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
        'mode': 'serial',
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
    return web.Response(text=json.dumps(payload), content_type='application/json',
                        headers={'Access-Control-Allow-Origin': '*'})

async def api_door(req: web.Request) -> web.Response:
    cors = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Content-Type'}
    if req.method == 'OPTIONS':
        return web.Response(headers=cors)
    try:
        body  = await req.json()
        pico  = int(body['pico']) - 1
        value = body.get('value')
        if pico not in (0, 1, 2):
            raise ValueError
        if value is not None:
            value = int(value)
            if value not in (0, 1):
                raise ValueError
    except Exception:
        return web.Response(status=400, text='Bad request', headers=cors)
    door_override[pico] = value
    action = 'AUTO' if value is None else ('OPEN' if value == 1 else 'CLOSE')
    print(f'Door override: Pico {pico+1} → {action}')
    # Send command to Pico over serial: DOOR1:1 / DOOR1:0 / DOOR1:A
    wire_val = 'A' if value is None else str(value)
    serial_write(f'DOOR{pico+1}:{wire_val}')
    return web.Response(text=json.dumps({'ok': True}), content_type='application/json', headers=cors)

async def api_cmd(req: web.Request) -> web.Response:
    pico_id = int(req.match_info['pico_id']) - 1
    return web.Response(
        text=json.dumps({'door': door_override[pico_id]}),
        content_type='application/json',
        headers={'Access-Control-Allow-Origin': '*'})

async def api_alerts(_req: web.Request) -> web.Response:
    return web.Response(text=json.dumps(list(alert_log)),
                        content_type='application/json',
                        headers={'Access-Control-Allow-Origin': '*'})

async def api_status(_req: web.Request) -> web.Response:
    uptime = datetime.datetime.now() - SERVER_START_TIME
    hours, rem = divmod(int(uptime.total_seconds()), 3600)
    minutes = rem // 60
    port = SERIAL_PORT or detect_pico_port() or 'unknown'
    return web.Response(
        text=json.dumps({
            'started': SERVER_START_TIME.strftime('%Y-%m-%d %H:%M:%S'),
            'uptime':  f'{hours}h {minutes}m',
            'mode':    'serial',
            'port':    port,
        }),
        content_type='application/json',
        headers={'Access-Control-Allow-Origin': '*'})

async def api_ports(_req: web.Request) -> web.Response:
    ports = [{'device': p.device, 'description': p.description}
             for p in serial.tools.list_ports.comports()]
    return web.Response(text=json.dumps(ports), content_type='application/json',
                        headers={'Access-Control-Allow-Origin': '*'})

async def api_server() -> None:
    app = web.Application()
    app.router.add_get('/data',          api_data)
    app.router.add_post('/door',         api_door)
    app.router.add_options('/door',      api_door)
    app.router.add_get('/cmd/{pico_id}', api_cmd)
    app.router.add_get('/alerts',        api_alerts)
    app.router.add_get('/status',        api_status)
    app.router.add_get('/ports',         api_ports)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', API_PORT)
    await site.start()
    print(f'API server running on http://0.0.0.0:{API_PORT}/data')
    print('-' * 33)

# ── Entry point ───────────────────────────────────────────────────────────────
async def main() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')
    print('╔══════════════════════════════════════╗')
    print('║      GreenIOT  Serial Server v5      ║')
    print('║  Genius Olympiad 2026 — S.Onderisin  ║')
    print('╠══════════════════════════════════════╣')
    port = SERIAL_PORT or detect_pico_port() or 'auto-detect'
    print(f'║  Mode : USB Serial                   ║')
    print(f'║  Port : {port:<29}║')
    print(f'║  API  : http://0.0.0.0:{API_PORT}/data     ║')
    print('╚══════════════════════════════════════╝')
    print()

    connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=300)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(api_server())
            tg.create_task(serial_recv())
            tg.create_task(data_send(session))
            tg.create_task(backup_data())

asyncio.run(main())
