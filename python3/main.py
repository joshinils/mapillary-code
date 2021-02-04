#!/usr/bin/env python3

import argparse

from addmaptags3 import process_image_tags
from jpegoptimizer3 import optimize_folder
from tinyuploader3 import upload_folder

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""Optimize images, process image tags and upload images from IMAGES_PATH as image sequence(s) to mapillary.com.
    If you do not process the tags, the images may not get recognized, or get put into one sequence regardless of the folder structure.
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

    args = parser.parse_args()
    images_path = args.images_path
    dry_run = args.dry_run
    optimize_images = args.optimize_images
    process_tags = args.process_tags
    upload_images = args.upload_images

    if optimize_images:
        optimize_folder(images_path, dry_run)
    else:
        print("not optimizing the images, as specified by commandline argument.")

    if process_tags:
        success = process_image_tags(images_path, dry_run)
        if not success:
            print("Processing of image tags failed, not continuing!")
            exit(1)
    else:
        print("not processing the image tags, as specified by commandline argument.")

    if upload_images:
        upload_folder(images_path, dry_run)
    else:
        print("not uploading the images, as specified by commandline argument.")
