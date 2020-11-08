@ECHO OFF
C:\Python38\python.exe C:\Users\moenk\OneDrive\Python\mapillary-code\python3\removedupes3.py
rmdir d:\Mapillary\DCIM\duplicates /s /q
rmdir d:\Mapillary\DCIM\errors /s /q
C:\Python38\python.exe C:\Users\moenk\OneDrive\Python\mapillary-code\python3\exifsort3.py
pause

D:
FOR /D %%d IN (d:\Mapillary\DCIM\OSM_*) DO (
	cd %%d
	C:\Python38\python.exe C:\Users\moenk\OneDrive\Python\mapillary-code\python3\jpegoptimizer3.py %%d
	pause
	
	cd d:\Mapillary\mapillary_tools\
	c:\python27\python.exe d:\Mapillary\mapillary_tools\mapillary_tools.py process --import_path %%d --user_name moenk --verbose --rerun --skip_subfolders
	c:\python27\python.exe d:\Mapillary\mapillary_tools\mapillary_tools.py upload --import_path %%d
	pause
	
	cd D:\Mapillary\openstreetcam\
	C:\Python38\python.exe osc_tools.py upload -p %%d
	pause

	cd ..
	rmdir %%d /s /q	
)
PAUSE

