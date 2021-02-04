import os
import sys
import json
import piexif
from tqdm import tqdm
import pprint
from exifpil3 import PILExifReader
import ast


def add_mapillary_tags(filepath):
    exif_reader = PILExifReader(filepath)

    exif_image_description = ast.literal_eval(
        exif_reader.get_exif_tag("ImageDescription"))
    print("\nDEBUG: print exif_image_description")
    pprint.pprint(exif_image_description)
    print()
    exif_reader.remove_XMP_description()

    wanted_description_tags = {
        "MAPCompassHeading":
        {
            "TrueHeading": 0,
            "MagneticHeading": 0,
            "AccuracyDegrees": 0
        },
        "MAPGpsTime": "",
        "MAPVersionString": "",
        "MAPLatitude": 0,
        "MAPCaptureTime": "",
        "MAPGPSSpeed": 0,
        "MAPDeviceModel": "",
        "MAPAppNameString": "",
        "MAPAltitude": 0,
        "MAPLocalTimeZone": "",
        "MAPGPSAccuracyMeters": 0,
        "MAPAtanAngle": 0,
        "MAPLongitude": 0,
        "MAPDeviceMake": "",
        "MAPAccelerometerVector":
        {
            "x": 0,
            "y": 0,
            "z": 0
        }
    }

    # setup payload_dict with initial data from exif:
    payload_dict = {}
    datetime = exif_reader.read_capture_time()
    if datetime != None:
        str_timestamp = datetime.strftime("%Y_%m_%d_%H_%M_%S_%f")[:-3]
        payload_dict["MAPCaptureTime"] = str_timestamp

    # set latitude and longitude
    try:
        lat, lon = exif_reader.get_lat_lon()
        if lat != None and lon != None:
            payload_dict["MAPLongitude"] = lon
            payload_dict["MAPLatitude"] = lat
    except:
        pass

    # set heading
    heading = exif_reader.get_rotation()
    if heading is not None:
        payload_dict["MAPCompassHeading"] = {}
        payload_dict["MAPCompassHeading"]["TrueHeading"] = heading

    print("\nDEBUG: print key, value of comment:")
    for key, value in wanted_description_tags.items():
        if key not in payload_dict:
            if type(wanted_description_tags[key]) is dict:
                payload_dict[key] = {}
                for key2, value2 in wanted_description_tags[key].items():
                    if key2 not in payload_dict[key]:
                        payload_dict[key][key2] = exif_image_description[key][key2]
                        print(key2, payload_dict[key][key2])
            else:
                payload_dict[key] = exif_image_description[key]
                print(key, payload_dict[key])
        else:
            print("not overwriting: ",
                  payload_dict[key], " with ", exif_image_description[key])
    print()

    payload_json = json.dumps(payload_dict)
    # print(payload_json)
    exif_dict = piexif.load(filepath)
    exif_dict['0th'][piexif.ImageIFD.ImageDescription] = payload_json.encode(
        'utf-8')
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, filepath)
    # pprint.pprint(exif_dict)
    return True


def image_files(files):
    return [f for f in files if f.lower().endswith('.jpg')
            or f.lower().endswith('.jpeg')]


def process_image_tags(folder_path) -> bool:
    """processes image tags like exif, XMP and adds the necessary and optional tags for mapillary if possible
       returns success
    """
    print("*** Add Mapillary EXIF ImageDescription ***")
    if not(os.path.isdir(folder_path)):
        print("No valid directory given as parameter.")
        return False
    # Loop over JPG files
    for path, dirs, files in os.walk(folder_path):
        if len(files) > 0:
            print("\nAdding ImageDescription: ", path)
            for file_name in tqdm(image_files(files)):
                absolute_file_path = path + os.sep + file_name
                add_mapillary_tags(absolute_file_path)

    return True


#
#   Main
#
if __name__ == "__main__":
    process_image_tags(sys.argv[1])
