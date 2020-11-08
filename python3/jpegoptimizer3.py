import os
import sys
from tqdm import tqdm
from PIL import Image
from PIL import ImageOps


print ("*** JPEG optimizer ***")
try:
    ordnerpfad = sys.argv[1]
except:
    ordnerpfad = r"D:\Mapillary\DCIM"
    pass

for subdirz, dirz, filez in os.walk(ordnerpfad):
    for f in tqdm(filez):
        file_path = subdirz + os.sep + f
        if file_path.lower().endswith('.jpg'):
            im1 = Image.open(file_path)
            try:
                exifdata = im1.info['exif']
                im2 = ImageOps.autocontrast(im1)
                im2.save(file_path, optimize=True, quality=75, exif=exifdata)
            except:
                im1.close()
                os.remove(file_path)