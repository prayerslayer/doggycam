from picamera import PiCamera, Color, exc as PiCameraException
from time import sleep
import signal
import sys
from threading import Thread

def handler(_1,_2):
    device.stop_recording()
    device.close()
    sys.exit(0)

signal.signal(signal.SIGINT, handler)

def loop1():
    device = PiCamera(
                resolution=(1640, 922),
                framerate=30,
            )
    device.annotate_frame_num = True
    sleeptime = 5
    filename = f'test_sleep{sleeptime}'
    device.start_recording(f"{filename}.h264",
                        format="h264",
                        quality=30)
    



def loop2():
    print("Hi! I am loop2.")
    while True:
        sleep(1)
        print("zzz")

t = Thread(target=loop1)
t.daemon = True
t.start()
loop2()
