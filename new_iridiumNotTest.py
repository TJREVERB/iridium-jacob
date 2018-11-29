import collections
import logging
import sys
import threading
import time
import serial

messageQueue = collections.deque([])
logger = logging.getLogger("iridium")
transmitting=0
ser=None

def checksend():
    logger.warning("checking starting")
    while True:
        logger.warning("transmitting: {}".format(transmitting))
        if transmitting%2==1:
            logger.warning("exiting listen from check")

        elif transmitting%2==0:
            logger.warning("starting listen from check")
            threading.Thread(target=listen()).start()
        time.sleep(.5)

def setup(port):
    logger.warning("setup starting")
    global ser
    ser = serial.Serial(port=port, baudrate=19200)
    ser.flush()
    logger.warning("setup finished, all good")
    

    sendCommand("AT")
    ser.readline().decode('UTF-8') # get the empty line
    resp = ser.readline().decode('UTF-8')
    logger.warning(resp)
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


def send(message):
    transmitting=transmitting+1
    alert=2
    if len(sys.argv) < 2:
        logger.warning("Not enough args")
        exit(255)
    if ser==None:
        setup(port='/dev/ttyUSB1')

    while alert==2:
        sendCommand("AT+CSQF")

        ser.readline().decode('UTF-8') # get the empty line
        signal = ser.readline().decode('UTF-8')
        # prepare message
        sendCommand("AT+SBDWT=" + thingToSend)
        ok = ser.readline().decode('UTF-8')
        ser.readline().decode('UTF-8') # get the empty line

        # send message
        sendCommand("AT+SBDI")
        resp = ser.readline().decode('UTF-8') # get the empty line
        resp = resp.replace(",", " ").split(" ")
        startTime = time.time()
        currTime = startTime

        while len(resp) > 0 and len(resp) <= 2:
            resp = ser.readline().decode('UTF-8')
            resp = resp.replace(",", " ").split(" ")
            currTime = time.time()
            if (currTime - startTime) > 30:
                logger.warning("timed out moving on")
                break
        # get the rsp
        try:
            alert = int(resp[1])
            logger.warning("alert:"+alert)
        except:
            logger.warning("exception thrown")
            continue
    logger.warning("send done")
    transmitting=transmitting+1



def listen():
    if len(sys.argv) < 1:
        logger.warning("No args")
        exit(255)
    if ser==None:
        setup(port='/dev/ttyUSB1')
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

threading.Thread(target=checksend()).start()
setup(sys.argv[1])
threading.Thread(target=listen()).start()