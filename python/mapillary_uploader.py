#!/usr/bin/python

#
#   file:       mapillary_uploader.py
#
#   coder:      moenkemt@geo.hu-berlin.de
#
#   purpose:    upload all pictures directly from GPS enabled digital camera to mapillary
#
#   credits:    modified original script of https://github.com/mapillary/mapillary_tools/tree/master/python
#

import sys
import os
from datetime import datetime
import urllib2, urllib
from Queue import Queue
import uuid
import exifread
import time

try:
    from upload import create_dirs, UploadThread, upload_file
except ImportError:
    print("To run this script you need upload.py in your PYTHONPATH or the same folder.")
    sys.exit()

MAPILLARY_USERNAME = "***"
MAPILLARY_PERMISSION_HASH = "***"
MAPILLARY_SIGNATURE_HASH = "***"

UPLOAD_PATH = "I:\\DCIM\\107_VIRB\\"

MAPILLARY_UPLOAD_URL = "https://s3-eu-west-1.amazonaws.com/mapillary.uploads.manual.images"
NUMBER_THREADS = 4
MOVE_FILES = False


def upload_done_file(params):
    print("Upload a DONE file to tell the backend that the sequence is all uploaded and ready to submit.")
    if not os.path.exists('DONE'):
        open("DONE", 'a').close()
    # upload
    upload_file("DONE", **params)
    # remove
    if not MOVE_FILES:
        os.remove("DONE")


def verify_exif(filename):
    # required tags in IFD name convention
    required_exif = [ ["GPS GPSLongitude", "EXIF GPS GPSLongitude"],
                      ["GPS GPSLatitude", "EXIF GPS GPSLatitude"],
                      ["EXIF DateTimeOriginal", "EXIF DateTimeDigitized", "Image DateTime", "GPS GPSDate", "EXIF GPS GPSDate"],
                      ["Image Orientation"]]
    description_tag = "Image ImageDescription"
    with open(filename, 'rb') as f:
        tags = exifread.process_file(f)
    # make sure no Mapillary tags
    if description_tag in tags:
        if "MAPSequenceUUID" in tags[description_tag].values:
            print("File contains Mapillary EXIF tags, use upload.py instead.")
            return False
    # make sure all required tags are there
    for rexif in required_exif:
        vflag = False
        for subrexif in rexif:
            if subrexif in tags:
                vflag = True
        if not vflag:
            print("Missing required EXIF tag: {0}".format(rexif[0]))
            return False
    return True


# old upload_with_auth.py in as fucntion
def upload_sequence(path):
    # if no success/failed folders, create them
    create_dirs()
    if path.lower().endswith(".jpg"):
        # single file
        file_list = [path]
    else:
        # folder(s)
        file_list = []
        for root, sub_folders, files in os.walk(path):
            file_list += [os.path.join(root, filename) for filename in files if filename.lower().endswith(".jpg")]
    # generate a sequence UUID
    sequence_id = uuid.uuid4()
    # S3 bucket
    s3_bucket = MAPILLARY_USERNAME+"/"+str(sequence_id)+"/"
    print("Uploading sequence {0}.".format(sequence_id))
    # set upload parameters
    params = {"url": MAPILLARY_UPLOAD_URL, "key": s3_bucket,
            "permission": MAPILLARY_PERMISSION_HASH, "signature": MAPILLARY_SIGNATURE_HASH,
            "move_files": MOVE_FILES}
    # create upload queue with all files
    q = Queue()
    for filepath in file_list:
        if verify_exif(filepath):
            q.put(filepath)
        else:
            print("Skipping: {0}".format(filepath))
    # create uploader threads with permission parameters
    uploaders = [UploadThread(q, params) for i in range(NUMBER_THREADS)]
    # start uploaders as daemon threads that can be stopped (ctrl-c)
    try:
        for uploader in uploaders:
            uploader.daemon = True
            uploader.start()
        for uploader in uploaders:
            uploaders[i].join(1)
        while q.unfinished_tasks:
            time.sleep(1)
        q.join()
    except (KeyboardInterrupt, SystemExit):
        print("\nBREAK: Stopping upload.")
        sys.exit()
    upload_done_file(params)
    print("Done uploading.")


def read_capture_time(filepath):
    # Use exifread to parse capture time from EXIF.
    time_tag = "EXIF DateTimeOriginal"
    with open(filepath, 'rb') as f:
        tags = exifread.process_file(f)
    # read and format capture time
    if time_tag in tags:
        capture_time = tags[time_tag].values
        capture_time = capture_time.replace(" ","_")
        capture_time = capture_time.replace(":","_")
    else:
        capture_time = 0
    # return as datetime object
    return datetime.strptime(capture_time, '%Y_%m_%d_%H_%M_%S')


def sort_file_list(file_list):
    capture_times = [read_capture_time(filepath) for filepath in file_list]
    sorted_times_files = zip(capture_times, file_list)
    sorted_times_files.sort()
    return zip(*sorted_times_files)


def move_groups(groups):
    print("Organizing into {0} groups.".format(len(groups)))
    for i,group in enumerate(groups):
        group_path = os.path.dirname(group[0])
        new_dir = os.path.join(group_path, str(i))
        if not os.path.exists(new_dir):
            os.mkdir(new_dir)
        for filepath in group:
            os.rename(filepath, os.path.join(new_dir, os.path.basename(filepath)))
        print("Moved {0} photos to {1}".format(len(group), new_dir))


def upload_all(groups):
    print("Uploading {0} sequences.".format(len(groups)))
    for i,group in enumerate(groups):
        group_path = os.path.dirname(group[0])
        new_dir = os.path.join(group_path, str(i))
        upload_sequence(new_dir)
        print("Uploaded photos from {0}".format(new_dir))


# from old time_split.py as main
if __name__ == '__main__':
    file_list = []
    for root, sub_folders, files in os.walk(UPLOAD_PATH):
        file_list += [os.path.join(root, filename) for filename in files if filename.lower().endswith(".jpg")]
    # sort based on EXIF capture time
    capture_times, file_list = sort_file_list(file_list)
    # diff in capture time
    capture_deltas = [t2-t1 for t1,t2 in zip(capture_times, capture_times[1:])]
    # assume cutoff is 5x median time delta
    median = sorted(capture_deltas)[len(capture_deltas)//2]
    cutoff_time = 5*median.total_seconds()
    # extract groups by cutting using cutoff time
    groups = []
    group = [file_list[0]]
    for i,filepath in enumerate(file_list[1:]):
        if capture_deltas[i].total_seconds() > cutoff_time:
            # delta too big, save current group, start new
            groups.append(group)
            group = [filepath]
        else:
            group.append(filepath)
    groups.append(group)
    # move groups to subfolders
    move_groups(groups)
    # and upload all groups
    upload_all(groups)
    # and done.
    print("Done uploading photos.")

