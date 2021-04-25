from flask import (
    Flask,
    request,
    make_response,
    render_template,
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
import uwsgi
from datetime import datetime
import os
from picamera import PiCamera, Color, exc as PiCameraException
from uwsgidecorators import timer

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


#@timer(5)
#def preview(signum):
#    uwsgi.mule_msg(json.dumps({"command": "preview"}))


#@timer(10)
#def update_ts(signum):
#    uwsgi.mule_msg(json.dumps({"command": "update_ts"}))


@app.route("/start-recording", methods=["POST"])
def start_recording():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{filename}.h264"
    try:
        device.start_recording(
            filename,
            format="h264",
            quality=config["camera"]["quality"],
        )
        device_state = DeviceState.Recording
        flash("New recording scheduled, if there wasn't one in progress already.")
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
            subprocess.run(["rm", f"{abs_filename}.mp4"])
        subprocess.run(
            ["MP4Box", "-add", abs_filename, f"{abs_filename}.mp4"]
        )
        subprocess.run(["MP4Box", "-inter", "500", f"{abs_filename}.mp4"])
        if not config["debug"]:
            subprocess.run(["rm", abs_filename])
        flash(
            "Scheduled stop recording, if there was one in progress. Video is being postprocessed in this case."
        )
    except:
        flash("Cannot stop recording, no recording is in progress.")

    return redirect(url_for("home"))
