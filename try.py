from time import sleep
import network, socket, random

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('Onderisinovci', 'radulo30')


connection = socket.getaddrinfo('0.0.0.0', 5666)[0][-1]
s = socket.socket()
s.bind(connection)
s.listen(1)
cl, addr = s.accept()
cl.close()


while True:
    cl, addr = s.accept()
    request = cl.recv(1024)
    print(request)
    data = str(random.randint(0,100))
    cl.send(data)
    print('Sent' +data)
    cl.close()
    
    
    