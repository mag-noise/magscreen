# Cole's project

This is text in markdown format. Edit it to describe the project
in your own words.


## The mag_shield_testing program

The main data collection program is `mag_shield_testing.py`.  It only
uses simple I/O and is ment to run in a terminal window or under 
`cmd.exe` on windows.  At present the data collection portion of the 
program and the magnetic moments calculations are not connected.

A terminal session follows with only an X axis sensor connected

```
$ ./mag_shield_testing.py -y "" -z "" 10 20 30 -t 10
Connecting to /dev/ttyUSB0 for X axis data.
VMR - Twinleaf VMR R12 N201 [2021-03-16/c7c589]
Use CTRL+C to quit early
Collecting ~10 seconds of data .........10.
X Axis: 204 rows collected
X Sensor, Row    0:   0.176 ( 12893.084,  14438.618,  29103.146)
          Row    1:   0.230 (  9663.970,  16602.135,  30022.584)
          Row    2:   0.282 (  4607.244,  18416.695,  31129.545)
          Row  204:  10.318 ( 13309.939,  21411.115, -28275.346)
Data formatter not yet implemented
CSV output function not yet implemented
PDF plotter function not yet implemented
```

Use the help option `-h` to get more info an running the program as it
currently stands.
```
mag_shield_testing.py -h
```

Current help text follows:
```
usage: mag_shield_testing.py [-h] [-r HZ] [-t SEC] [-x PORT] [-y PORT] [-z PORT]
                             [-n NAME] [-d DIR]
                             X_DIM Y_DIM Z_DIM

Collect magnetic sensor data from twinleaf sensors for a fixed time period and
output data and plot files.

positional arguments:
  X_DIM                 The X dimension of the test object in cm.
  Y_DIM                 The Y dimension of the test object in cm.
  Z_DIM                 The Z dimension of the test object in cm.

optional arguments:
  -h, --help            show this help message and exit
  -r HZ, --rate HZ      The number of data points to collect per sensor, per
                        second (TODO: UNUSED)
  -t SEC, --time SEC    The total number of seconds to collect data, defaults to
                        60.
  -x PORT, --x-port PORT
                        The communications port connected to the TwinLeaf Xaxis
                        magnetic sensor. Defaults to /dev/ttyUSB0 This string is
                        passed to tldevice.Device. To ignore data from this
                        sensor given an empty string as the portname (i.e. "").
  -y PORT, --y-port PORT
                        The communications port connected to the TwinLeaf Yaxis
                        magnetic sensor. Defaults to /dev/ttyUSB1 This string is
                        passed to tldevice.Device. To ignore data from this
                        sensor given an empty string as the portname (i.e. "").
  -z PORT, --z-port PORT
                        The communications port connected to the TwinLeaf Zaxis
                        magnetic sensor. Defaults to /dev/ttyUSB2 This string is
                        passed to tldevice.Device. To ignore data from this
                        sensor given an empty string as the portname (i.e. "").
  -n NAME, --out-name NAME
                        By default data and plots are written to mag_test_YYYY-
                        MM-DD_hh-mm-ss where YYYY-MM-DD is the current date, and
                        hh-mm-ss is the current time. Both a .csv and .pdf file
                        are written. Use this parameter to change the base name
                        of the file. File extensions are added outomatically.
  -d DIR, --out-dir DIR
                        Output files to folder/directory DIR instead of the
                        current location

Author: cole-dorman@uiowa.edu, chris-piker@uiowa.edu
Source: https://research-git.uiowa.edu/space-physics/tracers/magic/utilities
```

## Others
No other programs are currently defined

