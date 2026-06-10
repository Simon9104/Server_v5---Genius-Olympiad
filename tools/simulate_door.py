"""
GreenIOT Door Simulation Test
Run this on the PC (not the Pico) with the Pico connected via USB.
It opens the serial port, waits for data, sends door commands, and
verifies the door state changed in the next data packet.

Usage:
    python tools/simulate_door.py COM5
    python tools/simulate_door.py /dev/ttyACM0
"""
import sys
import time
import serial
import serial.tools.list_ports

# ── Config ────────────────────────────────────────────────────────────────────
BAUD = 115200
TIMEOUT_DATA = 60   # seconds to wait for a data packet

def find_pico():
    for p in serial.tools.list_ports.comports():
        if any(k in (p.description or '').lower() for k in ('pico','rp2040','cdc','micropython')):
            return p.device
    ports = serial.tools.list_ports.comports()
    return ports[0].device if ports else None

def read_packet(ser, timeout=TIMEOUT_DATA):
    """Read lines until --- end-of-frame marker, return dict of key:value."""
    packet = {}
    deadline = time.time() + timeout
    while time.time() < deadline:
        raw = ser.readline()
        if not raw:
            continue
        line = raw.decode(errors='ignore').strip()
        if line == '---':
            if packet:
                return packet
        elif ':' in line:
            k, _, v = line.partition(':')
            packet[k.strip()] = v.strip()
    return packet

def run():
    port = sys.argv[1] if len(sys.argv) > 1 else find_pico()
    if not port:
        print('ERROR: No COM port found.')
        sys.exit(1)

    print(f'Opening {port} @ {BAUD}...')
    ser = serial.Serial(port, BAUD, timeout=2)
    time.sleep(1)
    ser.reset_input_buffer()

    print('─' * 50)
    print('STEP 1 — Waiting for first data packet from Pico…')
    p1 = read_packet(ser)
    if not p1:
        print('ERROR: No data received. Is serial_main.py running on the Pico?')
        sys.exit(1)
    print(f'  Received: {p1}')
    door_before = p1.get('DRRS1', '?')
    print(f'  Door before command: DRRS1 = {door_before}')

    print('─' * 50)
    print('STEP 2 — Sending DOOR1:1 (OPEN command)…')
    ser.write(b'DOOR1:1\n')
    ser.flush()
    print('  Sent: DOOR1:1')

    print('─' * 50)
    print('STEP 3 — Waiting for Pico acknowledgement and next data packet…')
    p2 = read_packet(ser)
    print(f'  Received: {p2}')
    door_after = p2.get('DRRS1', '?')
    print(f'  Door after command: DRRS1 = {door_after}')

    print('─' * 50)
    if door_after == '1':
        print('✔  PASS — Door opened successfully (DRRS1 = 1)')
    else:
        print(f'✖  FAIL — Door did not open (DRRS1 = {door_after})')
        print('   Check that DOOR1:1 line was received by Pico.')

    print('─' * 50)
    print('STEP 4 — Sending DOOR1:0 (CLOSE command)…')
    ser.write(b'DOOR1:0\n')
    ser.flush()
    p3 = read_packet(ser)
    door_closed = p3.get('DRRS1', '?')
    print(f'  Door after close: DRRS1 = {door_closed}')
    if door_closed == '0':
        print('✔  PASS — Door closed successfully')
    else:
        print(f'✖  FAIL — Door did not close (DRRS1 = {door_closed})')

    print('─' * 50)
    print('STEP 5 — Sending DOOR1:A (AUTO mode)…')
    ser.write(b'DOOR1:A\n')
    ser.flush()
    print('  Auto mode set.')

    ser.close()
    print('Done.')

if __name__ == '__main__':
    run()
