import threading
import socket
import time

global peer
HEADER = 64
# SERVER_IP # CHANGE TO PEER FOR CONNECTING IN FUTURE USING INPUT
ADDR = () # should point to local ipv4 for to init a server
FORMAT = 'utf-8'
DISCONNECT = "DISCONNECT"
ROOMS = {}
ROOM_MEMBER = {}
ROOM_MEMBER_NODES = {}  # implement check if node current peer goes down, switch to next node in list
POS = {}


def handle_connect(conn, addr):  # Add check if node
    connected = True
    # Add Send ROOM_MEMBER_NODES list , ROOMS TO EACH NODE
    room = ""
    while connected:
        broadcast = ""
        msg_length = conn.recv(HEADER).decode(FORMAT)  # 64 BYTE HEADER MSG CONTAINING LENGTH OF ACTUAL MSG
        if msg_length:  # IF LENGTH IS NOT 0
            msg = conn.recv(int(msg_length)).decode(FORMAT)   # WAIT FOR MSG SIZE MSG_LENGTH

            if msg == DISCONNECT:
                connected = False
                break  # add removal of conn objects from ROOM_MEMBER
            elif msg[0:2] == "!R":
                if len(room) >= 1:
                    ROOM_MEMBER[room].remove(conn)
                    if len(ROOM_MEMBER[room]) < 1:
                        ROOMS.pop(room)

                room = msg[2:len(msg)]
                if room in ROOM_MEMBER:  # CHECK TO SEE IF MEMBER OF ROOM, ADD ALERT OF JOIN
                    POS[addr] = ROOM_MEMBER[room].append(conn)
                else:
                    ROOM_MEMBER[room] = []
                    POS[addr] = ROOM_MEMBER[room].append(conn)  # send index to dict for proper disconnects

                if room in ROOMS:  # check if new room
                    for value in ROOMS[room]:
                        h = value.encode(FORMAT)
                        h = len(h)
                        h = str(h).encode(FORMAT)
                        h += b' ' * (HEADER - len(h))
                        conn.send(h)
                        conn.send(value.encode(FORMAT))
                        broadcast = joined(addr)
                else:
                    ROOMS[room] = []
                    new_room = "[New Room] [{}] Created!".format(room)
                    new_room = new_room.encode(FORMAT)
                    rl = len(new_room)
                    rl = str(rl).encode(FORMAT)
                    rl += b' ' * (HEADER - len(rl))
                    conn.send(rl)
                    conn.send(new_room)
                    ROOMS[room].append(new_room.decode(FORMAT))
                    broadcast = joined(addr)
            else:
                for x in ROOM_MEMBER[room]:
                    if x != conn:
                        x.send(msg_length.encode(FORMAT))
                        x.send(msg.encode(FORMAT))

                ROOMS[room].append(msg)

            if broadcast:  # send mesasge to EVERY room member
                rl = len(broadcast.encode(FORMAT))
                rl = str(rl).encode(FORMAT)
                rl += b' ' * (HEADER - len(rl))
                for x in ROOM_MEMBER[room]:
                    x.send(rl)
                    x.send(broadcast.encode(FORMAT))

                ROOMS[room].append(broadcast)

    conn.close()


def handle_init():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)  # MY IP
    server.listen()
    print(f"[INIT] Server Is Listening on {ADDR} , you must port forward to fully participate in the network..")
    while True:
        conn, addr = server.accept()
        always_connect = threading.Thread(target=handle_connect, args=(conn, addr))
        always_connect.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 2}")


def syncwithpeer(addr):
    connect = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connect.connect(addr)  # change to user input .... should be IP / port of peer
    global peer
    peer = connect
    print("[SYNCED]")


def joined(addr):
    msg = "[{}] Has Joined the Room".format(addr)
    return msg


def receive():
    while True:
        msg_length = peer.recv(HEADER).decode(FORMAT)
        if msg_length:
            data = peer.recv(int(msg_length)).decode(FORMAT)
            print(f"{data}")


def enter_room(room):
    room = room.upper()
    send("!R" + room)
    print(f"-----------------[{room}]------------------------------------")


def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    msg_length = str(msg_length).encode(FORMAT)
    msg_length += b' ' * (HEADER - len(msg_length))
    peer.send(msg_length)
    peer.send(message)


v = input("[RUN AS NODE?] [Y/N]")
if v == 'Y' or v == 'y':
    ip = input("[IP TO BIND SERVER INSTANCE] >>> ")
    port = input("[PORT] >>> ")
    ADDR = (ip, int(port))
    print("[STARTING] Server Is Starting....")
    init = threading.Thread(target=handle_init)
    init.start()
else:
    pass

time.sleep(2)
print("[PEER INFO]")
ip = input("[IP] >>> ")
port = input("[PORT] >>> ")
addr = (ip, int(port))
syncwithpeer(addr)
print(f"[SYNCING] ::::: [{ip}][{port}]")

always_receive = threading.Thread(target=receive)
always_receive.start()

NAME = input("[Screen Name] >>> ")
ROOM = input("[Room ID] >>> ")
enter_room(ROOM)

while True:
    your_msg = input(">>> ")

    if your_msg == "!D":
        send(DISCONNECT)
    elif your_msg == "!R":
        ROOM = input("[Room ID] >>> ")
        enter_room(ROOM)
    else:
        t = time.localtime()
        current_time = time.strftime("[%H:%M:%S] ", t)
        your_msg = "[{}]".format(NAME) + current_time + your_msg
        send(your_msg)
