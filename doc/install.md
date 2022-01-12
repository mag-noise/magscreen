# Installing the Mag Screening Software

## Get Python 3.6 or above

The magnetic screening software is written in Python 3.  You'll need a functing python 3 interpreter.  The most common installation method varies by operating system as detailed below:

* **Windows** - Install the latest 3.8.x series version from [python.org](https://python.org),
  at present thats [this version](https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe)
  Developers have reported that the version of python from python.org works better then
  the version from the Microsoft store.  **Do not install for all users** unless
  you *know what you are doing*.  This will cause a split `PATH` which is a pain to deal
  with on Windows since the system `PATH` folders always proceed user `PATH` folders.

  When picking the install directory choose something sane like:
  ```batch
  C:\Users\USERNAME\python38
  ```
  to avoid very long paths and folder names with spaces.  Windows has a 255 charater path
  limit and script arguments split on spaces, no need to tempt fate.

* **Linux** - Python 3 is likely pre-installed on your system.  If not use the system package
  manager to add python3 and python3-pip.

* **MacOS** - Likely you will use the [Homebrew](https://brew.sh/) package manager to
  install python.  Detailed instructions are TBD.

## Install Prequisites

Since you can't count of having administrator access to a computer, the following
proceedure assumes installation in a non-priviledged user account.  Eliminate the
argument `--user` to install the software below in a system wide manner.

For **Windows** open a cmd.exe and issue the following commands to install
the library packages needed by the magnetic screening programs:
```batch
python -m pip install --upgrade pip
python -m pip install --prefer-binary --upgrade scipy
python -m pip install --prefer-binary --upgrade matplotlib
python -m pip install --prefer-binary --upgrade tio
```

The equivalent commands for the system python on **Linux** woud be:
```bash
python3 -m pip install --user --upgrade pip
python3 -m pip install --user --upgrade scipy
python3 -m pip install --user --upgrade matplotlib
python3 -m pip install --user --upgrade tio
```
Both command stets installs software *only* for the current user, since on  
Windows python is installed in the user home directory, not a system location.

For reference the twinleaf software can be found at [https://github.com/twinleaf/tio-python](https://github.com/twinleaf/tio-python). The Twinleaf sensor software is in package `tio` 
that we installed above.

## Install the Screening Programs

The screening program is a standard python package and may be installed using
`pip` as well.  Run the following command to download and install the vanscreen
package.
```bash
git clone https://research-git.uiowa.edu/space-physics/tracers/magic/vanscreen  # Get software
# Use your HawkID when prompted
```
You can test the software from the source code directory without installing in.
This is handy for testing software changes. Example commands for doing so follow.
```bash
git clone https://research-git.uiowa.edu/space-physics/tracers/magic/vanscreen   # Get software
cd vanscreen                                                           # Go to source directory

# Assuming sensors placed at 11, 15 & 20 cm
set PYTHONPATH=. && python vanscreen/mag_screen.py -r 11,15,20 test_object  # Windows
env PYTHONPATH=. python3 vanscreen/mag_screen.py -r 11,15,20 test_object    # Linux/MacOS
```

To install the software so thats available outside the source directory:
```bash
pip install vanscreen  # Install software
mag_screen -h          # A basic test, no sensors necessary
```


