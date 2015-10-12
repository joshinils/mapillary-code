#!/bin/bash

#
#	file: time_lapse.sh
#
#	coder: moenkemt@geo.hu-berlin.de
#
#	purpose: creates timelapse video from all digital camera pics (Garmin VIRB)
#
#	requires: avconv (formerly FFmpeg), convert (ImageMagick)
#

source_jpg="DCIM"
target_mp4="Video"

# create sorted list of pictures
cd /data/temp
mkdir $target_mp4
find DCIM -iname *.jpg | sort > $target_mp4/out.lst
X=1

# convert pictures to frames
cat $target_mp4/out.lst | while read bild
do
	echo $bild
	convert -resize 1024x768 $bild $target_mp4/img$(printf %04d.%s ${X%.*} ${i##*.})jpg
	let X="$X+1"
done

# convert frames to vudei
cd $target_mp4
avconv -framerate 4 -i 'img%04d.jpg' -r 25 -c:v libx264 out.mp4

# optional: add audio.mp3 of suitable length
avconv -i out.mp4 -i ../audio.mp3 -map 0:0 -map 1:0 -vcodec copy -acodec copy video.mp4 

# and done.
cd ..
