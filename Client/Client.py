from socket import *
import hashlib
from boltons import socketutils

DELIMITER = ';'


def receive(clientSocket):
    return clientSocket.recv_until(DELIMITER.encode()).decode()


def send(clientSocket, message):
    encoded_message = (message + DELIMITER).encode()
    clientSocket.send(encoded_message)


serverName = 'localhost'  # TBD IP de la maquina
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))

clientSocket = socketutils.BufferedSocket(clientSocket)

data = receive(clientSocket)

ready = 'READY'
if data == ready:
    send(clientSocket, ready)

    data = receive(clientSocket)
    data = data.split(':')
    if data[0] == 'FILE_NAME':
        fileName = data[1]
        print('Nombre del archivo:', fileName)

        hasher = hashlib.new('sha256')
        data = receive(clientSocket)
        if data == 'FILE_INIT':
            bytesRecibidos = 0
            with open(f'./ArchivosRecibidos/{fileName}', 'wb') as fileSend:
                i = 0
                data = receive(clientSocket)
                while data and data != 'FILE_END':
                    bytesRecibidos += len(data)
                    hasher.update(data)
                    fileSend.write(data)
                    data = receive(clientSocket)
                    i += 1

            data = receive(clientSocket).split(':')
            if data[0] == 'HASH':
                hashData = data[1]

                hashFile = hasher.hexdigest()
                if hashFile == hashData:
                    send(clientSocket, 'OK')
                    print(f'Bytes recibidos: {bytesRecibidos}')
                    print('Descarga Exitosa')
                else:
                    print(f'Hash recibido del servidor: {hashData} \n Hash calculado del archivo: {hashFile}')
                    send(clientSocket, 'ERROR')
            else:
                print(f'ERROR: se recibio {data[0]} y se esperaba "HASH"')
        else:
            recibido = data.decode()
            print(f'ERROR: se recibio {recibido} y se esperaba "FILE_INIT"')

    else:
        print(f'ERROR: se recibio {data[0]} y se esperaba "FILE_NAME"')
else:
    print(f'ERROR: se recibio {data} y se esperaba READY')

clientSocket.close()
