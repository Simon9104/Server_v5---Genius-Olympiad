import time
from machine import Pin, ADC, I2C, PWM

# ── Config ────────────────────────────────────────────────────────────────────
PICO_ID       = 1          # Change to 2 or 3 on other Picos
SEND_INTERVAL = 40         # seconds between data sends
SERVO_PIN     = 1
PUMP_PIN      = 15
HM_PIN        = 27
SDA_PIN       = 16
SCL_PIN       = 17

# ── Hardware init ─────────────────────────────────────────────────────────────
pump  = Pin(PUMP_PIN, Pin.OUT)
hm_adc = ADC(Pin(HM_PIN))
servo_pwm = PWM(Pin(SERVO_PIN))
servo_pwm.freq(50)

# ── SCD4X (CO2/temp) — optional, skip if not connected ───────────────────────
scd_ok = False
scd    = None
try:
    from scd4x import SCD4X
    i2c = I2C(0, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN))
    devs = i2c.scan()
    if devs:
        scd = SCD4X(i2c)
        scd.start_periodic_measurement()
        scd_ok = True
        print('SCD4X OK')
    else:
        print('SCD4X not found — skipping temperature sensor')
except Exception as e:
    print('SCD4X init failed:', e)

# ── Servo helpers ─────────────────────────────────────────────────────────────
def servo_open():
    servo_pwm.duty_u16(int(0.1 / 20 * 65535))

def servo_close():
    servo_pwm.duty_u16(int(0.05 / 20 * 65535))

# ── Read humidity (analog, 0-100%) ────────────────────────────────────────────
def read_humidity():
    raw = hm_adc.read_u16()
    return round(100 - (raw / 65535) * 100, 1)

# ── Door auto logic ───────────────────────────────────────────────────────────
door_manual = None   # None=auto, 0=force close, 1=force open

def update_door(temp):
    global door_manual
    if door_manual == 1:
        servo_open();  return 1
    if door_manual == 0:
        servo_close(); return 0
    if temp is not None and temp > 28:
        servo_open();  return 1
    servo_close(); return 0

# ── RAM usage ─────────────────────────────────────────────────────────────────
def ram_pct():
    import gc
    gc.collect()
    free  = gc.mem_free()
    alloc = gc.mem_alloc()
    total = free + alloc
    return round(alloc / total * 100, 1) if total else 0

# ── Send data over USB serial ─────────────────────────────────────────────────
def send_data(hm, temp, door, pump_state):
    pid = PICO_ID
    print(f'HM{pid}:{hm}')
    if temp is not None:
        print(f'TP{pid}:{temp}')
    print(f'DRRS{pid}:{door}')
    print(f'PS{pid}:{pump_state}')
    print(f'RAM{pid}:{ram_pct()}')
    print('---')          # end-of-frame marker

# ── Main loop ─────────────────────────────────────────────────────────────────
print(f'GreenIOT Pico {PICO_ID} — Serial Mode')
print('---')

while True:
    hm   = read_humidity()
    temp = None

    if scd_ok:
        try:
            if scd.data_ready:
                scd.measure()
                temp = round(scd.temperature, 1)
        except Exception as e:
            print('SCD4X read error:', e)

    pump_state = 1 if pump.value() else 0
    door_state = update_door(temp)

    send_data(hm, temp, door_state, pump_state)
    time.sleep(SEND_INTERVAL)
