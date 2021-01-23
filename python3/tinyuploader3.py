import os
import sys
import json
import requests
import piexif
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

#
#   Main
#
client_id = 'd0FVV29VMDR6SUVrcV94cTdabHBoZzoxZjc2MTE1Mzc1YjMxNzhi'
print ("*** Read access token")
f = open("accesstoken3.conf", "r")
access_token = f.read()
f.close()

try:
    ordnerpfad = sys.argv[1]
except:
    ordnerpfad = r"D:\Mapillary\DCIM"
if not(os.path.isdir(ordnerpfad)):
    print("No valid directory given for upload as parameter.")
    exit(1)
for subdirz, dirz, filez in os.walk(ordnerpfad):
    print("\n*** Upload directory:", subdirz)
    session = create_session(subdirz)
    for f in tqdm(filez):
        filepath = subdirz + os.sep + f
        if filepath.lower().endswith('.jpg'):
            # print(filepath)
            add_mapillary_tags(filepath)
            upload_imagery(session, filepath)
    publish_session(session)

