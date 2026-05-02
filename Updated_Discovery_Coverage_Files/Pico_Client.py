import time
import network
import socket
import machine import Pin

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('SM-G960W9196', 'yzup6802')
while wlan.isconnected() == False:
    print('Waiting for connection...')
    time.sleep(1)
print(wlan.ifconfig())
ip = wlan.ifconfig()[0]
print(f'Connected on {ip}')
Pin("LED", Pin.OUT).on()

BUFF_SIZE = 100
Port = 16000
buff = ""
data = " "
packet_type = 'A'
packet_data = " "
my_ip = wlan.ifconfig()[0]

IP_Address = "255.255.255.255"  # Change this to your local IP Address with the last part being .255
timer = 0
print(my_ip)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
already_connected = 0
sock_TCP = 0
sock.bind(("0.0.0.0", 16000))
condition_start_time = time.time()
while True:
    time.sleep(2)
    timer = timer + 1
    elapsed_time = time.time() - condition_start_time
    try:
        data, addr = sock.recvfrom(BUFF_SIZE)
        data = data.decode()
        print("CLIENT : Received:", data, "from", addr)
        # if my_ip == addr[0]:
        #    raise ValueError("Same IP Address as yourself")
        packet_type = data[0]
        packet_data = data[1:]
        print("CLIENT : type:", packet_type, "data:", packet_data)
    except:
        print("\nCLIENT : An exception occurred\n")
        continue

    if packet_type == "R":
        if already_connected == 0:
            packet_type = "R"
            packet_data = "Ready to Connect"
            buff = packet_type.encode() + packet_data.encode()
            sock.sendto(buff, (addr[0], addr[1]))

            packet_type = data[0]
            packet_data = data[1:]
            while data[0] != "B":
                data, addr = sock.recvfrom(BUFF_SIZE)
                data = data.decode()
            packet_type = data[0]
            packet_data = data[1:]
            sock_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            try:
                sock_TCP.connect((addr[0], int(packet_data)))

                data = sock_TCP.recv(BUFF_SIZE)
                data = data.decode()
                packet_type = data[0]
                packet_data = data[1:]
                print("CLIENT: server data\n", packet_data, "\n")
                if packet_type == "T":
                    print("CLIENT : Successfully added to network")
                    already_connected = 1

            except OSError:
                print("CLIENT : TCP connection failed")
        if already_connected == 1 and elapsed_time >= 7:
            print("CLIENT: Already connected, rebroadcasting")
            sock.sendto(data.encode(), (IP_Address, Port))
            condition_start_time = time.time()
    if packet_type == "M" and already_connected == 1:
        packet_data = packet_data[1:]
        parts = packet_data.split("|", 4)
        dest_ip = parts[0]
        dest_port = parts[1]
        loop_count = int(parts[2]) + 1
        msg = parts[3]
        Pin("LED", Pin.OUT).off()
        if dest_ip == my_ip:
            print("CLIENT: Received message: " + msg)
        elif loop_count - 1 < 3:  # Forward it
            if dest_ip != my_ip:
                msg = "M|" + dest_ip + "|" + str(dest_port) + "|" + str(loop_count) + "|" + msg
                sock.sendto(msg.encode(), ("10.158.5.255", Port))
                time.sleep(0.5)
        elif loop_count - 1 > 3:
            print("Message discarded, reached max loop count")

    if packet_type == "C" and already_connected == 1:
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
            with open('drone_GPS_Coords.csv', mode='w') as file:
                file.write("Longitude,Latitude,Height\n")
                file.write(longi + "," + lat + "," + height + "\n")
                print(file.read())
            print("\n\n LONG: " + longi + " LAT: " + lat)

        elif loop_count - 1 < 3:
            if dest_ip != my_ip:
                msg = "C|" + dest_ip + "|" + str(dest_port) + "|" + str(loop_count) + "|" + parts[3]
                sock.sendto(msg.encode(), (IP_Address, Port))
                time.sleep(0.5)
        elif loop_count - 1 > 3:
            print("Message discarded, reached max loop count")

    if packet_type == "R" and already_connected == 1 and timer == 4:
        timer = 0
        msg = "A|0|" + my_ip
        sock.sendto(msg.encode(), (IP_Address, Port + 1))
        print("CLIENT: succesfully sent ACK")

    if packet_type == "A":
        parts = packet_data.split("|", 3)
        loop_count = int(parts[1]) + 1
        if loop_count < 3:
            msg = "A|" + str(loop_count) + "|" + my_ip
            sock.sendto(msg.encode(), (IP_Address, Port + 1))
            print("CLIENT: successfully rebroadcast ACK")

    if packet_type == "Q":
        parts = packet_data.split("|", 2)
        loop_count = int(parts[1]) + 1
        if loop_count < 3:
            msg = "Q|" + str(loop_count) + "|" + parts[2]
            sock.sendto(msg.encode(), (IP_Address, Port + 1))
            print("CLIENT: successfully rebroadcast MQTT data")
    time.sleep(2)
