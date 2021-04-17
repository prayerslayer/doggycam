#!/bin/bash
uwsgi --master --http 0.0.0.0:5000 --manage-script-name --mount /=server:app --mule=mule.py
