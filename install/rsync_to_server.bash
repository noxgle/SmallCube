#!/bin/bash
# 
# Script start in project folder.
SRC="/home/pi/workspace/SmallCube/"
DST="pi@192.168.0.103:/opt/SmallCube/"

rsync -r -a -v --delete --exclude 'venv' --exclude 'tmp' --exclude '.git' --exclude '.idea' --exclude '__pycache__' \
--exclude 'db.sql'  --exclude 'conn_app.txt' --exclude 'smallcube.sock' --exclude 'api_smallcube.sock' $SRC $DST