import argparse
import datetime
import math
import random
import time

import paho.mqtt.client

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
    STATE_INITIAL: 'Ini',
    STATE_PICK_ROUTE: 'PRo',
    STATE_PICK_PATH_ROUTE: 'PPR',
    STATE_FIND_PATH_BUS_STOP: 'FPS',
    STATE_DRIVE_BUS_STOP: 'DBS',
    STATE_ENTER_DROP_PASSENGERS: 'EDP',
    STATE_INTER_TRIP_PAUSE: 'ITP',
    STATE_RETURN_DEPOT: 'RtD',
    STATE_FINISH: 'Fin'
}

MQTT_BROKER = 'mqtt.expolis.pt'

POLLUTION_HOTSPOTS = [
    (1000 ** 2, 2,   position.Position (latitude=38.757527, longitude=-9.172170)),
    (1500 ** 2, 3,   position.Position (latitude=38.74251291459529, longitude=-9.138365666383232)),
    (2000 ** 2, 1.5, position.Position (latitude=38.72523425222198, longitude=-9.150369309598695)),
    (3000 ** 2, 10,  position.Position (latitude=38.771702, longitude=-9.134060))
]


class Bus:
    def __init__ (
            self,
            sensor_id,
            velocity: float = 13.9,
            bus_stop_boarding_time: int = 60,
            number_trips: int = 6,
            inter_trip_pause: int = 300):
        self.sensor_node_id = sensor_id
        self.ZERO_TIME = time.time ()
        self.current_position = position.BUS_DEPOT
        self.VELOCITY = velocity
        self.DATA_RATE = 2
        self.BUS_STOP_BOARDING_TIME = bus_stop_boarding_time
        self.remaining_trips = number_trips
        self.INTER_TRIP_PAUSE = inter_trip_pause
        self.state = STATE_INITIAL
        self.selected_route = None
        self.selected_path = None
        self.doing_up_path = True
        self.path = None
        self.clock = None
        self.sequence = 0
        self.state_methods = {
            STATE_INITIAL: self.__state_initial,
            STATE_PICK_ROUTE: self.__state_pick_route,
            STATE_PICK_PATH_ROUTE: self.__state_pick_path_route,
            STATE_FIND_PATH_BUS_STOP: self.__state_find_path_bus_stop,
            STATE_DRIVE_BUS_STOP: self.__state_drive_bus_stop,
            STATE_ENTER_DROP_PASSENGERS: self.__state_enter_drop_passengers,
            STATE_INTER_TRIP_PAUSE: self.__state_inter_trip_pause,
            STATE_RETURN_DEPOT: self.__state_return_depot,
        }
        self.mqtt_client = paho.mqtt.client.Client ()
        self.mqtt_client.connect (
            host=MQTT_BROKER,
            port=1883,
            keepalive=60
        )

    def run (self):
        while self.state is not STATE_FINISH:
            self.state_methods[self.state] ()
            time.sleep (self.DATA_RATE)
            self.publish_state ()

    def publish_state (self):
        now = datetime.datetime.now ()
        timestamp_date = now.strftime ('%Y-%m-%d')
        timestamp_time = now.strftime ('%H:%M:%S')
        t = now.hour * 60 + now.minute
        fx = math.sin ((t - 360) * 2 * math.pi / 1440) + \
            math.exp (-((t - 540) ** 2) / 2 / 60 ** 2) +\
            math.exp (-((t - 1080) ** 2) / 2 / 60 ** 2)
        gas1 = 6 + 4 * fx
        gas2 = 7 + 5 * fx
        pm1 = 10 + 7 * fx
        pm25 = 9 + 6 * fx
        pm10 = 12 + 8 * fx
        for variance, amplitude, pollution_center in POLLUTION_HOTSPOTS:
            d = position.distance(self.current_position, pollution_center)
            d2 = d * d
            if d2 < 3 * variance:
                c = amplitude * math.exp (-d2 / variance / 2)
                gas1 += 10 * c
                gas2 += 33 * c
                pm1 += 24 * c
                pm25 += 21 * c
        temperature = 21 + 4 * math.cos (now.month * 2 * math.pi / 12) + 4 * math.cos (now.hour * 2 * math.pi / 24)
        pressure = 1
        humidity = 50 + \
            20 * math.cos (now.month * 2 * math.pi / 12) + \
            15 * math.cos (now.hour * 2 * math.pi / 24) + \
            5 * math.cos (self.current_position.latitude)
        gps_error = -1666
        kp = -1666
        kd = -1666
        self.sequence += 1
        data = [
            self.sensor_node_id,
            self.sequence,
            timestamp_date, timestamp_time,
            self.current_position.latitude, self.current_position.longitude,
            gas1, gas2, gas1, gas2,
            pm1, pm25, pm10,
            pm1, pm25, pm10,
            temperature, pressure, humidity,
            gps_error,
            -101,
            kp, kd,
            0, 0, 0
        ]
        message = [str (d) for d in data]
        self.mqtt_client.publish (
            topic='expolis_project/sensor_nodes/sn_{}'.format (self.sensor_node_id),
            payload=' '.join (message)
        )

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
        candidate_paths = open_route_service.path_expolis_open_route_service_machine (
            self.current_position, self.selected_path[0])
        self.path = random.choice (candidate_paths)
        print ('Doing path from %s to %s' % (self.current_position, self.selected_path[0]))
        print (self.path)
        self.state = STATE_DRIVE_BUS_STOP

    def __state_drive_bus_stop (self):
        if len (self.path) > 1:
            print ('At {} from waypoint and {} from bus stop'.format (
                position.distance (self.current_position, self.path[0]),
                position.distance (self.current_position, self.selected_path[0])))
        else:
            print ('At {} from bus stop'.format (
                position.distance (self.current_position, self.selected_path[0])))
        if position.distance (self.current_position, self.selected_path[0]) < RADIUS_BUS_STOP_CATCH_AREA:
            self.state = STATE_ENTER_DROP_PASSENGERS
        else:
            while position.distance (self.current_position, self.path[0]) < EPSILON_DISTANCE:
                self.path = self.path[1:]
            self.__drive_to (self.path[0])

    def __state_enter_drop_passengers (self):
        if self.clock is None:
            self.clock = time.time ()
        elif time.time () - self.clock < self.BUS_STOP_BOARDING_TIME:
            pass
        else:
            self.clock = None
            if len (self.selected_path) > 1:
                self.selected_path = self.selected_path[1:]
                self.state = STATE_FIND_PATH_BUS_STOP
            else:
                self.state = STATE_INTER_TRIP_PAUSE

    def __state_inter_trip_pause (self):
        if self.clock is None:
            self.clock = time.time ()
        elif time.time () - self.clock < self.INTER_TRIP_PAUSE:
            pass
        else:
            self.clock = None
            if self.remaining_trips > 0:
                self.remaining_trips -= 1
                self.state = STATE_PICK_PATH_ROUTE
            else:
                candidate_paths = open_route_service.path_expolis_open_route_service_machine (
                    self.current_position,
                    position.BUS_DEPOT
                )
                self.path = random.choice (candidate_paths)
                self.state = STATE_RETURN_DEPOT

    def __state_return_depot (self):
        while len (self.path) > 0 and position.distance (self.current_position, self.path[0]) < EPSILON_DISTANCE:
            self.path = self.path[1:]
        if len (self.path) > 0:
            self.__drive_to (self.path[0])
        else:
            self.state = STATE_FINISH

    # noinspection PyMethodMayBeStatic
    def __state_finish (self):
        print ('End state')

    def __drive_to (self, target):
        xy_from = self.current_position.to_2D ()
        xy_target = target.to_2D ()
        norm = (xy_target[0] - xy_from[0], xy_target[1] - xy_from[1])
        distance = math.sqrt (norm[0] ** 2 + norm[1] ** 2)
        norm = (norm[0] / distance, norm[1] / distance)
        # don't go beyond the target point
        delta = min (distance, self.VELOCITY * self.DATA_RATE)
        self.current_position.from_2D (xy_from[0] + norm[0] * delta, xy_from[1] + norm[1] * delta)


def process_arguments ():
    parser = argparse.ArgumentParser (
        description='Simulate a bus doing a trip from the CARRIS depot along a bus line, and returning to the depot.  '
                    'Bus line are chosen from data stored in file carris-routes.dat.  '
                    'This file should be present in the local directory.'
    )
    parser.add_argument (
        'sensor_node',
        metavar='SENSOR_ID',
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
    parser.add_argument (
        '--number-trips',
        type=int,
        default=6,
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
        '--hivemq',
        action='store_true',
        help='Use the server broker.hivemq.com as the MQTT broker'
    )
    parser.add_argument (
        '--eclipse1',
        action='store_true',
        help='Use the server mqtt.eclipse.org as the MQTT broker'
    )
    # noinspection SpellCheckingInspection
    parser.add_argument (
        '--eclipse2',
        action='store_true',
        help='Use the server mqtt.eclipseprojects.io as the MQTT broker'
    )
    parser.add_argument (
        '--localhost',
        action='store_true',
        help='Use the localhost as the MQTT broker'
    )
    parser.add_argument (
        '--mqtt',
        metavar='SERVER',
        type=str,
        default=MQTT_BROKER,
        help='MQTT broker server to use'
    )
    return parser.parse_args ()


if __name__ == '__main__':
    args = process_arguments ()
    if args.hivemq:
        MQTT_BROKER = 'broker.hivemq.com'
    elif args.eclipse1:
        MQTT_BROKER = 'mqtt.eclipse.org'
    elif args.eclipse2:
        # noinspection SpellCheckingInspection
        MQTT_BROKER = 'mqtt.eclipseprojects.io'
    elif args.localhost:
        MQTT_BROKER = 'localhost'
    else:
        MQTT_BROKER = args.mqtt
    route.read_routes_binary ()
    Bus (
        sensor_id=args.sensor_node,
        velocity=args.velocity,
        bus_stop_boarding_time=args.bus_stop_boarding_time,
        number_trips=args.number_trips,
        inter_trip_pause=args.inter_trip_pause
    ).run ()
