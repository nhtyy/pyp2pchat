import threading
import socket
import time


class Server:

    FORMAT = 'utf-8'
    DISCONNECT = "DISCONNECT"
    HEADER = 64

    def __init__(self):
        self.server_addr = ""
        self.peer_addr = ''
        self.my_node = None
        self.peer = None
        self.ROOMS_MSG = {}
        self.ROOM_MEMBER = {}
        self.ROOM_MEMBER_NODES = {}
        self.roomRequest = None
        self.CONNECTIONS = []  # Eventually implent a new routing system using ID for conn objects?# ?
        self.start()

    def handle_connect(self, conn, addr):
        connected = True
        # Add Send ROOM_MEMBER_NODES list , ROOMS TO EACH NODE
        current_room_conn = ""
        node = False
        while connected:
            broadcast = ""
            msg_length = conn.recv(Server.HEADER).decode(Server.FORMAT)
            if msg_length:  # IF LENGTH IS NOT 0
                msg = conn.recv(int(msg_length)).decode(Server.FORMAT)  # WAIT FOR MSG SIZE MSG_LENGTH

                # if node , only remove
                if msg == "!N":
                    node = True

                if msg[0:2] == "!B":
                    room = msg[2:len(msg)]
                    self.ROOM_MEMBER[room].remove(conn)

                # Get Room info

                if msg[0:2] == "!R":
                    room = msg[2:len(msg)]

                    if current_room_conn:
                        if len(self.ROOM_MEMBER[current_room_conn]) >= 1:
                            if node is not True:
                                self.ROOM_MEMBER[current_room_conn].remove(conn)

                        if len(self.ROOM_MEMBER[current_room_conn]) == 0:
                            self.ROOMS_MSG.pop(current_room_conn)
                            if self.server_addr != self.peer_addr:
                                self.send_to_peer("!B" + current_room_conn)  # Removes your node from
                                                                             # ROOM_MEMBER of peer

                    current_room_conn = room
                    if room in self.ROOM_MEMBER:
                        self.ROOM_MEMBER[room].append(conn)
                        broadcast = self.joined(addr)
                    else:
                        self.ROOM_MEMBER[room] = []
                        self.ROOM_MEMBER[room].append(conn)  # send index to dict for proper disconnects

                    if room in self.ROOMS_MSG:
                        for value in self.ROOMS_MSG[room]:
                            self.connsend(conn, "!K" + room)
                            self.connsend(conn, value)
                    else:
                        if self.peer_addr == self.server_addr:
                            self.ROOMS_MSG[room] = []
                            logs = "New Room Created! [{}]".format(room)
                            self.connsend(conn, "!K" + room)
                            self.connsend(conn, logs)
                            broadcast = (self.joined(addr))
                        else:
                            self.ROOMS_MSG[room] = []
                            self.send_to_peer(msg)  # sends message too peer if you have a peer
                            self.roomRequest = conn
                            time.sleep(1)

                if msg[0:2] == "!K":  # ROuter COMMAND
                    room = msg[2:len(msg)]
                    msg_size = conn.recv(Server.HEADER).decode(Server.FORMAT)
                    msg_text = conn.recv(int(msg_size))

                    if self.server_addr != self.peer_addr:
                        if conn != self.CONNECTIONS[0]:
                            self.send_to_peer(msg)
                            self.send_to_peer(msg_text.decode(Server.FORMAT))

                    for x in self.ROOM_MEMBER[room]:
                        if x != conn:
                            self.connsend(x, msg)
                            x.send(msg_size.encode(Server.FORMAT))
                            x.send(msg_text)

                    self.ROOMS_MSG[room].append(msg_text.decode(Server.FORMAT))

                if broadcast:  # send mesasge to EVERY room member
                    for x in self.ROOM_MEMBER[current_room_conn]:
                        self.connsend(x, "!K" + current_room_conn)
                        self.connsend(x, broadcast)

                    if self.peer_addr == self.server_addr:
                        self.ROOMS_MSG[current_room_conn].append(broadcast)

    def joined(self, addr):
        msg = "[{}] Has Joined the Room".format(addr)
        return msg

    def connsend(self, conn, msg):
        message = msg.encode(Server.FORMAT)
        msg_length = len(message)
        msg_length = str(msg_length).encode(Server.FORMAT)
        msg_length += b' ' * (Server.HEADER - len(msg_length))
        conn.send(msg_length)
        conn.send(message)

    def handle_init(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(self.server_addr)  # MY IP
        server.listen()
        print(
            f"[INIT] Server Is Listening {self.server_addr}, you must port forward to fully participate"
            f" in the network..")
        while True:
            conn, addr = server.accept()
            always_connect = threading.Thread(target=self.handle_connect, args=(conn, addr))
            always_connect.start()
            self.CONNECTIONS.append(conn)
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 3}")

    def syncwithpeer(self):
        connect = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connect.connect(self.peer_addr)  # change to user input .... should be IP / port of peer
        self.peer = connect
        self.send_to_peer("!N")
        print("[SYNCED]")

        if self.server_addr != self.peer_addr:
            connect = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connect.connect(self.server_addr)  # change to user input .... should be IP / port of peer
            self.my_node = connect

    def send_to_peer(self, msg):
        message = msg.encode(Server.FORMAT)
        msg_length = len(message)
        msg_length = str(msg_length).encode(Server.FORMAT)
        msg_length += b' ' * (Server.HEADER - len(msg_length))
        self.peer.send(msg_length)
        self.peer.send(message)

    def send_to_node(self, msg):
        message = msg.encode(Server.FORMAT)
        msg_length = len(message)
        msg_length = str(msg_length).encode(Server.FORMAT)
        msg_length += b' ' * (Server.HEADER - len(msg_length))
        self.my_node.send(msg_length)
        self.my_node.send(message)

    def receive(self):  # send everything received from peer to node
        while True:
            msg_length = self.peer.recv(Server.HEADER).decode(Server.FORMAT)
            if msg_length:
                data = self.peer.recv(int(msg_length)).decode(Server.FORMAT)
                if data[0:2] == "!K":
                    room = data[2:len(data)]
                    msg_length = self.peer.recv(Server.HEADER).decode(Server.FORMAT)
                    data = self.peer.recv(int(msg_length)).decode(Server.FORMAT)

                    if self.roomRequest is not None:
                        self.connsend(self.roomRequest, "!K" + room)
                        self.connsend(self.roomRequest, data)
                        self.roomRequest = None
                    else:
                        self.send_to_node("!K" + room)
                        self.send_to_node(data)

    def start(self):
        # Starts Your Server
        ip = input("[IP TO BIND SERVER INSTANCE] >>> ")
        if ip == "":
            ip = socket.gethostbyname(socket.gethostname())

        server_port = input("[PORT] >>> ")
        self.server_addr = (ip, int(server_port))
        print("[STARTING] Server Is Starting....")
        init = threading.Thread(target=self.handle_init)
        init.start()

        time.sleep(1)
        # Connects to Peer
        print("[PEER INFO]")
        ip = input("[IP] >>> ")
        if ip == "":
            ip = socket.gethostbyname(socket.gethostname())

        port = input("[PORT] >>> ")
        if port == "":
            port = server_port
        self.peer_addr = (ip, int(port))  # change to -> if blank , peer is node server.
        print(f"[SYNCING] ::::: [{ip}][{port}]")
        self.syncwithpeer()

        always_receive = threading.Thread(target=self.receive)
        always_receive.start()
