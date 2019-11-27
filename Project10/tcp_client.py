# Python Modules
import bluetooth
import colorama
import json
import os
import pprint
import select
import signal
import socket
import threading
import time

# Project Modules
from message_handler import MessageType, MessageHandler

# Globals
keepRunning = True

class TCPClient(threading.Thread):
    """
    Client that establishes socket connections with a server
    """

    def __init__(self, useWifi=True, selectTimeout=3, socketTimeout=5):
        """
        Constructor

        @param useWifi:       Flag denoting whether to use WiFi or Bluetooth
        @param selectTimeout: The select timeout when checking the socket list
        @param socketTimeout: The socket timeout

        @return None
        """

        threading.Thread.__init__(self)

        self.shutdownEvent = threading.Event()
        self._selectTimeout = selectTimeout

        # Initialize colorama and clear screen
        colorama.init()

        print('\033[2J')

        # Connect to server
        if useWifi:
            self._clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._clientSocket.settimeout(socketTimeout)

            self._clientSocket.connect(('192.168.1.67', 9000))  # RPi IP on home network
            #self._clientSocket.connect(('192.168.4.1', 9000))  # RPi wireless access point
        else:
            self._clientSocket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)


            self._clientSocket.connect(('DC:A6:32:17:6A:83', 5))

        # Set initial output data
        self._gpsData = {
            'time': '',
            'lon': 'NaN',
            'lat': 'NaN',
            'alt': 'NaN',
            'speed': 'NaN',
            'climb': 'NaN',
            'epx': 'NaN',
            'epy': 'NaN',
            'epv': 'NaN',
        }

        self._rpyData = {
            'roll': 'NaN',
            'pitch': 'NaN',
            'yaw': 'NaN'
        }

    def run(self):
        """
        Overriden method called when the thread is started

        @param None

        @return None
        """

        inputSocketList = []
        inputSocketList.append(self._clientSocket)

        while not self.shutdownEvent.is_set():
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

        # Retrieve the message type and data
        msgType = msgData[0]
        msg = json.loads(msgData[1])

        # Check to see if a GPS message was received
        if msgType == MessageType.GPS_MESSAGE:
            if msg['time'] is not None:
                self._gpsData['time'] = msg['time']
            
            if msg['lon'] is not None:
                self._gpsData['lon'] = '%4.6f %s (deg)' % (msg['lon'], 'E' if msg['lon'] > 0 else 'W')
            
            if msg['lat'] is not None:
                self._gpsData['lat'] = '%4.6f %s (deg)' % (msg['lat'], 'N' if msg['lat'] > 0 else 'S')
            
            if msg['alt'] is not None:
                self._gpsData['alt'] = '%4.6f (m)' % msg['alt']
            
            if msg['speed'] is not None:
                self._gpsData['speed'] = '%4.6f (MPH)' % msg['speed']
            
            if msg['climb'] is not None:
                self._gpsData['climb'] = '%4.6f (ft/min)' % msg['climb']
            
            # Estimated Longitude Error
            if msg['epx'] is not None:
                self._gpsData['epx'] = '+/- %4.6f (m)' % msg['epx']
            
            # Estimated Latitude Error
            if msg['epy'] is not None:
                self._gpsData['epy'] = '+/- %4.6f (m)' % msg['epy']
            
            # Estimated Vertical Error
            if msg['epv'] is not None:
                self._gpsData['epv'] = '+/- %4.6f (m)' % msg['epv']
        # Check to see if a RPY message was received
        elif msgType == MessageType.RPY_MESSAGE:
            self._rpyData['roll'] = '%4.6f (deg)' % msg['roll']
            self._rpyData['pitch'] = '%4.6f (deg)' % msg['pitch']
            self._rpyData['yaw'] = '%4.6f (deg)' % msg['yaw']

        # Print the current GPS and RPY data
        print('\033[H')  # Moves cursor to 0,0 on screen

        outputStrs = []
        outputStrs.append('------------------------------ GPS ------------------------------')
        outputStrs.append('           Time:  %s' % self._gpsData['time'])
        outputStrs.append('      Longitude:  %s' % self._gpsData['lon'])
        outputStrs.append('       Latitude:  %s' % self._gpsData['lat'])
        outputStrs.append('       Altitude:  %s' % self._gpsData['alt'])
        outputStrs.append('          Speed:  %s' % self._gpsData['speed'])
        outputStrs.append('          Climb:  %s' % self._gpsData['climb'])
        outputStrs.append('Longitude Error:  %s' % self._gpsData['epx'])
        outputStrs.append(' Latitude Error:  %s' % self._gpsData['epy'])
        outputStrs.append(' Altitude Error:  %s' % self._gpsData['epv'])
        outputStrs.append('')
        outputStrs.append('------------------------------ RPY ------------------------------')
        outputStrs.append('')
        outputStrs.append('           Roll: %s' % self._rpyData['roll'])
        outputStrs.append('          Pitch: %s' % self._rpyData['pitch'])
        outputStrs.append('            Yaw: %s' % self._rpyData['yaw'])

        fullOutputStr = '\n'.join(outputStr for outputStr in outputStrs)

        print(fullOutputStr)

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
    tcpClient = TCPClient(useWifi=False)
    tcpClient.start()

    # Keep alive
    while keepRunning:
        time.sleep(1)

    tcpClient.shutdownEvent.set()
