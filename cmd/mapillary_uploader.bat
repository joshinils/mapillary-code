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
rem					python 3.5 with pip install -r requirements (openstreetcam)
rem
rem		note:		important to use python version 2.7 and 3.5
rem

rem 	credentials
set MAPILLARY_USERNAME=***
set MAPILLARY_PERMISSION_HASH=***
set MAPILLARY_SIGNATURE_HASH=***

D:
FOR /D %%d IN (d:\Mapillary\DCIM\???_VIRB) DO (
	cd %%d
    rem remove duplcates
	c:\python27\python.exe D:\Mapillary\mapillary_tools\python\remove_duplicates.py -a 180 -t 250 -v %%d
    rmdir %%d\duplicates /s /q

	rem resize and sequence
    FOR %%f IN (*.jpg) DO "\Mapillary\image_magick\convert.exe" -verbose "%%f" -normalize -quality 85 -resize 1920x "%%f"
    c:\python27\python.exe D:\Mapillary\mapillary_tools\python\sequence_split.py %%d 120 300

	rem upload to mapillary
    FOR /D %%s IN (%%d\??) DO (
		del %%d\DONE
		c:\python27\python.exe D:\Mapillary\mapillary_tools\python\upload_with_authentication.py %%s --auto_done
	)

	rem upload to openstreetview
	cd \Mapillary\openstreetview\upload-scripts\upload_photos_by_exif
	FOR /D %%s IN (%%d\??) DO (
		start c:\python35\python.exe upload_exif.py -t 1 -p %%s\success
	)
)

rem and done
pause
