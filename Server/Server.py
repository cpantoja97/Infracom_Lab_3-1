from socket import *
from threading import Thread
from threading import Lock
import hashlib
import time
from Server.ServerView import select


class ClientThread(Thread):
    def __init__(self, connection, address, fileSelect, fileSize):
        Thread.__init__(self)
        self.connection = connection
        self.address = address
        self.fileSelect = fileSelect
        self.fileSize = fileSize
        print("[+] New server socket thread started for " + address[0] + ":" + str(address[1]))

    def run(self):
        global numReady
        conn = self.connection

        # Client confirmation
        conn.send(READY.encode())
        time.sleep(0.1)
        cli = conn.recv(BUFFER_SIZE).decode()

        if cli != READY:
            raise

        # Increase number of ready clients
        numReadyLock.acquire()
        numReady += 1
        numReadyLock.release()

        # Actively wait until all clients are ready
        while numReady < clients:
            continue

        hash_fn = hashlib.sha256()
        file = open('./' + DIRECTORY + '/' + fileSelect)
        total_sent = 0
        chunks = 0

        conn.send((FILE_NAME + SEP + fileSelect).encode())
        time.sleep(0.1)

        # SEND FILE...
        conn.send(FILE_INIT.encode())
        time.sleep(0.1)
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
        time.sleep(0.1)

        conn.send(FILE_END.encode())
        time.sleep(0.1)

        conn.send((HASH + SEP + hash_fn.hexdigest()).encode())
        time.sleep(0.1)
        
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
#numClients = 1  # should be asked
#fileName = 'Prueba.txt'  # should be asked


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
clients, fileSelect, fileSize = select()
while True:
    serverSocket.listen(25)
    print('The server is ready to receive')

    connectionSocket, address = serverSocket.accept()

    newThread = ClientThread(connectionSocket, address, fileSelect, fileSize)
    newThread.start()

    threads.append(newThread)

for t in threads:
    t.join()


# Creacion log

def format_logname(now):
    dt_string = now.strftime("%Y-%m-%d-%H-%M-%S")
    logname = dt_string + "-log.txt"
    return logname

def log(addr, now, exitosa, tiempoTotal, fileSelect, fileSize, enviados, bytesEnv, recibidos, bytesRec):
    # Crear file de log
    formatname = format_logname(now)
    f = open("Logs/" + formatname, "x")
    # Nombre y tamano enviado
    f.write("El nombre del archivo enviado es " + fileSelect + " y su tamaño es " + fileSize + "MB \n")
    # Cliente
    f.write("El cliente al que se realiza la transferencia es " + str(addr) + "\n")
    # Info transferencia
    estado = "exitosa" if exitosa else "no exitosa"
    f.write("La entrega del archivo fue " + estado + "\n")
    f.write("El tiempo total de transferencia, en segundos, fue " + str(tiempoTotal) + "\n")
    f.write("El numero de paquetes enviados es " + enviados + "\n")
    f.write("El valor total en bytes enviado es " + bytesEnv + "\n")
    f.write("El numero de paquetes recibidos es " + recibidos + "\n")
    f.write("El valor total en bytes reciibido es " + bytesRec + "\n")
    f.close()
    return formatname