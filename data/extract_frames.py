
import os
from subprocess import call

from config import SOURCE_VIDEO_DIR, SOURCE_FRAMES_DIR, IMAGES_PER_SECOND


videos = os.listdir(SOURCE_VIDEO_DIR)
images = [s[:s.find('.')]+"_%05d.png" for s in videos]
os.makedirs('frames', exist_ok=True)
for vid, img in zip(videos, images):
	call("ffmpeg -i %s -r %i %s"%(os.path.join(SOURCE_VIDEO_DIR, vid), IMAGES_PER_SECOND, os.path.join(SOURCE_FRAMES_DIR, img)), shell=True)
