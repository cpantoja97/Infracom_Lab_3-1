from socket import *
from threading import Thread
import hashlib
from boltons import socketutils


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
    def __init__(self,connection, idClient):
        Thread.__init__(self)
        self.socket = connection
        self.idClient = idClient
        self.ns_socket = socketutils.NetstringSocket(connection)
        print("[+] New client socket started - idCliente:", idClient )

    def receive(self):
        return self.ns_socket.read_ns().decode()

    def receive_file(self):
        return self.ns_socket.read_ns()

    def send(self, message):
        encoded_message = message.encode()
        self.ns_socket.write_ns(encoded_message)

    def run(self):
        conn = self.ns_socket
        data = self.receive()

        ready = 'READY'
        if data == ready:
            self.send(ready)

            data = self.receive()
            data = data.split(':')
            if data[0] == 'FILE_NAME':
                fileName = data[1]
                print('Nombre del archivo:', fileName)

                hasher = hashlib.new('sha256')
                data = self.receive()
                if data == 'FILE_INIT':
                    bytesRecibidos = 0
                    with open(f'./ArchivosRecibidos/cliente{self.idClient}-{fileName}', 'wb') as fileSend:
                        i = 0
                        data = self.receive_file()
                        while data and data != 'FILE_END'.encode():
                            bytesRecibidos += len(data)
                            hasher.update(data)
                            fileSend.write(data)
                            data = self.receive_file()
                            i += 1

                    data = self.receive().split(':')
                    if data[0] == 'HASH':
                        hashData = data[1]

                        hashFile = hasher.hexdigest()
                        if hashFile == hashData:
                            self.send('OK')
                            print(f'Bytes recibidos: {bytesRecibidos}')
                            print(f'Descarga Exitosa del cliente {self.idClient}')
                        else:
                            print(f'Hash recibido del servidor: {hashData} \n Hash calculado del archivo: {hashFile}')
                            self.send('ERROR')
                    else:
                        print(f'ERROR: se recibio {data[0]} y se esperaba "HASH"')

                    self.send(str(bytesRecibidos) + ":" + str(i))
                else:
                    recibido = data.decode()
                    print(f'ERROR: se recibio {recibido} y se esperaba "FILE_INIT"')

            else:
                print(f'ERROR: se recibio {data[0]} y se esperaba "FILE_NAME"')
        else:
            print(f'ERROR: se recibio {data} y se esperaba READY')

        self.socket.close()


        

serverName = 'localhost'  # TBD IP de la maquina
serverPort = 12000

READY = 'READY'
FILE_NAME = 'FILE_NAME'
SEP = ':'
FILE_INIT = 'FILE_INIT'
FILE_END = 'FILE_END'
HASH = 'HASH'
OK = 'OK'
ERROR = 'ERROR'

DIRECTORY = 'ArchivosRecibidos'


threads = []

numClients = select()

for i in range(numClients):
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    clientSocket.connect((serverName, serverPort))
    newThread = ClientThread(clientSocket,i)
    newThread.start()

    threads.append(newThread)

for t in threads:
    t.join()