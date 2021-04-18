from socket import *
from threading import Thread
from threading import Lock
from boltons import socketutils
import hashlib
import time
import datetime
import pathlib
from ServerView import select


# Manage each Client connection
class ClientThread(Thread):
    def __init__(self, connection, tcp_address, transfer_port):
        Thread.__init__(self)
        self.tcp_address = tcp_address
        self.tcp_socket = connection
        self.ns_socket = socketutils.NetstringSocket(connection)  # Socket Wrapper to use Netstring wrapping technique

        self.transfer_port = transfer_port
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.udp_socket.bind(('', transfer_port))

        self.udp_address = None

        print("[+] New server socket thread started for " + tcp_address[0] + ":" + str(tcp_address[1]))

    # Send a message in text format
    def send_message(self, message):
        self.ns_socket.write_ns(message.encode())

    # Send file in binary
    def send_file(self, chunk):
        self.udp_socket.sendto(chunk, self.udp_address)

    # Receive message in text format
    def receive_message(self):
        return self.ns_socket.read_ns().decode()

    # Print a message in console preceding with client identification
    def print_info(self, info):
        print("[" + self.tcp_address[0] + ":" + str(self.tcp_address[1]) + "] " + info)

    def run(self):
        global numReady

        # Send client UDP port
        self.send_message(TRANSFER_PORT + SEP + str(self.transfer_port))
        self.print_info("Sent port " + str(self.transfer_port))

        # Receive hello in udp socket
        handshake = False
        self.udp_socket.settimeout(3)
        while not handshake:
            try:
                print("receiving ready")
                message, self.udp_address = self.udp_socket.recvfrom(4096)
                message = message.decode()
                self.print_info("Received UDP message: " + message)
                if message == READY:
                    print("received ready")
                    self.send_message(READY)
                    print("sent ready")
                    handshake = True
            except timeout:
                print("timedout")
                continue

        # Client ready confirmation
        self.send_message(READY)
        cli = self.receive_message()
        if cli != READY:
            raise Exception(self.tcp_address + " Received " + cli + " instead of READY")
        self.print_info("Client ready")

        # Increase number of ready clients
        numReadyLock.acquire()
        numReady += 1
        client_id = numReady
        numReadyLock.release()

        # Inform client of his number and total clients
        self.send_message(str(client_id) + SEP + str(clients))

        # Actively wait until all clients are ready
        while numReady < clients:
            continue
        hash_fn = hashlib.sha256()
        file = open('../' + DIRECTORY + '/' + fileSelect, "rb")
        bytes_sent = 0
        chunks_sent = 0

        # Send file info
        self.send_message(FILE_NAME + SEP + fileSelect)
        self.send_message(FILE_SIZE + SEP + str(fileSize))
        self.print_info("File info sent")

        # SEND FILE...
        self.print_info("About to start sending file")
        self.send_message(FILE_INIT)
        f_read = file.read(BUFFER_SIZE)
        t0 = time.time()  # Start timer
        while len(f_read) > 0:
            self.send_file(f_read)
            bytes_sent += len(f_read)
            chunks_sent += 1
            hash_fn.update(f_read)
            f_read = file.read(BUFFER_SIZE)
        #self.send_message(FILE_END)

        # Confirmación de recepcion
        cli = self.receive_message()
        if cli != RECEIVED:
            raise Exception(self.tcp_address + " Received " + cli + " instead of RECEIVED")
        t1 = time.time()  # End timer
        self.print_info("File transferred")

        # Send Hash
        self.send_message(HASH + SEP + hash_fn.hexdigest())

        # Client confirmation (OK | ERROR)
        status = self.receive_message()
        self.print_info("Client status " + status)

        # Client bytes and packets received
        cli = self.receive_message()
        [bytes_received, chunks_received] = cli.split(":")
        self.print_info("Client received " + str(bytes_received) + " bytes")
        self.print_info("Client received " + str(chunks_received) + " packets")

        # Close socket
        self.tcp_socket.close()

        # Write log
        log(client_id, clients, self.tcp_address, datetime.datetime.now(), status == OK, t1 - t0, fileSelect, fileSize, chunks_sent, bytes_sent)


# Escritura del log
def log(client_id, clients, addr, now, exitosa, tiempoTotal, fileSelect, fileSize, enviados, bytesEnv):
    # Crear file de log
    formatname = "Cliente" + str(client_id) + "-" + "Conexiones" + str(clients) + "-" + now.strftime("%Y-%m-%d-%H-%M-%S") + "-log.txt"
    pathlib.Path('../LogsServer').mkdir(exist_ok=True)
    f = open("../LogsServer/" + formatname, "x")
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
    f.close()
    return formatname


# PROTOCOL COMMANDS IN CASE THEY ARE CHANGED
READY = 'READY'
TRANSFER_PORT = 'TRANSFER_PORT'
FILE_NAME = 'FILE_NAME'
FILE_SIZE = 'FILE_SIZE'
SEP = ':'
FILE_INIT = 'FILE_INIT'
FILE_END = 'FILE_END'
RECEIVED = 'RECEIVED'
HASH = 'HASH'
OK = 'OK'
ERROR = 'ERROR'

# Server options
DIRECTORY = 'Files'

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

transfer_port_count = SERVER_PORT

# Corre el metodo del view para obtener los datos
clients, fileSelect = select()
fileSize = pathlib.Path('../' + DIRECTORY + '/' + fileSelect).stat().st_size

while len(threads) < clients:
    serverSocket.listen(clients)

    connectionSocket, address = serverSocket.accept()

    transfer_port_count += 1

    newThread = ClientThread(connectionSocket, address, transfer_port_count)
    newThread.start()

    threads.append(newThread)

for t in threads:
    t.join()
