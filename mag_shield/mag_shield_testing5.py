# -*- coding: utf-8 -*-
"""
Created on Sat Oct 16 13:20:13 2021

@author: cjdorman
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.constants import pi
from scipy.constants import mu_0
from scipy.optimize import curve_fit
import scipy.stats as stats

from scipy import signal
import time
import tldevice

from matplotlib.backends.backend_pdf import PdfPages
from PyPDF2 import PdfFileMerger
pdf = PdfPages('magnetic_screening_list.pdf')

import csv
import os, glob
import pandas as pd

import tkinter as tk

#get new B list every time
#delete log file
#get csv and pdf save to work

f_csv = None

def func(r, m):
    """equation of a magnetic field from a dipole moment"""
    return ((mu_0 * m) / (2*pi * r**3))

def ratio(magnetometer_distance, distance):
    """
    Due to the Bx field and Bz field magnetometer being farther away from the object than the By field
    magnetometer, a ratio is needed to project the 3 B field components to the same place to accurately
    measure magntitude and direction
    """
    return ((magnetometer_distance + distance)**3 / (distance)**3)

def rms(x, y, z):
    """root mean squared function, eventually used to find magnitude of B"""
    return np.sqrt(x**2 + y**2 + z**2)

def angle(vector, B1, B2, B3):
    """function finding angle from dot product of vectors"""
    z = np.array([0, 0, 1])
    return np.arccos( np.dot(vector, z) / np.sqrt(B1**2 + B2**2 + B3**2) )

def dipole_moment(distance, B, angle):
    """General formula for finding dipole moment based off vector's magnitude and direction"""
    return (4*pi*(distance)**3*B) / (mu_0*(2*np.cos(angle)**2 - np.sin(angle)**2))

def fit(name, x11, y11, z11, x21, y21, z21, x31, y31, z31):
    '''
    Below is the main function used to magnetic screen. The 
    function finds the magnitude and direction of the object's dipole moment, then 
    calculates a best fit. Using this best fit, the function calculates the stray field 
    at one (1) meter away assuming the strongest possible dipole orientation. If the 
    stray field is too large, the object fails the test. If he stray field is below the 
    required threshold but is within the top 95%, it passes with caution.
    '''
    distance = np.array([9, 11, 15])*1e-2 #three distances object is being measured at, converted to meters

    #converting the input magnetic fields into Tesla
    B_Tesla = np.array([x11*ratio(.01025, distance[0]), y11, z11*ratio(.00475, distance[0]), 
                        x21*ratio(.01025, distance[1]), y21, z21*ratio(.00475, distance[1]), 
                        x31*ratio(.01025, distance[2]), y31, z31*ratio(.00475, distance[2])])*1e-9
   
    #Organizing vectors of Bx, By, Bz components from 3 different orientations at 3 different distances
    # Hint: complex index calculations in loop below could be shortened if a 3-D array were used here.
    #       The axes would be row, column, component, i.e. B_Tesla[row,col,comp]
    vector = np.array([
        np.array([B_Tesla[ 0], B_Tesla[ 1], B_Tesla[ 2]]),
        np.array([B_Tesla[ 3], B_Tesla[ 4], B_Tesla[ 5]]),
        np.array([B_Tesla[ 6], B_Tesla[ 7], B_Tesla[ 8]])])
   
    #finding dipole moment from each orientation at each distance, totaling 9 different dipole moments
    m11 = dipole_moment(distance[0], rms(B_Tesla[0], B_Tesla[1], B_Tesla[2]), angle(vector[0], B_Tesla[0], B_Tesla[1], B_Tesla[2]))
    m21 = dipole_moment(distance[1], rms(B_Tesla[3], B_Tesla[4], B_Tesla[5]), angle(vector[1], B_Tesla[3], B_Tesla[4], B_Tesla[5]))
    m31 = dipole_moment(distance[2], rms(B_Tesla[6], B_Tesla[7], B_Tesla[8]), angle(vector[2], B_Tesla[6], B_Tesla[7], B_Tesla[8]))
   
    m_observed = abs(np.array([m11, m21, m31]))    

    xdata = np.array([distance[0], distance[1], distance[2]])
    ydata = func(xdata, m_observed) #y-axis is mangetic fields from strongest possible dipole orientation
    
    plt.plot(xdata*1e2, ydata*1e9, 'bo',label="observed data") #plotting measured strongest magnetic field vs. distance
    plt.title(str(name))
    plt.xlabel("distance (centimeters)")
    plt.ylabel("magnetic field (nanoTesla)")
    popt, pcov = curve_fit(func, xdata, ydata) #curve fitting best fit of the nine magnetic fields measured
    plt.plot(xdata*1e2, func(xdata, popt)*1e9, 'r-',label='best fit') #plotting best fit line
    plt.legend()
    
    '''
    After taking and projecting the dipole moments. Function saves a .pdf of
    each matplotlib graph into the folder where the .py script is held.
    The function then merges every .pdf files into one for organization purposes
    '''
    pdf.savefig()
    pdf.close()
   
    m_err = np.sqrt(np.diag(pcov)) #estimated covariance of popt, aka one standard deviation errors on the parameters

    stray_B = (mu_0 * popt) / (2*pi*1**3) #calculating stray field at 1 meter from strongest orientation best-fit magnetic dipole moment
   
    print("magnetic dipole moment m = %.16f" %popt, "+/- %.16f" %m_err) #printing best fit magnetic dipole moment
    print("stray field B = %.4f nT" %(stray_B*1e9), "+/- %.4f" %(((mu_0 * m_err) / (4*pi))*1e9)) #printing stray magnetic field at 1 meter

    # If best fit dipole moment over .1 mA^2, object does not pass test.
    # If m is under 95% of .1, it passes completely.
    # If m is between .1 and 95% of .1, it should be used with caution    
    if popt+m_err > .05:
        result = str("-> FAIL")
    elif popt+m_err < (.95*.05):
        result = str("-> PASS")
    else:
        result = str("-> CAUTION")
    
    print(result)
    
    '''
    After calculating dipole moment, projected field, and passing results,
    function will save all of these outputs into a csv file, then combine
    each .csv file into one main .csv file for organizational purposes
    '''
    

    f = open('magnetic_screen_list.csv', 'w', encoding='UTF8', newline='')

    f.write('"%s",%.4e,%.4e,"%s"\r\n'%(name, popt, stray_B, result))
    f.flush()
    
"""
    mydict =[{'name': str(name), 'dipole': popt, 'stray': stray_B, 'result': result}] 
    fields = ['name', 'dipole', 'stray', 'result'] 

    filename = ("magnetic_screen_"+str(name)+".csv")
    # writing to csv file 
    with open(filename, 'w') as csvfile: 
    # creating a csv dict writer object 
       writer = csv.DictWriter(csvfile, fieldnames = fields) 
    # writing headers (field names) 
       writer.writeheader()   
    # writing data rows 
       writer.writerows(mydict) 
       
    path = r"/Users/cjdorman/Documents/Python Scripts/"
    all_files = glob.glob(os.path.join(path, "magnetic_screen_*.csv"))
    df_from_each_file = (pd.read_csv(f, sep=',') for f in all_files)
    df_merged   = pd.concat(df_from_each_file, ignore_index=True)
    df_merged.to_csv( "magnetic_screen_list.csv")
    return mydict
"""

Bx = [] #Creating empty lists of B-field vector components to save Twinleaf VMR data into
By = []
Bz = []    


def VMR(vmr, name): #Write as COM5, COM1, COM4, etc.
    '''
    Function reads the USB port the Twinleaf VMR is running from then takes data
    for 10 seconds. It saves this data into a list defined above. This process
    repeats for each USB port a Twinleaf is in
    '''
    #vmr = tldevice.Device(COM_n) #reading the USB port
    file = open('log'+str(name)+'.csv','w') #logging data into a csv file, this WONT conflict with .csv files above
    timeout = time.time() + 10 #tells function how long to take data
    #change time to whatever period is supposed to be
    for row in vmr.data.stream_iter():
      rowstring = "\t".join(map(str,row))+"\n"
      print(rowstring)
      file.write(rowstring) #writing data itself into csv
      test = 0
      if test == 5 or time.time() > timeout:
          break
      test = test - 1
      vmr._close();    

    B = np.loadtxt('log'+str(name)+'.csv', delimiter='\t') #pulling data from .csv
    B_x, B_y, B_z = B[:,0], B[:,1], B[:,2] #organzing
    
    f_x, Pxx_x = signal.welch(B_x, scaling='spectrum')
    Bx.append(np.sqrt(Pxx_x.max())) #adding B vectors into list to be used in fit function above
    
    f_y, Pxx_y = signal.welch(B_y, scaling='spectrum')
    By.append(np.sqrt(Pxx_y.max()))
    
    f_z, Pxx_z = signal.welch(B_z, scaling='spectrum')
    Bz.append(np.sqrt(Pxx_z.max()))

    #os.remove('log'+str(name)+'.csv')
    
    return Bx, By, Bz

def reset_B():
    try:
        del Bx[abs(len(Bx)-6)], Bx[abs(len(Bx)-5)], Bx[abs(len(Bx)-4)]
    # 20 other lines
    except IndexError:
        dummy=1
        
    try:
        del By[abs(len(By)-6)], By[abs(len(By)-5)], By[abs(len(By)-4)]
    # 20 other lines
    except IndexError:
        dummy=1
        
    try:
        del Bz[abs(len(Bz)-6)], Bz[abs(len(Bz)-5)], Bz[abs(len(Bz)-4)]
    # 20 other lines
    except IndexError:
        dummy=1

def screen(name):
    '''
    This function is soley for manual testing purposes. It is the manual version
    of our GUI below. Function gathers data from 3 Twinleaf VMRs and takes this
    data into our fit function to find dipole moment and friends
    '''
    vmr1 = tldevice.Device('COM4') #reading the USB port
    vmr2 = tldevice.Device('COM5') #reading the USB port
    vmr3 = tldevice.Device('COM6')
    VMR(vmr1)
    VMR(vmr2)
    VMR(vmr3)
    reset_B()
    fit(name, Bx[0], By[0], Bz[0], Bx[1], By[1], Bz[1], Bz[2], By[2], Bz[2])
    
def GUI_func(): #automatic version of screen function
    VMR(vmr1, ent_object.get())
    VMR(vmr2, ent_object.get())
    VMR(vmr3, ent_object.get())
    reset_B()
    Input = fit(ent_object.get(), Bx[0], By[0], Bz[0], Bx[1], By[1], Bz[1], Bz[2], By[2], Bz[2])
    output = str(Input)
    lbl_result["text"] = output

# Set-up the window
window = tk.Tk()
window.title("Magnetic Screening Apparatus")
window.resizable(width=True, height=True)

# Create the object entry frame with an Entry
# widget and label in it
frm_entry = tk.Frame(master=window)
ent_object = tk.Entry(master=frm_entry, width=10)
lbl_object = tk.Label(master=frm_entry, text="OBJECT NAME")

# Layout the window Entry and Label in frm_entry
# using the .grid() geometry manager
ent_object.grid(row=0, column=0, sticky="e")
lbl_object.grid(row=0, column=1, sticky="w")

vmr1 = tldevice.Device('COM4') #reading the USB port
vmr2 = tldevice.Device('COM5') #reading the USB port
vmr3 = tldevice.Device('COM6') #reading the USB port

# Create the conversion Button and result display Label
btn_convert = tk.Button(
    master=window,
    text="SCREEN",
    command=GUI_func
)

lbl_result = tk.Label(master=window, text="\N{RIGHTWARDS BLACK ARROW} DIPOLE MOMENT, STRAY FIELD AT 1 METER, PASS/FAIL")

# Set-up the layout using the .grid() geometry manager
frm_entry.grid(row=0, column=0, padx=10)
btn_convert.grid(row=0, column=1, pady=10)
lbl_result.grid(row=0, column=2, padx=10)

fieldnames = ['Name', 'Dipole Moment [Am^2]', 'Stray Field [nT]', 'Result'] 

if os.path.isfile('magnetic_screen_list.csv'):
    f_csv = open('magnetic_screen_list.csv', 'w', encoding='UTF8')
    f_csv.seek(0, os.SEEK_END)
else:
    f_csv = open('magnetic_screen_list.csv', 'w', encoding='UTF8')
    for n in fieldnames:
        f_csv.write('"%s"'%n)
    f_csv.write("\r\n")
        
# Run the application
window.mainloop()
