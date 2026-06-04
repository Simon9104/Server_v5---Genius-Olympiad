import network
import random
import socket
import time




# Just making our internet connection
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('Onderisinovci', '000')

# Wait for connect or fail
max_wait = 10
while max_wait > 0:
  if wlan.status() < 0 or wlan.status() >= 3:
    break
  max_wait -= 1
  print('waiting for connection...')
  time.sleep(1)
# Handle connection error
if wlan.status() != 3:
   raise RuntimeError('network connection failed')
else:
  print('connected')
  status = wlan.ifconfig()
  print('ip = ' + status[0])

# Open socket
addr = socket.getaddrinfo('0.0.0.0', 5666)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)
cl, addr = s.accept()
cl.close()

print('listening on', addr)

# Listen for connections
while True:
    try:
        cl, addr = s.accept()
        request = cl.recv(1024)
        print(request)
        # No need to unpack request in this example
        ran_num = str(random.randint(0, 100))
        cl.send(ran_num)
        print("Sent: " + ran_num)
        cl.close()

    except OSError as e:
        cl.close()
        print('connection closed')
