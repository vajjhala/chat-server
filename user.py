import socket
import argparse
import threading


rlock = threading.RLock()


def byte2string(byte_data):
    return str(byte_data, "utf-8")


def string2byte(string_data):
    return bytes(string_data, "utf-8")


class User(threading.Thread):

    global rlock

    def __init__(self, socket_):
        super().__init__()
        assert isinstance(socket_, ClientApp)
        self.socket = socket_

    def run(self):
        try:
            while True :
                recv_buffer = self.socket.recv_data()
                # keep receiving data
                with rlock:
                    all_msgs = recv_buffer.split(';')
                    # process and print one message after the other

                    for msg in all_msgs:
                        split_msg = msg.split(' ')
                        msg_tag = split_msg[0]

                        if msg_tag == '#statusPosted':
                            print(">>#statusPosted")

                        elif msg_tag == '#welcome':
                            print(">>'{}' connected to server on {}".format(self.socket.username, self.socket.address))

                        elif msg_tag == "#busy":
                            print(">>**Server busy**")
                            break

                        elif msg_tag == "#newStatus":
                            print(">>new status from '{}'': {}".format(split_msg[1], " ".join(split_msg[2:])))

                        elif msg_tag == "#newuser":
                            print(">>new user '{}' has joined the app".format(split_msg[1]))

                        elif msg_tag == "#Leave":
                            print(">>'{}' has left the app".format(split_msg[1]))

                        elif msg_tag == "#Bye":
                            print(">>Exiting app ...")
                            break

                        elif msg_tag == "#friendme":
                            print(">>received friend request from {}: type '@friend {}' to accept  OR type '@deny {}' "
                                  "to reject".format(split_msg[1], split_msg[1], split_msg[1]))

                        elif msg_tag == "#OKfriends":
                            print(">>{} and {} are now friends".format(split_msg[1], split_msg[2]))

                        elif msg_tag == "#FriendRequestDenied":
                            print(">>{} denied your friend request".format(split_msg[1]))

                        elif msg_tag == "#NotFriends":
                            print(">>{} and {} are no more friends".format(split_msg[1], split_msg[2]))

                        elif msg_tag == "#group":
                            print(">>{} is now in group {}".format(split_msg[2], split_msg[1]))

                        elif msg_tag == "#gstatus":
                            print(">>[{}] [{}] {}".format(split_msg[1], split_msg[2], " ".join(split_msg[3:])))

                        elif msg_tag == "#ungroup":
                            print(">>{} is no longer a member of group {}".format(split_msg[2], split_msg[1]))

                    else:
                        continue

                    break

            with self.socket.lock:
                self.socket.close_socket()

        except OSError or ConnectionError:
            with self.socket.lock:
                self.socket.close_socket()
            print("Disconnecting ...")


class SendTh(threading.Thread):

    global rlock

    def __init__(self, client_socket):
        super().__init__()
        self.socket = client_socket

    def run(self):
        try:
            while not self.socket.is_closed:
                with rlock:
                    user_post = input("<<")
                split_post = user_post.split(' ')
                data_tag = split_post[0]

                if data_tag == "@connect":
                    msg = "#friendme {}".format(split_post[1])
                    self.socket.send_data(msg)

                elif data_tag == "@deny":
                    msg = "#DenyFriendRequest {}".format(split_post[1])
                    self.socket.send_data(msg)

                elif data_tag == "@friend":
                    msg = "#friends {}".format(split_post[1])
                    self.socket.send_data(msg)

                elif data_tag == "@disconnect":
                    msg = "#unfriend {}".format(split_post[1])
                    self.socket.send_data(msg)

                elif data_tag == "@add":
                    msg = "#group {} {}".format(split_post[1], split_post[2])
                    self.socket.send_data(msg)

                elif data_tag == "@send":
                    msg = "#gstatus {} {} {}".format(split_post[1], self.socket.username, " ".join(split_post[2:]))
                    self.socket.send_data(msg)

                elif data_tag == "@delete":
                    msg = "#ungroup {} {}".format(split_post[1], split_post[2])
                    self.socket.send_data(msg)

                else:
                    self.socket.send_data(user_post)

        except OSError or ConnectionError or KeyboardInterrupt:
            print("Disconnecting ..")
            self.socket.send_data("Exit")

        self.socket.close_socket()


class ClientApp():

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.address = (self.host, self.port)
        self.is_closed = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lock = threading.Lock()
        self.username = "{} + {}".format(host, port)

    def connect(self):
        try:
            self.socket.connect(self.address)
        except OSError as ex:
            with self.lock:
                self.close_socket()


    def recv_data(self):
        data = byte2string(self.socket.recv(1024).strip())
        return data

    def send_data(self, message):
        self.socket.sendall(string2byte(message))

    def close_socket(self):
        with self.lock:
            self.close_socket()
            self.is_closed = True


def run_client(client_socket):
    global rlock
    client_socket.connect()
    try:

        user_thread = User(client_socket)
        user_thread.start()

        with rlock:
            username = input("Enter username: ")
        client_socket.username = username
        client_socket.send_data("#join {}".format(username))

        send_thread = SendTh(client_socket)
        send_thread.start()

    except OSError or ConnectionError or KeyboardInterrupt:
        client_socket.send_data("Exit")
        with client_socket.lock:
            client_socket.close_socket()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', dest='host', help='specify remote server name or ip-address', default=socket.gethostname())
    parser.add_argument('-p', dest='port', help='specify port number', default=58732, type=int)
    ARGS = parser.parse_args()
    HOST, PORT = ARGS.host, ARGS.port
    client = ClientApp(HOST, PORT)
    try:
        run_client(client)
    except KeyboardInterrupt:
        client.close_socket()
