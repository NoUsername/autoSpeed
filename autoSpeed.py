import subprocess
import os
import time
import re
import traceback
DOWN="down"
UP="up"

NWIF = "3g-umts"
DEBUG = False
DEBUG2 = True

PING_THRES_HIGH = 800 #550
PING_THRES_LOW = 450

ADJUST_UP_TIMEOUT = 30
ADJUST_RESET_TIMEOUT = 60*30

# bandwith cap values
BW_CAP_MINSTEP=100
BW_CAP_MAXSTEP=1000
# min measured badwith to step up (kb/s)
BW_MIN_ADJUST=140

BW_STEPS = [500,1000,1500,2000,2500,3000,3500,4000,4500,5000,5500,6000,7000]
BW_IDX_DEFAULT = 7

class BANDWIDTH:
	currentIdx = BW_IDX_DEFAULT
	current = BW_STEPS[BW_IDX_DEFAULT]
	lastDirection = UP

SLEEPTIME=10

def runCommand(command):
	return os.popen(command).read()

def measurePing():
	result = runCommand("ping -c 3 8.8.8.8 | grep min/avg/max")
	m = re.search("\d+/(\d+).?(\d+)?/", result)
	if m == None:
		return None
	if len(m.groups()) > 0:
		result = m.group(1)
		if DEBUG: print("ping result %s"%result)
		return long(result)
	return None

def getReceivedBytes():
	result = runCommand("ifconfig %s | grep \"RX bytes\""%NWIF)
	m = re.search("RX bytes:(\d+)", result)
	if m == None:
		return None
	if len(m.groups()) > 0:
		return long(m.group(1))
	return None

def getThroughput():
	bytes = getReceivedBytes()
	if bytes == None:
		return None
	time.sleep(1)
	bytesAfter = getReceivedBytes()
	if bytesAfter == None:
		return None
	result = bytesAfter - bytes
	if DEBUG: print("throughput result %s"%result)
	return long(result/1024)

def getCurrentThroughputUpperThres():
	currentSpeedCap = rereadSpeedCap()
	return long(currentSpeedCap/10)

def adjustmentDownNeeded():
	return adjustmentDownNeededIntern(1)

def adjustmentDownNeededIntern(remaining):
	badCount = 0
	NUM_PINGS = 3
	for i in xrange(NUM_PINGS):
		ping = measurePing()
		if ping != None and ping > PING_THRES_HIGH:
			badCount += 1
	if badCount == NUM_PINGS:
		if remaining > 0:
			time.sleep(2)
			return adjustmentDownNeededIntern(remaining-1)
		return True
	return False

def adjustmentUpNeeded():
	ping = measurePing()
	if ping != None and ping < PING_THRES_LOW:
		speedThres = getCurrentThroughputUpperThres()
		speed = getThroughput()
		if DEBUG2: print("measured: %s thres: %s"%(speed, speedThres))
		if speed > speedThres:
			return True
	return False

def getRealSpeedCap():
	speed = runCommand("sh speedCap -p")
	return long(speed)

def findBwIdx(value):
	for i in xrange(len(BW_STEPS)):
		if BW_STEPS[i] >= value:
			return i
	return len(BW_STEPS)-1

def rereadSpeedCap():
	global BANDWIDTH
	BANDWIDTH.current = getRealSpeedCap()
	BANDWIDTH.currentIdx = findBwIdx(BANDWIDTH.current)
	return BANDWIDTH.current

def setSpeedCap(speed):
	global BANDWIDTH
	speed = long(speed)
	speed = max(speed, BW_STEPS[0])
	speed = min(speed, BW_STEPS[-1])
	runCommand("sh speedCap %s"%speed)
	BANDWIDTH.current = speed
	BANDWIDTH.currentIdx = findBwIdx(BANDWIDTH.current)

def adjust(direction):
	global BANDWIDTH
	idx = BANDWIDTH.currentIdx
	if direction == UP:
		idx += 1
	else:
		idx -= 1
	idx = min(max(0, idx), len(BW_STEPS)-1)
	print("adjusting %s to %s"%("UP" if direction==UP else "DOWN", BW_STEPS[idx]))
	setSpeedCap(BW_STEPS[idx])

def adjustLoop():
	adjustTimes = [time.time()]
	adjustedCount = 0
	adjusted = False
	rereadSpeedCap()
	print("current idx & speed (%s, %s)"%(BANDWIDTH.currentIdx, BANDWIDTH.current))

	while True:
		speed = getThroughput()
		if DEBUG: print("current measured throughput %s"%(speed))
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
		# remove old switching entries (leave one)
		while len(adjustTimes) > 1 and (time.time() - adjustTimes[0]) > 60:
			adjustTimes = adjustTimes[1:]
		if time.time() - adjustTimes[-1] > ADJUST_RESET_TIMEOUT:
			rereadSpeedCap()
			if BANDWIDTH.current < BW_STEPS[BW_IDX_DEFAULT]:
				setSpeedCap(BW_STEPS[BW_IDX_DEFAULT])
			adjustTimes = [time.time()]
			print("resetting adjustment stats")

def testLoop():
	rereadSpeedCap()
	print("current speedCap is %s"%BANDWIDTH.current)
	while True:
		print("measured %s ping, %s throughput"%(measurePing(), getThroughput()))
		print("should turn up? %s"%adjustmentUpNeeded())
		print("should turn down? %s"%adjustmentDownNeeded())
		time.sleep(1)

if runCommand('uname -a').lower().find("openwrt") == -1:
	print("not running on router")
	NWIF = "wlan0"

if __name__== "__main__":
	print("real current cap: %s"%getRealSpeedCap())
	#testLoop()
	try:
		adjustLoop()
	except:
		traceback.print_exc(None, open('error.log', 'w'))
