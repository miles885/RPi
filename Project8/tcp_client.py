import json
import os
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

        self._clientSocket.connect(('192.168.1.67', 9000))  # RPi IP on home network
        #self._clientSocket.connect(('192.168.4.1', 9000))  # RPi wireless access point

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
            time = ''
            lon = 'NaN'
            lat = 'NaN'
            alt = 'NaN'
            speed = 'NaN'
            climb = 'NaN'
            epx = 'NaN'
            epy = 'NaN'
            epv = 'NaN'

            if 'time' in msg and msg['time'] is not None:
                time = msg['time']
            
            if 'lon' in msg and msg['lon'] is not None:
                lon = '%4.6f %s (deg)' % (msg['lon'], 'E' if msg['lon'] > 0 else 'W')
            
            if 'lat' in msg and msg['lat'] is not None:
                lat = '%4.6f %s (deg)' % (msg['lat'], 'N' if msg['lat'] > 0 else 'S')
            
            if 'alt' in msg and msg['alt'] is not None:
                alt = '%4.6f (m)' % msg['alt']
            
            if 'speed' in msg and msg['speed'] is not None:
                speed = '%4.6f (MPH)' % msg['speed']
            
            if 'climb' in msg and msg['climb'] is not None:
                climb = '%4.6f (ft/min)' % msg['climb']
            
            # Estimated Longitude Error
            if 'epx' in msg and msg['epx'] is not None:
                epx = '+/- %4.6f (m)' % msg['epx']
            
            # Estimated Latitude Error
            if 'epy' in msg and msg['epy'] is not None:
                epy = '+/- %4.6f (m)' % msg['epy']
            
            # Estimated Vertical Error
            if 'epv' in msg and msg['epv'] is not None:
                epv = '+/- %4.6f (m)' % msg['epv']

            if os.name == 'nt':
                os.system('cls')
            else:
                os.system('clear')

            print('           Time:  %s' % time)
            print('      Longitude:  %s' % lon)
            print('       Latitude:  %s' % lat)
            print('       Altitude:  %s' % alt)
            print('          Speed:  %s' % speed)
            print('          Climb:  %s' % climb)
            print('Longitude Error:  %s' % epx)
            print(' Latitude Error:  %s' % epy)
            print(' Altitude Error:  %s' % epv)

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