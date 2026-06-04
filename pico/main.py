import gc
import socket
import ujson
import uasyncio
import machine
import network
import scd4x
import urequests
from machine import Pin, ADC
from servo import Servo
from time import sleep

# ── Constants ─────────────────────────────────────────────────────────────────
SSID        = 'Duchon'
PASSWORD    = 'Skrecok10Skrecok10.'
SERVER_IP   = '10.0.0.101'
SERVER_PORT = 9991
API_PORT    = 8080
PICO_ID     = 1          # ← change to 2 or 3 on other Picos

HM_MAX = 54340
HM_MIN = 20889
DOOR_OPEN_TEMP  = 25    # °C — open door above this
PUMP_ON_HM      = 60    # %  — run pump below this
RAM_GC_THRESH   = 50    # %  — force gc.collect above this

SEND_INTERVAL   = 40    # seconds between TCP sends
DOOR_INTERVAL   = 20
PUMP_INTERVAL   = 20
RAM_INTERVAL    = 300
CMD_INTERVAL    = 5     # seconds between polling for door commands
CONNECT_TIMEOUT = 15    # seconds to wait for WiFi

# ── State (plain ints/floats — no string copies until send) ───────────────────
humidity    = 0.0
temp        = 0.0
door        = 0
pump_state  = 0
ram_pct     = 0
sequence    = 0
scd_ok      = False     # set to True only if SCD4X initialises successfully
door_manual = None      # None = auto, 0 = forced closed, 1 = forced open

# ── Hardware init ─────────────────────────────────────────────────────────────
led = Pin('LED', Pin.OUT)
led.low()

gc.enable()
gc.collect()

# WiFi
network.hostname('Semi_cl_picow')
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

deadline = CONNECT_TIMEOUT
while not wlan.isconnected() and deadline > 0:
    sleep(1)
    deadline -= 1

if not wlan.isconnected():
    print('WiFi failed — rebooting')
    machine.reset()

print('WiFi OK:', wlan.ifconfig()[0])
led.high()

# Sensors
i2c = machine.I2C(0, sda=Pin(16), scl=Pin(17), freq=100000)
try:
    scd = scd4x.SCD4X(i2c)
    sleep(0.5)
    scd.start_periodic_measurement()
    scd_ok = True
    print('SCD4X: OK')
except Exception as e:
    scd = None
    scd_ok = False
    print('SCD4X not found — temperature disabled:', e)

hm_adc  = ADC(Pin(27))
pump_pin = Pin(15, Pin.OUT)
pump_pin.high()

servo1 = Servo(pin=1)
servo1.move(90)

# ── Tasks ─────────────────────────────────────────────────────────────────────
async def humidity_measure():
    global humidity
    while True:
        raw = hm_adc.read_u16()
        val = (HM_MAX - raw) * 100 / (HM_MAX - HM_MIN)
        humidity = max(0.0, min(100.0, round(val, 1)))
        await uasyncio.sleep(1)


async def temperature_measure():
    global temp
    if not scd_ok:
        return
    while True:
        try:
            if scd.data_ready:
                temp = round(scd.temperature, 1)
        except Exception as e:
            print('SCD4X read error:', e)
        await uasyncio.sleep(1)


async def door_control():
    global door
    while True:
        try:
            # manual override from website takes priority over auto
            target = door_manual if door_manual is not None else (1 if temp >= DOOR_OPEN_TEMP else 0)
            if target == 1:
                servo1.move(170)
                door = 1
            else:
                servo1.move(70)
                door = 0
        except Exception as e:
            print('Door control error:', e)
        await uasyncio.sleep(DOOR_INTERVAL)


async def cmd_poll():
    global door_manual
    url = 'http://{}:{}/cmd/{}'.format(SERVER_IP, API_PORT, PICO_ID)
    while True:
        try:
            r = urequests.get(url, timeout=4)
            data = ujson.loads(r.content)
            r.close()
            val = data.get('door')
            if val is not None:
                door_manual = int(val)
                print('Door command received:', 'OPEN' if door_manual else 'CLOSE')
        except Exception as e:
            print('cmd_poll error:', e)
        await uasyncio.sleep(CMD_INTERVAL)


async def pump_control():
    global pump_state
    while True:
        if humidity <= PUMP_ON_HM:
            pump_pin.low()
            sleep(0.5)
            pump_pin.high()
            pump_state = 1
        else:
            pump_pin.high()
            pump_state = 0
        await uasyncio.sleep(PUMP_INTERVAL)


async def ram_monitor():
    global ram_pct
    while True:
        alloc = gc.mem_alloc()
        ram_pct = int(alloc * 100 / (alloc + gc.mem_free()))
        if ram_pct > RAM_GC_THRESH:
            gc.collect()
            ram_pct = int(gc.mem_alloc() * 100 / (gc.mem_alloc() + gc.mem_free()))
            print('GC collected — RAM now:', ram_pct, '%')
        await uasyncio.sleep(RAM_INTERVAL)


async def data_transfer():
    global sequence
    await uasyncio.sleep(5)     # wait for first sensor readings
    while True:
        # Build payload once — reuse buffer
        payload = (
            'HM1:{}\nTP1:{}\nDRRS1:{}\nPS1:{}\nRAM1:{}\n'
            .format(humidity, temp, door, pump_state, ram_pct)
            .encode()
        )
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            sock.connect((SERVER_IP, SERVER_PORT))
            sock.send(payload)
            sequence += 1
            print(sequence, '. Sent — HM:', humidity, 'TP:', temp,
                  'DRRS:', door, 'PS:', pump_state, 'RAM:', ram_pct, '%')
        except OSError as e:
            print('Send failed:', e)
        finally:
            sock.close()
            del payload, sock   # free immediately
        await uasyncio.sleep(SEND_INTERVAL)


async def main():
    uasyncio.create_task(humidity_measure())
    uasyncio.create_task(temperature_measure())
    uasyncio.create_task(door_control())
    uasyncio.create_task(pump_control())
    uasyncio.create_task(ram_monitor())
    uasyncio.create_task(data_transfer())
    uasyncio.create_task(cmd_poll())
    while True:
        await uasyncio.sleep(60)


uasyncio.run(main())
