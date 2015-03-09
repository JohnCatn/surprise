from ConfigParser import SafeConfigParser
from datetime import datetime
import time

timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
# increase volume as voice is quiet
config = SafeConfigParser()
config.read('config.ini')
#config.add_section('main')
config.set('main', 'trigger_time', timestamp)

with open('config.ini', 'w') as f:
	config.write(f)

