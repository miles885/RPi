#!/usr/bin/env python

# Python Modules
try:
    import queue
except ImportError:
    import Queue as queue

import bluetooth
import select
import signal
import socket
import time
import threading

# Project Modules
from gps_reader import GPSReader
from message_handler import MessageHandler
from rpy_reader import RPYReader
from tcp_sender import TCPSender

# Globals
keepRunning = True

class TCPServer(threading.Thread):
    """
    Server that establishes socket connections between the server and clients
    """

    def __init__(self, wifiAddress='0.0.0.0', wifiPort=9000, btPort=5, useWifi=True, backLog=1, selectTimeout=5):
        """
        Constructor

        @param wifiAddress:   The WiFi address
        @param wifiPort:      The WiFi port
        @param btPort:        The Bluetooth port
        @param useWifi:       Flag denoting whether to use WiFi or Bluetooth
        @param backLog:       Number of unaccepted connections allowed 
                              before refusing new connections
        @param selectTimeout: The select timeout when checking the socket list (seconds)

        @return None
        """

        threading.Thread.__init__(self)

        self.shutdownEvent = threading.Event()

        self._selectTimeout = selectTimeout

        # Create a server socket to listen for connections
        if useWifi:
            self._serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self._serverSocket.bind((wifiAddress, wifiPort))
        else:
            self._serverSocket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self._serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self._serverSocket.bind(('', btPort))

        self._serverSocket.listen(backLog)

        # Add the server socket to the socket list
        self._socketList = []
        self._socketList.append(self._serverSocket)

        self._socketListMutex = threading.Lock()
        self._msqQueue = queue.Queue()

        # Create TCP sender
        self._tcpSender = TCPSender(self._msqQueue, self._serverSocket, self._socketList, self._socketListMutex)
        self._tcpSender.start()

        # Create GPS reader
        self._gpsReader = GPSReader(self._msqQueue)
        self._gpsReader.start()

        # Create RPY reader
        self._rpyReader = RPYReader(self._msqQueue)
        self._rpyReader.start()

    def run(self):
        """
        Overriden method called when the thread is started

        @param None

        @return None
        """

        print('Listening for client connections...')

        while not self.shutdownEvent.is_set():
            readyToRead, readyToWrite, inputError = select.select(self._socketList, [], [], self._selectTimeout)

            # Iterate over input sockets
            for sock in readyToRead:
                # Received new connection request
                if sock is self._serverSocket:
                    print('Received connection request. Establishing connection with client.')

                    # Accept the connection and append it to the socket list
                    clientSocket, address = self._serverSocket.accept()

                    # Prevent recv calls from blocking indefinitely
                    #TODO: Could use this as message timeout instead of MessageHandler timeout?
                    clientSocket.settimeout(1)

                    self._socketListMutex.acquire()
                    self._socketList.append(clientSocket)
                    self._socketListMutex.release()
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

                        self._socketListMutex.acquire()
                        self._socketList.remove(sock)
                        self._socketListMutex.release()

                        sock.close()

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

        self._rpyReader.shutdownEvent.set()
        self._gpsReader.shutdownEvent.set()
        self._tcpSender.shutdownEvent.set()

        self._rpyReader.join()
        self._gpsReader.join()
        self._tcpSender.join()

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
    tcpServer = TCPServer(useWifi=False)
    tcpServer.start()

    # Keep alive
    while keepRunning:
        time.sleep(1)

    tcpServer.shutdownEvent.set()
