import asyncio
import datetime
import os
import socket

import pandas as pd
import requests

print('System is starting right now!!!!')
print('All rights reserved by Simon Onderisin ® 2025')
print('Any way of copying this code is strictly prohibited!!!!')

# ── Network ──────────────────────────────────────────────────────────────────
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9991

PICO_IPS = {
    1: '192.168.1.59',
    2: '192.168.1.118',
    3: '192.168.1.118',
}

# ── ThingSpeak ────────────────────────────────────────────────────────────────
THINGSPEAK_URL = 'https://api.thingspeak.com/update'
TS_KEYS = {
    'semi_closed': 'XRHM95UX4K3FVX0J',
    'fully_closed': 'VT7JT0U9KSCCYMTG',
    'free_planting': 'KK2CRU2B3CKZW40C',
    'ram':           'ENMLII2NCVO8DNZM',
}

# ── Discord ───────────────────────────────────────────────────────────────────
DISCORD_TOKEN   = 'MTM5OTA4Mzg2ODk4Mzc4NzU0MQ.GNxs36.ijxA50O87YSg3hA1O1kCqWwaoz6Dns4iysXXkA'
DISCORD_TOKEN_ERR = 'MTQyNjg2MTk3MDEzNjYyOTM3OA.GzNIim.AhxqZ7Qmw-fyADKUtP2pvTNUqGJiKPdgtw4-Aw'
DISCORD_STATUS_URL = 'https://discord.com/api/v9/channels/1409588804951605413/messages'
DISCORD_ERROR_URL  = 'https://discord.com/api/v9/channels/1426862416565764139/messages'
DISCORD_HEADERS     = {'authorization': DISCORD_TOKEN}
DISCORD_ERR_HEADERS = {'authorization': DISCORD_TOKEN_ERR}

# ── Intervals ─────────────────────────────────────────────────────────────────
INTERVAL_THINGSPEAK = 120
INTERVAL_DISCORD    = 7200
INTERVAL_BACKUP     = 600
INTERVAL_PING       = 3600

# ── Sensor state ─────────────────────────────────────────────────────────────
state = {
    'hm':   [0.0, 0.0, 0.0],
    'temp': [0.0, 0.0, 0.0],
    'door': [0.0, 0.0, 0.0],
    'pump': [0.0, 0.0, 0.0],
    'ram':  [None, None, None],
}

# sequence counters: seq[field][pico_index]
seq = {k: [0, 0, 0] for k in ('hm', 'temp', 'door', 'pump', 'ram')}

# CSV accumulator
backup_rows = []

# ── TCP server ────────────────────────────────────────────────────────────────
tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcp_server.bind((SERVER_HOST, SERVER_PORT))
tcp_server.listen(5)
tcp_server.setblocking(False)

# ── Helpers ───────────────────────────────────────────────────────────────────
def discord_post(url, headers, content):
    try:
        requests.post(url, data={'content': content}, headers=headers, timeout=10)
    except Exception as e:
        print(f'Discord post failed: {e}')

def thingspeak_send(api_key, **fields):
    params = {'api_key': api_key}
    params.update({f'field{i+1}': v for i, v in enumerate(fields.values())})
    try:
        requests.get(THINGSPEAK_URL, params=params, timeout=10)
        print('ThingSpeak: data sent.')
        return True
    except Exception as e:
        print(f'ThingSpeak error: {e}')
        return False

# ── Parse incoming line ───────────────────────────────────────────────────────
_PREFIX_MAP = {
    'HM1': ('hm', 0), 'HM2': ('hm', 1), 'HM3': ('hm', 2),
    'TP1': ('temp', 0), 'TP2': ('temp', 1), 'TP3': ('temp', 2),
    'DRRS1': ('door', 0), 'DRRS2': ('door', 1), 'DRRS3': ('door', 2),
    'PS1': ('pump', 0), 'PS2': ('pump', 1), 'PS3': ('pump', 2),
    'RAM1': ('ram', 0), 'RAM2': ('ram', 1), 'RAM3': ('ram', 2),
}

LABEL = {'hm': 'Humidity', 'temp': 'Temperature', 'door': 'Door status', 'pump': 'Pump status', 'ram': 'RAM usage'}
PICO_NAME = ['first', 'second', 'third']

def parse_line(line: str):
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
    seq[field][idx] += 1
    print(f"{seq[field][idx]}. {LABEL[field]} of {PICO_NAME[idx]} Pico: {value}")
    print('-' * 33)

# ── Async tasks ───────────────────────────────────────────────────────────────
async def data_recv():
    loop = asyncio.get_event_loop()
    while True:
        try:
            client, addr = await loop.sock_accept(tcp_server)
            data = await loop.sock_recv(client, 4096)
            client.close()
            for line in data.decode(errors='ignore').strip().split('\n'):
                parse_line(line)
        except Exception as e:
            print(f'data_recv error: {e}')
        await asyncio.sleep(0)


async def data_send():
    await asyncio.sleep(INTERVAL_THINGSPEAK)
    while True:
        channels = [
            ('semi_closed',  'hm', 'temp', 'door', 'pump', 0),
            ('fully_closed', 'hm', 'temp', 'door', 'pump', 1),
            ('free_planting','hm', 'temp', 'door', 'pump', 2),
        ]
        names = ['Semi-Closed', 'Fully-Closed', 'Free Planting']
        for (ch, *fields, i), name in zip(channels, names):
            ok = thingspeak_send(TS_KEYS[ch],
                                 hm=state['hm'][i],
                                 temp=state['temp'][i],
                                 door=state['door'][i],
                                 pump=state['pump'][i])
            if not ok:
                discord_post(DISCORD_ERROR_URL, DISCORD_ERR_HEADERS,
                             f'@simon9104 ERROR sending to ThingSpeak — {name}')

        ok_ram = thingspeak_send(TS_KEYS['ram'],
                                 r1=state['ram'][0],
                                 r2=state['ram'][1],
                                 r3=state['ram'][2])
        if not ok_ram:
            discord_post(DISCORD_ERROR_URL, DISCORD_ERR_HEADERS,
                         '@simon9104 ERROR sending to ThingSpeak — RAM')

        await asyncio.sleep(INTERVAL_THINGSPEAK)


async def transfer_discord():
    await asyncio.sleep(INTERVAL_DISCORD)
    while True:
        r = state['ram']
        msg = (f'RAM usage — Pico 1: {r[0]}%  |  '
               f'Pico 2: {r[1]}%  |  '
               f'Pico 3: {r[2]}%')
        discord_post(DISCORD_STATUS_URL, DISCORD_HEADERS, msg)
        print('Discord status message sent.')
        print('-' * 33)
        await asyncio.sleep(INTERVAL_DISCORD)


async def backup_data():
    await asyncio.sleep(INTERVAL_BACKUP)
    while True:
        row = {
            'Time':        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Humidity SC': state['hm'][0],   'TP SC':   state['temp'][0],
            'DRRS SC':     state['door'][0],  'PS SC':   state['pump'][0],
            'HM C':        state['hm'][1],    'TP C':    state['temp'][1],
            'DRRS C':      state['door'][1],  'PS C':    state['pump'][1],
            'HM FREE':     state['hm'][2],    'TP FREE': state['temp'][2],
            'DRRS FREE':   state['door'][2],  'PS FREE': state['pump'][2],
        }
        backup_rows.append(row)
        pd.DataFrame(backup_rows).to_csv('backup_data_server.csv', index=False)
        print('Backup saved.')
        print('-' * 33)
        await asyncio.sleep(INTERVAL_BACKUP)


async def ping_pico(index: int):
    ip = PICO_IPS[index + 1]
    name = PICO_NAME[index].capitalize()
    while True:
        result = os.system(f'ping -c 1 {ip} > /dev/null 2>&1')
        status = 'ONLINE' if result == 0 else 'OFFLINE — check connection!'
        print(f'{name} Pico ({ip}): {status}')
        print('-' * 33)
        await asyncio.sleep(INTERVAL_PING)


async def main():
    os.system('clear')
    print('System started successfully!')

    discord_post(DISCORD_STATUS_URL, DISCORD_HEADERS, 'Server v5 started.')

    async with asyncio.TaskGroup() as tg:
        tg.create_task(data_recv())
        tg.create_task(data_send())
        tg.create_task(transfer_discord())
        tg.create_task(backup_data())
        for i in range(3):
            tg.create_task(ping_pico(i))


asyncio.run(main())
