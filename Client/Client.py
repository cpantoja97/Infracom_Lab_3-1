from socket import *
import hashlib
import datetime
from boltons import socketutils
import pathlib
import time


def receive(clientSocket):
    return clientSocket.read_ns().decode()


def receive_file(clientSocket):
    return clientSocket.read_ns()


def send(clientSocket, message):
    encoded_message = message.encode()
    clientSocket.write_ns(encoded_message)


# Escritura del log
def log(client_id, now, exitosa, tiempoTotal, fileSelect, fileSize, enviados, bytesEnv):
    # Crear file de log
    formatname = "Cliente" + client_id + "-" + now.strftime("%Y-%m-%d-%H-%M-%S")
    pathlib.Path('./LogsClient').mkdir(exist_ok=True)
    f = open("./LogsClient/" + formatname, "x")
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


serverName = 'localhost'  # '192.168.226.128' IP de la maquina
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
    idClient = data[0]
    clients = data[1]
    data = receive(ns_socket)
    data = data.split(':')
    if data[0] == 'FILE_NAME':
        fileName = data[1]
        print('Nombre del archivo:', fileName)

        data = receive(ns_socket)
        data = data.split(':')

        if data[0] == 'FILE_SIZE':
            fileSize = data[1]
            print('Tamaño del archivo:', fileSize)
            hasher = hashlib.new('sha256')
            data = receive(ns_socket)
            if data == 'FILE_INIT':
                bytesRecibidos = 0
                pathlib.Path('./ArchivosRecibidos').mkdir(exist_ok=True)
                with open(f'./ArchivosRecibidos/Cliente{idClient}-Prueba-{clients}-{fileName}', 'wb') as fileSend:
                    i = 0
                    t0 = time.time()
                    data = receive_file(ns_socket)
                    while data and data != 'FILE_END'.encode():
                        bytesRecibidos += len(data)
                        hasher.update(data)
                        fileSend.write(data)
                        data = receive_file(ns_socket)
                        i += 1
                    t1 = time.time()
                data = receive(ns_socket).split(':')
                if data[0] == 'HASH':
                    hashData = data[1]

                    hashFile = hasher.hexdigest()
                    status = ''
                    if hashFile == hashData:
                        send(ns_socket, 'OK')
                        status = 'OK'
                        print(f'Bytes recibidos: {bytesRecibidos}')
                        print(f'Descarga Exitosa del cliente {idClient}')
                    else:
                        print(f'Hash recibido del servidor: {hashData} \n Hash calculado del archivo: {hashFile}')
                        send(ns_socket, 'ERROR')
                        status = 'ERROR'
                else:
                    print(f'ERROR: se recibio {data[0]} y se esperaba "HASH"')

                send(ns_socket, str(bytesRecibidos) + ":" + str(i))
            else:
                recibido = data.decode()
                print(f'ERROR: se recibio {recibido} y se esperaba "FILE_INIT"')
        else:
            print(f'ERROR: se recibio {data[0]} y se esperaba "FILE_SIZE"')
    else:
        print(f'ERROR: se recibio {data[0]} y se esperaba "FILE_NAME"')
else:
    print(f'ERROR: se recibio {data} y se esperaba READY')

clientSocket.close()

log(idClient, datetime.datetime.now(), status == 'OK', t1 - t0, fileName, fileSize, i, bytesRecibidos)
