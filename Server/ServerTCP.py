from socket import *
from threading import Thread
from threading import Lock
from boltons import socketutils
import hashlib
import time
import datetime
import pathlib

from Server.ServerView import select


class ClientThread(Thread):
    def __init__(self, connection, address, fileSelect, fileSize):
        Thread.__init__(self)
        self.address = address
        self.fileSelect = fileSelect
        self.fileSize = fileSize
        self.socket = connection
        self.ns_socket = socketutils.NetstringSocket(connection)
        print("[+] New server socket thread started for " + address[0] + ":" + str(address[1]))

    def send_message(self, message):
        self.ns_socket.write_ns(message.encode())

    def send_file(self, chunk):
        self.ns_socket.write_ns(chunk)

    def receive_message(self):
        return self.ns_socket.read_ns().decode()

    def print_info(self, info):
        print("[" + self.address[0] + ":" + str(self.address[1]) + "] " + info)

    def run(self):
        global numReady
        conn = self.ns_socket

        # Client confirmation
        self.send_message(READY)
        cli = self.receive_message()
        if cli != READY:
            raise Exception(self.address + " Received " + cli + " instead of READY")
        self.print_info("Client ready")

        # Increase number of ready clients
        numReadyLock.acquire()
        numReady += 1
        numReadyLock.release()

        # Actively wait until all clients are ready
        while numReady < clients:
            continue
        hash_fn = hashlib.sha256()
        file = open('./' + DIRECTORY + '/' + fileSelect, "rb")
        bytes_sent = 0
        chunks_sent = 0

        self.send_message(FILE_NAME + SEP + fileSelect)

        # SEND FILE...
        self.send_message(FILE_INIT)
        f_read = file.read(BUFFER_SIZE)
        t0 = time.time()  # Start timer
        while len(f_read) > 0:
            self.send_file(f_read)
            bytes_sent += len(f_read)
            chunks_sent += 1
            hash_fn.update(f_read)
            f_read = file.read(BUFFER_SIZE)
        t1 = time.time()  # End timer
        self.send_message(FILE_END)
        self.print_info("File transferred")

        self.send_message(HASH + SEP + hash_fn.hexdigest())

        # Client confirmation (OK | ERROR)
        cli = self.receive_message()
        self.print_info("Client status " + cli)

        # Client bytes and packets received
        cli = self.receive_message()
        [bytes_received, chunks_received] = cli.split(":")
        self.print_info("Client received " + str(bytes_received) + " bytes")
        self.print_info("Client received " + str(chunks_received) + " packets")

        self.socket.close()

        log(self.address, datetime.datetime.now(), cli == OK, t1 - t0, fileSelect, fileSize, chunks_sent, bytes_sent,
            chunks_received, bytes_received)


# Creacion log
def format_logname(now):
    dt_string = now.strftime("%Y-%m-%d-%H-%M-%S")
    logname = dt_string + "-log.txt"
    return logname


def log(addr, now, exitosa, tiempoTotal, fileSelect, fileSize, enviados, bytesEnv, recibidos, bytesRec):
    # Crear file de log
    formatname = format_logname(now)
    pathlib.Path('./Logs').mkdir(exist_ok=True)
    f = open("./Logs/" + formatname, "x")
    # Nombre y tamano enviado
    f.write("El nombre del archivo enviado es " + fileSelect + " y su tamaño es " + str(fileSize) + " B \n")
    # Cliente
    f.write("El cliente al que se realiza la transferencia es " + str(addr) + "\n")
    # Info transferencia
    estado = "exitosa" if exitosa else "no exitosa"
    f.write("La entrega del archivo fue " + estado + "\n")
    f.write("El tiempo total de transferencia, en segundos, fue " + str(tiempoTotal) + "\n")
    f.write("El numero de paquetes enviados es " + str(enviados) + "\n")
    f.write("El valor total en bytes enviado es " + str(bytesEnv) + "\n")
    f.write("El numero de paquetes recibidos es " + str(recibidos) + "\n")
    f.write("El valor total en bytes reciibido es " + str(bytesRec) + "\n")
    f.close()
    return formatname


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
# numClients = 1  # should be asked
# fileName = 'Prueba.txt'  # should be asked


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

# Corre el metodo del view para obtener los datos
clients, fileSelect = select()
fileSize = pathlib.Path('./' + DIRECTORY + '/' + fileSelect).stat().st_size

while True:
    serverSocket.listen(25)

    connectionSocket, address = serverSocket.accept()

    newThread = ClientThread(connectionSocket, address, fileSelect, fileSize)
    newThread.start()

    threads.append(newThread)

for t in threads:
    t.join()
