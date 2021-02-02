import os
import sys
import json
import piexif
from tqdm import tqdm
import pprint
from exifpil3 import PILExifReader
import ast

def add_mapillary_tags(filepath):
    reader = PILExifReader(filepath)
    image_description =  ast.literal_eval(reader.get_exif_tag("ImageDescription"))
    print((reader.get_exif_tag("ImageDescription")))
    pprint.pprint(image_description)

    datetime = reader.read_capture_time()
    str_timestamp = datetime.strftime("%Y_%m_%d_%H_%M_%S_%f")[:-3]
    try:
        lat, lon = reader.get_lat_lon()
    except:
        lat, lon = 0, 0
    payload_dict = {
      "MAPLongitude": lon,
      "MAPLatitude": lat,
      "MAPCaptureTime": str_timestamp
    }
    payload_dict = {}

    comment = {
        "MAPCompassHeading":
        {
            "TrueHeading": 51.294972095164098,
            "MagneticHeading": 51.294972095164098,
            "AccuracyDegrees": 0
        },
        "MAPGpsTime": "2021_02_02_10_17_30_217",
        "MAPVersionString": "4.20.3 (380)",
        "MAPLatitude": 52.630904055138977,
        "MAPCaptureTime": "2021_02_02_10_17_31_126",
        "MAPGPSSpeed": 1.7702888250350952,
        "MAPDeviceModel": "iPhone 8",
        "MAPDeviceUUID": "A661877E-2291-4EAB-BF41-381709F16FD3",
        "MAPSettingsUserKey": "EnKnkPu35HGG6eUyAGkM7E",
        "MAPAppNameString": "mapillary_ios",
        "MAPSettingsTokenValid": 1,
        "MAPAltitude": 51.014470369333239,
        "MAPLocalTimeZone": "Europe\/Berlin (MEZ) offset 3600",
        "MAPGPSAccuracyMeters": 8.0012082736808772,
        "MAPAtanAngle": 3.1201469898223877,
        "MAPPhotoUUID": "0CCDF139-263C-4814-91AC-34E428A2205E",
        "MAPLongitude": 13.309697456784811,
        "MAPSettingsUploadHash": "250174de8f6bf2ec984481950826cce95b828d1445d9518ff32b9fad45d89989",
        "MAPDeviceMake": "Apple",
        "MAPSequenceUUID": "74B1F562-1890-4D76-89BB-A348BC4E3219",
        "MAPAccelerometerVector":
        {
            "x": -0.92238730192184448,
            "y": 0.019784132018685341,
            "z": -0.38575905561447144
        }
    }

    payload_json = json.dumps(payload_dict)
    # print(payload_json)
    exif_dict = piexif.load(filepath)
    exif_dict['0th'][piexif.ImageIFD.ImageDescription] = payload_json.encode('utf-8')
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, filepath)
    # pprint.pprint(exif_dict)
    return True

#
#   Main
#
if __name__ == "__main__":
    print ("*** Add Mapillary EXIF ImageDescription ***")
    ordnerpfad = sys.argv[1]
    if not(os.path.isdir(ordnerpfad)):
        print("No valid directory given as parameter.")
        exit(1)
    # Loop over JPG files
    for subdirz, dirz, filez in os.walk(ordnerpfad):
        if len(filez) > 0:
            print("\nAdding ImageDescription: ", subdirz)
            for f in tqdm(filez):
                file_path = subdirz + os.sep + f
                if file_path.lower().endswith('.jpg'):
                    success = add_mapillary_tags(file_path)
