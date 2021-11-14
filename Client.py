import socket
import threading
import time



class Client:

    FORMAT = 'utf-8'
    DISCONNECT = "DISCONNECT"
    HEADER = 64

    def __init__(self):
        self.peer = None
        self.peer_addr = ''
        self.start()

    def receive(self):  # send everything received from peer to node
        while True:
            msg_length = self.peer.recv(Client.HEADER).decode(Client.FORMAT)
            if msg_length:
                data = self.peer.recv(int(msg_length)).decode(Client.FORMAT)
                if data[0:2] == "!K":
                    msg_length = self.peer.recv(Client.HEADER).decode(Client.FORMAT)
                    data = self.peer.recv(int(msg_length)).decode(Client.FORMAT)
                    print(f"{data}")
                else:
                    pass

    def start(self):
        print("[PEER INFO]")
        ip = input("[IP] >>> ")
        if ip == "":
            ip = socket.gethostbyname(socket.gethostname())
        port = input("[PORT] >>> ")
        peer_addr = (ip, int(port))  # change to -> if blank , peer is node server.
        print(f"[SYNCING] ::::: [{ip}][{port}]")

        connect = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connect.connect(peer_addr)  # change to user input .... should be IP / port of peer
        self.peer = connect
        print("[SYNCED]")

        always_receive = threading.Thread(target=self.receive)
        always_receive.start()


def send(msg):
    message = msg.encode(Client.FORMAT)
    msg_length = len(message)
    msg_length = str(msg_length).encode(Client.FORMAT)
    msg_length += b' ' * (Client.HEADER - len(msg_length))
    new_client.peer.send(msg_length)
    new_client.peer.send(message)


def enter_room(room):
    room = room.upper()
    print(f"-----------------[{room}]------------------------------------")
    send("!R" + room)
    global current_room
    current_room = room


current_room = ''
new_client = Client()
NAME = input("[Screen Name] >>> ")
ROOM = input("[Room ID] >>> ")
enter_room(ROOM)

while True:
    your_msg = input(">>> ")

    if your_msg == "!D":
        send(Client.DISCONNECT)
    elif your_msg == "!R":
        ROOM = input("[Room ID] >>> ")
        enter_room(ROOM)
    else:
        t = time.localtime()
        current_time = time.strftime("[%H:%M:%S] ", t)
        your_msg = "[{}]".format(NAME) + current_time + your_msg
        room_router = "!K" + current_room
        send(room_router)
        send(your_msg)
