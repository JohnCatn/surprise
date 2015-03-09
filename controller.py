# Import required Python libraries
import MySQLdb as mdb
import os
import RPi.GPIO as GPIO
import time
from twilio.rest import TwilioRestClient
from ConfigParser import SafeConfigParser
from datetime import datetime

# TWILIO Account settings
account_sid = "YOUR_ACCOUNT_SID"
auth_token  = "YOUR_AUTH_TOKEN"
client = TwilioRestClient(account_sid, auth_token)

# set the pins numbering mode
GPIO.setmode(GPIO.BOARD)

# Select the GPIO pins used for the encoder K0-K3 data inputs
GPIO.setup(11, GPIO.OUT)
GPIO.setup(15, GPIO.OUT)
GPIO.setup(16, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)

# Select the signal to select ASK/FSK
GPIO.setup(18, GPIO.OUT)

# Select the signal used to enable/disable the modulator
GPIO.setup(22, GPIO.OUT)

# Disable the modulator by setting CE pin lo
GPIO.output (22, False)

# Set the modulator to ASK for On Off Keying 
# by setting MODSEL pin lo
GPIO.output (18, False)

# Initialise K0-K3 inputs of the encoder to 0000
GPIO.output (11, False)
GPIO.output (15, False)
GPIO.output (16, False)
GPIO.output (13, False)

# Configure DB settings
DB_SERVER = "YOUR_DB_SERVER"
DB_NAME = "surprise"
DB_USER = "surprise"
DB_PASSWORD = "Surpr1se!"

HOME_DIR = "/home/pi/surprise/"

# Send text message update
def sendMessage(stage):
        message = client.messages.create(body="Triggered Stage: " + str(stage),
                to="TO_NUMBER",                                    
                from_="FROM_NUMBER")  
        print message.sid


# Checks what step to run next
def getNextStage():
	id = 0
	con = mdb.connect(DB_SERVER, DB_USER, DB_PASSWORD, DB_NAME);
	cur = con.cursor(mdb.cursors.DictCursor)
	cur.execute("SELECT id, name FROM surprise_stages ss WHERE `order` = (SELECT MIN(`order`) FROM surprise_stages ss1 WHERE completed IS NULL)")
	for i in xrange(cur.rowcount):
    		row = cur.fetchone()
		print 'name = ' + row['name']
		id = row['id']
	#tidy up the connection and close the curser
	ret_val = id
	cur.close()
	con.close()
	return ret_val

# Checks if a trigger has been set
def checkTrigger():
	print 'in check trigger'
	openTrigger = False
        con = mdb.connect(DB_SERVER, DB_USER, DB_PASSWORD, DB_NAME);
        cur = con.cursor(mdb.cursors.DictCursor)
        cur.execute("SELECT id FROM triggers WHERE actioned = 0")
	print len(xrange(cur.rowcount))
	if len(xrange(cur.rowcount)) > 0:
		openTrigger = True
        #tidy up the connection and close the curser
        ret_val = openTrigger
	print ret_val
        cur.close()
	con.close()
        return ret_val

# Flag the stage as complere
def completeStage(id):
	print 'in complete stage'
        con = mdb.connect(DB_SERVER, DB_USER, DB_PASSWORD, DB_NAME);
        cur = con.cursor(mdb.cursors.DictCursor)
        cur.execute("UPDATE surprise_stages SET completed=NOW() WHERE id=" + str(id))
        cur.close()
        con.close()

# Funtion to close down any open actions
def actionTriggers():
	print 'in action triggers'
        con = mdb.connect(DB_SERVER, DB_USER, DB_PASSWORD, DB_NAME);
        cur = con.cursor(mdb.cursors.DictCursor)
	# Lazy update but just set any open trggers to 1 as we shouldn;t have another trigger so soom
        cur.execute("UPDATE triggers SET actioned=1 WHERE actioned =0")
        cur.close()
        con.close()

def stage_one():
	print 'in stage one'
	# Turn on plug 1
	#print "sending code 1111 socket 1 on"
        GPIO.output (11, True)
        GPIO.output (15, True)
        GPIO.output (16, True)
        GPIO.output (13, True)
        # let it settle, encoder requires this
        time.sleep(0.1)
        # Enable the modulator
        GPIO.output (22, True)
        # keep enabled for a period
        time.sleep(0.25)
        # Disable the modulator
        GPIO.output (22, False)


def stage_two():
	print 'in stage two'
        # Turn on plug 2
        #print "sending code 1110  socket 2 on"
        GPIO.output (11, False)
        GPIO.output (15, True)
        GPIO.output (16, True)
        GPIO.output (13, True)
        # let it settle, encoder requires this
        time.sleep(0.1)
        # Enable the modulator
        GPIO.output (22, True)
        # keep enabled for a period
        time.sleep(0.25)
        # Disable the modulator
        GPIO.output (22, False)
	# Reduce volume of song as it's loud
	os.system('amixer cset numid=1 -- 70%')
	os.system('aplay ' + HOME_DIR + 'audio/song1.wav')

def stage_three():
	print 'in stage 3'
	timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
	# increase volume as voice is quiet
	config = SafeConfigParser()
	config.read('config.ini')
	config.set('main', 'trigger_time', timestamp)
	config.set('main', 'ran','0')

	with open('config.ini', 'w') as f:
    		config.write(f)

	os.system('amixer cset numid=1 -- 100%')
	os.system('mpg321 ' + HOME_DIR + 'audio/audio2.mp3')

def stage_zero():
	print 'no rows found so done'


#et up mapping between array and function blocks
stages = { 0 : stage_zero, 
	1 : stage_one,
	2 : stage_two,
	3 : stage_three
}

try:
	#Check if there are any open triggers
	if checkTrigger():
		# We've got a trigger so deal with it
		# close triggers so it doesn't gte picked up twice
		actionTriggers()
		# work out the stage running
		stage = getNextStage()
		print 'stage = ' + str(stage)
		# mow only message if stage greater than 0
		if stage > 0:
			sendMessage(stage)
			#implement logic
			completeStage(stage)	
                # Call the relevant function for the returned stage
		stages[stage]()
			
		GPIO.cleanup()

# Clean up the GPIOs for next time
except KeyboardInterrupt:
        GPIO.cleanup()
