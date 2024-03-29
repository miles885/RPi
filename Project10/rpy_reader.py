# Python Modules
import json
import pigpio
import serial
import struct
import threading
import time

# Project Modules
from message_handler import MessageType

class RPYReader(threading.Thread):
    """
    Class used for reading roll, pitch, yaw data from an Arduino over serial
    """

    def __init__(self, msgQueue, useSerial=True, readPeriod=0.1):
        """
        Constructor

        @param msgQueue   The queue to place GPS messages on
        @param useSerial  Flag dictating whether to use Serial or I2C bus
        @param readPeriod The time between RPY reads (seconds)

        @return None
        """

        threading.Thread.__init__(self)

        self.shutdownEvent = threading.Event()

        self._msgQueue = msgQueue
        self._useSerial = useSerial
        self._readPeriod = readPeriod

        # Initialize the specified bus
        if useSerial:
            self.__establishSerConn()
        else:
            self._gpio = pigpio.pi()
            self._gpioHandle = self._gpio.i2c_open(1, 0x05)
    
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

        # Check to see if serial is being used
        if self._useSerial:
            # Retrieve serial data
            try:
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
            except serial.serialutil.SerialException:
                print('Exception while reading RPY data. Attempting to reestabilish serial connection...')

                self._serialPort.close()

                time.sleep(1)

                self.__establishSerConn()
        # I2C bus is being used
        else:
            try:
                # Command the Arduino to read from the IMU
                self._gpio.i2c_write_byte(self._gpioHandle, 1)

                time.sleep(.2)

                # Read the RPY data
                numBytesRead, readBytes = self._gpio.i2c_read_device(self._gpioHandle, 12)

                # Check to make sure the read was successful
                if numBytesRead == 12:
                    rollBytes = bytes(readBytes[0:4])
                    pitchBytes = bytes(readBytes[4:8])
                    yawBytes = bytes(readBytes[8:12])

                    rpyData['roll'] = struct.unpack('f', rollBytes)[0]
                    rpyData['pitch'] = struct.unpack('f', pitchBytes)[0]
                    rpyData['yaw'] = struct.unpack('f', yawBytes)[0]
                # The read was not successful
                else:
                    print('Invalid I2C read. Attempting to reestablish I2C connection...')

                    self._gpio.i2c_close(self._gpioHandle)
                    self._gpio.stop()

                    time.sleep(1)

                    self._gpio = pigpio.pi()
                    self._gpioHandle = self._gpio.i2c_open(1, 0x05)
            except (OSError, pigpio.error) as e:
                print('Exception while reading/writing over I2C. Make sure the Arduino is connected to the I2C bus.')

        return rpyData

    def __establishSerConn(self):
        """
        Etablishes a serial connection on a ttyACM* port

        @param None

        @return None
        """

        for portNum in range(0, 10):
            try:
                port = '/dev/ttyACM' + str(portNum)

                self._serialPort = serial.Serial(port, 115200)

                print('Successfully (re)established serial connection on port: %s' % port)

                break
            except serial.serialutil.SerialException:
                pass

    def __shutdown(self):
        """
        Performs shutdown procedures for the thread

        @param None

        @return None
        """

        if self._useSerial:
            self._serialPort.close()
        else:
            self._gpio.i2c_close(self._gpioHandle)
            self._gpio.stop()
