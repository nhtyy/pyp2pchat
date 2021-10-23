import threading
import socket
import time


n = False
global NODE_CONN
global my_node
global peer
HEADER = 64
# SERVER_IP # CHANGE TO PEER FOR CONNECTING IN FUTURE USING INPUT
FORMAT = 'utf-8'
DISCONNECT = "DISCONNECT"
ROOMS_MSG = {}
ROOM_MEMBER = {}
ROOM_MEMBER_NODES = {}  # implement check if node current peer goes down, switch to next node in list
current_room = ""
server_addr = ""
PEERS = []


def handle_connect(conn, addr):
    connected = True
    # Add Send ROOM_MEMBER_NODES list , ROOMS TO EACH NODE
    current_room_conn = ""
    while connected:
        broadcast = ""
        msg_length = conn.recv(HEADER).decode(FORMAT)  # 64 BYTE HEADER MSG CONTAINING LENGTH OF ACTUAL MSG
        if msg_length:  # IF LENGTH IS NOT 0
            msg = conn.recv(int(msg_length)).decode(FORMAT)  # WAIT FOR MSG SIZE MSG_LENGTH

            if msg == "!N":
                global NODE_CONN
                NODE_CONN = conn

            if msg == "!P":
                PEERS.append(conn)

            if msg[0:2] == "!R":
                room = msg[2:len(msg)]

                if len(current_room_conn) >= 1:
                    ROOM_MEMBER[current_room_conn].remove(conn)
                    if len(ROOM_MEMBER[current_room_conn]) == 0:
                        ROOMS_MSG.pop(current_room_conn)

                current_room_conn = room
                if room in ROOM_MEMBER:  # CHECK TO SEE IF ROOM IS CREATED IF NOT CREATE IT , ADD ALERT OF JOIN
                    ROOM_MEMBER[room].append(conn)
                    broadcast = joined(addr, room)
                else:
                    ROOM_MEMBER[room] = []
                    ROOM_MEMBER[room].append(conn)  # send index to dict for proper disconnects

                if room in ROOMS_MSG:
                    for value in ROOMS_MSG[room]:
                        connsend(conn, "!K" + room)
                        connsend(conn, value)
                else:
                    if peer_addr == server_addr:
                        ROOMS_MSG[room] = []
                        logs = "New Room Created! [{}]".format(room)
                        connsend(conn, "!K" + room)
                        connsend(conn, logs)
                        broadcast = (joined(addr, room))
                    else:
                        ROOMS_MSG[room] = []
                        send(msg)  # sends message too peer if not 0 peer
                        time.sleep(1)

            if msg[0:2] == "!K":  # ROuter COMMAND
                room = msg[2:len(msg)]
                msg_size = conn.recv(HEADER).decode(FORMAT)
                msg_text = conn.recv(int(msg_size))

                if peer_addr != server_addr and conn != NODE_CONN:
                    if NODE_CONN not in ROOM_MEMBER[room]:
                        connsend(NODE_CONN, msg)
                        connsend(NODE_CONN, msg_text.decode(FORMAT))

                if room in ROOM_MEMBER:
                    for x in ROOM_MEMBER[room]:
                        if x != conn:
                            connsend(x, msg)
                            x.send(msg_size.encode(FORMAT))
                            x.send(msg_text)

                for PEER in PEERS:
                    if conn != PEER:
                        if PEER not in ROOM_MEMBER[room]:
                            connsend(PEER, msg)
                            connsend(PEER, msg_text.decode(FORMAT))

                if room in ROOMS_MSG:
                    ROOMS_MSG[room].append(msg_text.decode(FORMAT))

            if msg == "!D":
                connnected = False
                ROOM_MEMBER[current_room_conn].remove(conn)
                if len(ROOM_MEMBER[current_room_conn]) == 0:
                    ROOMS_MSG.pop(current_room_conn)

                break

            if broadcast:  # send mesasge to EVERY room member
                for x in ROOM_MEMBER[current_room_conn]:
                    connsend(x, "!K" + current_room_conn)
                    connsend(x, broadcast)

                if peer_addr == server_addr:
                    ROOMS_MSG[room].append(broadcast)

    conn.close()


def handle_init():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(server_addr)  # MY IP
    server.listen()
    global n
    n = True
    print(f"[INIT] Server Is Listening on {server_addr} , you must port forward to fully participate in the network..")
    while True:
        conn, addr = server.accept()
        always_connect = threading.Thread(target=handle_connect, args=(conn, addr))
        always_connect.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 2}")


def syncwithpeer(peer_addr):
    connect = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connect.connect(peer_addr)  # change to user input .... should be IP / port of peer
    global peer
    peer = connect
    print("[SYNCED]")
    global n
    if n:
        if server_addr != peer_addr:
            connect = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connect.connect(server_addr)  # change to user input .... should be IP / port of peer
            global my_node
            my_node = connect


def joined(addr, room):
    msg = "[{}] Has Joined the Room".format(addr)
    return msg


def receive():  # send everything received from peer to node
    while True:
        msg_length = peer.recv(HEADER).decode(FORMAT)
        if msg_length:
            data = peer.recv(int(msg_length)).decode(FORMAT)
            if data[0:2] == "!K":
                room = data[2:len(data)]
                msg_length = peer.recv(HEADER).decode(FORMAT)
                data = peer.recv(int(msg_length)).decode(FORMAT)
                if n and peer_addr != server_addr:
                    send_to_node("!K" + room)
                    send_to_node(data)

                if current_room == room:
                    print(f"{data}")
            else:
                pass


def get_from_node():  # everything that i recieve from the node send to peer
    while True:
        msg_length = my_node.recv(HEADER).decode(FORMAT)
        if msg_length:
            data = my_node.recv(int(msg_length)).decode(FORMAT)
            if data[0:2] == "!K":
                room = data[2:len(data)]
                msg_length = my_node.recv(HEADER).decode(FORMAT)
                data = my_node.recv(int(msg_length)).decode(FORMAT)
                send("!K" + room)
                send(data)

                if current_room == room:
                    print(f"{data}")
            else:
                pass


def enter_room(room):
    room = room.upper()
    print(f"-----------------[{room}]------------------------------------")
    if n and server_addr != peer_addr:
        send_to_node("!R" + room)
    else:
        send("!R" + room)

    global current_room
    current_room = room


def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    msg_length = str(msg_length).encode(FORMAT)
    msg_length += b' ' * (HEADER - len(msg_length))
    peer.send(msg_length)
    peer.send(message)


def send_to_node(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    msg_length = str(msg_length).encode(FORMAT)
    msg_length += b' ' * (HEADER - len(msg_length))
    my_node.send(msg_length)
    my_node.send(message)


def connsend(conn, msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    msg_length = str(msg_length).encode(FORMAT)
    msg_length += b' ' * (HEADER - len(msg_length))
    conn.send(msg_length)
    conn.send(message)


v = input("[RUN AS NODE?] [Y/N]")
if v == 'Y' or v == 'y':
    ip = input("[IP TO BIND SERVER INSTANCE] >>> ")
    if ip == "":
        ip = socket.gethostbyname(socket.gethostname())

    port = input("[PORT] >>> ")
    server_addr = (ip, int(port))
    print("[STARTING] Server Is Starting....")
    init = threading.Thread(target=handle_init)
    init.start()
else:
    pass

time.sleep(2)
print("[PEER INFO]")
ip = input("[IP] >>> ")
if ip == "":
    ip = socket.gethostbyname(socket.gethostname())

port = input("[PORT] >>> ")
peer_addr = (ip, int(port))  # change to -> if blank , peer is node server.
print(f"[SYNCING] ::::: [{ip}][{port}]")
syncwithpeer(peer_addr)


always_receive = threading.Thread(target=receive)
always_receive.start()

if server_addr != peer_addr and n:
    get_from_node_ = threading.Thread(target=get_from_node)
    get_from_node_.start()
    send_to_node("!N")
    send("!P")

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
        room_router = "!K" + current_room

        if n and server_addr != peer_addr:
            send_to_node(room_router)
            send_to_node(your_msg)
            send(room_router)
            send(your_msg)
        else:
            send(room_router)
            send(your_msg)
