# Python Modules
import json
import threading

# 3rd Party Modules
from gps import *

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

        # Initialize GPS
        self._gpsd = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
    
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

    def __getGPSData(self):
        """
        Retrieves GPS data from a USB sensor

        @param None

        @return GPS data (dictionary)
        """

        gpsData = {}

        data = self._gpsd.next()

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
