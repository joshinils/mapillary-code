import json
import logging
import os
import pprint
import sys
import time

import requests
import tqdm


def upload_image(session, filepath):
    filename = os.path.basename(filepath)
    fields = session['fields'].copy()
    fields['key'] = session['key_prefix'] + filename
    with open(filepath, 'rb') as f:
        r = requests.post(session['url'], data=fields,
                          files={'file': (filename, f)})
    r.raise_for_status()


def create_session(subdir, access_token, client_id, log):
    data = {
        'type': 'images/sequence'
    }
    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json"
    }
    r = requests.post('https://a.mapillary.com/v3/me/uploads?client_id=' +
                      client_id, data=json.dumps(data), headers=headers)
    session = r.json()
    # pprint(session)
    log.info("Session open: " + session['key'])
    f = open(subdir + os.sep + "session.json", "w")
    f.write(json.dumps(session, sort_keys=True, indent=4))
    f.close()
    return session


def publish_session(session, access_token, client_id, log):
    key = session['key']
    headers = {
        "Authorization": "Bearer " + access_token
    }
    r = requests.put("https://a.mapillary.com/v3/me/uploads/" +
                     key + "/closed?client_id=" + client_id, headers=headers)
    log.info("*** Session published: " + session['key'])
    log.info(pprint.pformat(r))
    return


def delete_session(access_token, client_id, log):
    headers = {
        "Authorization": "Bearer " + access_token
    }
    r = requests.get(
        "https://a.mapillary.com/v3/me/uploads?client_id=" + client_id, headers=headers)
    sessions = r.json()
    for session in sessions:
        log.info("Delete Session:", session['key'])
        r = requests.delete("https://a.mapillary.com/v3/uploads/" +
                            session['key'] + "?client_id=" + client_id, headers=headers)
        r.raise_for_status()


def image_files(files):
    return [f for f in files if f.lower().endswith('.jpg')
            or f.lower().endswith('.jpeg')]


def upload_folder(folder_path, dry_run, log):
    if dry_run:
        log.warning(
            "*** DRY RUN, NOT ACTUALLY UPLOADING ANY IMAGERY, THE FOLLOWING IS SAMPLE OUTPUT")

    client_id = 'd0FVV29VMDR6SUVrcV94cTdabHBoZzoxZjc2MTE1Mzc1YjMxNzhi'
    log.info("   *** Read access token")
    with open(os.path.dirname(os.path.realpath(sys.argv[0])) + os.sep + "accesstoken3.conf", "r") as image_name:
        access_token = image_name.read()

    if not(os.path.isdir(folder_path)):
        log.warning("No valid directory given for upload as parameter.")
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
    total_pbar = tqdm.tqdm(total=total_images)
    if total_image_dirs > 1:
        dirs_pbar = tqdm.tqdm(total=total_image_dirs)
    else:
        dirs_pbar = None

    for path, _, files in os.walk(folder_path):
        if len(files) > 0:
            log.info("   *** Uploading directory: " + path)
            if not dry_run:
                session = create_session(path, access_token, client_id, log)
            for image_name in image_files(files):
                absolute_filepath = path + os.sep + image_name
                if not dry_run:
                    upload_image(session, absolute_filepath)
                else:
                    time.sleep(1/total_images)
                total_pbar.update()
            if not dry_run:
                publish_session(session, access_token, client_id, log)
            else:
                time.sleep(1)
            if dirs_pbar:
                dirs_pbar.update()
    total_pbar.close()
    if dirs_pbar:
        dirs_pbar.close()


#
#   Main
#
if __name__ == "__main__":
    logging.info("*** Mapillary Tiny Uploader ***")
    ordnerpfad = sys.argv[1]
    if not(os.path.isdir(ordnerpfad)):
        logging.info("No valid directory given as parameter.")
        exit(1)
    upload_folder(ordnerpfad, False, log=logging.getLogger(__name__))
