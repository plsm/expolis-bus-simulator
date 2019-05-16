# -*- coding: utf-8 -*-

from __future__ import print_function

import copy
import random
import xml.etree.ElementTree

from position import Position

"""
Represents a bus route with its up and down paths.
Currently we support only a single up and down path.
"""
class Route:
    """
    Constructs a new route with the given up and down paths.
    If the down path is None it is assumed that the down path is the reverse of the up path.
    This is suitable for routes whose up and down stops are close by.
    """
    def __init__ (self, number, up, down = None):
        self.number = number
        self.__up = up
        if down is None:
            down = copy.copy (up)
            down.reverse ()
        self.__down = down
    """
    Returns a list with the positions of the up path of this route.
    """
    def path_up (self):
        return copy.copy (self.__up)
    """
    Returns a list with the positions of the down path of this route.
    """
    def path_down (self):
        return copy.copy (self.__down)

__TEST_PATH = [
    Position (38.7927517, -9.1216364),
    Position (38.7910487, -9.1235028),
    Position (38.7901403, -9.1231415),
    Position (38.7882261, -9.1239125),
    Position (38.7841157, -9.1247923),
]

__ROUTES = {
    999 : Route (999, __TEST_PATH)
}

"""
Return a random route.
"""
def random_route ():
    return random.choice (__ROUTES.values ())

"""
Return the route with the given number
"""
def get_route (number):
    return __ROUTES [number]

"""
Reads data from a XML to construct route data.
The structure of the XML data should consists of route elements.

Each route element must have a number element with an integer, a series of up,
down and updown elements.
These elements contain the paths that a bus of the given route do.
They should have a name element with a string describing the path, and a stops
element containing a sequence of stop elements.
Each stop element should have two attributes: lat and lon with the latitude and
longitude of the stop.

Currently we support only a single up and down path.
"""
def read_routes_xml (filename, verbose = False):
    global __ROUTES
    __ROUTES = {}
    root = xml.etree.ElementTree.parse (filename)
    for route in root.findall ('route'):
        if len (route.findall ('updown')) > 1 or \
            len (route.findall ('up')) > 1 or \
            len (route.findall ('down')) > 1:
            print ('Routes with multiple up and down paths are not handled!')
            continue
        number = route.find ('number')
        if verbose:
            print ('Creating routes for {}'.format (number.text))
        up = None
        down = None
        for path in route.findall ('up'):
            if verbose:
                print ('   ', path.find ('name').text)
            up = __build_path_from_stops (path)
        for path in route.findall ('down'):
            if verbose:
                print ('   ', path.find ('name').text)
            down = __build_path_from_stops (path)
        for path in route.findall ('updown'):
            if verbose:
                print ('   ', path.find ('name').text)
            up = __build_path_from_stops (path)
        key = int (number.text)
        __ROUTES [key] = Route (key, up, down)

def __build_path_from_stops (up_down_element):
    result = []
    for stop in up_down_element.find ('stops').findall ('stop'):
        p = Position (float (stop.get ('lat')), float (stop.get ('lon')))
        result.append (p)
    return result
