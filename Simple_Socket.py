# Author Martin Pek
# 2CP - TeamEscape - Engineering

'''
Todo:
fringe case where we dont restart the pi with the socket....
OSError: [Errno 98] Address already in use
https://stackoverflow.com/questions/6380057/python-binding-socket-address-already-in-use
'''

import socket
from threading import Thread
from time import sleep


class TESocketServer:
    def __init__(self, port):
        self.clients = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # this fixes socket.error: [Errno 98] Address already in use
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # empty IP means its will accept from any connection, we could predefine some later
        # for now its only used on the Pi and GM potentially in the future
        self.sock.bind(("", port))
        # maximum of 5 connection allowed
        self.sock.listen(5)
        # sock.settimeout(5)
        thread = Thread(target=self.__manage_sockets)
        thread.start()

    def __manage_sockets(self):
        print('starting to seek clients on the socket server')
        while True:
            client, address = self.sock.accept()
            self.clients.append(client)
            print('Got connection from', address)

    def transmit(self, line):
        line = line.rstrip() + "\n"
        line = line.encode()
        for client in self.clients:
            try:
                client.send(line)
            except socket.error as msg:
                print("Socket transmission Error: {}".format(msg))
                print("a client dropped")
                self.clients.remove(client)


class SocketClient:
    # trials to create a client (0 or less will try forever,
    #                            1 will not connect at all
    #                            2 or more will try trials -1 times)
    def __init__(self, ip, port, timeout=None):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.buffer = []
        thread = Thread(target=self.__run_socket_client)
        thread.start()

    def __connect(self):
        try:
            self.s.connect((self.ip, self.port))
            print("client has connected to {}:{}".format(self.ip, self.port))
        except socket.error as msg:
            self.s.close()
            print(msg)
            return False
        return True

    def __received(self):
        try:
            lines = self.s.recv(1024)
            if type(lines) is not str:
                for line in lines.splitlines():
                    line = line.decode()
                    # Todo: buffer overflow? mby have a ringbuffer? limited size?
                    self.buffer.append(line)
                    print(line)
            return True
        except socket.timeout:
            return False

    def __run_socket_client(self):
        while True:
            self.successful = False
            s = socket.socket()
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.settimeout(self.timeout)
            self.s = s
            print('socket client looking for connection')
            if self.__connect():
                while self.__received():
                    try:
                        self.s.send(bytes("Ping", "UTF-8"))
                    except socket.error:
                        break
            else:
                sleep(1)

    def read_buffer(self):
        ret = self.buffer
        self.buffer = []
        return ret

    def transmit(self, line):
        line = line.rstrip() + "\n"
        line = line.encode()
        try:
            self.s.send(line)
        except socket.error as msg:
            print("Socket transmission Error: {}".format(msg))


if __name__ == "__main__":
    print("not imported")
    SocketClient('127.0.0.1', 12345)

