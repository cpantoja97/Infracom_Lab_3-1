from socket import *
from threading import Thread
import hashlib
import datetime
from boltons import socketutils
import pathlib
import time

def select():
    clients = 0

    # Inicio
    print("Aplicacion del Cliente de Transferencia de Archivos")
    print("Aquí podrá seleccionar un numero de clientes que van a solicitar un archivo en simultaneo")
    print("Puede haber entre 1 y 25 conexiones. Si quiere finalizar ponga 0.")
    
    clients = int(input())
    if (clients < 26 and clients != 0):
        print("Se conectaran " + str(clients) + " clientes")    
    
    return clients

class ClientThread(Thread):
    def __init__(self, connection):
        Thread.__init__(self)
        self.socket = connection
        self.socket.settimeout(2)
        self.ns_socket = socketutils.NetstringSocket(connection)
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.udp_socket.settimeout(2)

    def receive(self):
        return self.ns_socket.read_ns().decode()

    def receive_file(self):
        return self.udp_socket.recvfrom(4096)[0]

    def send(self, message):
        encoded_message = message.encode()
        self.ns_socket.write_ns(encoded_message)

    def run(self):
        conn = self.ns_socket

        # Recibir info de puerto UDP
        data = self.receive()
        data = data.split(':')
        udp_port = int(data[1])
        print("Recibió puerto: " + str(udp_port))

        # Conexión por UDP
        handshake = False
        while not handshake:
            self.udp_socket.sendto('READY'.encode(), (serverName, udp_port))
            print("Sent Ready")
            try:
                print("Receiving ready")
                received = self.receive()
                if received == 'READY':
                    print("Received ready")
                    handshake = True
            except timeout:
                print("timedout")
                continue

        # Recibir READY
        data = self.receive()
        ready = 'READY'
        if data == ready:
            self.send(ready)
            print('El cliente se conecto con el servidor')
            
            data = self.receive()
            data = data.split(':')
            idClient = data[0]
            clients = data[1]    
            
            print(f'Se le asigno el id {idClient} al cliente')
            data = self.receive()
            data = data.split(':')
            if data[0] == 'FILE_NAME':
                fileName = data[1]
                print('Nombre del archivo:', fileName)
                
                data = self.receive()
                data = data.split(':')

                if data[0] == 'FILE_SIZE':
                    fileSize = data[1]
                    print('Tamaño del archivo:', fileSize)
                    hasher = hashlib.new('sha256')
                    data = self.receive()
                    if data == 'FILE_INIT':
                        bytesRecibidos = 0
                        pathlib.Path('../ArchivosRecibidos').mkdir(exist_ok=True)
                        with open(f'../ArchivosRecibidos/Cliente{idClient}-Prueba-{clients}-{fileName}', 'wb') as fileSend:
                            i = 0
                            t0 = time.time()
                            data = self.receive_file()
                            try:
                                while data:
                                    bytesRecibidos += len(data)
                                    fileSend.write(data)
                                    hasher.update(data)
                                    data = self.receive_file()
                                    i += 1
                            except timeout:
                                self.udp_socket.close()
                            
                            #data = self.receive()
                            #if data != 'FILE_END'.encode():
                            #    raise Exception(self.tcp_address + " Received " + cli + " instead of FILE_END")
                            t1 = time.time()
                            self.send(RECIBIDO)
                        data = self.receive().split(':')
                        if data[0] == 'HASH':
                            hashData = data[1]
                            hashFile = hasher.hexdigest()
                            status = ''
                            if hashFile == hashData:
                                self.send('OK')
                                status = 'OK'
                                print(f'Bytes recibidos: {bytesRecibidos}')
                                print(f'Descarga Exitosa del cliente {idClient}')
                            else:
                                print(f'Hash recibido del servidor: {hashData} \n Hash calculado del archivo: {hashFile}')
                                self.send('ERROR')
                                status = 'ERROR'
                        else:
                            print(f'ERROR: se recibio {data[0]} y se esperaba "HASH"')

                        self.send(str(bytesRecibidos) + ":" + str(i))
                    else:
                        recibido = data.decode()
                        print(f'ERROR: se recibio {recibido} y se esperaba "FILE_INIT"')
                else:
                 print(f'ERROR: se recibio {data[0]} y se esperaba "FILE_SIZE"')   
            else:
                print(f'ERROR: se recibio {data[0]} y se esperaba "FILE_NAME"')
        else:
            print(f'ERROR: se recibio {data} y se esperaba READY')

        self.socket.close()

        log(idClient, clients, datetime.datetime.now(), status == OK, t1 - t0, fileName, fileSize, i, bytesRecibidos)
    

# Escritura del log
def log(client_id, clients, now, exitosa, tiempoTotal, fileSelect, fileSize, enviados, bytesEnv):
    # Crear file de log
    formatname = "Cliente" + client_id + "-" + "Conexiones" + clients + "-" + now.strftime("%Y-%m-%d-%H-%M-%S") + "-log.txt"
    pathlib.Path('../LogsClient').mkdir(exist_ok=True)
    f = open("../LogsClient/" + formatname, "x")
    # Nombre y tamano enviado
    f.write("El nombre del archivo recibido es " + fileSelect + " y su tamaño es " + str(fileSize) + " B \n")
    # Info transferencia
    estado = "exitosa" if exitosa else "no exitosa"
    f.write("La recepción del archivo fue " + estado + "\n")
    f.write("El tiempo total de transferencia, en segundos, fue " + str(tiempoTotal) + "\n")
    f.write("El numero de paquetes recibidos es " + str(enviados) + "\n")
    f.write("El valor total en bytes recibidos es " + str(bytesEnv) + "\n")
    f.close()
    return formatname


        

serverName =  input('Dirección IP del servidor :') # '192.168.226.128'  # 'localhost' TBD IP de la maquina
serverPort = 12000

READY = 'READY'
FILE_NAME = 'FILE_NAME'
SEP = ':'
FILE_INIT = 'FILE_INIT'
FILE_END = 'FILE_END'
HASH = 'HASH'
OK = 'OK'
ERROR = 'ERROR'
RECIBIDO = 'RECEIVED'
DIRECTORY = 'ArchivosRecibidos'


threads = []

numClients = select()

for i in range(numClients):
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))
    newThread = ClientThread(clientSocket)
    newThread.start()

    threads.append(newThread)

for t in threads:
    t.join()