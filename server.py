from flask import (
    Flask,
    request,
    make_response,
    render_template,
    send_file,
    flash,
    redirect,
    url_for,
)
from io import BytesIO
from time import sleep
import json
import glob
import subprocess
import signal
import toml
from datetime import datetime
import os
from picamera import PiCamera, Color, exc as PiCameraException
from enum import Enum

from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__, static_url_path="/static")
app.config.update(SECRET_KEY=b"nobody_cares")

config = dict()
with open("./config.toml") as configfile:
    config = toml.load(configfile)

startup_time = datetime.now()


def clean_up_files(extensions, config):
    for extension in extensions:
        for rel_path in glob.glob(f"./static/*.{extension}"):
            abs_path = os.path.abspath(rel_path)
            ctime = os.path.getctime(abs_path)
            creation_date = datetime.fromtimestamp(ctime)
            delta = startup_time - creation_date
            delta_hours = delta.seconds / 3600
            if delta_hours >= config["files"]["max_age_hours"]:
                subprocess.run(["rm", abs_path])
                print(f"Cleaned up {abs_path}")


clean_up_files(["mp4", "h264"], config)

class DeviceState(Enum):
    Initializing = 0
    Ready = 1
    Recording = 2


device_state = DeviceState.Initializing
device = PiCamera(
    resolution=(config["camera"]["width"], config["camera"]["height"]),
    framerate=config["camera"]["fps"],
)
device.annotate_frame_num = True
device.annotate_background = Color("black")
device.annotate_text = datetime.now().strftime("%Y-%m-%d %H:%M")
device_state = DeviceState.Ready

scheduler = BackgroundScheduler()

def update_video_ts():
    device.annotate_text = datetime.now().strftime("%Y-%m-%d %H:%M")

scheduler.add_job(update_video_ts, trigger='interval', seconds=5)
scheduler.start()


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/start-video")
def start_video():
    return render_template("start-video.html")


@app.route("/stop-video")
def stop_video():
    return render_template("stop-video.html")


@app.route("/videos")
def videos():
    videos = [os.path.basename(video) for video in glob.glob("./static/*.mp4")]
    return render_template("videos.html", videos=videos)


@app.route('/preview')
def preview():
    still = BytesIO()
    device.capture(still, format='jpeg', use_video_port=True)
    still.seek(0)
    return send_file(still, mimetype='image/jpeg')



@app.route("/start-recording", methods=["POST"])
def start_recording():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"./static/{now}.h264"
    try:
        device.start_recording(
            filename,
            format="h264",
            quality=config["camera"]["quality"],
        )
        device_state = DeviceState.Recording
        flash(f"New recording started.")
    except PiCameraException.PiCameraAlreadyRecording:
        flash("Cannot start recording, recording already in progress.")
    return redirect(url_for("home"))


@app.route("/stop-recording", methods=["POST"])
def stop_recording():
    try:
        device.stop_recording()
        device_state = DeviceState.Ready
        for filename in glob.glob("./static/*.h264"):
            abs_filename = os.path.abspath(filename)
            if os.path.exists(f"{abs_filename}.mp4"):
                # skip over
                # subprocess.run(["rm", f"{abs_filename}.mp4"])
                continue
            subprocess.run(
                ["MP4Box", "-add", abs_filename, f"{abs_filename}.mp4"]
            )
            subprocess.run(["MP4Box", "-inter", "500", f"{abs_filename}.mp4"])
            if not config["debug"]:
                subprocess.run(["rm", abs_filename])
        flash(
            "Stopped recording and postprocessed video."
        )
    except:
        flash("Cannot stop recording, no recording is in progress.")

    return redirect(url_for("home"))
