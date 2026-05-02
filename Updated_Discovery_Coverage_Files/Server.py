# This is a sample Python script.
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import socket
import time
import MaxCoverage

BUFF_SIZE = 100
Port = 16000

# IP_Address = "255.255.255.255"
IP_Address = "255.255.255.255"  # Change this to your local IP Address with the last part being .255
watchdog_max = 50

buff = ""
data = " "

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
packet_type = 'A'
packet_data = " "
sock.bind(("0.0.0.0", 16001))

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # doesn't actually send data
        return s.getsockname()[0]
    finally:
        s.close()

my_ip = get_local_ip()
print("My local IP is:", my_ip)

sock.setblocking(False)

sock_TCP = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(8)]
TCP_IP_Addresses = [" " for _ in range(10)]
TCP_Ports = [0 for _ in range(10)]
watchdog_timer = [0 for _ in range(10)]


def send_csv_all_drones():
    active = [i3 for i3, port in enumerate(TCP_Ports) if port != 0]
    num_of_nodes = len(active)
    area_length = 3
    area_width = 1.5
    coverage_radius = 0.5
    ref_long = 79.38083
    ref_lat = 43.65891
    cell_size = 0.5
    data1 = MaxCoverage.MaxCoverage(num_of_nodes, area_length, area_width, coverage_radius, ref_long, ref_lat, cell_size)
    for i1, drone_i1 in enumerate(active):
        node = data1[i1]
        msg = str(node[0]) + "," + str(node[1]) + "," + str(node[2])
        send_to_drone(msg, TCP_IP_Addresses[drone_i1], TCP_Ports[drone_i1], 1)

        print("SERVER: Sent GPS Coordinates to all nodes")


def send_to_drone(MSG, target_IP, target_Port, csv):
    msg = "M|" + target_IP + "|" + str(target_Port) + "|0|" + MSG
    if csv == 1:
        msg = "C|" + target_IP + "|" + str(target_Port) + "|0|" + MSG

    index = -1
    for i, port in enumerate(TCP_Ports):
        if port != 0:
            index = i
            break

    if index != -1:
        try:
            print(f"SERVER: sending to first drone in list: {TCP_IP_Addresses[index]}:{TCP_Ports[index]}")
            sock.sendto(msg.encode(), (TCP_IP_Addresses[index], TCP_Ports[index]))
        except Exception as e:
            print(f"SERVER: UDP send failed: {e}")
    else:
        print("SERVER:No active drones found to send the message.")


op = 0
while True:

    time.sleep(5)

    for i, port in enumerate(TCP_Ports):
        if TCP_Ports[i] != 0:
            watchdog_timer[i] = watchdog_timer[i] + 1
        if watchdog_timer[i] == watchdog_max:
            print("SERVER: removed from network due to inactivity")
            sock_TCP[i].close()
            sock_TCP[i] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            TCP_IP_Addresses[i] = " "
            TCP_Ports[i] = 0
            send_csv_all_drones()

    print("\nTo Start")
    print("SERVER PRINTING:", TCP_IP_Addresses)
    packet_type = 'R'

    packet_data = "Asking for IP Address"
    buff = packet_type.encode() + packet_data.encode()
    sock.sendto(buff, (IP_Address, Port))
    print("SERVER : Sent ", buff)

    try:

        data, addr = sock.recvfrom(BUFF_SIZE)
        data = data.decode()
        print("SERVER : Received:", data, "from", addr)
        # if my_ip == addr[0]:
        #    raise ValueError("Same IP Address as yourself")
        print("SERVER PRINTING:", TCP_IP_Addresses)

        packet_type = data[0]
        packet_data = data[1:]
        print("SERVER :type:", packet_type, "data:", packet_data)

    except:
        for index, a in enumerate(sock_TCP):
            try:
                a.send(b'')
            except OSError:
                a.close()
                sock_TCP[index] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                TCP_IP_Addresses[index] = " "
                TCP_Ports[index] = 0

        continue

    if packet_type == "R":
        print("SERVER : Received:", addr[0], "from", addr[1])
        for index, a in enumerate(sock_TCP):
            open_socket = 0
            try:
                a.send(b'')
                print("SERVER :Socket is active")
            except OSError:
                open_socket = 1
                print("SERVER : Socket is open")
            if open_socket == 1:
                packet_type = "B"
                packet_data = str(16001 + index)
                buff = packet_type.encode() + packet_data.encode()
                sock.sendto(buff, addr)

                a.bind(("0.0.0.0", 16001 + index))
                a.listen()
                c, TCP_addr = a.accept()

                TCP_IP_Addresses[index] = addr[0]
                TCP_Ports[index] = addr[1]
                sock_TCP[index] = c

                packet_type = "T"
                packet_data = "Successfully connected"
                buff = packet_type.encode() + packet_data.encode()
                c.send(buff)
                print("SERVER :Successfully added to list of sockets")
                send_csv_all_drones()
                break
    if packet_type == "A":
        parts = packet_data.split("|", 3)
        for i, ip in enumerate(TCP_IP_Addresses):
            if ip == parts[2]:
                watchdog_timer[i] = -2
                print(f"SERVER: Successfully reset watchdog timer for {ip}")

    if packet_type == "Q":

        parts = packet_data.split("|", 3)
        ip = my_ip
        if ip == parts[2]:
            print(f"SERVER: Sending MQTT Packet to Database")
            with open("MQTT_data.txt", "w") as file:
                file.write(parts[3])


