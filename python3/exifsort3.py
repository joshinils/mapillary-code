#
#   file: exifsort3.py
#
#   coder: geomoenk@googlemail.com
#
#   purpose: sorts all JPG files with EXIF headers from a directory
#           to new directories according to the OpenStreetMap tiles
#           schema with a given zoom level before uploading.
#           this makes it easier to find pictures from a given area
#           after capturing a big load pictures on a trip.
#

import os
import math
import exifread

source_path="D:\\Mapillary\\DCIM\\"
target_path="D:\\Mapillary\\DCIM\\"
zoom_level=12


# coovert to decimal degrees
def convert_to_degress(value):
    d = float(value.values[0].num) / float(value.values[0].den)
    m = float(value.values[1].num) / float(value.values[1].den)
    s = float(value.values[2].num) / float(value.values[2].den)
    return d + (m / 60.0) + (s / 3600.0)


# get coords from picture
def getGPS(filepath):
    with open(filepath, 'rb') as f:
        tags = exifread.process_file(f)
        latitude = tags.get('GPS GPSLatitude')
        latitude_ref = tags.get('GPS GPSLatitudeRef')
        longitude = tags.get('GPS GPSLongitude')
        longitude_ref = tags.get('GPS GPSLongitudeRef')
        if latitude:
            lat_value = convert_to_degress(latitude)
            if latitude_ref.values != 'N':
                lat_value = -lat_value
        else:
            return {}
        if longitude:
            lon_value = convert_to_degress(longitude)
            if longitude_ref.values != 'E':
                lon_value = -lon_value
        else:
            return {}
        lat_text=str(latitude_ref.values)+str(convert_to_degress(latitude))
        lon_text=str(longitude_ref.values)+str(convert_to_degress(longitude))
        return lat_value, lon_value, lat_text, lon_text


# make a directory name accoding to OSM tile in given zoom level
def get_tile_directory_name(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    tile = r"OSM_{0}_{1}_{2}"
    return tile.format(zoom, xtile, ytile)


# get coords from file, create target dir and move file to it
def create_and_move_to_target(file_path,zoom_level):
    gps = getGPS(file_path)
    if gps!={}:
        target_dir = target_path + get_tile_directory_name(gps[0], gps[1], zoom_level) + os.sep
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir)
        target_file=target_dir + os.path.basename(os.path.dirname(file_path)) + "_" + os.path.basename(file_path)
        print (target_file)
        os.rename(file_path,target_file)



# main
for subdir, dirs, files in os.walk(source_path):
    for file in files:
        file_path = subdir + os.sep + file
        if ".jpg" in file_path.lower() and not "OSM_" in file_path:
            create_and_move_to_target(file_path,zoom_level)

