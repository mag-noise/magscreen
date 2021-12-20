# Installing the Mag Screening Software

## Get Python 3.6 or above

The magnetic screening software is written in Python 3.  You'll need a functing python 3 interpreter.  The most common installation method varies by operating system as detailed below:

* Windows - Install version 3.6 or better from (here)[https://www.python.org/downloads/windows/].
  When doing so make sure that the python install directory is added to the system PATH.

* Linux - Python 3 is likely pre-installed on your system.  If not use the system package
  manager to add python3 and python3-pip.

* MacOS - Likely you will use the (Homebrew)[https://brew.sh/] packagae manager to
  install python.  Detailed instructions are TBD.

## Install Prequisites

Since you can't count of having administrator access to a computer, the following
proceedure assumes installation in a non-priviledged user account.  Eliminate the
argument `--user` to install the software below in a system wide manner.

Open a cmd.exe, or bash shell and issue the following commands to install the
library  packages needed by the magnetic cleanliness screening programs:
```bash
python3 -m pip install --user -U pip 
python3 -m pip install --user --prefer-binary -U scipy
python3 -m pip install --user --prefer-binary -U matplotlib
python3 -m pip install --user --prefer-binary -U tio
```
Not that this installs software *only* for the current user.  This step will have
to be repeated for each user that wishes to run the screening program.  

For reference the twinleaf software can be found at (https://github.com/twinleaf/tio-python)[https://github.com/twinleaf/tio-python].  The Twinleaf sensor software is in package `tio` 
that we installed above.

## Installing the Screening Programs

The screening program is a standard python package and may be installed using
`pip` as well.  Run the following command to download and install the vanscreen
package.
```bash
git clone https://research-git.uiowa.edu/space-physics/tracers/magic/vanscreen  # Get software
# Use your HawkID when prompted

pip install vanscreen   # Install software

mag_screen_gui          # Run the program
```
If you are working on the source code then you can run the software from the
source tree with out installation.  Example commands for doing so follow.
```bash
git clone https://research-git.uiowa.edu/space-physics/tracers/magic/vanscreen   # Get software

cd vanscreen  # Got to source directory

cmd.exe /c "set PYTHONPATH=. && python3 vanscreen/mag_screen.py -h"   # Windows
env PYTHONPATH=. python3 vanscreen/mag_screen.py -h                   # Linux/MacOS
```

### Custom Port Names (optional)

Twinleaf magnetometers are serial devices which are typically connected to the 
host computer via USB-to-Serial adapters.  After connecting a USB cable to the
host computer, end-user programs can communicate with the sensors via the standard
ports COM1, COM2, etc. (Windows) or /dev/ttyUSB0, /dev/ttyUSB1, etc. (Linux).  This
works well enough, but end-user programs do not know which comm port corresponds to
which physical sensor in your apparatus.  On Linux this confusion may be eliminated
by:

1. Using the converter boxes have been numbered (0 to 3) in permanent marker.

2. Installing the included [99-twinleaf-usb.rules](etc/99-twinleaf-usb.rules) udev file.

The `rules` file maps adapter names and serial numbers as follows:

   * Adapter 0 (Serial DT04H6OF) --> /dev/ttyTL0
   * Adapter 1 (Serial DT04H6OX) --> /dev/ttyTL1
   * Adapter 2 (Serial DT04H6NY) --> /dev/ttyTL2

To use the rules file:

```bash
sudo cp vanscreen/99-twinleaf-usb.rules /etc/udev/rules.d
sudo udevadm control --reload-rules
```

## Test installation

A basic test of the software is to make sure it starts and can print it's help text.  To do this open a new bash or cmd window and run:
```bash
mag_screen -h
```
If this runs and prints the command line help for the program then you are ready to plug in sensors and go on to the next step.

