from picamera import PiCamera, Color, exc as PiCameraException
import json
import io
import uwsgi
from datetime import datetime
import subprocess
import os
from time import sleep
import glob
from threading import Thread
from queue import Queue
import toml
from enum import Enum

config = dict()
with open("./config.toml") as configfile:
    config = toml.load(configfile)


class DeviceState(Enum):
    Initializing = 0
    Ready = 1
    Recording = 2

queue = Queue(maxsize=5)

def thready():
    device_state = DeviceState.Initializing
    device = PiCamera(
        resolution=(config["camera"]["width"], config["camera"]["height"]),
        framerate=config["camera"]["fps"],
    )
    device.annotate_frame_num = True
    device.annotate_background = Color("black")
    device.annotate_text = datetime.now().strftime("%Y-%m-%d %H:%M")
    device_state = DeviceState.Ready
    sleep(2)

    while True:
        task = queue.get()
        cmd = task['command']

        if cmd == "preview":
            # use video port for perfect positioning of camera
            device.capture(
                "./static/preview.jpg",
                use_video_port=True,
            )

        elif cmd == "update_ts":
            device.annotate_text = datetime.now().strftime("%Y-%m-%d %H:%M")

        elif cmd == "start_rec":
            filename = task["filename"]
            try:
                device.start_recording(
                    f"{filename}.h264",
                    format="h264",
                    quality=config["camera"]["quality"],
                )
                device_state = DeviceState.Recording
            except PiCameraException.PiCameraAlreadyRecording:
                print("Cannot start recording, recording already in progress.")

        elif cmd == "stop_rec":
            try:
                device.stop_recording()
                device_state = DeviceState.Ready
                for filename in glob.glob("./static/*.h264"):
                    abs_filename = os.path.abspath(filename)
                    if os.path.exists(f"{abs_filename}.mp4"):
                        subprocess.run(["rm", f"{abs_filename}.mp4"])
                    subprocess.run(
                        ["MP4Box", "-add", abs_filename, f"{abs_filename}.mp4"]
                    )
                    subprocess.run(["MP4Box", "-inter", "500", f"{abs_filename}.mp4"])
                    if not config["debug"]:
                        subprocess.run(["rm", abs_filename])
            except PiCameraException.PiCameraNotRecording:
                print("Cannot stop recording, no recording is in progress.")

        elif cmd == 'shutdown':
            device.close()
            queue.task_done()
            return

        queue.task_done()

def main():
    Thread(target=thready, daemon=True).start()
    while True:
        print(f"Mule waiting, device is {device_state}...")
        message = uwsgi.mule_get_msg()
        print(f"Mule received: {message}")

        if message == "":
            print("SHUTDOWN")
            queue.put({ 'command': 'shutdown'})
            return

        task = json.loads(message)
        queue.put(task)


if __name__ == "__main__":
    main()
