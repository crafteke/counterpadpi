import time
import busio
from board import SCL, SDA
import RPi.GPIO as GPIO
from adafruit_trellis import Trellis
from signal import signal, SIGINT
from sys import exit
import socketio
import counterPi.counter as counter
import time
from timeloop import Timeloop #pip3 install timeloop
from datetime import timedelta

GPIO.setmode(GPIO.BCM)

tl = Timeloop() # for counter scheduling
HACKING_BOX_SIGNAL_OUT=27 # pin for hacking box
HACKING_BOX_SIGNAL_IN=22 # pin for hacking box


countdown = counter.Counter()
countdown.setup(4,5,6)
running_countdown=False
remaining_time=0
sio = socketio.Client()

SIO_SERVER='http://face6core.local:4567'
#SIO_SERVER='http://192.168.1.211:4567'
# Create the I2C interface
i2c = busio.I2C(SCL, SDA)

# Create a Trellis object
trellis = Trellis(i2c,[0x70,0x71])  # 0x70 when no I2C address is supplied

input_code=[False]*24
#mapping pad to one-D array for code, 42 means unused pad (validation,hidden pads, led for doors state)
PAD_MAPPING=[19,23,42,42,18,22,42,42,17,21,42,42,16,20,42,42,3,7,11,15,2,6,10,14,1,5,9,13,0,4,8,12]

VALIDATION_PAD=3
CANCEL_PAD=11
ROOMS_LIGHTS_PAD=[2,6,10,14]
ACTIVE_LIGHT_PAD= 15

enabled_pad=False
hacking_box_activated=False
# Turn on every LED
def allLedsOn():
    print("Turning all LEDs on...")
    trellis.led.fill(True)
    #trellis.led[CANCEL_PAD] = False
    #trellis.led[VALIDATION_PAD] = False




# Turn off every LED
def allLedsOff():
    print("Turning all LEDs off...")
    trellis.led.fill(False)
    #trellis.led[CANCEL_PAD] = True
    #trellis.led[VALIDATION_PAD] = True


def switchPadLed(state,toggle_control=False):
    for i,val in enumerate(PAD_MAPPING):
        if val != 42:
            trellis.led[i]=state
    if(toggle_control):
        trellis.led[CANCEL_PAD] = state
        trellis.led[VALIDATION_PAD] = state


def resetCode():
    global input_code
    input_code=[False]*24

def formatCodeMessage():
    return ''.join(list(map(lambda x: '1' if x else '0', input_code)))

def binaryToInt():
    return int(formatCodeMessage(),2)

pressed_buttons = None
def initTrellis():
    global pressed_buttons
    trellis.led[VALIDATION_PAD] = True
    trellis.led[CANCEL_PAD] = True
    pressed_buttons = set()
    trellis.read_buttons()
    time.sleep(2) # to avoid init noise
    allLedsOff()


def monitorButtons():
    global pressed_buttons
    just_pressed, released = trellis.read_buttons()
    msg={}
    for b in just_pressed:
        print("pressed:", b)
        if(b==VALIDATION_PAD):
            print("Sending code n reset")
            trellis.led[VALIDATION_PAD] = False
            switchPadLed(True)
            msg["controller_id"]="push_pad_code"
            msg["value"]=binaryToInt()
            if sio.connected:
                sio.emit('Command',msg)
            resetCode()
            time.sleep(1)
            switchPadLed(False)

            #send array with code and reset it
            #blink all pads and erase
        elif(b==CANCEL_PAD):
            trellis.led[CANCEL_PAD] = False
            trellis.led[VALIDATION_PAD] = False
            resetCode()
            switchPadLed(True)
            time.sleep(1)
            switchPadLed(False)
            trellis.led[CANCEL_PAD] = True
            trellis.led[VALIDATION_PAD] = True
        else:
            index=PAD_MAPPING[b]
            if(index<len(input_code)):
                input_code[index] = not input_code[index]
                trellis.led[b]= input_code[index]

    pressed_buttons.update(just_pressed)
    for b in released:
        print("released:", b)
        if(b==VALIDATION_PAD):
            trellis.led[b] = True
        elif(b==CANCEL_PAD):
            trellis.led[CANCEL_PAD] = True
    pressed_buttons.difference_update(released)
    # for b in pressed_buttons:
    #     print("still pressed:", b)
        #trellis.led[b] = True
@sio.event
def Command(data):
    global running_countdown,remaining_time,enabled_pad,hacking_box_activated
    #print(data)
    if(data['controller_id']=='start_counter'):
        running_countdown=True
        remaining_time=2*int(data['value'])
        print("Starting counter with ",data['value'], 'seconds')
    if(data['controller_id']=='pause_counter'):
        running_countdown=False
        print("Pausing counter.")
    if(data['controller_id']=='trigger_pad_state'):
        if(int(data['value'])==1):
            enabled_pad = True
            trellis.led[CANCEL_PAD] = True
            trellis.led[VALIDATION_PAD] = True
            resetCode()
            print("Enable pad.")
        else:
            enabled_pad = False
            switchPadLed(False,True)
            resetCode()
            print("Disable pad.")
    if(data['controller_id']=='corridor_room_on'):
        trellis.led[ROOMS_LIGHTS_PAD[int(data['value'])-1]] = True
        print("Switch room ", data['value']," led on.")
    if(data['controller_id']=='corridor_room_off'):
        trellis.led[ROOMS_LIGHTS_PAD[int(data['value'])-1]] = False
        print("Switch room ", data['value']," led off.")
    if(data['controller_id']=='corridor_padled_state'):
        if(data['value'] == '1'):
            state=True
        else:
            state=False
        trellis.led[ACTIVE_LIGHT_PAD] = state
        print("Switch LED activate ", data['value'],".")
    if(data['controller_id']=='hacking_box_activate'):
        if(data['value'] == '1'):
            state=1
            hacking_box_activated=True
        else:
            state=0
            hacking_box_activated=False
        print("Hacking box state:", data['value'],".")
        if(hacking_box_activated):
            GPIO.output(HACKING_BOX_SIGNAL_OUT, state)
            #GPIO.add_event_detect(HACKING_BOX_SIGNAL, GPIO.RISING, callback=lambda c : print("box signal"), bouncetime=200)
        else:
            GPIO.output(HACKING_BOX_SIGNAL_OUT, state)






check_ok=0
#check if hacking box was up for 1 seconds
@tl.job(interval=timedelta(seconds=0.05))
def watch_hackingbox():
    global check_ok,hacking_box_activated
    if(hacking_box_activated):
        #print(GPIO.input(HACKING_BOX_SIGNAL))
        if(GPIO.input(HACKING_BOX_SIGNAL_IN)==1):
            check_ok+=1
        else:
            check_ok=0
        if(check_ok==20):
            check_ok=0
            print("hacking box signal received.")
            msg={}
            msg["controller_id"]="hacking_box_validate"
            msg["value"]=1
            if sio.connected:
                sio.emit('Command',msg)

@tl.job(interval=timedelta(seconds=0.5))
def final_countDown():
    global remaining_time
    if(running_countdown and remaining_time>=0):
        i=remaining_time
        #seconds is multiplied by 2, so we can blink the dots
        #seconds/60= minutes, /120 because we *2
        #minutes*100 to display in XX:00
        #seconds %60 for remaining seconds on this minute. display in 00:XX
        countdown.display_number(int(int(i/120)*100+int(i/2)%60),i%2)
        remaining_time-=1
        # if(remaining_time%2==0):
        #     print( "Remaining time : ",remaining_time/2)

def hackingbox_event(channel):
    print("hacking box signal received.")
    msg={}
    msg["controller_id"]="hacking_box_ping"
    msg["value"]=1
    if sio.connected:
        sio.emit('Command',msg)

def main():
    global enabled_pad
    print("Starting corridor controller...")
    try:
        sio.connect(SIO_SERVER)
    except:
        print("SocketIO server not available")
    if sio.connected:
        sio.emit('Register',"counterpadPi")
        print("Connected with SID ",sio.sid)
        msg={}
        msg["controller_id"]="what_time_is_it_big_ben"
        msg["value"]=1
        sio.emit('Command',msg)
    tl.start(block=False)
    #animationStart()
    print("Blinking counter.")
    countdown.test_led()
    allLedsOn()
    time.sleep(0.5)
    allLedsOff() # for trellis
    time.sleep(0.5)
    allLedsOn()
    initTrellis()
    GPIO.setup(HACKING_BOX_SIGNAL_IN,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(HACKING_BOX_SIGNAL_OUT,GPIO.OUT)
    GPIO.output(HACKING_BOX_SIGNAL_OUT, 0)
    while True:
        try:
            if enabled_pad:
                monitorButtons()
        except OSError:
            print("Lost connection to I2C trellis. Trying back...")
        time.sleep(0.05)

def handler(signal_received, frame):
    # Handle any cleanup here
    print('SIGINT or CTRL-C detected. Exiting gracefully')
    sio.disconnect()
    tl.stop()
    exit(0)

if __name__ == "__main__":
    signal(SIGINT, handler)
    main()

# Turn on every LED, one at a time
def animationStart():
    print("Turning on each LED, one at a time...")
    for i in range(32):
        trellis.led[i] = True
        time.sleep(0.05)
    # Turn off every LED, one at a time
    print("Turning off each LED, one at a time...")
    for i in range(31, 0, -1):
        trellis.led[i] = False
        time.sleep(0.05)
