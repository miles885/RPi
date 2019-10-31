#!/usr/bin/env python

import json
import os
import select
import signal
import socket
import threading
import time

from message_handler import MessageType, MessageHandler

# Globals
keepRunning = True
shutdownEvent = threading.Event()

#TODO: Remove when reading actual GPS data
msg = {
    'test': 'yawp',
    'test2': 5
}

class TCPServer(threading.Thread):
    """
    Server that establishes socket connections between the server and clients
    """

    def __init__(self, serverAddress='0.0.0.0', serverPort=9000, backLog=1, selectTimeout=1):
        """
        Constructor

        @param serverAddress: The server address
        @param serverPort:    The server port
        @param backLog:       Number of unaccepted connections allowed 
                              before refusing new connections
        @param selectTimeout: The select timeout when checking the socket list

        @return None
        """

        threading.Thread.__init__(self)

        self._selectTimeout = selectTimeout

        # Create a server socket to listen for connections
        self._serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._serverSocket.bind((serverAddress, serverPort))
        self._serverSocket.listen(backLog)

    def run(self):
        """
        Overriden method called when the thread is started

        @param None

        @return None
        """

        # Add the server socket to the socket list
        socketList = []
        socketList.append(self._serverSocket)

        print('Listening for client connections...')

        while not shutdownEvent.is_set():
            readyToRead, readyToWrite, inputError = select.select(socketList, [], [], self._selectTimeout)

            # Iterate over input sockets
            for sock in readyToRead:
                # Received new connection request
                if sock is self._serverSocket:
                    print('Received connection request. Establishing connection with client.')

                    # Accept the connection and append it to the socket list
                    clientSocket, address = self._serverSocket.accept()

                    #TODO: Add this if there's a timeout blocking issue, or make the sockets non-blocking
                    #clientSocket.settimeout(0.5)

                    socketList.append(clientSocket)
                    # Received message from client
                else:
                    # Read a message off of the socket
                    msgData = MessageHandler.recvMsg(sock)

                    # Process the message
                    if msgData is not None:
                        self.__processMsg(sock, msgData)
                    # The client disconnected
                    else:
                        print('Client disconnected')

                        socketList.remove(sock)

                        sock.close()
            
            # Broadcast data
            for sock in socketList:
                if sock is not self._serverSocket:
                    msgData = json.dumps(msg)

                    MessageHandler.sendMsg(sock, msgData, MessageType.GPS_MESSAGE)
            
            time.sleep(1)

        # Cleanup
        self.__shutdown()

    def __processMsg(self, sock, msgData):
        """
        Processes a message received from a client

        @param sock:    The client socket
        @param msgData: The message data

        @return None
        """

        pass

    def __shutdown(self):
        """
        Performs shutdown procedures for the thread

        @param None

        @return None
        """

        self._serverSocket.close()

def service_shutdown(signum, fname):
    """
    Handles signals (interrupts)

    @param signum: The signal to be handled
    @param fname:  The callback function name

    @return None
    """

    global keepRunning

    keepRunning = False

if __name__ == "__main__":
    # Register a signal handler
    signal.signal(signal.SIGINT, service_shutdown)

    # Start the TCP server
    tcpServer = TCPServer()
    tcpServer.start()

    # Keep alive
    while keepRunning:
        time.sleep(1)

    shutdownEvent.set()