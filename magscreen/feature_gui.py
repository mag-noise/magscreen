# -*- coding: utf-8 -*-
"""
Created on Wed Jun  1 11:27:34 2022

@author: jonpe
"""

import tkinter as tk
from tkinter import *
from tkinter import ttk
# from tkscrolledframe import ScrolledFrame 

''' This class will represent the default values helping manage our global
    variables'''
class Globals:
    
    root = None 
    mainFrame = None
    topFrame = None
    window = None 
    num_sensors = 3
    selected_num_sensors = None
    sensor_A = 'DT04H6OX'
    sensor_B = 'DT04H6NY'
    sensor_C = 'DT04H6OF'
    no_sensor = 'N/A'
    num_radii = 3       # Don't need anymore
    default_tech = 'Your name'
    default_part = 'Enter part name'
    default_system = 'Enter system name'
    default_rate = 10
    

    
    

def initializeGUI(): 
    
   Globals.root = Tk()
   Globals.root.geometry('650x375')
   Globals.root.title("MagScreen Testing")
   
   ''' Create main containers '''
   topFrame = Frame(Globals.root, width=500, height=75, pady=10, padx=10)
   secondFrame = Frame(Globals.root, width=500, height=50, pady=10, padx=10)
   middleFrame = Frame(Globals.root, width=500, height=275, pady=10, padx=10)     
   bottomFrame = Frame(Globals.root, width=500, height=100, pady=10, padx=10)
   bottomFrame2 = Frame(Globals.root, width=500, height=50, pady=10, padx=10)
   
   ''' Layout all the main containers/frames '''
   #Globals.root.grid_rowconfigure(0, weight=1)
   #Globals.root.grid_columnconfigure(0, weight=1)
   
   topFrame.grid(row=0, sticky='nsew')
   secondFrame.grid(row=1, sticky='ew')
   middleFrame.grid(row=2, sticky='nsew')
   bottomFrame.grid(row=3, sticky='nsew')
   bottomFrame2.grid(row=4, sticky='ew')
   
   ''' Create subcontainers. These will be the two scroll frames. '''
   # sfOne = ScrolledFrame(middleFrame, bg='coral', width=230, height=255, pady=10, padx=10)
   # sfTwo = ScrolledFrame(middleFrame, bg='chartreuse', width=230, height=255, pady=10, padx=10)
   
   ''' Bind arrow keys and scroll wheel to sub containers '''

   
   ''' Place subcontainers '''
   
   
   #middleFrame.grid_columnconfigure(0, weight=1)
   #middleFrame.grid_columnconfigure(1, weight=3)
   
   ''' Create the widgets for top frame. These include technician label and entry,
   part label and entry, and system label and entry. '''
   tech_label = ttk.Label(topFrame, text="Technician:", font=("Calibri", 12))
   tech = ttk.Entry(topFrame, textvariable=Globals.default_tech)
   tech.insert(0, Globals.default_tech)
   
   part_label = ttk.Label(topFrame, text="Part:", font=("Calibri", 12))
   part = ttk.Entry(topFrame)
   part.insert(0, Globals.default_part)
   
   system_label = ttk.Label(topFrame, text="System:", font=("Calibri", 12))
   system = ttk.Entry(topFrame)
   system.insert(0, Globals.default_system)
   
   ''' Placing the widgets in the top frame. '''
   tech_label.pack(fill='x', side='left')
   tech.pack(fill='x', side='left', padx=10)
   
   part_label.pack(fill='x', side='left', padx=10)
   part.pack(fill='x', side='left', padx=5)
   
   system_label.pack(fill='x', side='left', padx=10)
   system.pack(fill='x', side='left', padx=5)
   
   ''' Create widgets for second frame. This is the combobox for number of sensors 
       being used. '''
   num_sensors_label = ttk.Label(secondFrame, text='Number of Sensors:')
   Globals.selected_num_sensors = tk.IntVar()
   num_sensors_chosen = ttk.Combobox(secondFrame, width=5)
   num_sensors_chosen["values"] = (2, 3, 4, 5)
   num_sensors_chosen.state(["readonly"])
   num_sensors_chosen.set(Globals.num_sensors)      # default number of sensors
   # num_sensors_chosen.bind('<<Combobox Selected>>', ***Need function here to change number of sensors***)
   
   ''' Placing the combobox in the second frame. '''
   num_sensors_label.pack(side='left')
   num_sensors_chosen.pack(fill='x', side='left', padx=10)
   
   ''' Create widgets for middle frame. This will be the label for serial numbers,
       comboboxes for serial numbers, label for radii, and entries for radii. Planning
       to use five, but will provide NA for comboboxes not used and 0 for entries not
       used.'''
   sensor_serials_label = ttk.Label(middleFrame, text="Sensor Serial Numbers:")
   
   sensor1 = tk.StringVar()
   sensor1_cb = ttk.Combobox(middleFrame, width=10, textvariable=sensor1)
   sensor1_cb["values"] = (Globals.sensor_A, Globals.sensor_B, Globals.sensor_C, Globals.no_sensor)
   sensor1_cb.state(["readonly"])
   
   sensor2 = tk.StringVar()
   sensor2_cb = ttk.Combobox(middleFrame, width=10, textvariable=sensor2)
   sensor2_cb["values"] = (Globals.sensor_A, Globals.sensor_B, Globals.sensor_C, Globals.no_sensor)
   sensor2_cb.state(["readonly"])
   
   sensor3 = tk.StringVar()
   sensor3_cb = ttk.Combobox(middleFrame, width=10, textvariable=sensor3)
   sensor3_cb["values"] = (Globals.sensor_A, Globals.sensor_B, Globals.sensor_C, Globals.no_sensor)
   sensor3_cb.state(["readonly"])
   
   sensor4 = tk.StringVar()
   sensor4_cb = ttk.Combobox(middleFrame, width=10, textvariable=sensor4)
   sensor4_cb["values"] = (Globals.sensor_A, Globals.sensor_B, Globals.sensor_C, Globals.no_sensor)
   sensor4_cb.state(["readonly"])
        
   sensor5 = tk.StringVar()
   sensor5_cb = ttk.Combobox(middleFrame, width=10, textvariable=sensor5)
   sensor5_cb["values"] = (Globals.sensor_A, Globals.sensor_B, Globals.sensor_C, Globals.no_sensor)
   sensor5_cb.state(["readonly"])

   radii_label = ttk.Label(middleFrame, text="Radii [cm]:")
   
   radii1 = ttk.Entry(middleFrame, width=5)
   radii2 = ttk.Entry(middleFrame, width=5)
   radii3 = ttk.Entry(middleFrame, width=5)
   radii4 = ttk.Entry(middleFrame, width=5)
   radii5 = ttk.Entry(middleFrame, width=5)
   
   ''' Place widgets into middle frame. '''
   sensor_serials_label.grid(column=0, row=1)
   
   sensor1_cb.grid(column=1, row=1, padx=10, pady=25)
   sensor2_cb.grid(column=2, row=1, padx=10, pady=25)
   sensor3_cb.grid(column=3, row=1, padx=10, pady=25)
   sensor4_cb.grid(column=4, row=1, padx=10, pady=25)
   sensor5_cb.grid(column=5, row=1, padx=10, pady=25)
   
   radii_label.grid(column=0, row=3)
   
   radii1.grid(column=1, row=3, padx=10, pady=25)
   radii2.grid(column=2, row=3, padx=10, pady=25)
   radii3.grid(column=3, row=3, padx=10, pady=25)
   radii4.grid(column=4, row=3, padx=10, pady=25)
   radii5.grid(column=5, row=3, padx=10, pady=25)
   
   ''' Create widgets for bottom frame. This will be rate label and entry, 
       options button, and reset all button. '''
   rate_label = ttk.Label(bottomFrame, text="Rate [Hz]:")
   rate = ttk.Entry(bottomFrame, width='10')
   rate.insert(0, Globals.default_rate)
   
   options = ttk.Button(bottomFrame, text='Options', width=40)        # Need to create funtion and add command for Option button   
   
   ''' Place widgets into bottom frame. '''
   rate_label.pack(side='left', padx=25, pady=5)
   rate.pack(side='left', padx=25, pady=5)
   
   options.pack(side='left', fill='both', expand=True, padx=153, pady=5)
   
   ''' Create widgets for bottomFrame2. This will be progress bar, clear all button, and run button'''
   clear_all = ttk.Button(bottomFrame2, text='Clear all', width=15)    # Need to create funtion and add command for Clear all button
   
   run = ttk.Button(bottomFrame2, text='Run', width=15)        # Need to add command to run button
   
   # Progress bar mode can be set to determinant once I know how to measure relative progress of the program.
   # Could possibly set it so if it takes more than 22 seconds it displays bad run or error???
   progress_bar = ttk.Progressbar(bottomFrame2, orient='horizontal', length='300', mode='indeterminate')  
   
   ''' Place widgets in bottomFrame2. '''
   
   progress_bar.pack(side='left', padx=25, pady=5)
   
   clear_all.pack(side='left', fill='x', padx=25, pady=5)
   
   run.pack(side='left', fill='x', padx=25, pady=5)
   
   return


def GUI():
    initializeGUI()
    Globals.root.mainloop()