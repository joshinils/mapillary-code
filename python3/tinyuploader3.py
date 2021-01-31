import os
import sys
import json
import requests
import piexif
import argparse
import time
from tqdm import tqdm
from pprint import pprint
from exifpil3 import PILExifReader


def upload_imagery(session, filepath):
    filename = os.path.basename(filepath)
    fields = session['fields'].copy()
    fields['key'] = session['key_prefix'] + filename
    with open(filepath, 'rb') as f:
        r = requests.post(session['url'], data=fields, files={'file': (filename, f)})
    r.raise_for_status()


def create_session(subdir):
    data = {
        'type': 'images/sequence'
    }
    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json"
    }
    r = requests.post('https://a.mapillary.com/v3/me/uploads?client_id=' + client_id, data=json.dumps(data), headers=headers)
    session = r.json()
    # pprint(session)
    print("Session open:", session['key'])
    f = open(subdir + os.sep + "session.json", "w")
    f.write(json.dumps(session, sort_keys=True, indent=4))
    f.close()
    return session


def publish_session(session):
    key = session['key']
    headers = {
        "Authorization": "Bearer " + access_token
    }
    r = requests.put("https://a.mapillary.com/v3/me/uploads/" +key + "/closed?client_id=" + client_id, headers=headers)
    print("*** Session published:", session['key'])
    pprint(r)
    return


def delete_session():
    headers = {
        "Authorization": "Bearer " + access_token
    }
    r = requests.get("https://a.mapillary.com/v3/me/uploads?client_id=" + client_id, headers=headers)
    sessions = r.json()
    for session in sessions:
        print("Delete Session:", session['key'])
        r = requests.delete("https://a.mapillary.com/v3/uploads/" + session['key'] + "?client_id=" + client_id, headers=headers)
        r.raise_for_status()


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

def image_files(files):
    return [f for f in files if    f.lower().endswith('.jpg')
                                or f.lower().endswith('.jpeg')
                                or f.lower().endswith('.png')]

#
#   Main
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'uploads images from IMAGES_PATH as an image sequence to mapillary',
                                     formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--images_path', type = str, default = r"D:\Mapillary\DCIM", help = 'path to images')
    parser.add_argument('-n', '--dry_run', help = 'dry run, do not actually upload imagery', action = "store_true")
    parser.add_argument('-m', '--no_mapillary_tags', help = 'dry run, do not actually upload imagery', action = "store_false")
    args = parser.parse_args()
    images_path = args.images_path
    dry_run = args.dry_run
    if dry_run:
        print("DRY RUN, NOT ACTUALLY UPLOADING ANY IMAGERY, THE FOLLOWING IS SAMPLE OUTPUT")
    no_mapillary_data = args.no_mapillary_tags


    client_id = 'd0FVV29VMDR6SUVrcV94cTdabHBoZzoxZjc2MTE1Mzc1YjMxNzhi'
    print ("*** Read access token")
    with open("accesstoken3.conf", "r") as image_name:
        access_token = image_name.read()

    if not(os.path.isdir(images_path)):
        print("No valid directory given for upload as parameter.")
        exit(1)

    total_files = 0
    total_dirs = 0
    for path, dirs, files in os.walk(images_path):
        total_files += len(image_files(files))
        if len(files) > 0:
            total_dirs += 1

    total_pbar = tqdm(total = total_files)
    if total_dirs > 1:
        dirs_pbar = tqdm(total = total_dirs)
    else:
        dirs_pbar = None

    for path, dirs, files in os.walk(images_path):
        tqdm.write("path " + path)
        tqdm.write("dirs +" + str(dirs))
        tqdm.write("files " + str(len(files)))
        tqdm.write("")
        if len(files) > 0:
            tqdm.write("*** Uploading directory: " + path)
            if not dry_run:
                session = create_session(path)
            for image_name in image_files(files):
                filepath = path + os.sep + image_name
                if not no_mapillary_data:
                    add_mapillary_tags(filepath)
                if not dry_run:
                    upload_imagery(session, filepath)
                else:
                    time.sleep(1/total_files)
                total_pbar.update()
            if not dry_run:
                publish_session(session)
            else:
                time.sleep(1)
            if dirs_pbar:
                dirs_pbar.update()
    total_pbar.close()
    if dirs_pbar:
        dirs_pbar.close()


