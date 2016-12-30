@echo off
rem
rem		file:		mapillary_uploader.bat
rem
rem		purpose:	upload all pics from my garmin virb
rem
rem		requires: 	image magick portable version extracted
rem 				mapillary_tools from github extracted
rem 				openstreetview\upload-scripts extracted
rem					python 2.7 with pip install -r requirements (mapillary)
rem					python 3.4 with pip install -r requirements (openstreetcam)
rem

set MAPILLARY_USERNAME=moenk
set MAPILLARY_PERMISSION_HASH=***
set MAPILLARY_SIGNATURE_HASH=***

D:
FOR /D %%d IN (d:\Mapillary\DCIM\???_VIRB) DO (
	cd %%d
    c:\python27\python.exe D:\Mapillary\mapillary_tools\python\remove_duplicates.py -a 180 -t 250 -v %%d
    rmdir %%d\duplicates /s /q
    FOR %%f IN (*.jpg) DO "\Mapillary\image_magick\convert.exe" -verbose "%%f" -normalize -quality 85 -resize 2048x "%%f"
    c:\python27\python.exe D:\Mapillary\mapillary_tools\python\sequence_split.py %%d 120 300
    FOR /D %%s IN (%%d\??) DO c:\python27\python.exe D:\Mapillary\mapillary_tools\python\upload_with_authentication.py %%s --auto_done
	cd \Mapillary\openstreetview\upload-scripts\upload_photos_by_exif
	FOR /D %%s IN (%%d\??) DO c:\python34\python.exe upload_photos_by_exif.py -p %%s\success
)

pause
