# Installing the Mag Screening Software

## Get Python 3.6 or above

The magnetic screening software is written in Python 3.  You'll need a functing python 3 interpreter.  The most common installation method varies by operating system as detailed below:

* Windows - Install version 3.6 or better from (here)[https://www.python.org/downloads/windows/].
  When doing so make sure that the python install directory is added to the system PATH.

* Linux - Python 3 is likely pre-installed on your system.  If not use the system package
  manager to add python3 and python3-pip.

* MacOS - Likely you will use the (Homebrew)[https://brew.sh/] packagae manager to
  install python.  Detailed instructions are TBD.

## Install matplotlib

Open a cmd.exe shell and issue the following commands to install matplotlib:
```batch
python3 -m pip install -U pip 
python3 -m pip install --prefer-binary -U scipy
python3 -m pip install --prefer-binary -U matplotlib   
```
Not that this installs matplotlib *only* for the current user.  This step will have
to be repeated for each user that wishes to run the screening program

On newer versions of Linux (CentOS 8+, Ubuntu 18+) the package manager can be 
used to install matplotlib:
```bash
dnf install python3-matplotlib     # Fedora, CentOS 8
apt-get install python3-matplotlib # Debian, Ubuntu
```

If there are no pre-made matplotlib packages for your system, you can have PIP 
install it into your home directory.  
```bash
python3 -m pip install --user -U scipy 
python3 -m pip install --user -U pip 
python3 -m pip install --user -U matplotlib
```
As mentioned above, this will require re-running pip for each user account that wishes to run the mag screen ing progam.


## Install the TwinLeaf I/O Package

The twinleaf python software can be found at (https://github.com/twinleaf/tio-python)[https://github.com/twinleaf/tio-python].  But premade packages are available via pip:

```bash
python3 -m pip install --user -U tio
```


## Installing the Screening Program

The screening program contains a standard `setup.py` distutils install file.  
To install the program first clone the sources from gitlab, then run the setup.py
file.  This works the same on Windows, Linux or MacOS
```bash
git clone https://research-git.uiowa.edu/space-physics/tracers/magic/utilities
# Use your HawkID when prompted
cd mag_screen
python3 setup.py install
```

## Test installation

A basic test of the software is to make sure it starts and can print it's help text.  To do this open an new bash or cmd.exe window and run:
```bash
mag_screen -h
```
If this runs and prints the command line help for the program then you are ready to plug in sensors and go on to the next step.
