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
# import cv2
import numpy as np
from tqdm import tqdm
from PIL import Image
from PIL import ImageOps
# import piexif


def optimize_file(file_path):
    image_org = Image.open(file_path)
    try:
        exif_data = image_org.info['exif']
        image_rgb = ImageOps.autocontrast(image_org)
        image_rgb.save(file_path, optimize=True, quality=75, exif=exif_data)
    except Exception as error:
        print(error)
        image_org.close()
        return False
    return True


#
#   Main
#
if __name__ == "__main__":
    print ("*** JPEG optimizer ***")
    try:
        ordnerpfad = sys.argv[1]
    except:
        ordnerpfad = r"D:\Mapillary\DCIM"
        pass
    # Loop over JPG files
    for subdirz, dirz, filez in os.walk(ordnerpfad):
        print("\nOptimizing:", subdirz)
        for f in tqdm(filez):
            file_path = subdirz + os.sep + f
            if file_path.lower().endswith('.jpg'):
                success = optimize_file(file_path)
                if not(success):
                    os.remove(file_path)

