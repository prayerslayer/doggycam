from flask import Flask, request, make_response, render_template, flash, redirect, url_for
from io import BytesIO
from time import sleep
import json
import glob
import uwsgi
from datetime import datetime
import os
from uwsgidecorators import timer

app = Flask(__name__, static_url_path="/static")
app.config.update(
    SECRET_KEY=b'nobody_cares'
)

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
    videos = list(reversed(videos))
    return render_template("videos.html", videos=videos)


@timer(5)
def make_preview(signum):
    uwsgi.mule_msg(json.dumps({"command": "preview"}))


@timer(60)
def update_ts(signum):
    uwsgi.mule_msg(json.dumps({"command": "update_ts"}))


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
    flash('Recording started.')
    return redirect(url_for('home'))


@app.route("/stop-recording", methods=["POST"])
def stop_recording():
    uwsgi.mule_msg(json.dumps({"command": "stop_rec"}))
    flash('Recording stopped, video is being postprocessed.')
    return redirect(url_for('home'))
