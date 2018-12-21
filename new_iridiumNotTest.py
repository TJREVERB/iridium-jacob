import collections
import logging
import sys
import threading
import time
import serial

messageQueue = collections.deque([])
logger = logging.getLogger("iridium")
transmitting=0
debug = True

def setup(port):
    global ser
    ser = serial.Serial(port=port, baudrate = 19200, timeout = 15)
    ser.flush()    

    sendCommand("AT")
    ser.readline().decode('UTF-8') # get the empty line
    resp = ser.readline().decode('UTF-8')
    # # print (resp)
    if 'OK' not in resp:
        # # print("Echo"+resp)
        exit(-1)
    # show signal quality
    sendCommand('AT+CSQ')
    ser.readline().decode('UTF-8') # get the empty line
    resp = ser.readline().decode('UTF-8')
    ser.readline().decode('UTF-8') # get the empty line
    ok = ser.readline().decode('UTF-8') # get the 'OK'
    # # # print("resp: {}".format(repr(resp)))
    if 'OK' not in ok:
        # # print('Unexpected "OK" response: ' + ok)
        exit(-1)
    sendCommand("AT+SBDMTA=0")
    #if debug:
        # # print("Signal quality 0-5: " + resp)
    ser.write("AT+SBDREG? \r\n".encode('UTF-8'))
    while True:
        try:
            regStat = int(ser.readline().decode('UTF-8').split(":")[1])
            break
        except:
            continue
        break
    if regStat != 2:
         sendCommand("AT+SBDREG")


def sendCommand(cmd):
    logger.warning("sendCommand starting")
    if cmd[-1] != '\r\n':
        cmd += '\r\n'
    logger.warning("Sending command: {}".format(cmd))
    ser.write(cmd.encode('UTF-8'))
    ser.flush()



    
def send(thingToSend):
    # try to send until it sends
    startTime = time.time()
    alert = 2
    while alert == 2:
        #signal = ser.readline().decode('UTF-8')#empty line
        #signal = ser.readline().decode('UTF-8')#empty line
        sendCommand("AT+CSQF")

        signal = ser.readline().decode('UTF-8')#empty line
        signal = ser.readline().decode('UTF-8')
        # # print("last known signal strength: "+signal)
        # prepare message
        sendCommand("AT+SBDWT=" + thingToSend)
        ok = ser.readline().decode('UTF-8') # get the 'OK'
        ser.readline().decode('UTF-8') # get the empty line

        # send message
        sendCommand("AT+SBDI")
        
        resp = ser.readline().decode('UTF-8') # get the empty line
        resp = resp.replace(",", " ").split(" ")
        startTime = time.time()
        currTime = startTime

        #signal = ser.readline().decode('UTF-8')#empty line
        #signal = ser.readline().decode('UTF-8')#empty line
        while len(resp) > 0 and len(resp) <= 2:
            # # print(resp)
            resp = ser.readline().decode('UTF-8')    
            resp = resp.replace(",", " ").split(" ")
            curTime = time.time()
            if (curTime-startTime)>30:
                # # print("time out moving on")
                break
        # get the rsp
        
          #  if debug:
        # # #print("resp: {}"t )
        try:
            # # print("*******************" + str(resp))
            alert = int(resp[1])
            # # print(alert)
        except:
            # # print("********************exception thrown")
            continue

        #if debug:
            # # #print("alert: {}".format(alert))
    exit(-1)



def listen():
    if len(sys.argv) < 1:
        logger.warning("No args")
        exit(255)
    logger.warning("listen starting")
    sendCommand("AT+SBDMTA=1")
    signalStrength = 0
    ringSetup = 0
    iteration = 0
    while ringSetup != 2:
        ring = ser.readline().decode('UTF-8')
        logger.warning(ring)
        if "SBDRING" in ring:
            bytesLeft = 1
            ser.timeout = 120
            while bytesLeft != 0:
                sendCommand("AT+SBDIXA")
                resp = "A"
                while len(resp) < 2:
                    test = ser.readline().decode('UTF-8')
                    logger.warning("Response before Splitting: "+test)
                    resp = test.split(': ')
                    logger.warning("Response after splitting:  "+resp[1]+" "+resp[0]+" END")
                try:
                    resp = resp[1].split(', ')
                except:
                    logger.error("index out of bounds exception \r\n closing program")
                    exit(-1)
                bytesLeft = int(resp[0])
            sendCommand("AT+SBDRT")
            sendCommand("at+sbdmta=0")
            break

global port
port=sys.argv[1]

setup(port)
send(sys.argv[2])