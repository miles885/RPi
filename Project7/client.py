import json
import pprint
import select
import signal
import socket
import threading
import time

from message_handler import MessageType, MessageHandler

# Globals
keepRunning = True
shutdownEvent = threading.Event()

class TCPClient(threading.Thread):
    """
    Client that establishes socket connections with a server
    """

    def __init__(self, selectTimeout=3, socketTimeout=5):
        """
        Constructor

        @param selectTimeout: The select timeout when checking the socket list
        @param socketTimeout: The socket timeout

        @return None
        """

        threading.Thread.__init__(self)

        self._selectTimeout = selectTimeout

        self._clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._clientSocket.settimeout(socketTimeout)

        #TODO: Replace localhost with RPi IP
        self._clientSocket.connect(('localhost', 9000))

    def run(self):
        """
        Overriden method called when the thread is started

        @param None

        @return None
        """

        inputSocketList = []
        inputSocketList.append(self._clientSocket)

        while not shutdownEvent.is_set():
            readyToRead, readyToWrite, inputError = select.select(inputSocketList, [], [], self._selectTimeout)

            for sock in readyToRead:
                # Read a message off of the socket
                msgData = MessageHandler.recvMsg(sock)

                # Process the message
                if msgData is not None:
                    self.__processMsg(msgData)
                else:
                    break

        # Cleanup
        self.__shutdown()

    def __processMsg(self, msgData):
        """
        Processes a message received from the server

        @param msgData: The message data

        @return None
        """

        msgType = msgData[0]
        msg = json.loads(msgData[1])

        if msgType == MessageType.GPS_MESSAGE:
            print(pprint.pformat(msg))

    def __shutdown(self):
        """
        Performs shutdown procedures for the thread

        @param None

        @return None
        """

        self._clientSocket.close()

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

    # Start the TCP client
    tcpClient = TCPClient()
    tcpClient.start()

    # Keep alive
    while keepRunning:
        time.sleep(1)

    shutdownEvent.set()