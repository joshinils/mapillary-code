#!/usr/bin/env python3

import argparse
import logging
import os
import sys
import time
from datetime import datetime

import tqdm

from addmaptags3 import process_image_tags
from jpegoptimizer3 import optimize_folder
from tinyuploader3 import upload_folder

# https://stackoverflow.com/a/38739634/10314791


class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""Optimize images, process image tags and upload images from IMAGES_PATH as image sequence(s) to mapillary.com.\n
    If you do not process the tags, the images may not get recognized, or get put into one sequence regardless of the folder structure.\n
    If the optimize flag is set, images may get deleted""",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--images_path', type=str,
                        default=r"D:\Mapillary\DCIM", help='path to images')
    parser.add_argument(
        '-n', '--dry_run', help='dry run, do not actually change any imagery, instead sleep for a very short while', action="store_true")
    parser.add_argument('-o', '--optimize_images',
                        help='do not optimize jpeg images', action="store_false")
    parser.add_argument('-p', '--process_tags',
                        help='do not process the image tags', action="store_false")
    parser.add_argument('-u', '--upload_images',
                        help='do not upload the images', action="store_false")
    parser.add_argument('-l', '--log_level',
                        help="""set the wanted logging verbosity,
                        0: DEBUG,
                        1: INFO,
                        2: WARNING,
                        3: ERROR,
                        4: FATAL""", default=1, type=int)

    # parse arguments
    args = parser.parse_args()
    images_path = args.images_path
    dry_run = args.dry_run
    optimize_images = args.optimize_images
    process_tags = args.process_tags
    upload_images = args.upload_images
    log_level = args.log_level

    # set up logging
    log_path = os.path.dirname(os.path.realpath(
        sys.argv[0])) + os.sep + "logs" + os.sep
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    if log_level <= 0:
        log_level = logging.DEBUG
    elif log_level == 1:
        log_level = logging.INFO
    elif log_level == 2:
        log_level = logging.WARNING
    elif log_level == 3:
        log_level = logging.ERROR
    elif log_level >= 4:
        log_level = logging.FATAL

    logging.basicConfig(filename=log_path + "mapillary_main_" + datetime.now().strftime("%Y-%m-%dT%H%M%S") +
                         ".log", level=log_level, format='%(levelname)-7s %(asctime)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    log = logging.getLogger(__name__)
    log.addHandler(TqdmLoggingHandler())

    log.debug("cwd: " + os.getcwd())

    log.debug("images_path " + str(images_path))
    log.debug("dry_run " + str(dry_run))
    log.debug("optimize_images " + str(optimize_images))
    log.debug("process_tags " + str(process_tags))
    log.debug("upload_images " + str(upload_images))


    # for i in tqdm.tqdm(range(100)):
    #     time.sleep(1)
    #     log.info(i)

    # do the main work
    if optimize_images:
        optimize_folder(images_path, dry_run, log)
    else:
        log.info(
            "not optimizing the images, as specified by commandline argument.")

    if process_tags:
        success = process_image_tags(images_path, dry_run, log)
        if not success:
            log.info("Processing of image tags failed, not continuing!")
            exit(1)
    else:
        log.info(
            "not processing the image tags, as specified by commandline argument.")

    if upload_images:
        upload_folder(images_path, dry_run, log)
    else:
        log.info(
            "not uploading the images, as specified by commandline argument.")
