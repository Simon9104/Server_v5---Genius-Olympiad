from machine import Pin
from time import sleep

pumpa = Pin(15, Pin.OUT)

pumpa.high()




pumpa.low()
sleep(0.5)
pumpa.high()
print('OK')
print('Prajem vsetkym vesle a statsne vianoce nech sa vsetkym dari')
