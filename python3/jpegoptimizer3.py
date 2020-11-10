import os
import sys
from tqdm import tqdm
from PIL import Image
# from PIL import ImageOps
import cv2
import numpy as np


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
            # try:
            exifdata = image_org.info['exif']
            # image_yuv = cv2.cvtColor(np.array(image_org), cv2.COLOR_RGB2YUV)
            # image_yuv[:, :, 0] = cv2.equalizeHist(image_yuv[:, :, 0])
            # image_rgb = Image.fromarray(cv2.cvtColor(image_yuv, cv2.COLOR_YUV2RGB))
            image_bgr = cv2.cvtColor(np.array(image_org), cv2.COLOR_RGB2BGR)
            image_bgr = cv2.normalize(image_bgr, None, 0, 255, cv2.NORM_MINMAX)
            image_rgb = Image.fromarray(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB))
            image_rgb.save(file_path, optimize=True, quality=75, exif=exifdata)
        # except:
        #         image_org.close()
        #         os.remove(file_path)