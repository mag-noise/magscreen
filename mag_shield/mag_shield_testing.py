# -*- coding: utf-8 -*-
"""
Created on %(date)s

@author: %Cole Dorman
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.constants import pi
from scipy.constants import mu_0
from scipy.optimize import curve_fit
import scipy.stats as stats

def func(r, m): #equation of a magnetic field from a dipole moment
    return ((mu_0 * m) / (2*pi * r**3))

#Due to the Bx field and Bz field magnetometer being farther away from the object than the By field magnetometer, a ratio is needed to project the 3 B field components to the same place to accurately measure magntitude and direction
def ratio(magnetometer_distance, distance, object_length):
    return ((magnetometer_distance + distance + object_length/2 )**3 / (distance + object_length/2)**3)

def rms(x, y, z): #root mean squared function, eventually used to find magnitude of B
    return np.sqrt(x**2 + y**2 + z**2)

def angle(vector, B1, B2, B3): #function finding angle from dot product of vectors
    z = np.array([0, 0, 1])
    return np.arccos( np.dot(vector, z) / np.sqrt(B1**2 + B2**2 + B3**2) )

def dipole_moment(object_length, distance, B, angle): #General formula for finding dipole moment based off vector's magnitude and direction
    return (4*pi*(object_length/2+distance)**3*B) / (mu_0*(2*np.cos(angle)**2 - np.sin(angle)**2))

'''
Below is the main function used to magnetic screen. User will enter size of arbitrary
length, width, and height in centimeters, then record the magneitc fields in nanoTelsa
from the object's different orientations at three (3) different distances. The 
function finds the magnitude and direction of the object's dipole moment, then 
calculates a best fit. Using this best fit, the function calculates the stray field 
at one (1) meter away assuming the strongest possible dipole orientation. If the 
stray field is too large, the object fails the test. If he stray field is below the 
required threshold but is within the top 95%, it passes with caution.
'''
def fit(length_x, length_y, length_z, x11, y11, z11, x12, y12, z12, x13, y13, z13, x21, y21, z21, x22, y22, z22, x23, y23, z23, x31, y31, z31, x32, y32, z32, x33, y33, z33):
    
    distance = np.array([20, 25, 27])*1e-2 #three distances object is being measured at, converted to meters
    
    length_meters = np.array([length_x, length_y, length_z])*1e-2 #converting length of objects to meters
    
    #converting the input magnetic fields into Tesla
    B_Tesla = np.array([x11*ratio(.01025, distance[0], length_meters[0]), y11, z11*ratio(.00475, distance[0], length_meters[0]), x12*ratio(.01025, distance[0], length_meters[1]), y12, z12*ratio(.00475, distance[0], length_meters[1]), x13*ratio(.01025, distance[0], length_meters[2]), y13, z13*ratio(.00475, distance[0], length_meters[2]), 
                        x21*ratio(.01025, distance[1], length_meters[0]), y21, z21*ratio(.00475, distance[1], length_meters[0]), x22*ratio(.01025, distance[1], length_meters[1]), y22, z22*ratio(.00475, distance[1], length_meters[1]), x23*ratio(.01025, distance[1], length_meters[2]), y23, z23*ratio(.00475, distance[1], length_meters[2]), 
                        x31*ratio(.01025, distance[2], length_meters[0]), y31, z31*ratio(.00475, distance[2], length_meters[0]), x32*ratio(.01025, distance[2], length_meters[1]), y32, z32*ratio(.00475, distance[2], length_meters[1]), x33*ratio(.01025, distance[2], length_meters[2]), y33, z33*ratio(.00475, distance[2], length_meters[2])])*1e-9
    
    #Organizing vectors of Bx, By, Bz components from 3 different orientations at 3 different distances
    vector = np.array([np.array([B_Tesla[0], B_Tesla[1], B_Tesla[2]]), np.array([B_Tesla[3], B_Tesla[4], B_Tesla[5]]), np.array([B_Tesla[6], B_Tesla[7], B_Tesla[8]]), np.array([B_Tesla[9], B_Tesla[10], B_Tesla[11]]), np.array([B_Tesla[12], B_Tesla[13], B_Tesla[14]]), np.array([B_Tesla[15], B_Tesla[16], B_Tesla[17]]), np.array([B_Tesla[18], B_Tesla[19], B_Tesla[20]]), np.array([B_Tesla[21], B_Tesla[22], B_Tesla[23]]), np.array([B_Tesla[24], B_Tesla[25], B_Tesla[26]])])
    
    #finding dipole moment from each orientation at each distance, totaling 9 different dipole moments
    m11 = dipole_moment(length_meters[0], distance[0], rms(B_Tesla[0], B_Tesla[1], B_Tesla[2]), angle(vector[0], B_Tesla[0], B_Tesla[1], B_Tesla[2]))
    m12 = dipole_moment(length_meters[1], distance[0], rms(B_Tesla[3], B_Tesla[4], B_Tesla[5]), angle(vector[1], B_Tesla[3], B_Tesla[4], B_Tesla[5]))
    m13 = dipole_moment(length_meters[2], distance[0], rms(B_Tesla[6], B_Tesla[7], B_Tesla[8]), angle(vector[2], B_Tesla[6], B_Tesla[7], B_Tesla[8]))
    m21 = dipole_moment(length_meters[0], distance[1], rms(B_Tesla[9], B_Tesla[10], B_Tesla[11]), angle(vector[3], B_Tesla[9], B_Tesla[10], B_Tesla[11]))
    m22 = dipole_moment(length_meters[1], distance[1], rms(B_Tesla[12], B_Tesla[13], B_Tesla[14]), angle(vector[4], B_Tesla[12], B_Tesla[13], B_Tesla[14]))
    m23 = dipole_moment(length_meters[2], distance[1], rms(B_Tesla[15], B_Tesla[16], B_Tesla[17]), angle(vector[5], B_Tesla[15], B_Tesla[16], B_Tesla[17]))
    m31 = dipole_moment(length_meters[0], distance[2], rms(B_Tesla[18], B_Tesla[19], B_Tesla[20]), angle(vector[6], B_Tesla[18], B_Tesla[19], B_Tesla[20]))
    m32 = dipole_moment(length_meters[1], distance[2], rms(B_Tesla[21], B_Tesla[22], B_Tesla[23]), angle(vector[7], B_Tesla[21], B_Tesla[22], B_Tesla[23]))
    m33 = dipole_moment(length_meters[2], distance[2], rms(B_Tesla[24], B_Tesla[25], B_Tesla[26]), angle(vector[8], B_Tesla[24], B_Tesla[25], B_Tesla[26]))
    m_observed = abs(np.array([m11, m12, m13, m21, m22, m23, m31, m32, m33]))    
    
    #x-axis is distances of from magnetometer plus center of object
    xdata = np.array([distance[0]+length_meters[0]/2, distance[0]+length_meters[1]/2, distance[0]+length_meters[2]/2, distance[1]+length_meters[0]/2, distance[1]+length_meters[1]/2, distance[1]+length_meters[2]/2, distance[2]+length_meters[0]/2, distance[2]+length_meters[1]/2, distance[2]+length_meters[2]/2])
    ydata = func(xdata, m_observed) #y-axis is mangetic fields from strongest possible dipole orientation
    plt.plot(xdata*1e2, ydata*1e9, 'bo',label="observed data") #plotting measured strongest magnetic field vs. distance
    
    plt.xlabel("distance (centimeters)")
    plt.ylabel("magnetic field (nanoTesla)")
    popt, pcov = curve_fit(func, xdata, ydata) #curve fitting best fit of the nine magnetic fields measured
    plt.plot(xdata*1e2, func(xdata, *popt)*1e9, 'r-',label='best fit') #plotting best fit line
    plt.legend()
    plt.show()
    
    m_err = np.sqrt(np.diag(pcov)) #estimated covariance of popt, aka one standard deviation errors on the parameters
    
    print("chi-squared test statistic: %.3f" %stats.chisquare(f_obs=m_observed, f_exp=popt)[0]) #Chi-squared calculated from values deviated from the expected
    print("p-value: %.3f" %stats.chisquare(f_obs=m_observed, f_exp=popt)[1]) #p-value calculated from chi-squared
    
    stray_B = (mu_0 * popt) / (2*pi*1**3) #calculating stray field at 1 meter from strongest orientation best-fit magnetic dipole moment
    
    print("magnetic dipole moment m = %.5f" %popt, "+/- %.4f" %m_err) #printing best fit magnetic dipole moment
    print("stray field B = %.4f nT" %(stray_B*1e9), "+/- %.4f" %(((mu_0 * m_err) / (4*pi))*1e9)) #printing stray magnetic field at 1 meter
    
    if popt+m_err > .05: #if best fit dipole moment over .1 mA^2, object does not pass test. If m is under 95% of .1, it passes completely. If m is between .1 and 95% of .1, it should be used with caution
        print("-> FAIL")
    elif popt+m_err < (.95*.05):
        print("-> PASS")
    else:
        print("-> CAUTION")