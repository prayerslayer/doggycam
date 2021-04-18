from picamera import PiCamera, Color, exc as PiCameraException
import json
import io
import uwsgi
from datetime import datetime
import subprocess
import os
from time import sleep
import glob
import toml

config = dict()
with open("./config.toml") as configfile:
    config = toml.load(configfile)


def main():
    try:
        device = PiCamera(
            resolution=(
                config["camera"]["resolution"]["width"],
                config["camera"]["resolution"]["height"],
            ),
            framerate=config["camera"]["fps"],
        )
        device.annotate_background = Color("black")
        device.annotate_text = datetime.now().strftime("%Y-%m-%d %H:%M")

        while True:
            print(f"Mule waiting...")
            message = uwsgi.mule_get_msg()
            print(f"Mule received: {message}")

            if message == "":
                print("SHUTDOWN")
                device.close()
                return

            task = json.loads(message)

            cmd = task["command"]

            if cmd == "preview":
                device.annotate_text = datetime.now().strftime("%Y-%m-%d %H:%M")
                device.capture("./static/preview.jpg")

            elif cmd == "start_rec":
                filename = task["filename"]
                try:
                    device.start_recording(
                        f"{filename}.h264", format="h264", quality=task["q"]
                    )
                except PiCameraException.PiCameraAlreadyRecording:
                    print("Cannot start recording, recording already in progress.")

            elif cmd == "stop_rec":
                try:
                    device.stop_recording()
                    for filename in glob.glob("./static/*.h264"):
                        abs_filename = os.path.abspath(filename)
                        if os.path.exists(f"{abs_filename}.mp4"):
                            subprocess.run(["rm", f"{abs_filename}.mp4"])
                        subprocess.run(
                            ["MP4Box", "-add", abs_filename, f"{abs_filename}.mp4"]
                        )
                        subprocess.run(["rm", abs_filename])
                except PiCameraException.PiCameraNotRecording:
                    print("Cannot stop recording, no recording is in progress.")

    finally:
        device.close()


if __name__ == "__main__":
    main()
