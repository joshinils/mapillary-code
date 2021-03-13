import os
import sys
from tqdm import tqdm
from math import asin, cos, radians, sin, sqrt
from exifpil3 import PILExifReader


class GPSDirectionDuplicateFinder:
    """Finds duplicates based on the direction the camera is pointing.
  This supports the case where a panorama is being made."""

    def __init__(self, max_diff):
        self._prev_rotation = None
        self._prev_unique_rotation = None
        self._max_diff = max_diff
        self._latest_text = ""

    def get_latest_text(self):
        return self._latest_text

    def latest_is_duplicate(self, is_duplicate):
        if not is_duplicate:
            self._prev_unique_rotation = self._prev_rotation

    def is_duplicate(self, file_path, exif_reader):
        # rotation = exif_reader.get_rotation()
        #
        # if rotation is None:
        #     return None
        #
        # if self._prev_unique_rotation is None:
        #     self._prev_rotation = rotation
        #     return False
        #
        # diff = abs(rotation - self._prev_unique_rotation)
        # is_duplicate = diff < self._max_diff
        #
        # self._prev_rotation = rotation
        # self._latest_text = str(int(diff)) + " deg: " + str(is_duplicate)
        is_duplicate = None
        return is_duplicate


class GPSDistance:
    """Calculates the distance between two sets of GPS coordinates."""
    @staticmethod
    def get_gps_distance(lat1, lon1, lat2, lon2):
        """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees with a result in meters).
    This is done using the Haversine Formula.
    """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = list(map(radians, [lat1, lon1, lat2, lon2]))
        # Haversine formula
        difflat = lat2 - lat1
        difflon = lon2 - lon1
        a = (sin(difflat / 2) ** 2) + (cos(lat1)
                                       * cos(lat2) * sin(difflon / 2) ** 2)
        # difflon = lon2 - lon1
        c = 2 * asin(sqrt(a))
        r = 6371000  # Radius of The Earth in meters.
        # It is not a perfect sphere, so this is just good enough.
        return c * r


class GPSSpeedErrorFinder:
    """Finds images in a sequence that might have an error in GPS data
     or suggest a track to be split. It is done by looking at the
     speed it would take to travel the distance in question."""

    def __init__(self, max_speed_km_h, way_too_high_speed_km_h):
        self._prev_lat_lon = None
        self._previous = None
        self._latest_text = ""
        self._previous_filepath = None
        self._max_speed_km_h = max_speed_km_h
        self._way_too_high_speed_km_h = way_too_high_speed_km_h
        self._high_speed = False
        self._too_high_speed = False

    def set_verbose(self, verbose):
        self.verbose = verbose

    def get_latest_text(self):
        return self._latest_text

    def is_error(self, file_path, exif_reader):
        """
    Returns if there is an obvious error in the images exif data.
    The given image is an instance of PIL's Image class.
    the given exif is the data from the get_exif_data function.
    """
        speed_gps = exif_reader.get_speed()
        if speed_gps is None:
            self._latest_text = "No speed given in EXIF data."
            return False
        self._latest_text = "Speed GPS: " + str(speed_gps) + " km/h"
        if speed_gps > self._way_too_high_speed_km_h:
            self._latest_text = ("GPS speed is unrealistically high: %s km/h."
                                 % speed_gps)
            self._too_high_speed = True
            return True
        elif speed_gps > self._max_speed_km_h:
            self._latest_text = ("GPS speed is high: %s km/h."
                                 % speed_gps)
            self._high_speed = True
            return True
        latlong = exif_reader.get_lat_lon()
        timestamp = exif_reader.get_time()
        if self._prev_lat_lon is None or self._prev_time is None:
            self._prev_lat_lon = latlong
            self._prev_time = timestamp
            self._previous_filepath = file_path
            return False
        if latlong is None or timestamp is None:
            return False
        diff_meters = GPSDistance.get_gps_distance(
            self._prev_lat_lon[0], self._prev_lat_lon[1], latlong[0],
            latlong[1])
        diff_secs = (timestamp - self._prev_time).total_seconds()
        if diff_secs == 0:
            return False
        speed_km_h = (diff_meters / diff_secs) * 3.6
        if speed_km_h > self._way_too_high_speed_km_h:
            self._latest_text = ("Speed between %s and %s is %s km/h, which is"
                                 " unrealistically high." % (self._previous_filepath, file_path, int(speed_km_h)))
            self._too_high_speed = True
            return True
        elif speed_km_h > self._max_speed_km_h:
            self._latest_text = "Speed between %s and %s is %s km/h." % (
                self._previous_filepath, file_path, int(speed_km_h)
            )
            self._high_speed = True
            return True
        else:
            return False

    def is_fast(self):
        return self._high_speed

    def is_too_fast(self):
        return self._too_high_speed


class GPSDistanceDuplicateFinder:
    """Finds duplicates images by looking at the distance between
  two GPS points."""

    def __init__(self, distance):
        self._distance = distance
        self._prev_lat_lon = None
        self._previous = None
        self._latest_text = ""
        self._previous_filepath = None
        self._prev_unique_lat_lon = None

    def get_latest_text(self):
        return self._latest_text

    def latest_is_duplicate(self, is_duplicate):
        if not is_duplicate:
            self._prev_unique_lat_lon = self._prev_lat_lon

    def is_duplicate(self, file_path, exif_reader):
        """
    Returns if the given image is a duplicate of the previous image.
    The given image is an instance of PIL's Image class.
    the given exif is the data from the get_exif_data function.
    """
        latlong = exif_reader.get_lat_lon()

        if self._prev_lat_lon is None:
            self._prev_lat_lon = latlong
            return False

        if self._prev_unique_lat_lon is not None and latlong is not None:
            diff_meters = GPSDistance.get_gps_distance(
                self._prev_unique_lat_lon[0], self._prev_unique_lat_lon[1],
                latlong[0], latlong[1])
            self._previous_filepath = file_path
            is_duplicate = diff_meters <= self._distance
            self._prev_lat_lon = latlong
            self._latest_text = file_path + ": " + str(
                int(diff_meters)) + " m: " + str(is_duplicate)
            return is_duplicate
        else:
            return False


class ImageRemover:
    """Moves images that are (almost) duplicates or contains errors in GPS
  data into separate directories."""

    def __init__(self, src_dir):
        self._testers = []
        self._error_finders = []
        self._src_dir = src_dir
        self._dryrun = False
        self.verbose = 0

    def set_verbose(self, verbose):
        self.verbose = verbose

    def set_dry_run(self, dryrun):
        self._dryrun = dryrun

    def add_duplicate_finder(self, tester):
        self._testers.append(tester)

    def add_error_finder(self, finder):
        self._error_finders.append(finder)

    def _move_into_error_dir(self, file):
        self._move_into_dir(file)

    def _move_into_duplicate_dir(self, file):
        self._move_into_dir(file)

    def _move_into_dir(self, file):
        if not self._dryrun:  # and not os.path.exists(dir):
            if verbose != 0:
                print("Delete:", file)
            os.remove(file)

    def _read_capture_time(self, filepath):
        reader = PILExifReader(filepath)
        return reader.read_capture_time()

    def _sort_file_list(self, file_list):
        '''
        Read capture times and sort files in time order.
        '''
        capture_times = [self._read_capture_time(
            filepath) for filepath in file_list]
        sorted_times_files = list(zip(capture_times, file_list))
        sorted_times_files.sort()
        return list(zip(*sorted_times_files))

    def do_magic(self):
        """Perform the task of finding and moving images."""
        # files = [os.path.join(self._src_dir, f) for f in os.listdir(self._src_dir)
        #         if os.path.isfile(os.path.join(self._src_dir, f)) and
        #         f.lower().endswith('.jpg')]
        files = []
        for subdirz, dirz, filez in os.walk(self._src_dir):
            print("Search files:", subdirz)
            for f in tqdm(filez, dynamic_ncols=True):
                file_path = subdirz + os.sep + f
                if file_path.lower().endswith('.jpg'):
                    # print(file_path)
                    files.append(file_path)
        capturetime, files = self._sort_file_list(files)
        print("Check", len(files), "files.")
        for file_path in tqdm(files, dynamic_ncols=True):
            exif_reader = PILExifReader(file_path)
            is_error = self._handle_possible_erro(file_path, exif_reader)
            if not is_error:
                self._handle_possible_duplicate(file_path, exif_reader)

    def _handle_possible_duplicate(self, file_path, exif_reader):
        is_duplicate = True
        verbose_text = []
        for tester in self._testers:
            is_this_duplicate = tester.is_duplicate(file_path, exif_reader)
            if is_this_duplicate != None:
                is_duplicate &= is_this_duplicate
                verbose_text.append(tester.get_latest_text())
            else:
                verbose_text.append("No orientation")

        if self.verbose >= 1:
            print(", ".join(verbose_text), "=>", is_duplicate)
        if is_duplicate:
            self._move_into_duplicate_dir(file_path)
        for tester in self._testers:
            tester.latest_is_duplicate(is_duplicate)
        return is_duplicate

    def _handle_possible_erro(self, file_path, exif_reader):
        is_error = False
        for finder in self._error_finders:
            err = finder.is_error(file_path, exif_reader)
            if err:
                print(finder.get_latest_text())
            is_error |= err
        if is_error:
            self._move_into_error_dir(file_path)
        return is_error


if __name__ == "__main__":
    distance = 3
    pan = 20
    fast_km_h = 150
    too_fast_km_h = 200
    min_duplicates = 3
    dryrun = False
    verbose = 0
    print("*** Dupe remover ***")
    src_dir = sys.argv[1]
    if not(os.path.isdir(src_dir)):
        print("No valid directory given as parameter.")
        exit(1)
    distance_finder = GPSDistanceDuplicateFinder(distance)
    image_remover = ImageRemover(src_dir)
    image_remover.add_duplicate_finder(distance_finder)
    image_remover.do_magic()
