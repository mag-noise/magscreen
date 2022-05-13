# Magnetic Cleanliness Screening via Constant Rotation

*Source Authors: Chris Piker, Cole Dorman*;  *Apparatus & Measurment Concept: David Miles*

Magnetic cleanliness screening is the process of determining the magnetic
properties of various parts before they are added to instrumentation that
measures magnetic fields.  The properties of interest are the stray field
and dipole moment.  Typically a full field characterization is unnecessary.
A simple pass/fail measurement of the worst possible magnetic field distortion
created by an object is typically good enough for instrument construction
purposes.  This software is intended for use with an apparatus that rotates
the part to be screened at a constant rate while the 3-axis magnetic field
is regularly sampled at 2-N locations in space near the part.  *Magscreen* 
was written using the [TwinLeaf VMR](https://github.com/twinleaf/tio-python) 
sensors for thier simple serial interface, though it easily could be adapted
for other equipment.


## Screening Apparatus

The following equipment is needed:

1. A cylinder of dry nitrogen.  This will be used to rotate the part
   without electric motors.

2. A turntable with paddles that intercept the escaping air.

3. Three Twinleaf VMR sensors.

4. The three labeled Twinleaf USB to differential serial UARTs 

5. A PC with this software installed.  For installation instructions
   see the file [doc/install.md](doc/install.md)

Sensors are arrange around the turntable as depicted below.

![Sensor Setup](doc/mag_screen_apperatus.jpg)

Each differential serial <=> USB adapter has been labeled with it's internal serial
number.  The screening software is able to read adapter numbers.  It uses these values
to relate input data to sensor distances from the center of the object.  The default
distances and serial numbers are given below.  If your setup differs from this chart,
be sure to notify the screening program via it's command line arguments.

| UART USB Serial | Default Radius (cm)|
| ----------------| ------------------ |
| DT04H6OF        |         9          |
| DT04H6OX        |        11          |
| DT04H6NY        |        15          |

To make sure the software has been installed, start a cmd.exe or bash shell and 
enter the following command:
```bash
mag_screen -h
```

If this command prints program help text, then your software environment is setup.
Otherwise see the [install.md](doc/install.md) document.

## Screening Procedure

1. Open a shell window and type `python3 mag_screen OBJECT_ID` and do *not* press enter. 
   Here `OBJECT_ID` is a name or other identifier by which the object's data will be tracked.

2. Make sure the rotating plate is at rest. Then place the object to be screened onto the plate.

3. Setup the screening command, similar to below, but don't hit ENTER yet.
```bash
mag_screen "PartName"                               # Example: Using all defaults
mag_screen -r 8.5,11,13.5 "PartName"                # Example: non-default sensor distances
mag_screen -u DT04H6OY,DT04H6OF,DT04H6M8 "PartName" # Example: non-default UART serial nums
mag_screen -r 10,15 -u DT04H6OF,DT04H6OX "PartName" # Example: only two sensors
```

4. Turn the nitrogen gas relase value until the plate spins at about one revolution per 2 to 8 seconds.

5. Once the rotator plate is moving, hit ENTER in the shell to run the program.  This will
   output data to a CSV file and a PDF.  One containing test results the other containing
   best fit plots.

5. Turn off the compressed air flow.

6. Remove the object from the plate

## Output Archiving and Utility Programs

Example program output files are given in the table below.

| Step                | Links                                    |
| ------------------- | ---------------------------------------- |
| Raw data collection | [screwdriver.csv](test/screwdriver.csv)  |
| Single test plots   | [screwdriver.p1.png](test/screwdriver.p1.png)  [screwdriver.p1.png](test/screwdriver.p1.png) [screwdriver.pdf](test/screwdriver.pdf)      |
| Summary spreadsheet | [summary.csv](test/summary.csv)          |

Though the screening program reads raw data, generates plots, and saves an experimental
summary record, only raw screening data need be captured during a test.  The following 
utility programs are also provided:
```bash
mag_screen_plot  # Reads raw *.csv data and generates single test summary plots
mag_screen_sum   # Reads raw *.csv data and updates a running summary of part test data.
```

After data are collected, files should be moved to a long term storage location.  

## Calculations

The data will be collected by three Twinleaf VMR magnetometers at three different
distances away using the mag_screen program. The object being screened has an
arbitrary dipole moment.  As the object is rotated it's internal field will 
periodically be positioned at a maxima and minima from each sensor.  Over the course
of a few rotations the magnetometers will measure the sinusoidal x, y, z functions
of the magnetic field B from the object. Using Welch's method, we will collapse the
sinusoidal field components into a power spectral density, which when taken the
square root of, will give us x, y, z scalar values of the magnetic field B.

The Bx, By, Bz data from each sensor (now 9 total points) is then put into a Python 3
function to project a dipole moment and stray field.  Using the law of cosines, we can
find the angle of the magnetic field and subsequently dipole moment relative to the
z-axis. Knowing this angle, we can project these values into their most aggressive
orientation (directly parallel with the z-axis), giving us 6 total data points. Each
magnetometer projects an aggressive dipole moment and an aggressive magnetic field for
its respective distance. These data points are then plot and best-fit to a function 
`1/distance^3`. The best fit taken is the new dipole moment with error being calculated
using the SciPy library curve_fit function. Using the calculated best-fit aggressive
dipole, we calculate the stray field away at one meters. The function finds 3 things:

	1. the best fit dipole moment from the object's data, 
	2. the stray field in nanoTesla 1 meter away, and,
	3. an indication the object has passed the test.

If its dipole moment is <.05, fail if the dipole moment is >.05, and a caution if the
dipole moment is .0475 < m < .05.
