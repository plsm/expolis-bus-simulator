# coding=utf-8

import math

# Represents a geographical position with latitude and longitude.
class Position:
    def __init__ (self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    # Return a string representation to be used with the open routing service.
    def to_ors (self):
        return '{},{}'.format (self.longitude, self.latitude)

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

# Geographic position of the Companhia Carris De Ferro De Lisboa, S.A
BUS_DEPOT = Position (38.715802, -9.235010)
