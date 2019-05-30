from __future__ import print_function

import csv
import math
import random
import time

import open_route_service
import position
import route

STATE_INITIAL = 1001
STATE_PICK_ROUTE = 1002
STATE_PICK_PATH_ROUTE = 1003
STATE_FIND_PATH_BUS_STOP = 1004
STATE_DRIVE_BUS_STOP = 1005
STATE_ENTER_DROP_PASSENGERS = 1006
STATE_INTER_TRIP_PAUSE = 1007
STATE_RETURN_DEPOT = 1008
STATE_FINISH = 9999

RADIUS_BUS_STOP_CATCH_AREA = 2

EPSILON_DISTANCE = 1

STATE_STRING = {
    STATE_INITIAL : 'Ini' ,
    STATE_PICK_ROUTE : 'PRo',
    STATE_PICK_PATH_ROUTE : 'PPR',
    STATE_FIND_PATH_BUS_STOP : 'FPS',
    STATE_DRIVE_BUS_STOP : 'DBS',
    STATE_ENTER_DROP_PASSENGERS : 'EDP',
    STATE_INTER_TRIP_PAUSE : 'ITP',
    STATE_RETURN_DEPOT : 'RtD',
    STATE_FINISH : 'Fin'
}

NUMBER_BUSES = 10

class Bus:
    def __init__ (self, start_position, velocity, bus_stop_boarding_time, data_rate, number_trips, inter_trip_pause):
        self.ID = random.randrange (NUMBER_BUSES) + 1
        self.ZERO_TIME = time.time ()
        self.current_time = self.ZERO_TIME
        self.current_position = position.BUS_DEPOT
        self.VELOCITY = velocity
        self.DATA_RATE = data_rate
        self.BUS_STOP_BOARDING_TIME = bus_stop_boarding_time
        self.remaining_trips = number_trips
        self.INTER_TRIP_PAUSE = inter_trip_pause
        self.state = STATE_INITIAL
        self.selected_route = None
        self.selected_path = None
        self.doing_up_path = True
        self.path = None
        self.clock = None
        self.state_methods = {
            STATE_INITIAL : self.__state_initial,
            STATE_PICK_ROUTE : self.__state_pick_route,
            STATE_PICK_PATH_ROUTE : self.__state_pick_path_route,
            STATE_FIND_PATH_BUS_STOP : self.__state_find_path_bus_stop,
            STATE_DRIVE_BUS_STOP : self.__state_drive_bus_stop,
            STATE_ENTER_DROP_PASSENGERS : self.__state_enter_drop_passengers,
            STATE_INTER_TRIP_PAUSE : self.__state_inter_trip_pause,
            STATE_RETURN_DEPOT : self.__state_return_depot,
        }
        tsv_fd = open ('bus-state.tsv', 'w')
        tsv_writer = csv.writer (tsv_fd, delimiter = '\t', quoting = csv.QUOTE_NONNUMERIC)
        self.tsv_output = (tsv_fd, tsv_writer)

    def run (self):
        self.save_state_TSV ()
        self.print_status ()
        while self.state is not STATE_FINISH:
            self.state_methods [self.state] ()
            self.current_time += self.DATA_RATE
            self.save_state_TSV ()
            self.print_status ()
        self.tsv_output [0].close ()
        self.tsv_output = None

    def __state_initial (self):
        self.state = STATE_PICK_ROUTE

    def __state_pick_route (self):
        self.selected_route = route.random_route ()
        print ('Doing route {}'.format (self.selected_route.number))
        self.state = STATE_PICK_PATH_ROUTE

    def __state_pick_path_route (self):
        if self.doing_up_path:
            self.selected_path = self.selected_route.path_up ()
        else:
            self.selected_path = self.selected_route.path_down ()
        self.doing_up_path = not self.doing_up_path
        self.state = STATE_FIND_PATH_BUS_STOP

    def __state_find_path_bus_stop (self):
        candidate_paths = open_route_service.path (self.current_position, self.selected_path [0])
        self.path = random.choice (candidate_paths)
        print ('Doing path from %s to %s' % (self.current_position, self.selected_path [0]))
        print (self.path)
        self.state = STATE_DRIVE_BUS_STOP

    def __state_drive_bus_stop (self):
        if len (self.path) > 1:
            print ('At {} from waypoint and {} from bus stop'.format (
                position.distance (self.current_position, self.path [0]),
                position.distance (self.current_position, self.selected_path [0])))
        else:
            print ('At {} from bus stop'.format (
                position.distance (self.current_position, self.selected_path [0])))
        if position.distance (self.current_position, self.selected_path [0]) < RADIUS_BUS_STOP_CATCH_AREA:
            self.state = STATE_ENTER_DROP_PASSENGERS
        else:
            while position.distance (self.current_position, self.path [0]) < EPSILON_DISTANCE:
                self.path = self.path [1:]
            self.__drive_to (self.path [0])

    def __state_enter_drop_passengers (self):
        if self.clock is None:
            self.clock = self.current_time
        elif self.current_time - self.clock < self.BUS_STOP_BOARDING_TIME:
            pass
        else:
            self.clock = None
            if len (self.selected_path) > 1:
                self.selected_path = self.selected_path [1:]
                self.state = STATE_FIND_PATH_BUS_STOP
            else:
                self.state = STATE_INTER_TRIP_PAUSE

    def __state_inter_trip_pause (self):
        if self.clock is None:
            self.clock = self.current_time
        elif self.current_time - self.clock < self.INTER_TRIP_PAUSE:
            pass
        else:
            self.clock = None
            if self.remaining_trips > 0:
                self.remaining_trips -= 1
                self.state = STATE_PICK_PATH_ROUTE
            else:
                candidate_paths = open_route_service.path (self.current_position, position.BUS_DEPOT)
                self.path = random.choice (candidate_paths)
                self.state = STATE_RETURN_DEPOT

    def __state_return_depot (self):
        while len (self.path) > 0 and position.distance (self.current_position, self.path [0]) < EPSILON_DISTANCE:
            self.path = self.path [1:]
        if len (self.path) > 0:
            self.__drive_to (self.path [0])
        else:
            self.state = STATE_FINISH

    def __state_finish (self):
        print ('End state')

    def __drive_to (self, target):
        xy_from = self.current_position.to_2D ()
        xy_target = target.to_2D ()
        norm = (xy_target [0] - xy_from [0], xy_target [1] - xy_from [1])
        distance = math.sqrt (norm [0] ** 2 + norm [1] ** 2)
        norm = (norm [0] / distance, norm [1] / distance)
        # don't go beyond the target point
        delta = min (distance, self.VELOCITY * self.DATA_RATE)
        self.current_position.from_2D (xy_from [0] + norm [0] * delta, xy_from [1] + norm [1] * delta)

    def print_status (self):
        print ('[{}]  Ellapsed time {:.1f}s   position {}'.format (
            STATE_STRING [self.state],
            self.current_time - self.ZERO_TIME,
            self.current_position
            ))

    def save_state_TSV (self):
        (x, y) = self.current_position.to_2D ()
        self.tsv_output [1].writerow ([
            self.current_time,
            self.current_position.latitude,
            self.current_position.longitude,
            self.ID,
            1000,
#            x,
#            y,
#            self.state
        ])
