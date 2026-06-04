from time import sleep
import socket, random, asyncio, requests, os, datetime,  pandas as pd

print('System is starting right now!!!!')
print('All rights reserved by Simon Onderisin ® 2025')
print("Any way of copying this code is strictly prohibited!!!!")
sleep(5)
os.system('clear')

print('System was started successfully!!!!')

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 9991))
server.listen(5)

hm1 = 0
hm2 = 0
hm3 = 0

temp1 = 0
temp2 = 0
temp3 = 0

door1 = 0
door2 = 0 
door3 = 0

pump1 = 0
pump2 = 0
pump3 = 0

sequence_hm1 = 0
sequence_tp1 = 0
sequence_drs1 = 0
sequence_pms1 = 0

sequence_hm2 = 0
sequence_tp2 = 0
sequence_drs2 = 0
sequence_pms2 = 0

sequence_hm3 = 0
sequence_tp3 = 0
sequence_drs3 = 0
sequence_pms3 = 0

sequence_RAM1 = 0
sequence_RAM2 = 0 
sequence_RAM3 = 0

RAM1_num = None
RAM2_num = None
RAM3_num = None

client1_IP = '192.168.1.59'
client2_IP = '192.168.1.118'
client3_IP = '192.168.1.118'


URL= 'https://api.thingspeak.com/update'
API1 = 'XRHM95UX4K3FVX0J'
API2 = 'VT7JT0U9KSCCYMTG'
API3 = 'KK2CRU2B3CKZW40C'
API_RAM = 'ENMLII2NCVO8DNZM'

URL_discord = 'https://discord.com/api/v9/channels/1409588804951605413/messages'
data ={
    "content": "Program was started"
}

header = {
    "authorization": 'MTM5OTA4Mzg2ODk4Mzc4NzU0MQ.GNxs36.ijxA50O87YSg3hA1O1kCqWwaoz6Dns4iysXXkA'
}

URL_discord_ERR = 'https://discord.com/api/v9/channels/1426862416565764139/messages'
header_ERR = {
    "authorization": 'MTQyNjg2MTk3MDEzNjYyOTM3OA.GzNIim.AhxqZ7Qmw-fyADKUtP2pvTNUqGJiKPdgtw4-Aw'
}

requests.post(URL_discord, data=data, headers=header)

async def data_recv():
    global hm1, temp1, door1, pump1 
    global sequence_hm1, sequence_tp1, sequence_drs1, sequence_pms1
    global sequence_hm2, sequence_tp2, sequence_drs2, sequence_pms2
    global sequence_hm3, sequence_tp3, sequence_drs3, sequence_pms3
    global hm2, temp2, door2, pump2
    global hm3, temp3, door3, pump3
    global RAM1_num, RAM2_num, RAM3_num
    global sequence_RAM1, sequence_RAM2, sequence_RAM3
    while True:
        client, addr = server.accept()
        data = client.recv(1024)
        data = data.decode()
        for line in data.strip().split('\n'):
            if line.startswith('HM1:'):
                hm1 = float(line[4:])
                sequence_hm1 += 1
                print(sequence_hm1,'.','Data transfer of humidity was DONE successfully!', hm1)
                print('---------------------------------')
            elif line.startswith('TP1:'):
                temp1 = float(line[4:])
                sequence_tp1 += 1
                print(sequence_tp1,'.','Data transfer of temperature was DONE successfully!', temp1)
                print('---------------------------------')
            elif line.startswith('DRRS1:'):
                door1 = float(line[6:])
                sequence_drs1 += 1
                print(sequence_drs1,'.','Data transfer of door status was DONE successfully!', door1)
                print('---------------------------------')
            elif line.startswith('PS1:'):
                pump1 = float(line[4:])
                sequence_pms1 += 1
                print(sequence_pms1,'.','Data transfer of pump status was DONE successfully!', pump1)
                print('---------------------------------')
            elif line.startswith('HM2:'):
                hm2 = float(line[4:])
                sequence_hm2 += 1
                print(sequence_hm2,'.','Data transfer of humidity was DONE successfully 2!', hm2)
                print('---------------------------------')
            elif line.startswith('TP2:'):
                temp2 = float(line[4:])
                sequence_tp2 += 1
                print(sequence_tp2,'.','Data transfer of temperature was DONE successfully 2!', temp2)
                print('---------------------------------')
            elif line.startswith('DRRS2:'):
                door2 = float(line[6:])
                sequence_drs2 += 1
                print(sequence_drs2,'.','Data transfer of door status was DONE successfully 2!', door2)
                print('---------------------------------')
            elif line.startswith('PS2:'):
                pump2 = float(line[4:])
                sequence_pms2 += 1
                print(sequence_pms2,'.','Data transfer of pump status was DONE successfully 2!', pump2)
                print('---------------------------------')
            elif line.startswith('HM3:'):
                hm3 = float(line[4:])
                sequence_hm3 += 1
                print(sequence_hm3,'.','Data transfer of humidity status was DONE successfully 3!', hm3)
                print('---------------------------------')
            elif line.startswith('TP3:'):
                temp3 = float(line[4:])
                sequence_tp3 += 1
                print(sequence_tp3,'.','Data transfer of temperature was DONE successfully 3!', temp3)
                print('---------------------------------')
            elif line.startswith('DRRS3:'):
                door3 = float(line[6:])
                sequence_drs3 += 1
                print(sequence_drs3,'.','Data transfer of door status was DONE successfully 3!', door3)
                print('---------------------------------')
            elif line.startswith('PS3:'):
                pump3 = float(line[4:])
                sequence_pms3 += 1
                print(sequence_pms3,'.','Data transfer of pump status was DONE successfully 3!', pump3)
                print('---------------------------------')
            elif line.startswith('RAM1:'):
                RAM1_num = float(line[5:])
                sequence_RAM1 += 1
                print(sequence_RAM1,'.','RAM usage of first RPI pico is:', RAM1_num,'%')
                print('---------------------------------')
            elif line.startswith('RAM2:'):
                RAM2_num = float(line[5:])
                sequence_RAM2 += 1
                print(sequence_RAM2,'.','RAM usage of second RPI pico is:', RAM2_num,'%')
                print('---------------------------------')
            elif line.startswith('RAM3:'):
                RAM3_num = float(line[5:])
                sequence_RAM3 += 1
                print(sequence_RAM3,'.','RAM usage of third RPI pico is:', RAM3_num,'%')
                print('---------------------------------')
        await asyncio.sleep(0.2)

async def control_RPI():
    global client1_IP, client2_IP, client3_IP
    global URL_discord_ERR, header_ERR
    while True:
        ping1 = os.system(f"ping -c 1 {client1_IP} > /dev/null 2>&1")
        if ping1 == 0:
            print('First RPI pico is ONLINE')
            print('---------------------------------')
        else:
            print('First RPI pico is OFLLINE!!!!!!! Please check connection!!!!!!!')
            print('---------------------------------')
        await asyncio.sleep(3600)       

async def control_RPI2():
    global client1_IP, client2_IP, client3_IP
    global URL_discord_ERR, header_ERR
    while True:
        ping2 = os.system(f"ping -c 1 {client2_IP} > /dev/null 2>&1")
        if ping2 == 0:
            print('Second RPI pico is ONLINE')
            print('---------------------------------')
        else:
            print('Second RPI pico is OFLLINE!!!!!!! Please check connection!!!!!!!')
            print('---------------------------------')
        await asyncio.sleep(3600)  

async def control_RPI3():
    global client1_IP, client2_IP, client3_IP
    global URL_discord_ERR, header_ERR
    while True:
        ping3 = os.system(f"ping -c 1 {client3_IP} > /dev/null 2>&1")
        if ping3 == 0:
            print('Third RPI pico is ONLINE')
            print('---------------------------------')
        else:
            print('Third RPI pico is OFLLINE!!!!!!! Please check connection!!!!!!!')
            print('---------------------------------')
        await asyncio.sleep(3600) 

async def data_send():
    global hm1, temp1, door1, pump1, response, response2, response3, response4
    global RAM1_num, RAM2_num, RAM3_num, requests
    global URL, API1, API2, API3, API_RAM
    global data, header, header_ERR, URL_discord, URL_discord_ERR
    while True:
        try:
            response = requests.get(f"{URL}?api_key={API1}&field1={hm1}&field2={temp1}&field3={door1}&field4={pump1}")
            print('Data was send!!')
            print('---------------------------------')
        except Exception as e:
            print('Error appaers when sending data! System control is necessary! - SEMI closed greenhouse')
            print('---------------------------------')
            data = {
                "content": "@simon9104 ERROR appears when sending data to THINGSPEAK - SEMI closed greenhouse"
            }
            requests.post(URL_discord_ERR, data=data, headers=header_ERR)
        try:
            response2 = requests.get(f"{URL}?api_key={API2}&field1={hm2}&field2={temp2}&field3={door2}&field4={pump2}")
            print('Data was send!!')
            print('---------------------------------')
        except Exception as e:
            print('Error appaers when sending data! System control is necessary! - Fully closed greenhouse')
            print('---------------------------------')
            data = {
                "content": "@simon9104 ERROR appears when sending data to THINGSPEAK - Fully closed greenhouse"
            }
            requests.post(URL_discord_ERR, data=data, headers=header_ERR)
        try:
            response3 = requests.get(f"{URL}?api_key={API3}&field1={hm3}&field2={temp3}&field3={door3}&field4={pump3}")
            print('Data was send!!')
            print('---------------------------------')
        except Exception as e:
            print('Error appaers when sending data! System control is necessary! - free planting')
            print('---------------------------------')
            data = {
                "content": "@simon9104 ERROR appears when sending data to THINGSPEAK - free planting"
            }
            requests.post(URL_discord_ERR, data=data, headers=header_ERR)
        try:
            response4 = requests.get(f"{URL}?api_key={API_RAM}&field1={RAM1_num}&field2={RAM2_num}&field3={RAM3_num}")
            print('Data was send!!')
            print('---------------------------------')
        except Exception as e:
            print('Error appaers when sending data! System control is necessary! - RAM information')
            print('---------------------------------')
            data = {
                "content": "@simon9104 ERROR appears when sending data to THINGSPEAK - RAM information"
        }
            requests.post(URL_discord_ERR, data=data, headers=header_ERR)
        await asyncio.sleep(120)

async def transfer_discord():
    global hm1, header, data, RAM1_num, RAM2_num, RAM3_num, requests
    while True:
        data = {
            "content": f"Data usage of first RPI pico is: {RAM1_num} \nData usage of second RPI pico is: {RAM2_num} \nData usage of second RPI pico is: {RAM3_num}" 
        }
        requests.post(URL_discord, data=data, headers=header)
        print('Discord massage was send!!')
        print('---------------------------------')
        await asyncio.sleep(7200)

async def backup_data():
    global hm1, hm2, hm3
    global temp1, temp2, temp3
    global door1, door2, door3
    global pump1, pump2, pump3
    results = []
    while True:
        now = datetime.datetime.now()
        data = {
            'Time': now.strftime("%Y-%m-%d %H:%M:%S"),
            'Humidity SC': hm1,
            'TP SC': temp1,
            'DRRS SC': door1,
            'PS SC': pump1,
            'HM C': hm2,
            'TP C': temp2,
            'DRRS C': door2,
            'PS C': pump2,
            'HM FREE': hm3,
            'TP FREE': temp3,
            'DRRS FREE': door3,
            'PS FREE': pump3
        }
        results.append(data)
        df = pd.DataFrame(results)
        df.to_csv('backup_data_server.csv', index=False)
        print('Backup data was saved successfully!!')
        print('---------------------------------')
        await asyncio.sleep(600)

async def main():
    asyncio.create_task(data_recv())
    asyncio.create_task(data_send())
    asyncio.create_task(transfer_discord())
    asyncio.create_task(backup_data())
    asyncio.create_task(control_RPI())
    asyncio.create_task(control_RPI2())
    asyncio.create_task(control_RPI3())
    while True:
        await control_RPI()
        await control_RPI2()
        await control_RPI3()
        print('program is running!')
        await asyncio.sleep(120)

asyncio.run(main())
