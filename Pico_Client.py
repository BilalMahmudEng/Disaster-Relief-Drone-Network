# Author : Bilal Mahmud
# Raspberry Pi Pico W Client

import time
import network
import socket
import machine
import bme680
from bme680 import BME680_I2C
from machine import I2C, Pin

# Connecting to Network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('', '')
while wlan.isconnected() == False:
    print('Waiting for connection...')
    time.sleep(1)
print(wlan.ifconfig())
ip = wlan.ifconfig()[0]
print(f'Connected on {ip}')
led = machine.Pin("LED", machine.Pin.OUT)
led.toggle()

# Setting Sensor SDA and SCL Pins to 0 and 1 respectively
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=500000)
sensor = BME680_I2C(i2c, 0x77)

# Initial Setup
BUFF_SIZE = 100
Port = 16000
buff = ""
data = " "
packet_type = 'A'
packet_data = " "
my_ip = wlan.ifconfig()[0]
IP_Address = "255.255.255.255"
timer = 0
print(my_ip)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
already_connected = 0
sock_TCP = 0
sock.bind(("0.0.0.0", 16000))
condition_start_time = time.time()

# Main loop
while True:
    time.sleep(5)
    # watchdog timer
    timer = timer + 1
    elapsed_time = time.time() - condition_start_time

    # Receiving Packets
    try:
        data, addr = sock.recvfrom(BUFF_SIZE)
        data = data.decode()
        print("CLIENT : Received:", data, "from", addr)
        if my_ip == addr[0]:
           raise ValueError("Same IP Address as yourself")
        packet_type = data[0]
        packet_data = data[1:]
        print("CLIENT : type:", packet_type, "data:", packet_data)
    except:
        continue

    # Acknowledges Server Broadcast, contests to network, otherwise rebroadcasts the packet
    if packet_type == "R":
        if already_connected == 0:
            packet_type = "R"
            packet_data = "Ready to Connect"
            buff = packet_type.encode() + packet_data.encode()
            sock.sendto(buff, (addr[0], addr[1]))

            while data[0] != "T":
                data, addr = sock.recvfrom(BUFF_SIZE)
                data = data.decode()
                resend_counter = resend_counter + 1
                if resend_counter == 3000000:
                    packet_type = "R"
                    packet_data = "Ready to Connect"
                    buff = packet_type.encode() + packet_data.encode()
                    sock.sendto(buff, (addr[0], addr[1]))
                    resend_counter = 0
            packet_type = data[0]
            packet_data = data[1:]
            if packet_type == "T":
                print("CLIENT: Successfully added to network")
                already_connected = 1

        if already_connected == 1 and elapsed_time >= 7:
            print("CLIENT: Already connected, rebroadcasting")
            sock.sendto(data.encode(), (IP_Address, Port))
            condition_start_time = time.time()

    if already_connected == 1:

        # For MQTT formatted Packets
        if packet_type == "M":
            packet_data = packet_data[1:]
            parts = packet_data.split("|", 4)
            dest_ip = parts[0]
            dest_port = parts[1]
            loop_count = int(parts[2]) + 1
            msg = parts[3]
            led.toggle()
            if dest_ip == my_ip:
                print("CLIENT: Received message: " + msg)
            elif loop_count - 1 < 3:
                if dest_ip != my_ip:
                    msg = "M|" + dest_ip + "|" + str(dest_port) + "|" + str(loop_count) + "|" + msg
                    sock.sendto(msg.encode(), (IP_Address, Port))
                    time.sleep(0.5)
            elif loop_count - 1 > 3:
                print("Message discarded, reached max loop count")

        # Receiving GPS Coordinates, saving to CSV file and sending to Drone App
        if packet_type == "C":
            packet_data = packet_data[1:]
            parts = packet_data.split("|", 4)
            dest_ip = parts[0]
            dest_port = parts[1]
            loop_count = int(parts[2]) + 1
            msg = parts[3]
            if dest_ip == my_ip:
                print("CLIENT: Received message: " + msg)
                gps = msg.split(",")
                longi = gps[0]
                lat = gps[1]
                height = gps[2]
                header = ['Longitude', 'Latitude', 'Height']
                data = [[longi, lat, height]]
                sock.sendto("(" + longi + "," + lat + "," + height + ")", ("192.168.0.15", 16000))
                with open('drone_GPS_Coords.csv', mode='w') as file:
                    file.write("Longitude,Latitude,Height\n")
                    file.write(longi + "," + lat + "," + height + "\n")
                    print(file.read())
                print("\n\n LONG: " + longi + " LAT: " + lat)
                print("\nSent to Drone App")

            elif loop_count - 1 < 3:
                if dest_ip != my_ip:
                    msg = "C|" + dest_ip + "|" + str(dest_port) + "|" + str(loop_count) + "|" + parts[3]
                    sock.sendto(msg.encode(), (IP_Address, Port))
                    time.sleep(0.5)
            elif loop_count - 1 > 3:
                print("Message discarded, reached max loop count")

        # Sending Acknowledgment to Server that it is still in the netwrok
        if packet_type == "R" and timer == 4:
            timer = 0
            msg = "A|0|" + my_ip
            sock.sendto(msg.encode(), (IP_Address, Port))
            print("CLIENT: succesfully sent ACK")

        # Rebroadcasting of packets
        if packet_type == "Q" or packet_type == "S" or packet_type == "A":
            parts = packet_data.split("|", 3)
            loop_count = int(parts[1]) + 1
            if loop_count < 3:
                if packet_type == "A":
                    msg = "A|" + str(loop_count) + "|" + my_ip
                    sock.sendto(msg.encode(), (IP_Address, Port))
                    print("CLIENT: successfully rebroadcast ACK")
                elif packet_type == "Q" or packet_type == "S":
                    msg = packet_type + "|" + str(loop_count) + "|" + parts[2]
                    sock.sendto(msg.encode(), (IP_Address, Port))
                    if packet_type == "S":
                        print("CLIENT: successfully rebroadcast Sensor data")
                    if packet_type == "Q":
                        print("CLIENT: successfully rebroadcast MQTT data")

        # Taking in Sensor Data and sending to server
        temp = round(sensor.temperature, 2)
        humid = round(sensor.humidity, 2)
        gas = sensor.gas
        data = str(temp) + "," + str(humid) + "," + str(gas)
        print("CLIENT: sensor data = " + data)
        msg = "S|" + "0|" + my_ip + "|16000|" + data
        sock.sendto(msg.encode(), (IP_Address, Port))