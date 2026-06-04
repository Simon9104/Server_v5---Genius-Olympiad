from time import sleep
from machine import Pin, ADC
from servo import Servo
import socket, random, uasyncio, network, gc, urequests, machine, scd4x 

print('System is starting right now!!!!')
print('All rights reserved by Simon Onderisin ® 2025')
print("Any way of copying this code is strictly prohibited!!!!")
sleep(2)

led = Pin('LED', Pin.OUT)
led.low()

network.hostname('Semi_cl_picow')
sleep(1)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('Duchon', 'Skrecok10Skrecok10.')
sleep(10)
print(wlan.ifconfig())
led.high()

gc.enable()

sequence = 0

CTRL1_num = 1
CTRL1_num = str(CTRL1_num)

i2c = machine.I2C(0, sda=Pin(16), scl=Pin(17), freq=100000)
scd = scd4x.SCD4X(i2c)
sleep(0.5)
scd.start_periodic_measurement()

humidity_sensor = ADC(Pin(27))

max_hm = 54340
min_hm = 20889

pump = Pin(15, Pin.OUT)
pump.high()

servo1 = Servo(pin=1)

servo1.move(90)

async def Humidity_measure():
    global humidity, i2c, scd, max_hm, min_hm
    while True:
        humidity = (max_hm - humidity_sensor.read_u16())*100/(max_hm - min_hm)
        humidity = round(humidity, 1)
        if humidity >= 100:
            humidity = 100
        if humidity <= 1:
            humidity = 0
        await uasyncio.sleep(1)

async def temperature_measure():
    global temp1, sdc, i2c
    while True:
        if scd.data_ready:
            temp1 = scd.temperature
            temp1 = round(temp1, 1)
            await uasyncio.sleep(1)

async def door_status():
    global temp1, door_status1, door_status_num, servo1
    while True:
        if temp1 >= 25:
            servo1.move(170)
            door_status1 = 1
            door_status_num = str(door_status1)

        else:
            servo1.move(70)
            door_status1 = 0
            door_status_num = str(door_status1)
        await uasyncio.sleep(20)

async def pump_status():
    global humidity, pump_status1, pump_status_num, pump
    while True:
        if humidity <= 60:
            pump.low()
            sleep(0.5)
            pump.high()
            pump_status1 = 1
            pump_status_num = str(pump_status1)
        else:
            pump.high()
            pump_status1 = 0
            pump_status_num = str(pump_status1)
        await uasyncio.sleep(20)

async def data_transfer():
    global humidity, temp1, door_status_num, pump_status_num, RAM, CTRL1_num, sequence, pump
    while True:
        humidity = str(humidity)
        temp1 = str(temp1)
        socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data = f"HM1:{humidity}\nTP1:{temp1}\nDRRS1:{door_status_num}\nPS1:{pump_status_num}\nRAM1:{RAM}\nCTRL1:{CTRL1_num}\n"
        data = data.encode()
        socket1.connect(('10.0.0.101', 9991))
        socket1.send(data)
        sequence += 1
        print(sequence,'.',"Data transfer of all variables was DONE successfully!")
        print('Humdity:', humidity) 
        print("Temperature:", temp1) 
        print('Door status:', door_status_num) 
        print('Pump status:', pump_status_num)
        print('---------------------------------')
        socket1.close()
        await uasyncio.sleep(40)
        
async def RAM_usage():
    global gc, RAM
    while True:
        RAM = gc.mem_alloc()/1024
        RAM = int((RAM*100)/264)
        print('RAM usage is:', RAM,'%')
        print('---------------------------------')
        if RAM > 50:
            gc.collect()
            print('RAM was collected succesfully!!')
        await uasyncio.sleep(300)
        
       
async def main():
    global humidity, temp1, door_status_num, pump_status_num, sequence
    uasyncio.create_task(Humidity_measure())
    uasyncio.create_task(temperature_measure())
    uasyncio.create_task(door_status())
    uasyncio.create_task(pump_status())
    uasyncio.create_task(RAM_usage())
    uasyncio.create_task(data_transfer())
    while True:
        await Humidity_measure()
        await temperature_measure()
        await door_status()
        await pump_status()
        await RAM_usage()
        await data_transfer()
        print('program is running!')
        await uasyncio.sleep(120)

uasyncio.run(main())
