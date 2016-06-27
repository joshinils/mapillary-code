@echo off
rem
rem		file:		mapillary_uploader.bat
rem
rem		purpose:	upload all pics from my garmin virb
rem
rem		requires: 	image magick portable version extracted
rem 				mapillary_tools from github extracted
rem					pathon 2.7 installed with anaconda2
rem

set MAPILLARY_USERNAME=moenk
set MAPILLARY_PERMISSION_HASH=***
set MAPILLARY_SIGNATURE_HASH=***

D:
cd \Mapillary\DCIM
FOR /D %%d IN (d:\Mapillary\DCIM\???_VIRB) DO (
  cd %%d
  C:\Anaconda2\python.exe D:\Mapillary\mapillary_tools\python\remove_duplicates.py %%d
  FOR %%f IN (*.jpg) DO "\Mapillary\image_magick\convert.exe" -verbose "%%f" -normalize -quality 85 -resize 2048x "%%f"
  C:\Anaconda2\python.exe D:\Mapillary\mapillary_tools\python\sequence_split.py %%d 120 300
  FOR /D %%s IN (%%d\??) DO C:\Anaconda2\python.exe D:\Mapillary\mapillary_tools\python\upload_with_authentication.py %%s --auto_done
)

pause
