from threading import Thread
import socket
import sys
import json


class Server():
    def __init__(self, host='', port=1337):
        self.host = host
        self.port = port
        self.backlog = 5
        self.server = None
        self.threads = []

    def open_socket(self):
        try:
            self.server = socket.socket()
            self.server.bind((self.host, self.port))
            self.server.listen(self.backlog)
            self.server.setblocking(0)
        except socket.error:
            if self.server:
                self.server.close()
            sys.exit('Could not open socket')
        print('Server running on port', self.port)

    def start(self):
        self.open_socket()
        self.running = True
        while self.running:
            try:
                c = Connection(self.server, *self.server.accept())
                c.start()
                self.threads.append(c)
                print('Connection from', c.addr)
                self.broadcast('{} has joined the server'.format(c.addr), c)
            except socket.error:
                print ('Connection aborted')

    def broadcast(self, data, client=None):
        for c in self.threads:
            if c is not client:
                try:
                    c.client.send(
                        json.dumps({'type': 'msg', 'data': data}).encode())
                except:
                    self.threads.remove(c)

    def terminate(self):
        self.running = False
        self.server.close()
        for c in self.threads:
            try:
                c.client.send(json.dumps({'type': 'close'}).encode())
            except:
                self.threads.remove(c)
            c.join()
        self.join()
        sys.exit()


class Client():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.size = 1024
        self.conn = None

    def connect(self):
        try:
            self.conn = socket.socket()
            self.conn.connect((self.host, self.port))
        except socket.error:
            if self.conn:
                self.conn.close()
            sys.exit('Could not connect to socket')
        print('Connected to {}:{}'.format(self.host, self.port))

    def run(self):
        self.connect()
        self.running = True
        while self.running:
            try:
                data = json.loads(self.conn.recv(self.size).decode())
            except:
                data = ''
            if not data or data['type'] == 'close':
                print('Server closed')
                self.terminate()
            print(data['data'])

    def terminate(self):
        self.running = False
        self.conn.close()
        try:
            self.join()
        finally:
            sys.exit()


class Connection(Thread):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.size = 1024
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            data = self.conn.recv(self.size).decode()
            try:
                data = json.loads(self.client.recv(self.size).decode())['data']
            except:
                data = ''
            if data:
                msg = '{}: "{}"'.format(
                    self.addr, data)
                self.server.broadcast(msg, self)
                print(msg)
            else:
                self.client.close()
                print(self.addr, 'disconnected')
                self.server.broadcast('{} has left the server'
                    .format(self.addr))

    def terminate(self):
        self.running = False
        self.conn.close()


if __name__ == '__main__':
    try:
        if sys.argv[1] == '-s':
            s = Server()
            s.start()

        elif sys.argv[2]:
            c = Client(sys.argv[1], int(sys.argv[2]))
            c.start()

    except IndexError:
        print('Usage: python {} [-s | addr port] '.format(__file__))
