# Doggycam

A camera to check on my dog because

* it's a thing I need
* I didn't want to spend 200 quid on a consumer product
* I thought I can do this myself?
* no cloud!

Built with Pi Zero W and Raspicam v2, [Flask](https://flask.palletsprojects.com/en/1.1.x/) and [picamera](https://picamera.readthedocs.io).

## Requirements

* Python 3
* [gpac](https://github.com/gpac/gpac), because `MP4Box` is used to convert H264 videos from camera to actual MP4s
* See requirements file

## Installation

(not tested)

```
sudo apt-get update
sudo apt-get install -y gpc python3 python3-pip
pip3 install -r requirements.txt
```

Then clone the repository into your home directory.

```
cd ~
git clone <this repo>
```

## Usage

```
./startuwsgi.sh
```

This starts a uWSGI server at port 5000 with a small web app in which

* you see a preview image from the camera, useful for checking it works and positioning
* you can start a video recording
* you can stop a recording video
* you can view recorded videos


### Autostart

Add this to `/etc/rc.local` (prior to `exit 0`) so it's started automatically:

```
printf "Starting Doggycam"
./startuwsgi.sh &
```
