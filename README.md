# Motion
### Config
/etc/motion/motion.conf

### Service
sudo service motion restart
sudo motion

http://localhost:8081

### Output
/var/lib/motion

# GPS
### Service
stty -F /dev/ttyACM0 9600
sudo service gpsd stop
sudo gpsd -n -N -F /var/run/gpsd.sock /dev/ttyACM0

cgps -s
xgps
