#!/bin/bash
cd ~/doggycam
export FLASK_APP=server
/home/pi/.local/bin/flask run --host 0.0.0.0
