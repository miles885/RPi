# Python Modules
import threading
import time

# Project Modules
from message_handler import MessageType, MessageHandler

class TCPSender(threading.Thread):
    """
    Periodically sends messages to connected clients
    """

    def __init__(self, msgQueue, serverSocket, socketList, socketListMutex, sendPeriod=0.1):
        """
        Constructor

        @param msqQueue        The queue to read messages from
        @param serverSocket    The server socket
        @param socketList      The socker list used for sending messages
        @param socketListMutex The mutex used to ensure the socket list is correct
        @param sendPeriod      The time between checking the queue for messages to send

        @return None
        """

        threading.Thread.__init__(self)

        self.shutdownEvent = threading.Event()

        self._msqQueue = msgQueue
        self._serverSocket = serverSocket
        self._socketList = socketList
        self._socketListMutex = socketListMutex
        self._sendPeriod = sendPeriod
    
    def run(self):
        """
        Overriden method called when the thread is started

        @param None

        @return None
        """

        while not self.shutdownEvent.is_set():
            while not self._msqQueue.empty():
                msg = self._msqQueue.get()

                msgData = msg[0]
                msgType = msg[1]

                self._socketListMutex.acquire()

                try:
                    for sock in self._socketList:
                        if sock is not self._serverSocket:
                            MessageHandler.sendMsg(sock, msgData, msgType)
                finally:
                    self._socketListMutex.release()

            time.sleep(self._sendPeriod)
        
        # Cleanup
        self.__shutdown()

    def __shutdown(self):
        """
        Performs shutdown procedures for the thread

        @param None

        @return None
        """

        pass
