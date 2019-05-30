# introduction

A bus simulator that generates random sensor readings.

In order to run the program you have to specify a XML file containing candidate routes that the bus can go through.

The behaviour of the bus is controlled by the following parameters:

* the start position, that corresponds to one of the existing CARRIS depots.
* the velocity that the bus moves. In the current version it is constant.
* how much time the bus spends in a stop waiting for passengers to enter and leave the bus.
* how many trips the bus does before returning to the depot.
* how much time the bus waits before starting a new trip.

The behaviour of the sensors is controlled by the following parameters:

* the rate at wich data is produced.

# running

To run the simulator:

    python main.py --route-data FILENAME

The parameter `FILENAME` is the name of a XML file with candidate routes.  Its format is:

    <?xml version="1.0" encoding="UTF-8"?>
    <routes>
      <route>
        <number>26</number>
        <up>
          <name>26B: Parque das Nações Norte --- Parque das Nações Sul</name>
          <stops>
            <stop lat="38.7935356" lon="-9.0977435"/>
            <stop lat="38.7921144" lon="-9.0992984"/>
            ...
            <stop lat="38.7554027" lon="-9.0968101"/>
          </stops>
        </up>
        <down>
          <name>26B: Parque das Nações Sul --- Parque das Nações Norte</name>
          <stops>
            <stop lat="38.7549958" lon="-9.0965247"/>
            <stop lat="38.7571557" lon="-9.0981512"/>
            ...
            <stop lat="38.7737666" lon="-9.1048798"/>
          </stops>
        </down>
      </route>
    </routes>

Other parameters affect the bus and sensor behaviours.  Pass the option `--help` to check them.

# output

The simulator creates a tab separated file with bus and sensor data.  The columns of the file contain:

1. the unix timestamp.
2. the latitude of the bus.
3. the longitude of the bus.
4. the identification of the bus.
5. the sensor reading.

# requirements

    apt-get install python-pyproj
    pip install openrouteservice

# about

This simulator was developed in the context of the EXPOLIS project.
