# coding=utf-8

import math
import pyproj

EARTH_EQUATORIAL_RADIUS = 6378137.0
EARTH_POLAR_RADIUS = 6356752.3

# Projection used to convert geographic coordinates to a XY plane and vice-versa.
# For other projections and parameters see https://proj4.org/usage/projections.html
# and https://proj4.org/operations/projections/index.html.
PROJECTION = pyproj.Proj (
    proj = 'ortho',
    a = EARTH_EQUATORIAL_RADIUS,
    b = EARTH_POLAR_RADIUS,
    units = 'm'
)

# Represents a geographical position with latitude and longitude.
class Position:
    def __init__ (self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    # Return a string representation to be used with the open routing service.
    def to_ors (self):
        return '{},{}'.format (self.longitude, self.latitude)

    def t (self):
        return (self.longitude, self.latitude)

    # Performs a projection to a plane and return the XY coordinates
    def to_2D (self):
        return PROJECTION (self.longitude, self.latitude)

    def from_2D (self, x, y):
        self.longitude, self.latitude = PROJECTION (x, y, inverse = True)

    def __str__ (self):
        def to_degrees (x):
            seconds = int (math.fabs (x * 3600 + 0.5))
            minutes = (seconds / 60) % 60
            degrees = seconds / 3600
            seconds = seconds % 60
            return '{:02}° {:02}′ {:02}″'.format (degrees, minutes, seconds)
        return '{} {}, {} {}'.format (
            to_degrees (self.latitude),
            'N' if self.latitude > 0 else 'S',
            to_degrees (self.longitude),
            'W' if self.longitude < 0 else 'E'
        )

    def __repr__ (self):
        return str ({'lat' : self.latitude, 'lon' : self.longitude})

def from_2D (x, y):
    (_lambda, _phi) = PROJECTION (x, y, inverse = True)
    return Position (latitude = _phi, longitude = _lambda)

# Computes the distance between the two points.
# We use the projection to obtain points in the plane, and then those points are used to compute the distance.
# The results depends on the projection and on the points.
def distance (a, b):
    xya = a.to_2D ()
    xyb = b.to_2D ()
    return math.sqrt ((xya [0] - xyb [0]) ** 2 + (xya [1] - xyb [1]) ** 2)

# Geographic position of the Companhia Carris De Ferro De Lisboa, S.A
BUS_DEPOT = Position (38.715802, -9.235010)
