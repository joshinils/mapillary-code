#
#   file: jpegoptimizer3.py
#
#   coder: geomoenk@googlemail.com
#
#   purpose: optimize all JPG files with EXIF headers from a directory
#            to 75% quality using OpenCV and Pillow before uploading
#

import os
import sys
import cv2
import numpy as np
from tqdm import tqdm
from PIL import Image


print ("*** JPEG optimizer ***")
try:
    ordnerpfad = sys.argv[1]
except:
    ordnerpfad = r"D:\Mapillary\DCIM"
    pass

for subdirz, dirz, filez in os.walk(ordnerpfad):
    print("\nOptimizing:", subdirz)
    for f in tqdm(filez):
        file_path = subdirz + os.sep + f
        if file_path.lower().endswith('.jpg'):
            image_org = Image.open(file_path)
            try:
                exifdata = image_org.info['exif']
                image_cv2 = cv2.normalize(np.array(image_org), None, 0, 255, cv2.NORM_MINMAX)
                image_rgb = Image.fromarray(image_cv2)
                image_rgb.save(file_path, optimize=True, quality=75, exif=exifdata)
            except:
                image_org.close()
                os.remove(file_path)
