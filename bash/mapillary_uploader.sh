#!/bin/bash
#
#	file: mapillary_uploader.sh
#
#	coder: moenkemt@geo.hu-berlin.de
#
#	purpose: delete duplicates from Garmin VIRB, split image in 
#	squences, crop 4x3 pictures to upper 16x9 part (75%),
#	upload to mapillary sequences with at least 5 pictures
#

export MAPILLARY_DATA="/data/temp/DCIM"
export MAPILLARY_PATH="/root/mapillary_tools/python"
export MAPILLARY_USERNAME="moenk"
export MAPILLARY_PERMISSION_HASH="***"
export MAPILLARY_SIGNATURE_HASH="***"

function dupes {
	for file in $MAPILLARY_DATA/*
	do
		echo dupes: "$file"
		$MAPILLARY_PATH/remove_duplicates.py -d 2 $file $file/dup
		rm -r $file/dup
	done
}

function sequencer {
	for file in $MAPILLARY_DATA/*
	do
		echo sequencer: "$file"
		$MAPILLARY_PATH/sequence_split.py $file 180 400
	done
}

function cropper {
	for file in $(find $MAPILLARY_DATA -iname '*.jpg'); do 
		echo resize to 16x9: "$file"
		convert "$file" -gravity north -crop 100x75% +repage "$file"
	done
}

function normalizer {
	for file in $(find $MAPILLARY_DATA -iname '*.jpg'); do 
		echo normalize: "$file"
		convert "$file" -resize 2048x -normalize "$file"
	done
}


function upload {
	shopt -s nocaseglob
	find $MAPILLARY_DATA/ -type d | sort | while read file
	do
		num=`ls -l $file/*.jpg | wc -l`
		if [ "$num" -gt "5" ]; then
			if [ ! -d "$file/success" ]; then
				echo "Upload now: $file ($num)"
				yes | $MAPILLARY_PATH/upload_with_authentication.py $file
				echo "Pausing..."; sleep 5s
			else
				echo "Already done: $file"
			fi
		fi
		rm $file/success/ -r
	done  
}

#
# main
#
#git clone https://github.com/mapillary/mapillary_tools.git
dupes
sequencer
normalizer
upload
