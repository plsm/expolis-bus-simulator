#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse

import bus
import route


def process_arguments ():
    parser = argparse.ArgumentParser (
        description="A bus simulator developed for the EXPOLIS project."
    )
    parser.add_argument (
        '--start-position',
        type=str,
        choices=['1'],
        help='starting position of the bus'
    )
    # the default value of bus velocity was taken from http://www.carris.pt/pt/indicadores-de-atividade/
    parser.add_argument (
        '--velocity',
        type=float,
        default=13.9,
        metavar='V',
        help='bus velocity in km/h'
    )
    parser.add_argument (
        '--bus-stop-boarding-time',
        type=float,
        default=60.0,
        metavar='T',
        help='how much time the bus is in a bus stop waiting for passengers to board, units in s'
    )
    # TODO: use a default value that represents sensor integration time.
    parser.add_argument (
        '--data-rate',
        type=float,
        default=1,  # 34.0,
        metavar='R',
        help='rate at which data is produced, units in s'
    )
    parser.add_argument (
        '--number-trips',
        type=int,
        default=1,
        metavar='N',
        help='the number of trips that a bus does'
    )
    parser.add_argument (
        '--inter-trip-pause',
        type=float,
        default=300.0,
        metavar='T',
        help='how much time the bus waits before starting a new trip or returns to the depot, units in s'
    )
    parser.add_argument (
        '--route-data',
        type=str,
        default=None,
        metavar='FILENAME',
        help='XML file with route information'
    )
    return parser.parse_args ()


if __name__ == '__main__':
    args = process_arguments ()
    if args.route_data is not None:
        route.read_routes_xml (args.route_data)
    a_bus = bus.Bus (
        start_position=args.start_position,
        velocity=args.velocity,
        bus_stop_boarding_time=args.bus_stop_boarding_time,
        data_rate=args.data_rate,
        number_trips=args.number_trips,
        inter_trip_pause=args.inter_trip_pause
    )
    a_bus.run ()
