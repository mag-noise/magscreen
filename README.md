# Magnetic Cleanliness Screening via Constant Rotation

*Source Authors: Chris Piker, Cole Dorman*;  *Apparatus & Measurment Concept: David Miles*

Magnetic cleanliness screening is the process of determining the magnetic
properties of various parts before they are added to instrumentation that
measures magnetic fields.  The properties of interest are an object's dipole 
moment and the stray field, a magnetic field an object generates that interferes 
with other magnetic sensors on a spacecraft.  The stray field of an object is
determined not just by the magnitude of an object's dipole moment, but it's 
orientation relative to regions of interest.  To adequetly assume an object will 
not interfere with other magnetic sensors, its stray field must be under a certain 
threshold.  This assumes the magnitude of a magnetic dipole moment is under a
certain threshold, in the dipole's most aggressive orientation.

Typically a full field characterization is unnecessary.
A simple pass/fail measurement of the worst possible magnetic field distortion
created by an object is typically good enough for instrument construction
purposes.  This software characterizes whether objects have suitably low
stray magnetic fields at a certain distance by calculating the magnitude of 
magnetic dipole moment in an object, and measuring the stray field the object
would generate when the dipole moment is in its most aggressive orientation.

This software is intended for use with an apparatus that rotates
the part to be screened at a constant rate while the 3-axis magnetic field
is regularly sampled at 2-N locations in space near the part.  *Magscreen* 
was written using the [TwinLeaf VMR](https://github.com/twinleaf/tio-python) 
sensors for thier simple serial interface, though it easily could be adapted
for other equipment.

For further explanation and analysis, the authors refer you to:
Dorman, C. J., Piker, C., & Miles, D. M. (2024). 
Automated static magnetic cleanliness screening for the TRACERS small-satellite mission. 
Geoscientific Instrumentation, Methods and Data Systems, 13(1), 43-50.

Or contact:
david-miles@uiowa.edu

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
 

## Calculations

The data will be collected by three Twinleaf VMR magnetometers positioned at three 
different distances from the object using the 'mag_screen' program. The object being 
screened has an unknown dipole moment. As the object rotates, its internal magnetic 
field periodically aligns at maximum and minimum positions relative to each sensor. 
Over several rotations, the magnetometers record sinusoidal Bx, By, and Bz components 
of the magnetic field. Using Welch's method, these sinusoidal field components are 
converted into a power spectral density. Taking the square root of the spectral density 
provides the scalar Bx, By, and Bz values of the magnetic field.

The Bx, By, and Bz magnitudes from each sensor are then used to determine the orientation 
of the total magnetic field and, subsequently, the object's dipole moment relative to 
the z-axes of the Twinleaf VMR sensors. With the dipole moment's orientation and the total 
magnetic field magnitude measured at various distances, each sensor calculates the object's 
dipole moment magnitude. The strongest possible magnetic field strength at each VMR's 
distance from the rotating plate's origin is derived from the dipole moment magnitude. 
These values are fitted to a function that decreases proportionally to the inverse cube 
of the distance. From this fit, a best-fit dipole moment for the object is calculated.

The program outputs:
1. The best-fit dipole moment derived from the object's data.
2. An indication of whether the object "passes" (if its dipole moment is < 0.05 [A m^-2]),
   "fails" (if the dipole moment is > 0.05 [A m^-2]), or receives a "caution" 
   (if the dipole moment is 0.0475 < m < 0.05 [A m^-2]).
3. The stray magnetic field in nanotesla measured 1 meter away.

Passing values correspond to an object producing a magnetic field magnitude of less than 
100 nT when measured 1 meter away in its most aggressive dipole orientation.


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
