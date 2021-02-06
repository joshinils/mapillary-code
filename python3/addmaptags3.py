import ast
import json
import logging
import os
import pprint
import subprocess
import sys
import time

import piexif
from tqdm import tqdm

from exifpil3 import PILExifReader


def add_mapillary_tags(filepath, log):
    exif_dict = piexif.load(filepath)
    log.debug("before?: " + pprint.pformat(exif_dict))

    exif_reader = PILExifReader(filepath)
    log.debug("exif log:" + exif_reader.get_exif_log())

    exif_image_description = exif_reader.get_exif_tag("ImageDescription")
    try:
        exif_image_description = ast.literal_eval(exif_image_description)
    except:
        pass

    xmp_description = ast.literal_eval(
        exif_reader.get_XMP_description() or "{}")
    # pprint.pprint(xmp_description)

    #exif_reader.remove_XMP_description()

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

    if type(exif_image_description) is dict:
        for key, value in wanted_description_tags.items():
            if key not in payload_dict and key in exif_image_description:
                if type(wanted_description_tags[key]) is dict:
                    payload_dict[key] = {}
                    for key2, value2 in wanted_description_tags[key].items():
                        if key2 not in payload_dict[key] and key2 in exif_image_description[key]:
                            payload_dict[key][key2] = exif_image_description[key][key2]
                else:
                    payload_dict[key] = exif_image_description[key]

    payload_json = json.dumps(payload_dict)
    # log.info(payload_json)
    exif_dict = piexif.load(filepath)
    log.debug(pprint.pformat(exif_dict))
    exif_dict['0th'][piexif.ImageIFD.ImageDescription] = payload_json.encode(
        'utf-8')
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, filepath)
    # pprint.pprint(exif_dict)
    return True


def image_files(files):
    return [f for f in files if f.lower().endswith('.jpg')
            or f.lower().endswith('.jpeg')]


def process_image_tags(folder_path, dry_run, log) -> bool:
    """processes image tags like exif, XMP and adds the necessary and optional tags for mapillary if possible
       returns success
    """
    if dry_run:
        log.warning("*** DRY RUN, NOT ACTUALLY PROCESSING ANY IMAGE TAGS, THE FOLLOWING IS SAMPLE OUTPUT")
    log.info("   *** Add Mapillary EXIF ImageDescription ***")
    if not(os.path.isdir(folder_path)):
        log.warning("No valid directory given as parameter.")
        return False

    # compute totals for progress bar
    total_images = 0
    total_image_dirs = 0
    for path, _, files in os.walk(folder_path):
        new_images = len(image_files(files))
        total_images += new_images
        if new_images > 0:
            total_image_dirs += 1

    # initialize progress bars
    total_pbar = tqdm(total=total_images)
    if total_image_dirs > 1:
        dirs_pbar = tqdm(total=total_image_dirs)
    else:
        dirs_pbar = None

    # Loop over JPG files
    for path, _, files in os.walk(folder_path):
        if len(files) > 0:
            log.info("   *** Adding ImageDescription: " + path)
            for file_name in image_files(files):
                absolute_file_path = path + os.sep + file_name
                if not dry_run:
                    add_mapillary_tags(absolute_file_path, log)
                else:
                    time.sleep(1/total_images)
                total_pbar.update()
            if dirs_pbar:
                dirs_pbar.update()
    total_pbar.close()
    if dirs_pbar:
        dirs_pbar.close()

    return True


#
#   Main
#
if __name__ == "__main__":
    process_image_tags(sys.argv[1], log=logging.getLogger(__name__))
