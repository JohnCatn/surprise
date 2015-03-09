from ConfigParser import SafeConfigParser
import time
import picamera
from datetime import datetime

config = SafeConfigParser()
config.read('/home/pi/surprise/config.ini')

print config.get('main', 'trigger_time') # -> "value1"
start_time = config.get('main', 'trigger_time')
if config.getint('main', 'ran') == 0:
	config.set('main', 'ran', '1')
	with open('config.ini', 'w') as f:
                config.write(f)
	with picamera.PiCamera() as camera:
		camera.hflip = True
		camera.vflip = True
    		camera.start_preview()
    		time.sleep(2)
    		for filename in camera.capture_continuous('/home/pi/surprise/captures/img{counter:03d}.jpg'):
        		print('Captured %s' % filename)
        		time.sleep(60) # wait 1 minute
			difference = datetime.now() - datetime.strptime(start_time,"%Y-%m-%d_%H%M%S")
			if(difference.seconds/60 > 60):
				print 'stopping'
				# more that 60 minutes since started
				break
