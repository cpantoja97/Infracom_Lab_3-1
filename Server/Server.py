from socket import *
from threading import Thread
from threading import Lock
from boltons import socketutils
import hashlib
import time


class ClientThread(Thread):
    def __init__(self, connection, address):
        Thread.__init__(self)
        self.socket = connection
        self.ns_socket = socketutils.NetstringSocket(connection)
        print("[+] New server socket thread started for " + address[0] + ":" + str(address[1]))

    def send_message(self, message):
        self.ns_socket.write_ns(message.encode())

    def send_file(self, chunk):
        self.ns_socket.write_ns(chunk)

    def receive_message(self):
        return self.ns_socket.read_ns().decode()

    def run(self):
        global numReady
        conn = self.ns_socket

        # Client confirmation
        self.send_message(READY)
        cli = self.receive_message()

        if cli != READY:
            raise

        # Increase number of ready clients
        numReadyLock.acquire()
        numReady += 1
        numReadyLock.release()

        # Actively wait until all clients are ready
        while numReady < numClients:
            continue

        hash_fn = hashlib.sha256()
        file = open('./' + DIRECTORY + '/' + fileName, "rb")
        total_sent = 0
        chunks = 0

        self.send_message(FILE_NAME + SEP + fileName)

        # SEND FILE...
        self.send_message(FILE_INIT)
        f_read = file.read(BUFFER_SIZE)
        t0 = time.time()  # Start timer
        while len(f_read) > 0:
            self.send_file(f_read)
            # total_sent += sent
            chunks += 1
            hash_fn.update(f_read)
            f_read = file.read(BUFFER_SIZE)
        t1 = time.time()  # End timer
        self.send_message(FILE_END)

        self.send_message(HASH + SEP + hash_fn.hexdigest())

        # Client confirmation (OK | ERROR)
        cli = self.receive_message()
        print(cli)
        print("Socket will close")
        self.socket.close()


# PROTOCOL COMMANDS IN CASE THEY ARE CHANGED
READY = 'READY'
FILE_NAME = 'FILE_NAME'
SEP = ':'
FILE_INIT = 'FILE_INIT'
FILE_END = 'FILE_END'
HASH = 'HASH'
OK = 'OK'
ERROR = 'ERROR'
DELIMITER = ';'

# Server options
DIRECTORY = 'Files'
numClients = 1  # should be asked
fileName = 'IMG_3051.JPG'  # should be asked

# Sync shared variables
numReady = 0
numReadyLock = Lock()

# Socket Params
SERVER_PORT = 12000
BUFFER_SIZE = 4096

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('', SERVER_PORT))

threads = []

while True:
    serverSocket.listen(25)
    print('The server is ready to receive')

    connectionSocket, address = serverSocket.accept()

    newThread = ClientThread(connectionSocket, address)
    newThread.start()

    threads.append(newThread)

for t in threads:
    t.join()
