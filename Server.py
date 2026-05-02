# Author : Bilal Mahmud
# Main Server

import socket
import time
import MaxCoverage

# Variable Setup
BUFF_SIZE = 100
Port = 16000
IP_Address = "255.255.255.255"
watchdog_max = 100
buff = ""
data = " "

# Creating UDP Socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
packet_type = 'A'
packet_data = " "
sock.bind(("0.0.0.0", 16000))


# Obtaining Local IP
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


my_ip = get_local_ip()
print("My local IP is:", my_ip)

#  Setting socket to Non-Blockinh
sock.setblocking(False)

# Storing All Drones' IP, their watchdog timer and sensor data
UDP_IP_Addresses = [" " for _ in range(10)]
UDP_Ports = [0 for _ in range(10)]
watchdog_timer = [0 for _ in range(10)]

# Sensor data is a String containing "temperature (°C),humidity (%),air quality (Ohms)"
sensor_data = [[] for _ in range(10)]

when_to_time = 0
op = 0


# Sending GPS Coordinates to all drones
def send_all_drones():
    active = [i3 for i3, port in enumerate(UDP_Ports) if port != 0]
    num_of_nodes = len(active)
    area_length = 3
    area_width = 1.5
    coverage_radius = 0.5
    ref_long = 79.38083
    ref_lat = 43.65891
    cell_size = 0.5
    data1 = MaxCoverage.MaxCoverage(num_of_nodes, area_length, area_width, coverage_radius, ref_long, ref_lat,
                                    cell_size)
    for i1, drone_i1 in enumerate(active):
        node = data1[i1]
        msg = str(node[0]) + "," + str(node[1]) + "," + str(node[2])
        send_to_drone(msg, UDP_IP_Addresses[drone_i1], UDP_Ports[drone_i1], 1)

        print("SERVER: Sent GPS Coordinates to all nodes")


# Sending to individual drone
def send_to_drone(MSG, target_IP, target_Port, csv):
    msg = "M|" + target_IP + "|" + str(target_Port) + "|0|" + MSG
    if csv == 1:
        msg = "C|" + target_IP + "|" + str(target_Port) + "|0|" + MSG

    index = -1
    for i, port in enumerate(UDP_Ports):
        if port != 0:
            index = i
            break

    if index != -1:
        try:
            print(f"SERVER: sending to first drone in list: {UDP_IP_Addresses[index]}:{UDP_Ports[index]}")
            sock.sendto(msg.encode(), (UDP_IP_Addresses[index], UDP_Ports[index]))
        except Exception as e:
            print(f"SERVER: UDP send failed: {e}")
    else:
        print("SERVER:No active drones found to send the message.")


#  Main loop
while True:
    # Watchdog Timer only runs when server processes outer packets (not its own)
    if when_to_time == 0:
        time.sleep(2)
        for i, port in enumerate(UDP_Ports):
            if UDP_Ports[i] != 0:
                watchdog_timer[i] = watchdog_timer[i] + 1
            if watchdog_timer[i] == watchdog_max:
                print("SERVER: removed from network due to inactivity")
                UDP_IP_Addresses[i] = " "
                UDP_Ports[i] = 0
                sensor_data[i] = []
                watchdog_timer[i] = 0
                send_all_drones()

    # Initial Broadcast
    print("\nTo Start")
    print("SERVER PRINTING:", UDP_IP_Addresses)
    packet_type = 'R'

    packet_data = "Asking for IP Address"
    buff = packet_type.encode() + packet_data.encode()
    sock.sendto(buff, (IP_Address, Port))
    print("SERVER : Sent ", buff)

    try:
        # Receiving data, will skip its own packets
        data, addr = sock.recvfrom(BUFF_SIZE)
        data = data.decode()
        print("SERVER : Received:", data, "from", addr)
        if my_ip == addr[0] or addr[0] == "127.0.0.1":
            when_to_time = 1
            time.sleep(0.1)
            continue
        when_to_time = 0
        print("SERVER PRINTING:", UDP_IP_Addresses)

        packet_type = data[0]
        packet_data = data[1:]
        print("SERVER :type:", packet_type, "data:", packet_data)
    except:
        continue

    # Adds the drone to list and calculates the best GPS Coordinates when server gets a response
    if packet_type == "R":
        print("SERVER : Received:", addr[0], "from", addr[1])
        if addr[0] not in UDP_IP_Addresses:
            open_socket = 0
            for index, a in enumerate(UDP_IP_Addresses):
                if UDP_IP_Addresses[index] == " ":
                    open_socket = 1
                if open_socket == 1:
                    packet_type = "T"
                    packet_data = "Successfully connected"
                    buff = packet_type.encode() + packet_data.encode()
                    sock.sendto(buff, addr)

                    UDP_IP_Addresses[index] = addr[0]
                    UDP_Ports[index] = addr[1]

                    print("SERVER: Successfully added to list")
                    send_all_drones()
                    break

    # Resetting Watchdog Timer
    if packet_type == "A":
        parts = packet_data.split("|", 3)
        for i, ip in enumerate(UDP_IP_Addresses):
            if ip == parts[2]:
                watchdog_timer[i] = -2
                print(f"SERVER: Successfully reset watchdog timer for {ip}")

    # For sending an MQTT formatted packet to a database
    if packet_type == "Q":
        parts = packet_data.split("|", 3)
        ip = my_ip
        if ip == parts[2]:
            print(f"SERVER: Sending MQTT Packet to Database")
            with open("MQTT_data.txt", "w") as file:
                file.write(parts[3])

    # Saving Sensor Data
    if packet_type == "S":
        parts = packet_data.split("|", 4)
        data = parts[4]
        for i, ip in enumerate(UDP_IP_Addresses):
            if ip == parts[2]:
                if data not in sensor_data[i]:
                    # FIFO Based storage for sensor data
                    sensor_data[i].append(parts[4])
                    if len(sensor_data[i]) == 7:
                        sensor_data[i].pop(0)
                    print(f"SERVER: Recieved Sensor data")
                    print(sensor_data[i])
    time.sleep(5)
