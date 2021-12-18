# Magnetic Cleanliness Screnning

Authors: Cole Doorman, Chris Piker

## Summary

*short summary of purpose of the software here*

The test begins by users placing an object to be magnetically screened on the currently-still plate, then turning the stream of air on to rotate it. The users then input the name of the object into a GUI and hit the 'screen' button. The data will be collected by three Twinleaf VMR magnetometers at three different distances away using Python 3. The object being screened has an arbitrary dipole moment which as rotated, will periodically be positioned at a maxima and minima from the sensor. Over a set time (60 seconds per magnetometer, the magnetometers will measure the sinusoidal x, y, z functions of the magnetic field B from the object. Using Welch's function, we will collapse the sinusoidal field components into a power spectral density, which when taken the square root of, will give us x, y, z scalar values of the magnetic field B. After the data collection ceases, the user will turn off the air rotating the plate.

The Bx, By, Bz data from the three Twinleaf VMRs (9 total points) is then put into a Python 3 function to project a dipole moment and stray field. Using the law of cosines, we can find the angle of the magnetic field and subsequently dipole moment relative to the z-axis. Knowing this angle, we can project these values into their most aggressive orientation (directly parallel with the z-axis), giving us 6 total data points. Each magnetometer projects an aggressive dipole moment and an aggressive magnetic field for its respective distance. These data points are then plot and best-fit to a function 1/distance^3. The best fit taken is the new dipole moment with error being calculated using the SciPy library curve_fit function. Using the calculated best-fit aggressive dipole, we calculate the stray field away at one meters. The function finds 3 things:(1) The best fit dipole moment from the object's data, (2) The stray field in nanoTesla 1 meter away, and (3) an indication the object has passed the test if its dipole moment is <.05, fail if the dipole moment is >.05, and a caution if the dipole moment is .0475 < m < .05.

The data from this function should be organized and saved into a .csv file. There should be four columns. (1) Object name, (2) Dipole moment (A\*m^2), (3) Stray field 1 meter away (nT), (4) Pass/Fail/Caution? The best fit graphs for each object need to be organized and saved into a .pdf file.

## Apparatus

The sensors are known to the program as `vmrA`, `vmrB` and `vmrC`.  Arrange these as
specifed in the image below.


Screening uses the program mag_screen.py.  To install the program and it's prerequists
see the [installation instructions](install.md).  If you are not able to use the labeled
USB <-> Differental Serial boxes, then the `/etc/udev/rules.d/99-twinleaf-usb.rules` file
will need to be updated with the serial number of a new adaptor. 

## Screening Procedure

1. Open a shell window and type `python3 mag_screen OBJECT_ID` and do *not* press enter. 
   Here `OBJECT_ID` is a name or other identifier by which the object's data will be tracked.

2. Make sure the rotating plate is at rest. Then place the object to be screened onto the plate.

3. Turn the nitrogen gas relase value until the plate spins at about one revolution per **XXX** seconds.

4. Once the rotator plate is moving, hit enter in the shell to run the program.  This will
   output data to a CSV file and a PDF.  One containing test results the other containing
   best fit plots.

5. Turn off the compressed air flow.

6. Remove the object from the plate

## Output Archiving

*State where the output data are saved/tracked in the larger context of the TRACERS development program*

## Calculations




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