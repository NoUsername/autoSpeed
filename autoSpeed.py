import subprocess
import os
import time
import re
DOWN="down"
UP="up"

NWIF = "3g-umts"
DEBUG = True

PING_THRES_HIGH = 550
PING_THRES_LOW = 400

ADJUST_UP_TIMEOUT = 30
ADJUST_RESET_TIMEOUT = 60*30

# bandwith cap values
BW_CAP_DEFAULT=4000
BW_CAP_MAX=8000
BW_CAP_MIN=700
BW_CAP_MINSTEP=100
BW_CAP_MAXSTEP=1000
# min measured badwith to step up (kb/s)
BW_MIN_ADJUST=140

BANDWIDTH = {
"current":BW_CAP_DEFAULT,
"nextStep":1000,
"lastDirection":UP
}

SLEEPTIME=10

def runCommand(command):
	return os.popen(command).read()

def measurePing():
	result = runCommand("ping -c 3 8.8.8.8 | grep min/avg/max")
	m = re.search("\d+/(\d+).?(\d+)?/", result)
	if len(m.groups()) > 0:
		result = m.group(1)
		if DEBUG: print("ping result %s"%result)
		return long(result)
	return None

def getReceivedBytes():
	result = runCommand("ifconfig %s | grep \"RX bytes\""%NWIF)
	m = re.search("RX bytes:(\d+)", result)
	if len(m.groups()) > 0:
		return long(m.group(1))
	return None

def getThroughput():
	bytes = getReceivedBytes()
	if bytes == None:
		return None
	time.sleep(1)
	result = getReceivedBytes() - bytes
	if DEBUG: print("throughput result %s"%result)
	return result

def adjustmentDownNeeded():
	badCount = 0
	for i in xrange(2):
		ping = measurePing()
		if ping > PING_THRES_HIGH:
			badCount += 1
	if badCount > 1:
		return True
	return False

def adjustmentUpNeeded():
	speed = getThroughput()
	if (speed/1024) > BW_MIN_ADJUST:
		if measurePing() < PING_THRES_LOW:
			return True
	return False

def getRealSpeedCap():
	speed = runCommand("sh speedCap -p")
	return long(speed)

def rereadSpeedCap():
	global BANDWIDTH
	BANDWIDTH["current"] = getRealSpeedCap()

def setSpeedCap(speed):
	global BANDWIDTH
	speed = long(speed)
	speed = max(speed, BW_CAP_MIN)
	speed = min(speed, BW_CAP_MAX)
	runCommand("sh speedCap %s"%speed)
	BANDWIDTH["current"] = speed

def adjust(direction):
	global BANDWIDTH
	last = BANDWIDTH["lastDirection"]
	nextStep = BANDWIDTH["nextStep"]
	current = BANDWIDTH["current"]
	if direction == UP:
		print("adjusting up")
		speed = current + nextStep
		setSpeedCap(speed)
	else:
		print("adjusting down")
		speed = current - nextStep
		setSpeedCap(speed)
	print("set speedCap to %s"%speed)

	if last == direction:
		nextStep = nextStep * 1.5
	else:
		nextStep = nextStep / 2

	BANDWIDTH["nextStep"] = long(min(max(nextStep, BW_CAP_MINSTEP), BW_CAP_MAXSTEP))
	BANDWIDTH["lastDirection"] = direction

def mainLoop():
	adjustTimes = [time.time()]
	adjustedCount = 0
	adjusted = False
	rereadSpeedCap()

	while True:
		adjusted = False
		if adjustmentDownNeeded():
			adjust(DOWN)
			adjustTimes.append(time.time())
			adjustedCount += 1
			adjusted = True
		else:
			if time.time() - adjustTimes[-1] > ADJUST_UP_TIMEOUT:
				if adjustmentUpNeeded():
					adjust(UP)
					adjustTimes.append(time.time())
					adjustedCount += 1
					adjusted = True
		if adjusted: print("adjusted (#%s)"%adjustedCount)
		time.sleep(SLEEPTIME)
		if time.time() - adjustTimes[-1] > ADJUST_RESET_TIMEOUT:
			rereadSpeedCap()
			if BANDWIDTH["current"] < BW_CAP_DEFAULT:
				setSpeedCap(BW_CAP_DEFAULT)
			adjustTimes = [time.time()]
			BANDWIDTH["lastStep"] = 1000
			print("resetting adjustment stats")

if runCommand('uname -a').lower().find("openwrt") == -1:
	print("not running on router")
	NWIF = "wlan0"

print("real current cap: %s"%getRealSpeedCap())

mainLoop()

while True:
	#print("adjustment? %s"%adjustmentNeeded())
	print("speed %s"%(getThroughput()/1024))
import sys
sys.exit(0)

while True:
	print("throughput: %s"%(getThroughput()/1024))

