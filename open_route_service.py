import json
import requests

import position

API_KEY = '5b3ce3597851110001cf624837aee23f45014e35aba00a8b77e806c1'

class NoPathError (StandardError):
    def __init__ (self, start, end, status_code, reason):
        self.start = start
        self.end = end
        self.status_code = status_code
        self.reason = reason
    def __str__ (self):
        return 'No path from {} to {}, server returned {} with {}'.format (
                self.start, self.end, self.status_code, self.reason)
    def __repr__ (self):
        return str ({'start': self.start, 'end': self.end})


# Returns a list of routes between the start and end positions.
# Uses the open routing service.  The route consists of a list of Position instances.
def path (start, end):
    url = 'https://api.openrouteservice.org/v2/directions/driving-car?api_key={}&start={}&end={}'.format (
        API_KEY,
        start.to_ors (),
        end.to_ors ()
    )
    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
    }
    call = requests.get (url, headers = headers)
    if call.status_code == 200:
        response = json.loads (call.text)
        routes = [
            [
                position.Position (latitude = p [1], longitude = p [0])
                for p in feature ['geometry']['coordinates']
            ]
            for feature in response ['features']
        ]
        for r in routes:
            r.insert (0, start)
            r.append (end)
        return routes
    else:
        raise NoPathError (start, end, call.status_code, call.reason)
