#
#   file: jpegoptimizer3.py
#
#   coder: geomoenk@googlemail.com
#
#   purpose: optimize all JPG files with EXIF headers from a directory
#            to 75% quality using OpenCV and Pillow before uploading
#
#   warning: deletes all broken pictures!
#

import logging
import os
import pprint
import sys
import time

from PIL import Image, ImageOps
from tqdm import tqdm


def optimize_file(file_path, log):
    image_org = Image.open(file_path)
    try:
        exif_data = image_org.info['exif']
        log.debug("exif_data: " + pprint.pformat(exif_data))
        image_rgb = ImageOps.autocontrast(image_org)
        image_rgb.save(file_path, optimize=True, quality=75, exif=exif_data)
    except Exception as error:
        log.error(error)
        image_org.close()
        return False
    return True


def image_files(files):
    return [f for f in files if f.lower().endswith('.jpg')
            or f.lower().endswith('.jpeg')]


def optimize_folder(folder_path, dry_run, log):
    if dry_run:
        log.warning(
            "*** DRY RUN, NOT ACTUALLY OPTIMIZING ANY IMAGERY, THE FOLLOWING IS SAMPLE OUTPUT")
    log.info("   *** JPEG optimizer ***")
    if not(os.path.isdir(folder_path)):
        log.warning("No valid directory given as parameter.")
        exit(1)

    # compute totals for progress bar
    total_images = 0
    total_image_dirs = 0
    for path, _, files in os.walk(folder_path):
        new_images = len(image_files(files))
        total_images += new_images
        if new_images > 0:
            total_image_dirs += 1

    # initialize progress bars
    total_pbar = tqdm(total=total_images, dynamic_ncols=True)
    if total_image_dirs > 1:
        dirs_pbar = tqdm(total=total_image_dirs, dynamic_ncols=True)
    else:
        dirs_pbar = None

    # Loop over JPG files
    for path, _, files in os.walk(folder_path):
        if len(files) > 0:
            log.info("   *** Optimizing: " + path)
            for image_name in image_files(files):
                absolute_filepath = path + os.sep + image_name
                if not dry_run:
                    success = optimize_file(absolute_filepath, log)
                    if not success:
                        log.info("removing image:", absolute_filepath)
                        os.remove(absolute_filepath)
                else:
                    time.sleep(1/total_images)
                total_pbar.update()
            if dirs_pbar:
                dirs_pbar.update()
    total_pbar.close()
    if dirs_pbar:
        dirs_pbar.close()


#
#   Main
#
if __name__ == "__main__":
    optimize_folder(sys.argv[1], False, log=logging.getLogger(__name__))
