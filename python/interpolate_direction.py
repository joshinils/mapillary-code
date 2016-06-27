 #!/usr/bin/python

import os, sys, pyexiv2
from pyexiv2.utils import make_fraction
from lib.geo import compute_bearing, dms_to_decimal, offset_bearing
from lib.sequence import Sequence
from lib.exifedit import ExifEdit

'''
Interpolates the direction of an image based on the coordinates stored in
the EXIF tag of the next image in a set of consecutive images.

Uses the capture time in EXIF and looks up an interpolated lat, lon, bearing
for each image, and writes the values to the EXIF of the image.

An offset angele relative to the direction of movement may be given as an optional
argument to compensate for a sidelooking camera. This angle should be positive for
clockwise offset. eg. 90 for a rightlooking camera and 270 (or -90) for a left looking camera

@attention: Requires pyexiv2; see install instructions at http://tilloy.net/dev/pyexiv2/
@author: mprins
@license: MIT
'''

def write_direction_to_image(filename, direction):
    '''
    Write the direction to the exif tag of the photograph.
    @param filename: photograph filename
    @param direction: direction of view in degrees
    '''
    exif = ExifEdit(filename)
    try:
        exif.add_direction(direction, precision=10)
        exif.write()
        print("Added direction to: {0} ({1} degrees)".format(filename, float(direction)))
    except ValueError, e:
        print("Skipping {0}: {1}".format(filename, e))

if __name__ == '__main__':
    if len(sys.argv) > 3:
        print("Usage: python interpolate_direction.py path [offset_angle]")
        raise IOError("Bad input parameters.")
    path = sys.argv[1]

    # offset angle, relative to camera position, clockwise is positive
    offset_angle = 0
    if len(sys.argv) == 3 :
        offset_angle = float(sys.argv[2])

    s = Sequence(path)
    bearings = s.interpolate_direction(offset_angle)
    for image_name, bearing in bearings.iteritems():
        write_direction_to_image(image_name, bearing)

