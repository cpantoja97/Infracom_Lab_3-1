from socket import *
import hashlib
from boltons import socketutils

DELIMETER = ';'.encode()
serverName = 'localhost'  # TBD IP de la maquina
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))

clientSocket = socketutils.BufferedSocket(clientSocket)

data = clientSocket.recv_until(delimiter=DELIMETER)

ready = ('READY'+DELIMETER).encode()
if data == ready:
    clientSocket.send(ready)

    data = clientSocket.recv_until(delimiter=DELIMETER)
    data = data.decode().split(':')
    if data[0] == 'FILE_NAME':
        fileName = data[1]
        print('Nombre del archivo:', fileName)

        hasher = hashlib.new('sha256')
        data = clientSocket.recv_until(delimiter=DELIMETER)
        if data == 'FILE_INIT'.encode():
            bytesRecibidos = 0
            with open(f'./ArchivosRecibidos/{fileName}', 'wb') as fileSend:
                i = 0
                data = clientSocket.recv_until(delimiter=DELIMETER)
                while data and data != 'FILE_END'.encode():
                    bytesRecibidos += len(data)
                    hasher.update(data)
                    fileSend.write(data)
                    data = clientSocket.recv_until(delimiter=DELIMETER)
                    i += 1

            data = clientSocket.recv_until(delimiter=DELIMETER).decode().split(':')
            if data[0] == 'HASH':
                hashData = data[1]

                hashFile = hasher.hexdigest()
                if hashFile == hashData:
                    clientSocket.send(('OK'+DELIMETER).encode())
                    print(f'Bytes recibidos: {bytesRecibidos}')
                    print('Descarga Exitosa')
                else:
                    print(f'Hash recibido del servidor: {hashData} \n Hash calculado del archivo: {hashFile}')
                    clientSocket.send(('ERROR'+DELIMETER).encode())
            else:
                print(f'ERROR: se recibio {data[0]} y se esperaba "HASH"')
        else:
            recibido = data.decode()
            print('ERROR: se recibio {recibido} y se esperaba "FILE_INIT"')
            
    else:
        print('ERROR: se recibio {data[0]} y se esperaba "FILE_NAME"')
else:
    recibido = data.decode()
    print('ERROR: se recibio {recibido} y se esperaba READY')

clientSocket.close()
