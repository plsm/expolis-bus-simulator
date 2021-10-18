# -*- coding: utf-8 -*-

from __future__ import print_function

import copy
import pickle
import random
import string
import xml.etree.ElementTree
from typing import Any, List, Optional
import pandas

import position
from position import Position


class Route:
    """
    Represents a bus route with its up and down paths.
    Currently we support only a single up and down path.
    """
    def __init__ (
            self,
            number,
            up: List[List[Position]],
            down: Optional[List[List[Position]]] = None):
        """
        Constructs a new route with the given up and down paths.
        If the down path is None it is assumed that the down path is the reverse of the up path.
        This is suitable for routes whose up and down stops are close by.

        :param number:
        :param up:
        :param down:
        """
        self.number = number
        self.__up = up
        if down is None:
            down = []
            for u in up:
                u.reverse ()
                down.append (u)
        self.__down = down

    def path_up (self):
        """
        Returns a list with the positions of the up path of this route.
        :return: a list with the positions of the up path of this route.
        """
        return copy.copy (random.choice (self.__up))

    def path_down (self):
        """
        Returns a list with the positions of the down path of this route.
        :return: a list with the positions of the down path of this route.
        """
        return copy.copy (random.choice (self.__down))

    def nearest_path_up (self, p: position.Position):
        return Route.__nearest_path__ (p, self.__up)

    def nearest_path_down (self, p: position.Position):
        return Route.__nearest_path__ (p, self.__down)

    @staticmethod
    def __nearest_path__ (p: position.Position, paths: List[List[Position]]):
        if len (paths) == 1:
            return copy.copy (paths [0])
        best_index = 0
        best_value = position.distance (p, paths [0][0])
        for candidate_index, candidate_path in enumerate (paths [1:]):
            candidate_value = position.distance (p, candidate_path [0])
            if candidate_value < best_value or (candidate_value == best_value and random.random() < 0.5):
                best_index = candidate_index + 1
                best_value = candidate_value
        return copy.copy (paths [best_index])


__TEST_PATH = [[
    Position (38.7927517, -9.1216364),
    Position (38.7910487, -9.1235028),
    Position (38.7901403, -9.1231415),
    Position (38.7882261, -9.1239125),
    Position (38.7841157, -9.1247923),
]]

__ROUTES = {
    999: Route (999, __TEST_PATH)
}


def random_route ():
    """
    Return a random route.
    :return: a random route.
    """
    return random.choice (list (__ROUTES.values ()))


def get_route (number):
    """
    Return the route with the given number
    :return: the route with the given number
    """
    return __ROUTES [number]


def read_routes_xml (filename, verbose = False):
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

    :param filename:
    :param verbose:
    :return:
    """
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
        if up is None:
            continue
        up = [up]
        if down is not None:
            down = [down]
        key = int (number.text)
        __ROUTES [key] = Route (key, up, down)


def __build_path_from_stops (up_down_element):
    result = []
    for stop in up_down_element.find ('stops').findall ('stop'):
        p = Position (float (stop.get ('lat')), float (stop.get ('lon')))
        result.append (p)
    return result


def read_routes_carris (
        GTFS_FOLDER: str = '/home/pedro/other/xSearch/projects/expolis/datasets/carris/',
        debug: bool = False):
    global __ROUTES
    __ROUTES = {}
    routes_data_frame = pandas.read_csv (GTFS_FOLDER + 'routes.txt')
    trips_data_frame = pandas.read_csv (GTFS_FOLDER + 'trips.txt')
    shapes_data_frame = pandas.read_csv (GTFS_FOLDER + 'shapes.txt')
    info_carreiras = {}
    for _, a_route in routes_data_frame.iterrows ():
        route_id = a_route['route_id']
        route_long_name = a_route['route_long_name']
        print (a_route['route_long_name'])
        route_trips_data_frame = trips_data_frame.loc[lambda df: df['route_id'] == route_id]
        if debug:
            print (route_trips_data_frame)
        route_shape_ids = set (route_trips_data_frame['shape_id'])
        if len (route_shape_ids) > 1:
            print ('!!!!!! AVISO !!!!!\nRota {} tem mais do que uma shape!!!!!!!'.format (route_long_name))
        if debug:
            print (route_shape_ids)
        carreira_id = route_long_name.split ()[0]
        if carreira_id not in info_carreiras:
            info_carreiras[carreira_id] = []
        info_carreiras[carreira_id].append ((route_id, route_long_name, route_shape_ids))
    for carreira_id in info_carreiras:
        print (carreira_id)
        up = []
        down = []
        list_route_long_names = set ([route_long_name for (_, route_long_name, _) in info_carreiras[carreira_id]])
        ask_up_down = len (list_route_long_names) > 2
        up_route_long_name = None
        for index, (_, route_long_name, route_shape_ids) in enumerate (info_carreiras[carreira_id]):
            for route_shape_id in route_shape_ids:
                if ask_up_down:
                    print (route_shape_id)
                else:
                    print ('\t' + route_shape_id, end='')
                route_shape_data_frame = shapes_data_frame.loc[lambda df: df['shape_id'] == route_shape_id]
                route_list = [
                    Position (
                        latitude=r ['shape_pt_lat'],
                        longitude=r ['shape_pt_lon'])
                    for _, r in route_shape_data_frame.iterrows ()]
                if ask_up_down:
                    print ('Route {} from these {} is up or down?'.format (
                        route_long_name, list_route_long_names
                    ))
                    answer = input ()
                    answer = answer.upper()
                    if answer == 'U':
                        up.append (route_list)
                    else:
                        down.append (route_list)
                elif up_route_long_name is None or up_route_long_name == route_long_name:
                    up_route_long_name = route_long_name
                    up.append (route_list)
                else:
                    down.append (route_list)
        if not ask_up_down:
            print ()
        if not down:
            down = None
        __ROUTES [carreira_id] = Route (carreira_id, up, down)
    with open ('carris-routes.dat', 'wb') as _fd:
        pickle.dump (__ROUTES, _fd)


def read_routes_binary ():
    global __ROUTES
    with open ('carris-routes.dat', 'rb') as fd:
        __ROUTES = pickle.load (fd)


if __name__ == '__main__':
    read_routes_carris ()
    with open ('carris-routes.dat', 'wb') as _fd:
        pickle.dump (__ROUTES, _fd)
