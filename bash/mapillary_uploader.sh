#!/bin/bash
#
#	file: mapillary_uploader.sh
#
#	coder: moenkemt@geo.hu-berlin.de
#
#	purpose: delete duplicates from Garmin VIRB, build squences, 
#	upload to mapillary sequences with at least 5 pictures
#

export MAPILLARY_DATA="/data/temp/baumi"
export MAPILLARY_PATH="/root/mapillary_tools/python"
export MAPILLARY_USERNAME="moenk"
export MAPILLARY_PERMISSION_HASH="***"
export MAPILLARY_SIGNATURE_HASH="***"

for file in $MAPILLARY_DATA/*
do
	echo $file
	$MAPILLARY_PATH/remove_duplicates.py -d 2 $file $file/dup
	$MAPILLARY_PATH/sequence_split.py $file 120 500
	rm -r $file/dup
done

shopt -s nocaseglob
find $MAPILLARY_DATA/ -type d | sort | while read file
do
	num=`ls -l $file/*.jpg | wc -l`
	if [ "$num" -gt "5" ]; then
		if [ ! -d "$file/success" ]; then
			echo "Upload now: $file ($num)"
			yes | $MAPILLARY_PATH/upload_with_authentication.py $file
		else
			echo "Already done: $file"
		fi
	fi
	rm $file/success/ -r
done  
