#
#   file: sequencesplit3.py
#
#   coder: moenk
#
# Script for organizing images into sequence groups based on a cutoff distance and a cutoff time.
# This is useful as a step before uploading lots of photos with the manual uploader.
# If you capture the photos with pauses during your trip, it generally leads to
# photos with large distance gaps. Running this script with a 500-meter cutoff distance
# will produce sequences that avoid any gaps larger than 500 meters.
#
# Original Python 2.7 version:
# https://github.com/mapillary/mapillary_tools/blob/feature-no-pyexiv2/python/sequence_split.py
#


import os
import sys
import datetime
import math
import exifread
import tqdm


cutoff_time = 60
cutoff_distance = 161
MAXIMUM_SEQUENCE_LENGTH = 500


def eval_frac(value):
    return float(value.num) / float(value.den)


def exif_gps_fields():
    '''
    GPS fields in EXIF
    '''
    return [  ["GPS GPSLongitude", "EXIF GPS GPSLongitude"],
              ["GPS GPSLatitude", "EXIF GPS GPSLatitude"] ]


def exif_datetime_fields():
    '''
    Date time fields in EXIF
    '''
    return [["EXIF DateTimeOriginal",
             "Image DateTimeOriginal",
             "EXIF DateTimeDigitized",
             "Image DateTimeDigitized",
             "EXIF DateTime"
             "Image DateTime",
             "GPS GPSDate",
             "EXIF GPS GPSDate",
             "EXIF DateTimeModified"]]


def gps_to_decimal(values, reference):
    sign = 1 if reference in 'NE' else -1
    degrees = eval_frac(values[0])
    minutes = eval_frac(values[1])
    seconds = eval_frac(values[2])
    return sign * (degrees + minutes / 60 + seconds / 3600)


def get_float_tag(tags, key):
    if key in tags:
        return float(tags[key].values[0])
    else:
        return None


def get_frac_tag(tags, key):
    if key in tags:
        return eval_frac(tags[key].values[0])
    else:
        return None


def extract_exif_from_file(fileobj):
    if isinstance(fileobj, str):
        with open(fileobj) as f:
            exif_data = EXIF(f)
    else:
        exif_data = EXIF(fileobj)

    d = exif_data.extract_exif()
    return d

def required_fields():
    return exif_gps_fields() + exif_datetime_fields()


def verify_exif(filename):
    '''
    Check that image file has the required EXIF fields.
    Incompatible files will be ignored server side.
    '''
    # required tags in IFD name convention
    required_exif = required_fields()
    exif = EXIF(filename)
    required_exif_exist = exif.fields_exist(required_exif)
    return required_exif_exist


def verify_mapillary_tag(filename):
    '''
    Check that image file has the required Mapillary tag
    '''
    return EXIF(filename).mapillary_tag_exists()


def is_image(filename):
    return filename.lower().endswith(('jpg', 'jpeg', 'png', 'tif', 'tiff', 'pgm', 'pnm', 'gif'))


class EXIF:
    '''
    EXIF class for reading exif from an image
    '''
    def __init__(self, filename, details=False):
        '''
        Initialize EXIF object with FILE as filename or fileobj
        '''
        self.filename = filename
        if type(filename) == str:
            with open(filename, 'rb') as fileobj:
                self.tags = exifread.process_file(fileobj, details=details)
        else:
            self.tags = exifread.process_file(filename, details=details)


    def _extract_alternative_fields(self, fields, default=None, field_type=float):
        '''
        Extract a value for a list of ordered fields.
        Return the value of the first existed field in the list
        '''
        for field in fields:
            if field in self.tags:
                if field_type is float:
                    value = eval_frac(self.tags[field].values[0])
                if field_type is str:
                    value = str(self.tags[field].values)
                if field_type is int:
                    value = int(self.tags[field].values[0])
                return value, field
        return default, None


    def exif_name(self):
        '''
        Name of file in the form {lat}_{lon}_{ca}_{datetime}_{filename}
        '''
        lon, lat = self.extract_lon_lat()
        ca = self.extract_direction()
        if ca is None: ca = 0
        ca = int(ca)
        date_time = self.extract_capture_time()
        date_time = date_time.strftime("%Y-%m-%d-%H-%M-%S-%f")
        date_time = date_time[:-3]
        filename = '{}_{}_{}_{}_{}'.format(lat, lon, ca, date_time, os.path.basename(self.filename))
        return filename


    def extract_altitude(self):
        '''
        Extract altitude
        '''
        fields = ['GPS GPSAltitude', 'EXIF GPS GPSAltitude']
        altitude, _ = self._extract_alternative_fields(fields)
        return altitude


    def extract_capture_time(self):
        '''
        Extract capture time from EXIF
        return a datetime object
        TODO: handle GPS DateTime
        '''
        time_string = exif_datetime_fields()[0]
        capture_time, time_field = self._extract_alternative_fields(time_string, 0, str)
        capture_time = capture_time.replace(" ", "_")
        capture_time = capture_time.replace(":", "_")
        capture_time = datetime.datetime.strptime(capture_time, '%Y_%m_%d_%H_%M_%S')
        sub_sec = self.extract_subsec()
        capture_time = capture_time + datetime.timedelta(seconds=float(sub_sec)/10**len(str(sub_sec)))
        if capture_time == 0:
            # try interpret the filename
            try:
                capture_time = datetime.datetime.strptime(os.path.basename(self.filename)[:-4]+'000', '%Y_%m_%d_%H_%M_%S_%f')
            except:
                pass
        return capture_time


    def extract_direction(self):
        '''
        Extract image direction (i.e. compass, heading, bearing)
        '''
        fields = ['GPS GPSImgDirection',
                  'EXIF GPS GPSImgDirection',
                  'GPS GPSTrack',
                  'EXIF GPS GPSTrack']
        direction, _ = self._extract_alternative_fields(fields)
        if direction is not None: direction = normalize_bearing(direction)
        return direction


    def extract_dop(self):
        '''
        Extract dilution of precision
        '''
        fields = ['GPS GPSDOP', 'EXIF GPS GPSDOP']
        dop, _ = self._extract_alternative_fields(fields)
        return dop


    def extract_geo(self):
        '''
        Extract geo-related information from exif
        '''
        altitude = self.extract_altitude()
        dop = self.extract_dop()
        lon, lat = self.extract_lon_lat()
        d = {}
        if lon is not None and lat is not None:
            d['latitude'] = lat
            d['longitude'] = lon
        if altitude is not None:
            d['altitude'] = altitude
        if dop is not None:
            d['dop'] = dop
        return d


    def extract_exif(self):
        '''
        Extract a list of exif infos
        '''
        width, height = self.extract_image_size()
        make, model = self.extract_make(), self.extract_model()
        orientation = self.extract_orientation()
        geo = self.extract_geo()
        capture = self.extract_capture_time()
        direction = self.extract_direction()
        d = {
                'width': width,
                'height': height,
                'orientation': orientation,
                'direction': direction,
                'make': make,
                'model': model,
                'capture_time': capture
            }
        d['gps'] = geo
        return d


    def extract_image_size(self):
        '''
        Extract image height and width
        '''
        width, _ = self._extract_alternative_fields(['Image ImageWidth', 'EXIF ExifImageWidth'], -1, int)
        height, _ = self._extract_alternative_fields(['Image ImageLength', 'EXIF ExifImageLength'], -1, int)
        return width, height


    def extract_image_description(self):
        '''
        Extract image description
        '''
        description, _ = self._extract_alternative_fields(['Image ImageDescription'], "{}", str)
        return description


    def extract_lon_lat(self):
        if 'GPS GPSLatitude' in self.tags and 'GPS GPSLatitude' in self.tags:
            lat = gps_to_decimal(self.tags['GPS GPSLatitude'].values,
                                 self.tags['GPS GPSLatitudeRef'].values)
            lon = gps_to_decimal(self.tags['GPS GPSLongitude'].values,
                                 self.tags['GPS GPSLongitudeRef'].values)
        elif 'EXIF GPS GPSLatitude' in self.tags and 'EXIF GPS GPSLatitude' in self.tags:
            lat = gps_to_decimal(self.tags['EXIF GPS GPSLatitude'].values,
                                 self.tags['EXIF GPS GPSLatitudeRef'].values)
            lon = gps_to_decimal(self.tags['EXIF GPS GPSLongitude'].values,
                                 self.tags['EXIF GPS GPSLongitudeRef'].values)
        else:
            lon, lat = None, None
        return lon, lat


    def extract_make(self):
        '''
        Extract camera make
        '''
        fields = ['EXIF LensMake', 'Image Make']
        make, _ = self._extract_alternative_fields(fields, default='none', field_type=str)
        return make


    def extract_model(self):
        '''
        Extract camera model
        '''
        fields = ['EXIF LensModel', 'Image Model']
        model, _ = self._extract_alternative_fields(fields, default='none', field_type=str)
        return model


    def extract_orientation(self):
        '''
        Extract image orientation
        '''
        fields = ['Image Orientation']
        orientation, _ = self._extract_alternative_fields(fields, default=1, field_type=int)
        return orientation


    def extract_subsec(self):
        '''
        Extract microseconds
        '''
        fields = ['Image SubSecTimeOriginal',
                  'EXIF SubSecTimeOriginal',
                  'Image SubSecTimeDigitized',
                  'EXIF SubSecTimeDigitized',
                  'Image SubSecTime',
                  'EXIF SubSecTime'
                 ]
        sub_sec, _ = self._extract_alternative_fields(fields, default=0, field_type=str)
        sub_sec = int(sub_sec)
        return sub_sec


    def fields_exist(self, fields):
        '''
        Check existence of a list fields in exif
        '''
        for rexif in fields:
            vflag = False
            for subrexif in rexif:
                if subrexif in self.tags:
                    vflag = True
            if not vflag:
                print(("Missing required EXIF tag: {0}".format(rexif[0])))
                return False
        return True


    def mapillary_tag_exists(self):
        '''
        Check existence of Mapillary tag
        '''
        description_tag = "Image ImageDescription"
        if description_tag in self.tags:
            if "MAPSequenceUUID" in self.tags[description_tag].values:
                return True
        return False


class Sequence(object):

    def __init__(self, filepath, skip_folders=[], skip_subfolders=False, check_exif=True):
        self.filepath = filepath
        self._skip_folders = skip_folders
        self._skip_subfolders = skip_subfolders
        self.file_list = self.get_file_list(filepath, check_exif)
        self.num_images = len(self.file_list)

    def _is_skip(self, filepath):
        '''
        Skip photos in specified folders
            - filepath/duplicates: it stores potential duplicate photos
                                   detected by method 'remove_duplicates'
            - filepath/success:    it stores photos that have been successfully
        '''
        _is_skip = False
        for folder in self._skip_folders:
            if folder in filepath:
                _is_skip = True
        if self._skip_subfolders and filepath != self.filepath:
            _is_skip = True
        return _is_skip

    def _read_capture_time(self, filename):
        '''
        Use EXIF class to parse capture time from EXIF.
        '''
        exif = EXIF(filename)
        return exif.extract_capture_time()

    def _read_lat_lon(self, filename):
        '''
        Use EXIF class to parse latitude and longitude from EXIF.
        '''
        exif = EXIF(filename)
        lon, lat = exif.extract_lon_lat()
        return lat, lon

    def _read_direction(self, filename):
        '''
        Use EXIF class to parse compass direction from EXIF.
        '''
        exif = EXIF(filename)
        direction = exif.extract_direction()
        return direction

    def get_file_list(self, filepath, check_exif=True):
        '''
        Get the list of JPEGs in the folder (nested folders)
        '''
        if filepath.lower().endswith(".jpg"):
            # single file
            file_list = [filepath]
        else:
            file_list = []
            for root, sub_folders, files in os.walk(self.filepath):
                image_files = [os.path.join(root, filename) for filename in files if (filename.lower().endswith(".jpg"))]
                if check_exif:
                    image_files = [f for f in image_files if verify_exif(f)]
                file_list += image_files
        return file_list

    def sort_file_list(self, file_list):
        '''
        Read capture times and sort files in time order.
        '''
        capture_times = [self._read_capture_time(filepath) for filepath in file_list]
        sorted_times_files = list(zip(capture_times, file_list))
        sorted_times_files.sort()
        return list(zip(*sorted_times_files))

    def move_groups(self, groups, sub_path=''):
        '''
        Move the files in the groups to new folders.
        '''
        for i, group in enumerate(groups):
            new_dir = os.path.join(self.filepath, sub_path, str(i))
            if not os.path.isdir(new_dir):
                os.makedirs(new_dir)
            for filepath in tqdm.tqdm(group):
                filename = os.path.basename(filepath)
                dirk = os.path.dirname(filepath).split(os.sep)[-1] + "_"
                os.rename(filepath, os.path.join(new_dir, dirk + filename))
            print(("Moved {0} photos to {1}".format(len(group), new_dir)))

    def set_skip_folders(self, folders):
        '''
        Set folders to skip when iterating through the path
        '''
        self._skip_folders = folders

    def set_file_list(self, file_list):
        '''
        Set file list for the sequence
        '''
        self.file_list = file_list

    def split(self, cutoff_distance=500., cutoff_time=None, max_sequence_length=MAXIMUM_SEQUENCE_LENGTH):
        '''
        Split photos into sequences in case of large distance gap or large time interval
        @params cutoff_distance: maximum distance gap in meters
        @params cutoff_time:     maximum time interval in seconds (if None, use 1.5 x median time interval in the sequence)
        '''
        file_list = self.file_list
        groups = []
        if len(file_list) >= 1:
            # sort based on EXIF capture time
            capture_times, file_list = self.sort_file_list(file_list)
            # diff in capture time
            capture_deltas = [t2-t1 for t1,t2 in zip(capture_times, capture_times[1:])]
            # read gps for ordered files
            latlons = [self._read_lat_lon(filepath) for filepath in file_list]
            # distance between consecutive images
            distances = [gps_distance(ll1, ll2) for ll1, ll2 in zip(latlons, latlons[1:])]
            # if cutoff time is given use that, else assume cutoff is 1.5x median time delta
            if cutoff_time is None:
                median = sorted(capture_deltas)[len(capture_deltas)//2]
                # if type(median) is not  int:
                #     median = median.total_seconds()
                cutoff_time = 1.5*median
            # extract groups by cutting using cutoff time
            group = [file_list[0]]
            cut = 0
            for i,filepath in enumerate(file_list[1:]):
                cut_time = capture_deltas[i].total_seconds() > cutoff_time
                cut_distance = distances[i] > cutoff_distance
                cut_sequence_length = len(group) > max_sequence_length
                if cut_time or cut_distance or cut_sequence_length:
                    cut += 1
                    # delta too big, save current group, start new
                    groups.append(group)
                    group = [filepath]
                    if cut_distance:
                        print('Cut {}: Delta in distance {} meters is too big at {}'.format(cut,distances[i], file_list[i+1]))
                    elif cut_time:
                        print('Cut {}: Delta in time {} seconds is too big at {}'.format(cut, capture_deltas[i].total_seconds(), file_list[i+1]))
                    elif cut_sequence_length:
                        print('Cut {}: Maximum sequence length {} reached at {}'.format(cut, max_sequence_length, file_list[i+1]))
                else:
                    group.append(filepath)
            groups.append(group)
            # move groups to subfolders
            self.move_groups(groups)
            print(("Done split photos in {} into {} sequences".format(self.filepath, len(groups))))
        return groups

    def interpolate_direction(self, offset=0):
        '''
        Interpolate bearing of photos in a sequence with an offset
        @author: mprins
        '''
        bearings = {}
        file_list = self.file_list
        num_file = len(file_list)
        if num_file>1:
            # sort based on EXIF capture time
            capture_times, file_list = self.sort_file_list(file_list)
            # read gps for ordered files
            latlons = [self._read_lat_lon(filepath) for filepath in file_list]
            if len(file_list)>1:
                # bearing between consecutive images
                bearings = [compute_bearing(ll1[0], ll1[1], ll2[0], ll2[1])
                                for ll1, ll2 in zip(latlons, latlons[1:])]
                bearings.append(bearings[-1])
                bearings = {file_list[i]: offset_bearing(b, offset) for i, b in enumerate(bearings)}
        elif num_file==1:
            #if there is only one file in the list, just write the direction 0 and offset
            bearings = {file_list[0]: offset_bearing(0.0, offset)}
        return bearings

    def remove_duplicates(self, min_distance=1e-5, min_angle=5):
        '''
        Detect duplidate photos in a folder
        @source:  a less general version of @simonmikkelsen's duplicate remover
        '''
        file_list = self.file_list
        # ordered list by time
        capture_times, file_list = self.sort_file_list(file_list)
        # read gps for ordered files
        latlons = [self._read_lat_lon(filepath) for filepath in file_list]
        # read bearing for ordered files
        bearings = [self._read_direction(filepath) for filepath in file_list]
        # interploated bearings
        interpolated_bearings = [compute_bearing(ll1[0], ll1[1], ll2[0], ll2[1])
                                for ll1, ll2 in zip(latlons, latlons[1:])]
        interpolated_bearings.append(bearings[-1])
        # use interploated bearings if bearing not available in EXIF
        for i, b in enumerate(bearings):
            bearings[i] = b if b is not None else interpolated_bearings[i]

        is_duplicate = False
        prev_unique = file_list[0]
        prev_latlon = latlons[0]
        prev_bearing = bearings[0]
        groups = []
        group = []
        for i, filename in enumerate(file_list[1:]):
            k = i+1
            distance = gps_distance(latlons[k], prev_latlon)
            if bearings[k] is not None and prev_bearing is not None:
                bearing_diff = diff_bearing(bearings[k], prev_bearing)
            else:
                # Not use bearing difference if no bearings are available
                bearing_diff = 360
            if distance < min_distance and bearing_diff < min_angle:
                is_duplicate = True
            else:
                prev_latlon = latlons[k]
                prev_bearing = bearings[k]
            if is_duplicate:
                group.append(filename)
            else:
                if group:
                    groups.append(group)
                group = []
            is_duplicate = False
        groups.append(group)
        # move to filepath/duplicates/group_id (TODO: uploader should skip the duplicate folder)
        self.move_groups(groups, 'duplicates')
        print(("Done remove duplicate photos in {} into {} groups".format(self.filepath, len(groups))))
        return groups


def ecef_from_lla(lat, lon, alt):
    '''
    Compute ECEF XYZ from latitude, longitude and altitude.
    All using the WGS94 model.
    Altitude is the distance to the WGS94 ellipsoid.
    Check results here http://www.oc.nps.edu/oc2902w/coord/llhxyz.htm
    '''
    WGS84_a = 6378137.0
    WGS84_b = 6356752.314245
    a2 = WGS84_a**2
    b2 = WGS84_b**2
    lat = math.radians(lat)
    lon = math.radians(lon)
    L = 1.0 / math.sqrt(a2 * math.cos(lat)**2 + b2 * math.sin(lat)**2)
    x = (a2 * L + alt) * math.cos(lat) * math.cos(lon)
    y = (a2 * L + alt) * math.cos(lat) * math.sin(lon)
    z = (b2 * L + alt) * math.sin(lat)
    return x, y, z


def gps_distance(latlon_1, latlon_2):
    '''
    Distance between two (lat,lon) pairs.
    >>> p1 = (42.1, -11.1)
    >>> p2 = (42.2, -11.3)
    >>> 19000 < gps_distance(p1, p2) < 20000
    True
    '''
    x1, y1, z1 = ecef_from_lla(latlon_1[0], latlon_1[1], 0.)
    x2, y2, z2 = ecef_from_lla(latlon_2[0], latlon_2[1], 0.)
    dis = math.sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)
    return dis

def dms_to_decimal(degrees, minutes, seconds, hemisphere):
    '''
    Convert from degrees, minutes, seconds to decimal degrees.
    @author: mprins
    '''
    dms = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
    if hemisphere in "WwSs":
        dms = -1 * dms
    return dms


def decimal_to_dms(value, loc):
    '''
    Convert decimal position to degrees, minutes, seconds
    '''
    if value < 0:
        loc_value = loc[0]
    elif value > 0:
        loc_value = loc[1]
    else:
        loc_value = ""
    abs_value = abs(value)
    deg =  int(abs_value)
    t1 = (abs_value-deg)*60
    mint = int(t1)
    sec = round((t1 - mint)* 60, 6)
    return (deg, mint, sec, loc_value)


def utc_to_localtime(utc_time):
    utc_offset_timedelta = datetime.datetime.utcnow() - datetime.datetime.now()
    return utc_time - utc_offset_timedelta


def compute_bearing(start_lat, start_lon, end_lat, end_lon):
    '''
    Get the compass bearing from start to end.
    Formula from
    http://www.movable-type.co.uk/scripts/latlong.html
    '''
    # make sure everything is in radians
    start_lat = math.radians(start_lat)
    start_lon = math.radians(start_lon)
    end_lat = math.radians(end_lat)
    end_lon = math.radians(end_lon)
    dLong = end_lon - start_lon
    dPhi = math.log(math.tan(end_lat/2.0+math.pi/4.0)/math.tan(start_lat/2.0+math.pi/4.0))
    if abs(dLong) > math.pi:
        if dLong > 0.0:
            dLong = -(2.0 * math.pi - dLong)
        else:
            dLong = (2.0 * math.pi + dLong)
    y = math.sin(dLong)*math.cos(end_lat)
    x = math.cos(start_lat)*math.sin(end_lat) - math.sin(start_lat)*math.cos(end_lat)*math.cos(dLong)
    bearing = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0
    return bearing


def diff_bearing(b1, b2):
    '''
    Compute difference between two bearings
    '''
    d = abs(b2-b1)
    d = 360-d if d>180 else d
    return d

def offset_bearing(bearing, offset):
    '''
    Add offset to bearing
    '''
    bearing = (bearing + offset + 360) % 360
    return bearing


def normalize_bearing(bearing):
    if bearing > 360:
        # fix negative value wrongly parsed in exifread
        # -360 degree -> 4294966935 when converting from hex
        bearing = bin(int(bearing))[2:]
        bearing = ''.join([str(int(int(a)==0)) for a in bearing])
        bearing = -float(int(bearing, 2))
        bearing %= 360
    bearing = (bearing+360.0)%360
    return bearing


def interpolate_lat_lon(points, t):
    '''
    Return interpolated lat, lon and compass bearing for time t.
    Points is a list of tuples (time, lat, lon, elevation), t a datetime object.
    '''
    # find the enclosing points in sorted list
    if t<points[0][0]:
        raise ValueError("Photo's timestamp {0} is earlier than the earliest time {1} in the GPX file.".format(t, points[0][0]))
    if t>=points[-1][0]:
        raise ValueError("Photo's timestamp is later than the latest time in the GPX file.")
    for i,point in enumerate(points):
        if t<point[0]:
            if i>0:
                before = points[i-1]
            else:
                before = points[i]
            after = points[i]
            break
    # time diff
    dt_before = (t-before[0]).total_seconds()
    dt_after = (after[0]-t).total_seconds()
    # simple linear interpolation
    lat = (before[1]*dt_after + after[1]*dt_before) / (dt_before + dt_after)
    lon = (before[2]*dt_after + after[2]*dt_before) / (dt_before + dt_after)
    bearing = compute_bearing(before[1], before[2], after[1], after[2])
    if before[3] is not None:
        ele = (before[3]*dt_after + after[3]*dt_before) / (dt_before + dt_after)
    else:
        ele = None
    return lat, lon, bearing, ele


if __name__ == '__main__':
    print("*** Sequence splitter ***")
    try:
        path = sys.argv[1]
    except:
        path = r"D:\Mapillary\DCIM"
        pass
    s = Sequence(path)
    groups = s.split(cutoff_distance=cutoff_distance, cutoff_time=cutoff_time)

