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
import toml
import uwsgi
from datetime import datetime
import os
from uwsgidecorators import timer

app = Flask(__name__, static_url_path="/static")
app.config.update(SECRET_KEY=b"nobody_cares")

config = dict()
with open("./config.toml") as configfile:
    config = toml.load(configfile)

now = datetime.now()


def clean_up_files(extensions, config):
    for extension in extensions:
        for rel_path in glob.glob(f"./static/*.{extension}"):
            abs_path = os.path.abspath(rel_path)
            ctime = os.path.getctime(abs_path)
            creation_date = datetime.fromtimestamp(ctime)
            delta = now - creation_date
            delta_hours = delta.seconds * 3600
            if delta_hours >= config.files.max_age:
                subprocess.run(["rm", abs_path])
                print(f"Cleaned up {abs_path}")


clean_up_files(["mp4", "h264"], config)


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


@timer(5)
def make_preview(signum):
    uwsgi.mule_msg(json.dumps({"command": "preview"}))


@app.route("/start-recording", methods=["POST"])
def start_recording():
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M")
    uwsgi.mule_msg(
        json.dumps(
            {
                "command": "start_rec",
                "filename": f"./static/{filename}",
                "q": int(request.form.get("q", 30)),
            }
        )
    )
    flash("New recording scheduled, if there wasn't one in progress already.")
    return redirect(url_for("home"))


@app.route("/stop-recording", methods=["POST"])
def stop_recording():
    uwsgi.mule_msg(json.dumps({"command": "stop_rec"}))
    flash(
        "Scheduled stop recording, if there was one in progress. Video is being postprocessed in this case."
    )
    return redirect(url_for("home"))
