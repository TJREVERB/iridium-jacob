import collections
import logging
import sys
import threading
import time
import serial

messageQueue = collections.deque([])
logger = logging.getLogger("iridium")


def sendCommand(cmd):
    logger.warning("sendCommand starting")
    if cmd[-1] != '\r\n':
        cmd += '\r\n'
    logger.warning("Sending command: {}".format(cmd))
    ser.write(cmd.encode('UTF-8'))
    ser.flush()
    cmd_echo = serialRead()


def serialListen():
    global messageQueue
    while True:
        line = ser.readline().decode('UTF-8')
        if line == 'SBDRING':
            listenUp()
        else:
            messageQueue.append(line)
            logger.warning("line added")


def serialRead():
    logger.warning("starting serialRead")
    while len(messageQueue) < 1:
        time.sleep(0.5)
        logger.warning("waiting")
    logger.warning("pop: {}".format(messageQueue))
    return messageQueue.popleft()


def setup(port):
    logger.warning("setup starting")
    global ser
    ser = serial.Serial(port=port, baudrate=19200)
    ser.flush()
    # doTheOK()


def doTheOK():
    logger.warning("doTheOK starting")
    sendCommand("AT")
    logger.warning("gigathonk")
    serialRead()  # get empty line
    resp = serialRead()
    logger.warning(resp)
    if 'OK' not in resp:
        logger.error("OK:" + resp)
        raise RuntimeError("Invalid OK: {}".format(repr(resp)))
    # show signal quality
    sendCommand('AT+CSQ')
    serialRead()  # get empty lne
    resp = serialRead()
    serialRead()  # get empty line
    ok = serialRead()
    if 'OK' not in ok:
        logger.error('Unexpected "OK" response: ' + ok)
        raise RuntimeError("Invalid OK: {}".format(repr(ok)))
    sendCommand("AT+SBDMTA=0")
    logger.warning("Signal quality 0-5: " + resp)
    ser.write("AT+SBDREG? \r\n".encode('UTF-8'))
    while True:
        try:
            regStat = int(serialRead().split(":")[1])
            break
        except:
            continue
        break
    if regStat != 2:
        sendCommand("AT+SBDREG")


def main():
    logger.warning("main starting")
    if len(sys.argv) < 2:
        logger.warning("bad plz use proper - $0 <serialport> <msg>")
        exit(255)
    setup(sys.argv[1])
    t = threading.Thread(target=serialListen, daemon=True)
    t.start()
    doTheOK()
    logger.warning("thonk")
    send(sys.argv[2])


def listenUp():
    logger.warning("listenUp starting")
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
                    # logger.warning("Response before Splitting: "+test+"tttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttt")
                    resp = test.split(': ')
                    # logger.warning("Response after splitting:  "+resp[1]+" 0 "+resp[0]+" END")
                try:
                    resp = resp[1].split(', ')
                except:
                    logger.error("index out of bounds exception \r\n closing program")
                    raise
                bytesLeft = int(resp[0])
            sendCommand("AT+SBDRT")
            sendCommand("at+sbdmta=0")
            break


def send(thingToSend):
    logger.warning("send starting")
    # try to send until it sends
    startTime = time.time()
    alert = 2
    while alert == 2:
        sendCommand("AT+CSQF")

        serialRead()  # get empty line
        signal = serialRead()
        # prepare message
        sendCommand("AT+SBDWT=" + thingToSend)
        ok = serialRead()
        serialRead()

        # send message
        sendCommand("AT+SBDI")
        resp = serialRead()
        resp = resp.replace(",", " ").split(" ")
        startTime = time.time()
        currTime = startTime
        while len(resp) > 0 and len(resp) <= 2:
            resp = serialRead()
            resp = resp.replace(",", " ").split(" ")
            curTime = time.time()
            if (curTime - startTime) > 30:
                # # logger.warning("time out moving on")
                break
        # get the rsp
        try:
            # # logger.warning("*******************" + str(resp))
            alert = int(resp[1])
            # # logger.warning(alert)
        except:
            # # logger.warning("********************exception thrown")
            continue
    logger.warning("someone messed up their code, exiting")
    raise RuntimeError("ur bad")


if __name__ == '__main__':
    main()