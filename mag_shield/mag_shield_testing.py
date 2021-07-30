#!/usr/bin/env python3
"""
Collects data from twinleaf sensors for magnetic cleanliness testing.
"""
import sys           # System stuff
import os
import argparse    
import signal
import threading     # Mostly waiting on I/O so simple threads are okay
import time          # if the data rate needs to go up significantly we
import datetime      # will need to rewrite using the multiprocess module.

# Math stuff
import numpy as np   
from scipy.constants import pi
from scipy.constants import mu_0
from scipy.optimize import curve_fit
import scipy.stats as stats

# Output stuff
if (sys.platform != 'win32') and ('DISPLAY' not in os.environ):
    # Work around matplotlib bug on linux, it depends on the DISPLAY
    # environment variable but that's not always set anymore.
    os.environ['DISPLAY'] = ':0'
import matplotlib.pyplot as plt 

# Global variable and signal handler to halt main data collection loop
g_collect = False
g_quit    = False

def setQuit(signal, frame):
    """Signal handler for CTRL+C from the keyboard"""
    global g_quit
    g_quit = True      # Indicates early exit

perr = sys.stderr.write  # shorten a long function name


class VertFormatter(argparse.HelpFormatter):
    """Allow for manual line breaks in description and epilog blocks of help text.
    To insert a line break use the vertical tab (\\v) character into a text block."""
    def _fill_text(self, text, width, indent):
        import textwrap
        l = []
        for s in text.split('\v'):
            s = self._whitespace_matcher.sub(' ', s).strip()
            l.append(textwrap.fill(
                s, width, initial_indent=indent, subsequent_indent=indent
            ))
        return '\n'.join(l)

class Collector(threading.Thread):
    """Gather data from a single serial port and generate an list of
    data values and associated time values"""
    def __init__(self, tlmodule, axis, port, time0):
        threading.Thread.__init__(self)
        self.axis = axis
        self.port = port
        self.time0 = time0
        self.time = []
        self.raw_data = []
        perr('Connecting to %s for %s axis data.\n'%(port, axis))
        self.device = tlmodule.Device(port)
        
        # Save off the names of the data columns
        self.columns = self.device._tio.protocol.columns
    
    def run(self):
        global g_quit, g_collect
        for row in self.device.data.stream_iter():
            if g_quit or (not g_collect):
                break
            self.time.append(time.time() - self.time0)
            self.raw_data.append(row)
            
    def mag_vectors(self):
        """Output an [N x 3] array of the mag vectors"""
        vecs = np.zeros([len(self.raw_data), 3])
        iX = self.columns.index('vector.x')
        iY = self.columns.index('vector.y')
        iZ = self.columns.index('vector.z')
        
        # TODO: Vectorize this
        for i in range(len(self.raw_data)):
            vecs[i,0] = self.raw_data[i][iX]
            vecs[i,1] = self.raw_data[i][iY]
            vecs[i,2] = self.raw_data[i][iZ]
        
        return vecs
        
    def times(self):
        """Output an [N] length array of the time points"""
        return np.array(self.time)
        
    def time0(self):
        """Get time0 as an ISO-8601 string"""
        dt = datetime.datetime.utcfromtimestamp(self.time0)
        return "%04d-%02d-%02dT%02d:%02d:%02d"%(
            dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second
        )

            
def setDone():
    """Function triggered by a timer alarm that is setup in main()"""
    global g_collect
    g_collect = False  # Normal exit, g_quit stays false


class Display(threading.Thread):
    """This is a simple aliveness printer.  It outputs a single . once a 
    second to stdout.  You could customize it to do more interesting things
    if desire.
    """
    def __init__(self, prefix=""):
        threading.Thread.__init__(self)
        self.prefix = prefix
    
    def run(self):
        # Write dot's to screen so folks know the program isn't dead.  For a
        # fancier display see:
        # https://github.com/twinleaf/tio-python/blob/master/examples/tio-monitor.py
        # specifically the update() function.
        num_dots = 0
        while not g_quit and g_collect:
            if num_dots == 0: perr(self.prefix)
 
            time.sleep(1) # Sleep for 1 second           
            if num_dots % 10 == 9:
                perr('%d'%(num_dots+1))
            else:
                perr('.')
            sys.stderr.flush()
            num_dots += 1

# ############################################################################ #
# Data Processing #

def func(r, m): 
    """equation of a magnetic field from a dipole moment"""
    return ((mu_0 * m) / (2*pi * r**3))

def ratio(magnetometer_distance, distance, object_length):
    """
    Due to the Bx field and Bz field magnetometer being farther away from the object than the By field
    magnetometer, a ratio is needed to project the 3 B field components to the same place to accurately 
    measure magntitude and direction
    """
    return ((magnetometer_distance + distance + object_length/2 )**3 / (distance + object_length/2)**3)

def rms(x, y, z):
    """root mean squared function, eventually used to find magnitude of B"""
    return np.sqrt(x**2 + y**2 + z**2)

def angle(vector, B1, B2, B3):
    """function finding angle from dot product of vectors"""
    z = np.array([0, 0, 1])
    return np.arccos( np.dot(vector, z) / np.sqrt(B1**2 + B2**2 + B3**2) )

def dipole_moment(object_length, distance, B, angle):
    """General formula for finding dipole moment based off vector's magnitude and direction"""
    return (4*pi*(object_length/2+distance)**3*B) / (mu_0*(2*np.cos(angle)**2 - np.sin(angle)**2))

def fit(length_x, length_y, length_z, x, y, z):
    '''
    The main function used to magnetic screen. User will enter size of arbitrary
    length, width, and height in centimeters, then record the magneitc fields in nanoTelsa
    from the object's different orientations at three (3) different distances. The 
    function finds the magnitude and direction of the object's dipole moment, then 
    calculates a best fit. Using this best fit, the function calculates the stray field 
    at one (1) meter away assuming the strongest possible dipole orientation. If the 
    stray field is too large, the object fails the test. If he stray field is below the 
    required threshold but is within the top 95%, it passes with caution.    
    '''    
    distance = np.array([20, 25, 27])*1e-2 #three distances object is being measured at, converted to meters
    
    length_meters = np.array([length_x, length_y, length_z])*1e-2 #converting length of objects to meters
    
    #converting the input magnetic fields into Tesla
    B_Tesla = np.array([
        x[0,0]*ratio(.01025, distance[0], length_meters[0]), y[0,0], z[0,0]*ratio(.00475, distance[0], length_meters[0]), 
        x[0,1]*ratio(.01025, distance[0], length_meters[1]), y[0,1], z[0,1]*ratio(.00475, distance[0], length_meters[1]),
        x[0,2]*ratio(.01025, distance[0], length_meters[2]), y[1,2], z[1,2]*ratio(.00475, distance[0], length_meters[2]),
        
        x[1,0]*ratio(.01025, distance[1], length_meters[0]), y[1,0], z[1,0]*ratio(.00475, distance[1], length_meters[0]),
        x[1,1]*ratio(.01025, distance[1], length_meters[1]), y[1,1], z[1,1]*ratio(.00475, distance[1], length_meters[1]),
        x[1,2]*ratio(.01025, distance[1], length_meters[2]), y[1,2], z[1,2]*ratio(.00475, distance[1], length_meters[2]),
         
        x[2,0]*ratio(.01025, distance[2], length_meters[0]), y[2,0], z[2,0]*ratio(.00475, distance[2], length_meters[0]),
        x[2,1]*ratio(.01025, distance[2], length_meters[1]), y[2,1], z[2,1]*ratio(.00475, distance[2], length_meters[1]),
        x[2,2]*ratio(.01025, distance[2], length_meters[2]), y[2,2], z[2,2]*ratio(.00475, distance[2], length_meters[2])
    ])*1e-9
    
    #Organizing vectors of Bx, By, Bz components from 3 different orientations at 3 different distances
    # Hint: complex index calculations in loop below could be shortened if a 3-D array were used here.
    #       The axes would be row, column, component, i.e. B_Tesla[row,col,comp]
    vector = np.array([
        np.array([B_Tesla[ 0], B_Tesla[ 1], B_Tesla[ 2]]), 
        np.array([B_Tesla[ 3], B_Tesla[ 4], B_Tesla[ 5]]), 
        np.array([B_Tesla[ 6], B_Tesla[ 7], B_Tesla[ 8]]),
        np.array([B_Tesla[ 9], B_Tesla[10], B_Tesla[11]]), 
        np.array([B_Tesla[12], B_Tesla[13], B_Tesla[14]]),
        np.array([B_Tesla[15], B_Tesla[16], B_Tesla[17]]), 
        np.array([B_Tesla[18], B_Tesla[19], B_Tesla[20]]),
        np.array([B_Tesla[21], B_Tesla[22], B_Tesla[23]]), 
        np.array([B_Tesla[24], B_Tesla[25], B_Tesla[26]])
    ])
    
    #finding dipole moment from each orientation at each distance, totaling 9 different dipole moments
    #m11 = dipole_moment(length_meters[0], distance[0], rms(B_Tesla[0], B_Tesla[1], B_Tesla[2]), angle(vector[0], B_Tesla[0], B_Tesla[1], B_Tesla[2]))
    #m12 = dipole_moment(length_meters[1], distance[0], rms(B_Tesla[3], B_Tesla[4], B_Tesla[5]), angle(vector[1], B_Tesla[3], B_Tesla[4], B_Tesla[5]))
    #m13 = dipole_moment(length_meters[2], distance[0], rms(B_Tesla[6], B_Tesla[7], B_Tesla[8]), angle(vector[2], B_Tesla[6], B_Tesla[7], B_Tesla[8]))
    #m21 = dipole_moment(length_meters[0], distance[1], rms(B_Tesla[9], B_Tesla[10], B_Tesla[11]), angle(vector[3], B_Tesla[9], B_Tesla[10], B_Tesla[11]))
    #m22 = dipole_moment(length_meters[1], distance[1], rms(B_Tesla[12], B_Tesla[13], B_Tesla[14]), angle(vector[4], B_Tesla[12], B_Tesla[13], B_Tesla[14]))
    #m23 = dipole_moment(length_meters[2], distance[1], rms(B_Tesla[15], B_Tesla[16], B_Tesla[17]), angle(vector[5], B_Tesla[15], B_Tesla[16], B_Tesla[17]))
    #m31 = dipole_moment(length_meters[0], distance[2], rms(B_Tesla[18], B_Tesla[19], B_Tesla[20]), angle(vector[6], B_Tesla[18], B_Tesla[19], B_Tesla[20]))
    #m32 = dipole_moment(length_meters[1], distance[2], rms(B_Tesla[21], B_Tesla[22], B_Tesla[23]), angle(vector[7], B_Tesla[21], B_Tesla[22], B_Tesla[23]))
    #m33 = dipole_moment(length_meters[2], distance[2], rms(B_Tesla[24], B_Tesla[25], B_Tesla[26]), angle(vector[8], B_Tesla[24], B_Tesla[25], B_Tesla[26]))
    
    # Should be equvalent to text above but double check
    m = np.zeros((3,3))
    
    for row in range(3):
        for col in range(3):
            m[row,col] = dipole_moment(
                length_meters[col], distance[row],
                rms( B_Tesla[ row*9 + col*3], B_Tesla[row*9 + col*3 + 1], B_Tesla[row*9 + col*3 + 2]),
                angle( vector[row*3 + col],   B_Tesla[row*9 + col*3 + 1], B_Tesla[row*9 + col*3 + 2])
            )
            
    m_observed = abs(np.array([m[1,1], m[1,2], m[1,3], m[2,1], m[2,2], m[2,3], m[3,1], m[3,2], m[3,3] ]))

    
    #x-axis is distances of from magnetometer plus center of object
    # Hint: Could use vectorized math operations here to make this a one-liner 
    #       i.e. xdata = distance + length_meters/2
    #       which would implicitly loop over all similar indicies.
    xdata = np.array([
        distance[0]+length_meters[0]/2, distance[0]+length_meters[1]/2, distance[0]+length_meters[2]/2,
        distance[1]+length_meters[0]/2, distance[1]+length_meters[1]/2, distance[1]+length_meters[2]/2, 
        distance[2]+length_meters[0]/2, distance[2]+length_meters[1]/2, distance[2]+length_meters[2]/2
    ])
    ydata = func(xdata, m_observed) #y-axis is mangetic fields from strongest possible dipole orientation
    plt.plot(xdata*1e2, ydata*1e9, 'bo',label="observed data") #plotting measured strongest magnetic field vs. distance
    
    plt.xlabel("distance (centimeters)")
    plt.ylabel("magnetic field (nanoTesla)")
    popt, pcov = curve_fit(func, xdata, ydata) #curve fitting best fit of the nine magnetic fields measured
    plt.plot(xdata*1e2, func(xdata, *popt)*1e9, 'r-',label='best fit') #plotting best fit line
    plt.legend()
    plt.show()
    
    m_err = np.sqrt(np.diag(pcov)) #estimated covariance of popt, aka one standard deviation errors on the parameters
    
    #Chi-squared calculated from values deviated from the expected
    print("chi-squared test statistic: %.3f" %stats.chisquare(f_obs=m_observed, f_exp=popt)[0]) 
    
    #p-value calculated from chi-squared
    print("p-value: %.3f" %stats.chisquare(f_obs=m_observed, f_exp=popt)[1])
    
    stray_B = (mu_0 * popt) / (2*pi*1**3) #calculating stray field at 1 meter from strongest orientation best-fit magnetic dipole moment
    
    print("magnetic dipole moment m = %.5f" %popt, "+/- %.4f" %m_err) #printing best fit magnetic dipole moment
    print("stray field B = %.4f nT" %(stray_B*1e9), "+/- %.4f" %(((mu_0 * m_err) / (4*pi))*1e9)) #printing stray magnetic field at 1 meter

    # If best fit dipole moment over .1 mA^2, object does not pass test. 
    # If m is under 95% of .1, it passes completely. 
    # If m is between .1 and 95% of .1, it should be used with caution    
    if popt+m_err > .05: 
        print("-> FAIL")
    elif popt+m_err < (.95*.05):
        print("-> PASS")
    else:
        print("-> CAUTION")


def get_moments(collectors, obj_dims):
    """Convert the raw data stream off a TwinLeaf mag sensor set into
    a dictionary of values that contains information we care about.  Also
    folds in the object measurements.
    
    args:
        collectors: A list of Collector objects that presumably have
                    collected data from a TwinLeaf sensor. 
        obj_dims (array 1x3): The test objects dimensions in centimeters
    """    
    data = {'DIMS':obj_dims}
    
    for collector in collectors:
        axis = collector.axis
    
        perr('%s Axis: %d rows collected\n'%(collector.axis, len(collector.raw_data)))
        
        # Cole: Make calls to fit() and the other function above here.  Then 
        # Gather all output into a dictionary object and return it, for now
        # I'm just outputting the raw data.  Feel free to ajdust the output 
        # data dictionary to have whatever structure you deem suitable.
        data[axis] = {'T':collector.times(), 'B':collector.mag_vectors()}
    
        T = data[axis]['T']
        B = data[axis]['B']
    
        perr('%s Sensor, Row    0: %7.3f (%10.3f, %10.3f, %10.3f)\n'%(
            axis, T[0], B[ 0,0], B[ 0,1], B[ 0,2]
        ))
        perr('          Row    1: %7.3f (%10.3f, %10.3f, %10.3f)\n'%(
            T[1], B[1,0], B[1,1], B[1,2]
        ))
        perr('          Row    2: %7.3f (%10.3f, %10.3f, %10.3f)\n'%(
            T[2], B[2,0], B[2,1], B[2,2]
        ))
        perr('          Row %4d: %7.3f (%10.3f, %10.3f, %10.3f)\n'%(
            len(T), T[-1], B[-1,0], B[-1,1], B[-1,2]
        ))
        
    perr('Data formatter not yet implemented\n')
    return data

# Data Processing #
# ############################################################################ #

# ############################################################################ #
# Data Output #
def write_csv(directory, name, data):
    """Write formatted data to a CSV file for later analysis
    
    args:
        directory (str): The directory to write to, if None use current location.
        name (str): The filename to write, if None generate name based of current
            timestamp
        data (dict): The data dictionary as created by get_moments above
    """
    
    perr('CSV output function not yet implemented\n')
    

def write_pdf(directory, name, data):
    """Generate plots using matplotlib of formatted data and save to a PDF file
    
    args:
        directory (str): The directory to write to, if None use current location.
        name (str): The filename to write, if None generate name based of current
            timestamp
        data (dict): The data dictionary as created by get_moments above
    """
    
    perr('PDF plotter function not yet implemented\n')

# Data Output #
# ############################################################################ #

def main(argv):
    """Program entry point, see argparse setup below or run with -h for overall
    scope and usage information.

    Returns:
        A standard integer success or fail code suitable for return to
        the calling shell. 0 = success, non-zero = various error conditions
    """
    global g_collect, g_quit
    
    psr = argparse.ArgumentParser(formatter_class=VertFormatter)
    psr.description = '''\
        Collect magnetic sensor data from twinleaf sensors for a fixed time
        period and output data and plot files.'''
    psr.epilog = '''\
    Author: cole-dorman@uiowa.edu, chris-piker@uiowa.edu\v
    Source: https://research-git.uiowa.edu/space-physics/tracers/magic/utilities
    '''
    
    # By tradition, optional command line parameters are first...
    psr.add_argument(
        '-r', '--rate', dest='sample_hz', metavar='HZ', type=float, default=20.0,
        help='The number of data points to collect per sensor, per second '+\
        '(TODO: UNUSED)'
    )
    
    psr.add_argument(
        '-t', '--time', dest='duration', metavar='SEC', type=int, default=60,
		  help='The total number of seconds to collect data, defaults to 60.'
    )
         
    defs = {'name':('X','Y','Z'), 
        'short':('-x','-y','-z'), 'long':('--x-port','--y-port','--z-port'),
        'unix':('/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2'),
        'win':('COM0','COM1','COM2')
    }
    
    for i in range(3):
        if sys.platform == 'win32': port = defs['win'][i]
        else: port = defs['unix'][i]
        
        psr.add_argument(
            defs['short'][i], defs['long'][i], dest='port%s'%defs['name'][i],
            metavar='PORT', type=str, default=port,
            help='The communications port connected to the TwinLeaf ' +\
            defs['name'][i] + 'axis magnetic sensor.  Defaults to ' +\
            port + ' This string is passed to tldevice.Device.  To '+\
            'ignore data from this sensor given an empty string as '+\
            'the portname (i.e. "").'
        )
    
    psr.add_argument(
        '-n', '--out-name', dest='out_file', metavar='NAME', type=str,
        default=None, help='By default data and plots are written to '+\
        'mag_test_YYYY-MM-DD_hh-mm-ss where YYYY-MM-DD is the current date, '+\
        'and hh-mm-ss is the current time.  Both a .csv and .pdf file are '+\
        'written.  Use this parameter to change the base name of the file. '+\
        'File extensions are added outomatically. '
    )
    
    psr.add_argument(
        '-d', '--out-dir', dest='out_dir', metavar='DIR', type=str,
        default=None, help='Output files to folder/directory DIR instead of '+\
        'the current location'
    )
    
    # ... and positional parameters follow
    psr.add_argument("X_DIM", help="The X dimension of the test object in cm.")
    psr.add_argument("Y_DIM", help="The Y dimension of the test object in cm.")
    psr.add_argument("Z_DIM", help="The Z dimension of the test object in cm.")
    
    opts = psr.parse_args(argv[1:])
    
    # Delay importing the twin leaf libraries so that help text is available
    # even if the required python modules are not installed
    try:
        import tldevice
    except ImportError as exc:
        perr('%s\nGo to https://github.com/twinleaf/tio-python install instructions\n'%str(exc))
        return 3 # An error return value
        
    # Set user interup handlers in case user wants to quite early.
    signal.signal(signal.SIGINT, setQuit)
    signal.signal(signal.SIGTERM, setQuit)
    
    # Since SIGALRM isn't available on Windows, spawn a thread to countdown to
    # the end of the data collection period, check user supplied time
    if opts.duration < 1 or opts.duration > 60*60:
        perr('Test duration must be between 1 second and 1 hour\n')
        return 7
    
    time0 = time.time()  # Current unix time in floating point seconds
    
    g_collect = True   # Global stop flags
    g_quit = False
    
    # Create one data collection thread per sensor
    collectors = []
    if len(opts.portX)>0: collectors.append( Collector(tldevice, 'X', opts.portX, time0) )
    if len(opts.portY)>0: collectors.append( Collector(tldevice, 'Y', opts.portY, time0) )
    if len(opts.portZ)>0: collectors.append( Collector(tldevice, 'Z', opts.portZ, time0) )
    
    if len(collectors) == 0:
        perr('No data collection ports specified, successfully did nothing.\n')
        return 0
    
    # Create a display output thread
    perr("Use CTRL+C to quit early\n")
    display = Display("Collecting ~%d seconds of data "%opts.duration)
    
    # create an alarm thread to stop taking data
    alarm = threading.Timer(opts.duration + (time.time() - time0), setDone)
    
    # Start all the threads
    for collector in collectors:
        collector.start()
    alarm.start()
    display.start()
    
    # Wait on all my threads to exit
    for collector in collectors:
        if collector:
            collector.join()
    display.join()
    
    alarm.cancel() # Cancel the alarm if it hasn't gone off
    perr('\n')
    if g_quit:
        perr('Data collection terminated, no output written\n')
        return 4  # An error return value
    
    # Parse raw data from the collectors into meaningful measurments
    data = get_moments(collectors, [opts.X_DIM, opts.Y_DIM, opts.Z_DIM])
    
    # Output what we got
    write_csv(opts.out_file, opts.out_dir, data)
    write_pdf(opts.out_file, opts.out_dir, data)
    
    return 0  # An all-okay return value
    
    
# Run the main function and give it the command line arguments
if __name__ == "__main__":
    sys.exit(main(sys.argv))
