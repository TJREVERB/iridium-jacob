import collections
import threading
import serial
import time
import sys

debug = True
messageQueue = collections.deque([])

def sendCommand(cmd):
    if cmd[-1] != '\r\n':
        cmd += '\r\n'
    #if debug:
        # # # print("Sending command: {}".format(cmd))
    ser.write(cmd.encode('UTF-8'))
    ser.flush()
    cmd_echo = threading.Thread(target=serialListen())
    #if debug:
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # print("Echoed: " + cmd_echo.decode('UTF-8'))

def serialListen():
    global messageQueue
    while True:
        line = ser.readline().decode('UTF-8')
        if line == 'SBDRING':
            listenUp()
        else:
            messageQueue.append(line)
            serialRead()



def serialRead():
    while len(messageQueue) < 1:
        time.sleep(0.5)
    return messageQueue.popleft()

def setup(port):
    global ser
    ser = serial.Serial(port=port, baudrate = 19200, timeout = 15)
    ser.flush()
    doTheOK()

def doTheOK():
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
    
def main():
    argument = " "
    command = " "
    global port
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = '/dev/ttyUSB0'
    setup(port)
    if len(sys.argv) < 4:
        # # print("not enought args")
        exit(-1)
    else:
        if sys.argv[2] == "message":
            command = sys.argv[3]
            # # print("Message to send: "+command)
        elif sys.argv[2] == "command":
            argument = sys.argv[3]
            # # print("Command to execute: "+argument)
        elif sys.argv[2] == "listen":
            # # print("Listening for Ring")
            threading.Thread(target=listenUp.start())
        else:
            # # print("argument 3 is not valid, say either command, message or listen")
            exit(-1)

    #setup(port)
    #if debug:
        # # print("Connected to {}".format(ser.name))

    # clear everything in buffer
    #ser.reset_input_buffer()
    #ser.reset_output_buffer()
    # disable echo
    # sendCommand('ATE0', has_resp=True)

    
    if ' ' not in argument:
        # # print("Sending command: "+argument)
        threading.Thread(target=sendCommand(argument)).start()
        exit(-1)
    if ' ' not in command:
        # # print('Sending Message: '+command)
        threading.Thread(target=send(command)).start()
def listenUp():
    sendCommand("AT+SBDMTA=1")
    ser = serial.Serial(port=port, baudrate = 19200, timeout = 1)
    signalStrength = 0
    ringSetup = 0
    iteration = 0
    while ringSetup != 2 :
        ring = ser.readline().decode('UTF-8')
        # # print(ring)
        if "SBDRING" in ring:
            bytesLeft=1
            ser.timeout=120
            while bytesLeft != 0:
                sendCommand("AT+SBDIXA")
                resp = "A"
                while len(resp) < 2:
                    test = ser.readline().decode('UTF-8')
                    # # #print("Response before Splitting: "+test+"tttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttt")
                    resp = test.split(': ')
                # # #print("Response after splitting:  "+resp[1]+" 0 "+resp[0]+" END")
                try:
                    resp = resp[1].split(', ')
                except:
                    # # print("index out of bounds exception \r\n closing program")
                    exit(-1)
                bytesLeft= int(resp[0])
                # # #print("split response: "+resp[1])
                #bytesLeft = 0
            sendCommand("AT+SBDRT")
            #while True:
                #try:
                    # # #print(ser.readline().decode('UTF-8').split(":")[1])

                    # # #print("done")
                    #break
                #except:
                    #continue
            ringSetup = 0
            # # print(ser.readline().decode('UTF-8'))
            # # print(ser.readline().decode('UTF-8'))
            # # print(ser.readline().decode('UTF-8'))
            # # print(ser.readline().decode('UTF-8'))
            # # print(ser.readline().decode('UTF-8'))
            # # print(ser.readline().decode('UTF-8'))
            sendCommand("at+sbdmta=0")
            break
        #ser.flush()
        # # print("listening...")

def send(thingToSend):
    # try to send until it sends
    startTime = time.time()
    alert = 2
    while alert == 2:
        #signal = ser.readline().decode('UTF-8')#empty line
        #signal = ser.readline().decode('UTF-8')#empty line
        sendCommand("AT+CSQF")

        signal = threading.Thread(target=listenUp()).start()
        # # print("last known signal strength: "+signal)
        # prepare message
        sendCommand("AT+SBDWT=" + thingToSend)
        ok = threading.Thread(target=listenUp()).start() # get the 'OK'
        threading.Thread(target=listenUp()).start()

        # send message
        sendCommand("AT+SBDI")
        
        resp = threading.Thread(target=listenUp()).start()
        resp = resp.replace(",", " ").split(" ")
        startTime = time.time()
        currTime = startTime

        #signal = ser.readline().decode('UTF-8')#empty line
        #signal = ser.readline().decode('UTF-8')#empty line
        while len(resp) > 0 and len(resp) <= 2:
            # # print(resp)
            resp = threading.Thread(target=listenUp()).start()
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

if __name__ == '__main__':
    if len(sys.argv) < 4:
        # # print(len(sys.argv))
        # # print("Usage: $0 <serial port> <command or message or listenUp> <text to send or command>")
        exit(-1)
    try:
        # # print(len(sys.argv))
        main()
    finally:
        # sendCommand('ATE1', has_resp=False)
        pass

