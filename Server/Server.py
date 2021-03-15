from socket import *
from threading import Thread
from threading import Lock
import hashlib
import time


class ClientThread(Thread):
    def __init__(self, connection, address, ):
        Thread.__init__(self)
        self.connection = connection
        print("[+] New server socket thread started for " + address[0] + ":" + str(address[1]))

    def run(self):
        global numReady
        conn = self.connection

        # Client confirmation
        conn.send(READY.encode())
        cli = conn.recv(BUFFER_SIZE).decode()

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
        file = open('./' + DIRECTORY + '/' + fileName)
        total_sent = 0
        chunks = 0

        conn.send((FILE_NAME + SEP + fileName).encode())

        # SEND FILE...
        conn.send(FILE_INIT.encode())
        f_read = file.read(BUFFER_SIZE)
        t0 = time.time()  # Start timer
        while len(f_read) > 0:
            print(f_read)
            sent = conn.send(f_read.encode())
            total_sent += sent
            chunks += 1
            hash_fn.update(f_read.encode())
            f_read = file.read(BUFFER_SIZE)
        t1 = time.time()  # End timer
        conn.send(FILE_END.encode())

        conn.send((HASH + SEP + hash_fn.hexdigest()).encode())

        # Client confirmation (OK | ERROR)
        conn.recv(BUFFER_SIZE).decode()
        conn.close()


# PROTOCOL COMMANDS IN CASE THEY ARE CHANGED
READY = 'READY'
FILE_NAME = 'FILE_NAME'
SEP = ':'
FILE_INIT = 'FILE_INIT'
FILE_END = 'FILE_END'
HASH = 'HASH'
OK = 'OK'
ERROR = 'ERROR'

# Server options
DIRECTORY = 'Files'
numClients = 1  # should be asked
fileName = 'Prueba.txt'  # should be asked

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
