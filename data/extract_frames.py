#!/usr/bin/python3

import os
from subprocess import call

SOURCE_DIR = 'videos'
TARGET_DIR = 'frames'

videos = os.listdir(SOURCE_DIR)
images = [s[:s.find('.')]+"_%05d.png" for s in videos]
os.makedirs('frames', exist_ok=True)
for vid, img in zip(videos, images):
	call("ffmpeg -i %s -r 6 %s"%(os.path.join(SOURCE_DIR, vid), os.path.join(TARGET_DIR, img)), shell=True)
