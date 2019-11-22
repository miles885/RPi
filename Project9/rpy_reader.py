# Python Modules
import json
import serial
import threading
import time

# Project Modules
from message_handler import MessageType

class RPYReader(threading.Thread):
    """
    Class used for reading roll, pitch, yaw data from an Arduino over serial
    """

    def __init__(self, msgQueue, readPeriod=0.1):
        """
        Constructor

        @param msgQueue   The queue to place GPS messages on
        @param readPeriod The time between RPY reads (seconds)

        @return None
        """

        threading.Thread.__init__(self)

        self.shutdownEvent = threading.Event()

        self._msgQueue = msgQueue
        self._readPeriod = readPeriod

        # Initialize serial connection
        self._serialPort = serial.Serial('/dev/ttyACM0', 115200)
    
    def run(self):
        """
        Overriden method called when the thread is started

        @param None

        @return None
        """
        
        # Run until told to stop
        while not self.shutdownEvent.is_set():
            rpyData = self.__getRPYData()

            # Broadcast RPY data
            if rpyData:
                msgData = json.dumps(rpyData)

                self._msgQueue.put((msgData, MessageType.RPY_MESSAGE))

            time.sleep(self._readPeriod)

        # Cleanup
        self.__shutdown()

    def __getRPYData(self):
        """
        Retrieves RPY data from an Arduino over serial

        @param None

        @return RPY data (dictionary)
        """

        rpyData = {}

        # Retrieve serial data
        serialData = self._serialPort.readline().decode()
        serialData = serialData.rstrip('\r\n')

        # Split serial data to find RPY
        serialDataParts = serialData.split(',')

        if len(serialDataParts) == 3:
            rpyData['roll'] = float(serialDataParts[0])
            rpyData['pitch'] = float(serialDataParts[1])
            rpyData['yaw'] = float(serialDataParts[2])
        else:
            print(serialData)

        return rpyData

    def __shutdown(self):
        """
        Performs shutdown procedures for the thread

        @param None

        @return None
        """

        self._serialPort.close()
