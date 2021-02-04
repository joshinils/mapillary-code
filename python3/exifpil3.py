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
            pprint.pprint(self._exif)

    def remove_XMP_description(self) -> bool:
        """ sets the XMP description tag from the images metadata to " "
            returns success
        """
        xmp_file = libxmp.XMPFiles( file_path = self._filepath, open_forupdate=True )

        # Get XMP from file
        xmp = xmp_file.get_xmp()

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

        if xmp_file.can_put_xmp(xmp):
            xmp_file.put_xmp(xmp)
            xmp_file.close_file()
            return True
        else:
            print("can not put xmp")
            return False

    @staticmethod
    def get_exif_data(image):
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
        """
            returns None or datetime.datetime
        """
        time_tag = "DateTimeOriginal"

        # read and format capture time
        if self._exif == None:
            print("Exif is none.")

        if time_tag in self._exif:
            capture_time = self._exif[time_tag]
            capture_time = capture_time.replace(" ","_")
            capture_time = capture_time.replace(":","_")
            # return as datetime object
            return datetime.datetime.strptime(capture_time, '%Y_%m_%d_%H_%M_%S_%f')
        else:
            print("No time tag in " + self._filepath)
            return None

    @staticmethod
    def _get_if_exist(data, key):
        if key in data:
            return data[key]
        else:
            return None

    def get_exif_tag(self, key_name):
        return self._exif[key_name] or None

    @staticmethod
    def _convert_to_degress(value):
        """Helper function to convert the GPS coordinates stored in
        the EXIF to degrees in float format."""

        if type(value[0]) is tuple:
            d = float(value[0][0]) / float(value[0][1])
            m = float(value[1][0]) / float(value[1][1])
            s = float(value[2][0]) / float(value[2][1])
        else:
            d = value[0]
            m = value[1]
            s = value[2]

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

    @staticmethod
    def calc_tuple(tup):
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
            if gps_direction is not None:
                if type(gps_direction) is tuple:
                    return self.calc_tuple(gps_direction)
                return gps_direction
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

    @staticmethod
    def is_ok_num(val, minVal, maxVal):
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
