from flask import Flask
from flask import jsonify
from flask import request
import socket
import threading
import time

ROOMS_MSG = {}
app = Flask(__name__)


@app.route("/<room>", methods=['GET'])
def enter_room(room):
    room = room.upper()
    if room not in ROOMS_MSG:
        send("!R" + room)
        time.sleep(1)
    return jsonify(ROOMS_MSG[room])


@app.route("/send", methods=['POST'])
def message():
    msg = request.json  # !K or !R + ROOMID + (MESSAGE)

    if "router" in msg:
        send(msg["router"])
        send(msg["msg"])
    return ('', 201)


##################SOCKETS##############################


ROOMS_MSG = {}

FORMAT = 'utf-8'
DISCONNECT = "DISCONNECT"
HEADER = 64
ip = socket.gethostbyname(socket.gethostname())  # hardcode ip and port
port = 2021

peer_addr = (ip, int(port))
connect = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connect.connect(peer_addr)


def send(msg):
    msg = msg.encode(FORMAT)
    msg_length = len(msg)
    msg_length = str(msg_length).encode(FORMAT)
    msg_length += b' ' * (HEADER - len(msg_length))
    connect.send(msg_length)
    connect.send(msg)


def receive():
    while True:
        msg_length = connect.recv(HEADER).decode(FORMAT)
        if msg_length:
            data = connect.recv(int(msg_length)).decode(FORMAT)
            if data[0:2] == "!K":
                room = data[2:len(data)]
                msg_length = connect.recv(HEADER).decode(FORMAT)
                msg = connect.recv(int(msg_length)).decode(FORMAT)

                if room in ROOMS_MSG:
                    ROOMS_MSG[room].append(msg)
                else:
                    ROOMS_MSG[room] = []
                    ROOMS_MSG[room].append(msg)


always_receive = threading.Thread(target=receive)
always_receive.start()
