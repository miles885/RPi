# Python Modules
import json
import threading
import time

# 3rd Party Modules
import gps

# Project Modules
from message_handler import MessageType

class GPSReader(threading.Thread):
    """
    Class used for reading GPS data from a sensor
    """

    def __init__(self, msgQueue, readPeriod=0.5):
        """
        Constructor

        @param msgQueue   The queue to place GPS messages on
        @param readPeriod The time between GPS reads (seconds)

        @return None
        """

        threading.Thread.__init__(self)

        self.shutdownEvent = threading.Event()

        self._msgQueue = msgQueue
        self._readPeriod = readPeriod

        # Initialize GPS (Python 3 version info found at https://learn.adafruit.com/adafruit-ultimate-gps-on-the-raspberry-pi/using-your-gps)
        self._gpsSession = gps.gps('localhost', '2947')
        self._gpsSession.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
    
    def run(self):
        """
        Overriden method called when the thread is started

        @param None

        @return None
        """

        while not self.shutdownEvent.is_set():
            gpsData = self.__getGPSData()

            # Broadcast GPS data
            if gpsData:
                msgData = json.dumps(gpsData)

                self._msgQueue.put((msgData, MessageType.GPS_MESSAGE))

            time.sleep(self._readPeriod)

        # Cleanup
        self.__shutdown()

    def __getGPSData(self):
        """
        Retrieves GPS data from a USB sensor

        @param None

        @return GPS data (dictionary)
        """

        gpsData = {}

        data = self._gpsSession.next()

        # Filter on the Time Position Velocity class
        if data['class'] == 'TPV':
            gpsData['time'] = data.get('time')
            gpsData['lat'] = data.get('lat')
            gpsData['lon'] = data.get('lon')
            gpsData['alt'] = data.get('alt')
            gpsData['speed'] = data.get('speed')
            gpsData['climb'] = data.get('climb')
            gpsData['epy'] = data.get('epy')
            gpsData['epx'] = data.get('epx')
            gpsData['epv'] = data.get('epv')

        return gpsData

    def __shutdown(self):
        """
        Performs shutdown procedures for the thread

        @param None

        @return None
        """

        pass
