
class Utils:
    FORMAT = 'utf-8'
    DISCONNECT = "DISCONNECT"
    HEADER = 64

    @staticmethod
    def joined(addr):
        msg = "[{}] Has Joined the Room".format(addr)
        return msg

    @staticmethod
    def connsend(conn, msg):
        message = msg.encode(Utils.FORMAT)
        msg_length = len(message)
        msg_length = str(msg_length).encode(Utils.FORMAT)
        msg_length += b' ' * (Utils.HEADER - len(msg_length))
        conn.send(msg_length)
        conn.send(message)
