# from SocketServer import ThreadingMixIn
from socket import *
from threading import Thread


class ClientThread(Thread):
    def __init__(self, connection, address):
        Thread.__init__(self)
        self.connection = connection
        print("[+] New server socket thread started for " + address[0] + ":" + str(address[1]))

    def run(self):
            sentence = self.connection.recv(1024).decode()
            capitalizedSentence = sentence.upper()
            self.connection.send(capitalizedSentence.encode())
            self.connection.close()


serverPort = 12000
bufferSize = 1024

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('', serverPort))

threads = []

while True:
    serverSocket.listen(25)
    print('The server is ready to receive')

    connectionSocket, addr = serverSocket.accept()

    newThread = ClientThread(connectionSocket, addr)
    newThread.start()

    threads.append(newThread)

for t in threads:
    t.join()
