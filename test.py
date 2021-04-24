from picamera import PiCamera, Color, exc as PiCameraException
from time import sleep
import signal

device = PiCamera(
            resolution=(1640, 922,
            30,
        )
device.annotate_frame_num = True
filename = 'test'

def handler(_,_):
    device.stop_recording()
    device.close()

signal.signal(signal.SIGINT, handler)


device.start_recording(f"{filename}.h264",
                        format="h264",
                        quality=30)

while True:
    sleep(1)
    print('recording)
