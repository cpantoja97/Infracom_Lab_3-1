from socket import *
import hashlib

serverName = '192.168.136.1'  # TBD IP de la maquina
serverPort = 12000

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))


data = clientSocket.recv(4096)

ready = 'READY'.encode()
if data == ready:
    socket.send(ready)

    data = clientSocket.recv(4096)
    data = data.decode().split(':')
    if data[0] == 'FILE_NAME':
        fileName = data[1]
        print('Nombre del archivo:', fileName)
        
        hasher = hashlib.new('sha256')        
        data = clientSocket.recv(4096)
        if data == 'FILE_INIT'.encode():
            bytesRecibidos = 0
            with open(f'./ArchivosRecibidos/{fileName}','wb') as fileSend:
                i = 0
                data = clientSocket.recv(4096) 
                bytesRecibidos += len(data)
                while data and data != 'FILE_END'.encode():
                    hasher.update(data)
                    fileSend.write(data)
                    data = clientSocket.recv(4096) 
                    i += 1
                
            data = clientSocket.recv(4096).decode().split(':')
            if data[0] ==  'HASH':
                hashData = data[1]

                hashFile = hasher.hexdigest()
                if hashFile == hashData:
                    clientSocket.send('OK')
                    print(f'Bytes recibidos: {bytesRecibidos}')
                    print('Descarga Exitosa')
                else:
                    print(f'Hash recibido del servidor: {hashData} \n Hash calculado del archivo: {hashFile}')    
                    clientSocket.send('ERROR')    
            else :
                print(f'ERROR: se recibio {data[0]} y se esperaba "HASH"')
        else :
            recibido = data.decode()
            print('ERROR: se recibio {recibido} y se esperaba "FILE_INIT"')
    else:
        print('ERROR: se recibio {data[0]} y se esperaba "FILE_NAME"')
else :
    recibido = data.decode()
    print('ERROR: se recibio {recibido} y se esperaba READY')
                

clientSocket.close()
                


                 
            






sentence = 'hola'
clientSocket.send(sentence.encode())
modifiedSentence = clientSocket.recv(1024)
print('From Server: ', modifiedSentence.decode())
clientSocket.close()
