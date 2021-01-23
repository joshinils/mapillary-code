#
#   file: roadsplit3.py
#
#   coder: geomoenk@googlemail.com
#
#   purpose: sorts all JPG files with EXIF headers from a directory
#           to new directories according to the street name in the
#           OSM planet file in a PostGIS database (WGS84 lat/lon).
#           this gives one sequence per street in Mapillary upload.
#

import os
import psycopg2
import slugify
import exifread
import tqdm


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
        datetime_text = tags.get('EXIF DateTimeOriginal')
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
        lat_text = str(latitude_ref.values) + str(convert_to_degress(latitude))
        lon_text = str(longitude_ref.values) + str(convert_to_degress(longitude))
        return lat_value, lon_value, lat_text, lon_text, str(datetime_text)


# get coords from file, create target dir and move file to it
def create_and_move_to_target(filepath):
    gps = getGPS(filepath)
    if gps != {}:
        lat = gps[0]
        lon = gps[1]
        sql = """
        SELECT a.name, ST_Distance(CAST(ST_SetSRID( ST_Point( """ + str(lon) + """, """ + str(lat) + """), 4326) AS geography), a.way) as d
        from planet_osm_line as a 
        where a.name != '' and a.highway != ''
        order by d asc
        limit 1;
        """
        cur = conn.cursor()
        cur.execute(sql)
        row = cur.fetchone()
        row = "OSM_" + slugify.slugify(row[0])
        # print(row)
        target_dir = target_path + row + os.sep
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir)
        target_file=target_dir + os.path.basename(os.path.dirname(filepath)) + "_" + os.path.basename(filepath)
        # print (target_file)
        os.rename(filepath,target_file)


# main
source_path = "D:\\Mapillary\\DCIM\\"
target_path = "D:\\Mapillary\\DCIM\\"
conn = psycopg2.connect("dbname='gis' user='postgres' host='localhost' password='pgadmin'")
print("*** EXIF-GPS to OSM-street-name sorter started")
for subdir, dirz, filez in os.walk(source_path):
    print("\nSorting:", subdir)
    for file in tqdm.tqdm(filez):
        file_path = subdir + os.sep + file
        if (".jpg" in file_path.lower()) and not ("OSM_" in file_path):
            create_and_move_to_target(file_path)

