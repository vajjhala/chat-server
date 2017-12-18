import socket
import argparse
import threading
from collections import defaultdict


def byte2string(byte_data):
    return str(byte_data, "utf-8")


def string2byte(string_data):
    return bytes(string_data, "utf-8")


class ClientThread(threading.Thread):
    """
    Client thread handling class. A seperate thread for each client
    """
    def __init__(self, client_socket, client_address, server_socket, index):
        super().__init__()
        assert isinstance(server_socket, SocialServer)
        assert isinstance(client_socket, socket.socket)
        self.client = client_socket
        self.server = server_socket
        self.client_address = client_address
        self.client_name = client_address
        self.index = index
        self.is_member = False


    def run(self):
        try:
            recv_data = self.server.get_data(self.client)
            recv_split = recv_data.split(' ')
            recv_tag = recv_split[0]

            if recv_tag == "#join":
                self.server.send_data(self.client, '#welcome;')
                self.client_name = recv_split[1]
                self.server.broadcast_others("#newuser {};".format(self.client_name), self.client_address)
                self.server.address_book[self.client_name] = self.client
                # print(self.server.address_book)
                print('{} joined'.format(self.client_name))

            while True:
                recv_data = self.server.get_data(self.client)
                if not recv_data:
                    break
                recv_split = recv_data.split(' ')
                recv_tag = recv_split[0]

                if recv_tag == '#status':
                    self.server.send_data(self.client, '#statusPosted')
                    for friend in self.server.friends[self.client_name]:
                        self.server.unicast("#newStatus {} {};".format(self.client_name, " ".join(recv_split[1:])),
                                            friend)
                    print('{} posted: {}'.format(self.client_name, recv_data))

                elif recv_tag == "Exit":
                    self.server.send_data(self.client, "#Bye")
                    self.server.broadcast_others("#Leave {};".format(self.client_name), self.client_address)
                    print("{} has exited".format(self.client_name))
                    break

                elif recv_tag == "#friendme":
                    self.server.unicast("#friendme {};".format(self.client_name), recv_split[1])

                elif recv_tag == "#friends":
                    self.server.friends[self.client_name].add(recv_split[1])
                    self.server.friends[recv_split[1]].add(self.client_name)
                    for dest in [recv_split[1], self.client_name]:
                        self.server.unicast("#OKfriends {} {};".format(self.client_name, recv_split[1]), dest)
                    print("{} and {} are now friends".format(self.client_name, recv_split[1]))

                elif recv_tag == "#DenyFriendRequest":
                    self.server.unicast("#FriendRequestDenied {};".format(self.client_name), recv_split[1])

                elif recv_tag == "#unfriend":
                    self.server.friends[self.client_name].discard(recv_split[1])
                    self.server.friends[recv_split[1]].discard(self.client_name)
                    self.server.broadcast("#NotFriends {} {};".format(self.client_name, recv_split[1]))
                    print("{} and {} are not friends".format(self.client_name, recv_split[1]))

                elif recv_tag == "#group":
                    group_name = recv_split[1]
                    if (self.client_name in self.server.groups[group_name] or (not self.server.groups[group_name]))\
                            and (recv_split[2] in self.server.friends[self.client_name]):
                        self.server.groups[group_name].add(recv_split[2])
                        self.server.groups[group_name].add(self.client_name)
                        for member in self.server.groups[group_name]:
                            self.server.unicast("{};".format(recv_data), member)
                        print("group {} created by {} and {} added".format(recv_split[1],
                                                                           self.client_name, recv_split[2]))

                elif recv_tag == "#gstatus":
                    group_name = recv_split[1]
                    if self.client_name in self.server.groups[group_name]:
                        for member in self.server.groups[group_name]:
                            self.server.unicast("{};".format(recv_data), member)
                        print("group {} status: {}".format(recv_split[1], recv_split[2]))

                elif recv_tag == "#ungroup":
                    group_name = recv_split[1]
                    if (self.client_name in self.server.groups[group_name]
                         and recv_split[2] in self.server.groups[group_name]):

                        for member in self.server.groups[group_name]:
                            self.server.unicast("{};".format(recv_data), member)
                        print("{} removed from  {} by {}".format(recv_split[2], recv_split[1], self.client_name))

            with self.server.lock:
                self.server.clients[self.index] = None
                self.client.close()

        except OSError or ConnectionError:
            with self.server.lock:
                self.server.clients[self.index] = None

            print("{} has exited".format(self.client_name))


class SocialServer():
    """
    The main server class with helper functions defined.

    """

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.address = (self.host, self.port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = list()
        self.socket_closed = False
        # Stores list of friends by user-name.
        self.friends = defaultdict(set)
        # Address book is a user-name to socket dictionary.
        self.address_book = dict()
        # A group-name to user-names list dictionary
        self.groups = defaultdict(set)
        self.lock = threading.Lock()

    def bind(self):
        try:
            self.socket.bind(self.address)
        except OSError as ex:
            print("Address {} already in use".format(self.socket.getsockname()))
            self.close_socket()
            print("{}".format(ex))

    def listen(self, backlog):
        try:
            self.socket.listen(backlog)
        except OSError as ex:
            self.close_socket()
            print("Unable to set socket bound to {} to listen".format(self.address))
            print("Try Again in a minute")

    def accept(self):
        try:
            client_socket, client_address = self.socket.accept()
            return client_socket, client_address
        except Exception as ex:
            print("Unable to accept a connection now".format(ex))

    def get_data(self, client_socket):
        data = byte2string(client_socket.recv(1024).strip())
        return data

    def send_data(self, client_socket, data):
        client_socket.sendall(string2byte(data))

    def broadcast(self, data):
        for client in self.clients:
            if client is not None:
                assert isinstance(client, ClientThread)
                self.send_data(client.client, data)
            else:
                continue

    def broadcast_others(self, data, client_address):
        for other_client in self.clients:
            if other_client is not None:
                assert isinstance(other_client, ClientThread)
                if other_client.client_address != client_address:
                    self.send_data(other_client.client, data)
            else:
                continue

    def multicast(self, data, client_name):
        for friend in self.friends[client_name]:
            assert isinstance(friend, SocialServer)
            self.send_data(friend.socket, data)

    def unicast(self, data, dest_clientname):
        self.send_data(self.address_book[dest_clientname], data)

    def close_socket(self):
        self.socket.close()
        self.socket_closed = True


def run_server(server_socket, max_clients):
    """
    The main function that runs the sever

    server_socket: a Social Server class object
    max_clients: an integer for the maximum clients the server can connect to

    """
    assert isinstance(server_socket, SocialServer)
    server_socket.bind()
    server_socket.listen(max_clients)
    server_socket.clients = [None] * max_clients
    while not server_socket.socket_closed:

        client_socket, client_address = server_socket.accept()

        if None in server_socket.clients:

            index = server_socket.clients.index(None)
            client_thread = ClientThread(client_socket, client_address, server_socket, index)

            with server_socket.lock:
                server_socket.clients[index] = client_thread

            client_thread.start()

        else:
            server_socket.send_data(client_socket, "#busy;")
            client_socket.close()
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', dest='port', help='specify port number', default=58732, type=int)
    parser.add_argument('-c', dest='clients', help='maximum number of clients', default=5, type=int)
    ARGS = parser.parse_args()
    HOST, PORT = socket.gethostname(), ARGS.port
    print("Social App running on HOSTNAME - {} \n".format(HOST))
    server = SocialServer(HOST, PORT)
    try:
        run_server(server, ARGS.clients)
    except KeyboardInterrupt:
        server.close_socket()
