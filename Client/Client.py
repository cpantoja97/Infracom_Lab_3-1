from socket import *
import hashlib
from boltons import socketutils


def receive(clientSocket):
    return clientSocket.read_ns().decode()


def receive_file(clientSocket):
    return clientSocket.read_ns()


def send(clientSocket, message):
    encoded_message = message.encode()
    clientSocket.write_ns(encoded_message)


serverName = 'localhost'  # TBD IP de la maquina
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))

ns_socket = socketutils.NetstringSocket(clientSocket)

data = receive(ns_socket)

ready = 'READY'
if data == ready:
    send(ns_socket, ready)

    data = receive(ns_socket)
    data = data.split(':')
    if data[0] == 'FILE_NAME':
        fileName = data[1]
        print('Nombre del archivo:', fileName)

        hasher = hashlib.new('sha256')
        data = receive(ns_socket)
        if data == 'FILE_INIT':
            bytesRecibidos = 0
            with open(f'./ArchivosRecibidos/{fileName}', 'wb') as fileSend:
                i = 0
                data = receive_file(ns_socket)
                while data and data != 'FILE_END'.encode():
                    bytesRecibidos += len(data)
                    hasher.update(data)
                    fileSend.write(data)
                    data = receive_file(ns_socket)
                    i += 1

            data = receive(ns_socket).split(':')
            if data[0] == 'HASH':
                hashData = data[1]

                hashFile = hasher.hexdigest()
                if hashFile == hashData:
                    send(ns_socket, 'OK')
                    print(f'Bytes recibidos: {bytesRecibidos}')
                    print('Descarga Exitosa')
                else:
                    print(f'Hash recibido del servidor: {hashData} \n Hash calculado del archivo: {hashFile}')
                    send(ns_socket, 'ERROR')
            else:
                print(f'ERROR: se recibio {data[0]} y se esperaba "HASH"')

            send(ns_socket, str(bytesRecibidos) + ":" + str(i))
        else:
            recibido = data.decode()
            print(f'ERROR: se recibio {recibido} y se esperaba "FILE_INIT"')

    else:
        print(f'ERROR: se recibio {data[0]} y se esperaba "FILE_NAME"')
else:
    print(f'ERROR: se recibio {data} y se esperaba READY')

clientSocket.close()
