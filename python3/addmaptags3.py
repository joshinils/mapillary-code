import os
import sys
import json
import piexif
from tqdm import tqdm
import pprint
from exifpil3 import PILExifReader


def add_mapillary_tags(filepath):
    reader = PILExifReader(filepath)
    datetime = reader.read_capture_time()
    str_timestamp = datetime.strftime("%Y_%m_%d_%H_%M_%S_%f")[:-3]
    lat, lon = reader.get_lat_lon()
    payload_dict = {
      "MAPLongitude": lon,
      "MAPLatitude": lat,
      "MAPCaptureTime": str_timestamp
    }
    payload_json = json.dumps(payload_dict)
    # print(payload_json)
    exif_dict = piexif.load(filepath)
    exif_dict['0th'][piexif.ImageIFD.ImageDescription] = payload_json.encode('utf-8')
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, filepath)
    # pprint(exif_dict)
    return True


#
#   Main
#
if __name__ == "__main__":
    print ("*** Add Mapillary EXIF ImageDescription ***")
    ordnerpfad = sys.argv[1]
    # Loop over JPG files
    for subdirz, dirz, filez in os.walk(ordnerpfad):
        if len(filez) > 0:
            print("\nAdding ImageDescription:", subdirz)
            for f in tqdm(filez):
                file_path = subdirz + os.sep + f
                if file_path.lower().endswith('.jpg'):
                    success = add_mapillary_tags(file_path)
