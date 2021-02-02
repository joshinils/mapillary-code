import datetime
# import struct  # Only to catch struct.error due to error in PIL / Pillow.
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import pprint
import libxmp # python-xmp-toolkit, https://python-xmp-toolkit.readthedocs.io/en/latest/installation.html
from libxmp.utils import file_to_dict

# Original:  https://gist.github.com/erans/983821
# License:   MIT
# Credits:   https://gist.github.com/erans

import ast

class ExifException(Exception):
    def __init__(self, message):
        self._message = message

    def __str__(self):
        return self._message


class PILExifReader:
    def __init__(self, filepath):
        self._filepath = filepath
        with Image.open(filepath) as image:
            self._exif = self.get_exif_data(image)

        self.remove_XMP_description()

    def remove_XMP_description(self):
        xmpfile = libxmp.XMPFiles( file_path = self._filepath, open_forupdate=True )

        #Get XMP from file:
        xmp = xmpfile.get_xmp()

        # xmp_dict = file_to_dict(self._filepath)

        # try:
        #     ns_xmp = xmp_dict[libxmp.consts.XMP_NS_XMP]
        #     #pprint.pprint(ns_xmp)
        # except:
        #     print("XMP_NS_XMP")

        # try:
        #     ns_dc = xmp_dict[libxmp.consts.XMP_NS_DC]
        #     #pprint.pprint(ns_dc)
        # except:
        #     print("XMP_NS_DC")

        # try:
        #     ns_IPTCCore = xmp_dict[libxmp.consts.XMP_NS_IPTCCore]
        #     #pprint.pprint(ns_IPTCCore)
        # except:
        #     print("XMP_NS_IPTCCore")

        # #print("\nxmp:")
        # #pprint.pprint(xmp)

        # try:
        #     description = xmp.get_property(libxmp.consts.XMP_NS_XMP, 'xmp:description' )
        #     print("\ndescription:")
        #     #pprint.pprint(description)
        # except:
        #     pass

        # change the xmp
        try:
            xmp.set_property(libxmp.consts.XMP_NS_XMP, u'description', u'' )
        except:pass
        try:
            xmp.set_property(libxmp.consts.XMP_NS_IPTCCore, u'description', u'' )
        except:pass
        try:
            xmp.set_property(libxmp.consts.XMP_NS_DC, u'description[1]', u'' )
        except:pass

        if xmpfile.can_put_xmp(xmp):
            xmpfile.put_xmp(xmp)
        else:
            print("can not put xmp")
        xmpfile.close_file()

    def get_exif_data(self, image):
        """Returns a dictionary from the exif data of an PIL Image
        item. Also converts the GPS Tags"""
        exif_data = {}
        try:
            info = image._getexif()

        except OverflowError as e:
            if e.message == "cannot fit 'long' into an index-sized integer":
                # Error in PIL when exif data is corrupt.
                return None
            else:
                raise e
        # except struct.error as e:
        #     if e.message == "unpack requires a string argument of length 2":
        #         # Error in PIL when exif data is corrupt.
        #         return None
        #     else:
        #         raise e
        if info:
            for tag, value in list(info.items()):
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    gps_data = {}
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_data[sub_decoded] = value[t]
                    exif_data[decoded] = gps_data
                else:
                    exif_data[decoded] = value
        return exif_data

    def read_capture_time(self):
        time_tag = "DateTimeOriginal"

        # read and format capture time
        if self._exif == None:
            print("Exif is none.")

        #default value if none exists
        capture_time = "1970_01_01_00_00_00_000"
        if time_tag in self._exif:
            capture_time = self._exif[time_tag]
        elif "ImageDescription" in self._exif or "Description" in self._exif:
            pprint.pprint(self._exif)
            try:
                dict = ast.literal_eval(self._exif["ImageDescription"])
                capture_time = dict["MAPCaptureTime"]
                pprint.pprint(dict)
            except:
                try:
                    dict = ast.literal_eval(self._exif["Description"])
                    pprint.pprint(dict)
                    capture_time = dict["MAPCaptureTime"]
                except:
                    print("No time tag in " + self._filepath)
        else:
            print("No time tag in " + self._filepath)
        capture_time = capture_time.replace(" ","_")
        capture_time = capture_time.replace(":","_")

        # return as datetime object
        return datetime.datetime.strptime(capture_time, '%Y_%m_%d_%H_%M_%S_%f')

    def _get_if_exist(self, data, key):
        if key in data:
            return data[key]
        else:
            return None

    def get_exif_tag(self, key_name):
        return self._exif[key_name] or None

    def _convert_to_degress(self, value):
        """Helper function to convert the GPS coordinates stored in
        the EXIF to degrees in float format."""
        d = value[0]
        # d0 = value[0][0]
        # d1 = value[0][1]
        # d = float(d0) / float(d1)

        m = value[1]
        # m0 = value[1][0]
        # m1 = value[1][1]
        # m = float(m0) / float(m1)

        s = value[2]
        # s0 = value[2][0]
        # s1 = value[2][1]
        # s = float(s0) / float(s1)

        return d + (m / 60.0) + (s / 3600.0)

    def get_lat_lon(self):
        """Returns the latitude and longitude, if available, from the
        provided exif_data (obtained through get_exif_data above)."""
        lat = None
        lon = None

        gps_info = self.get_gps_info()
        if gps_info is None:
            return None

        gps_latitude = self._get_if_exist(gps_info, "GPSLatitude")
        gps_latitude_ref = self._get_if_exist(gps_info, 'GPSLatitudeRef')
        gps_longitude = self._get_if_exist(gps_info, 'GPSLongitude')
        gps_longitude_ref = self._get_if_exist(gps_info, 'GPSLongitudeRef')

        if (gps_latitude and gps_latitude_ref
            and gps_longitude and gps_longitude_ref):

            lat = self._convert_to_degress(gps_latitude)
            if gps_latitude_ref != "N":
                lat = 0 - lat

            lon = self._convert_to_degress(gps_longitude)
            if gps_longitude_ref != "E":
                lon = 0 - lon

        if isinstance(lat, float) and isinstance(lon, float):
            return lat, lon
        else:
            return None

    def calc_tuple(self, tup):
        if tup is None:
            return None
        return int(tup[0]) / int(tup[1])

    def get_gps_info(self):
        if self._exif is None or not "GPSInfo" in self._exif:
            return None
        else:
            return self._exif["GPSInfo"]

    def get_rotation(self):
        """Returns the direction of the GPS receiver in degrees."""
        gps_info = self.get_gps_info()
        if gps_info is None:
            return None

        for tag in ('GPSImgDirection', 'GPSTrack'):
            gps_direction = self._get_if_exist(gps_info, tag)
            # direction = self.calc_tuple(gps_direction)
            direction = gps_direction
            if direction == None:
                continue
            else:
                return direction
        return None

    def get_speed(self):
        """Returns the GPS speed in km/h or None if it does not exists."""
        gps_info = self.get_gps_info()
        if gps_info is None:
            return None

        if not "GPSSpeed" in gps_info or not "GPSSpeedRef" in gps_info:
            return None
        speed_frac = gps_info["GPSSpeed"]
        speed_ref = gps_info["GPSSpeedRef"]

        # speed = self.calc_tuple(speed_frac)
        speed = speed_frac

        if speed is None or speed_ref is None:
            return None

        speed_ref = speed_ref.lower()
        if speed_ref == "k":
            pass  # km/h - we are happy.
        elif speed_ref == "m":
            #Miles pr. hour => km/h
            speed *= 1.609344
        elif speed_ref == "n":
            # Knots => km/h
            speed *= 1.852
        else:
            print("Warning: Unknown format for GPS speed '%s' in '%s'." % (
                speed_ref, self._filepath))
            print("Please file a bug and attache the image.")
            return None
        return speed

    def is_ok_num(self, val, minVal, maxVal):
        try:
            num = int(val)
        except ValueError:
            return False
        if num < minVal or num > maxVal:
            return False
        return True

    def get_time(self):
        # Example data
        # GPSTimeStamp': ((9, 1), (14, 1), (9000, 1000))
        # 'GPSDateStamp': u'2015:05:17'
        gps_info = self.get_gps_info()
        if gps_info is None:
            return None

        if not 'GPSTimeStamp' in gps_info or not 'GPSDateStamp' in gps_info:
            return None
        timestamp = gps_info['GPSTimeStamp']
        datestamp = gps_info['GPSDateStamp']

        if len(timestamp) != 3:
            raise ExifException("Timestamp does not have length 3: %s" %
                                len(timestamp))
        (timeH, timeM, timeS) = timestamp
        h = self.calc_tuple(timeH)
        m = self.calc_tuple(timeM)
        s = self.calc_tuple(timeS)
        if None in (h, m, s):
            raise ExifException(
                "Hour, minute or second is not valid: '%s':'%s':'%s'." %
                (timeH, timeM, timeS))

        if datestamp.count(':') != 2:
            raise ExifException("Datestamp does not contain 2 colons: '%s'" %
                                datestamp)
        (y, mon, d) = [int(str) for str in datestamp.split(':')]
        if not self.is_ok_num(y, 1970, 2100) or not self.is_ok_num(
                mon, 1, 12) or not self.is_ok_num(d, 1, 31):
            raise ExifException(
                "Date parsed from the following is not OK: '%s'" % datestamp)

        return datetime.datetime(y, mon, d, h, m, s)
