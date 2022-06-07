# -*- coding: utf-8 -*-
"""
Created on Mon Jun  6 08:43:18 2022

@author: jonpe
"""

import tkinter as tk
from tkinter import *
from tkinter import ttk
import os


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
    
    secondWindow = None
    treeContainer = None
    tree = None
    cwd = os.getcwd()
    optionsEntry = None
 
    
''' Function will create file tree of directories.'''
def fileTree():
    listOfDirs = os.listdir(Globals.cwd)
    dirName = os.path.split(Globals.cwd)    

    # Now create the tree.
    Globals.tree = ttk.Treeview(Globals.treeContainer)
    Globals.tree.heading('#0', text=dirName[0], anchor='w')
    
    # add data
    Globals.tree.insert('', tk.END, text=dirName[1], iid=0, open=True)
    
    # adding children of node
    iidCount = 1
    for i in range(len(listOfDirs)):
        name = listOfDirs[i]
        Globals.tree.insert('', tk.END, text=name, iid=iidCount, open=False)
        Globals.tree.move(iidCount, 0, i)
        
        iidCount = iidCount + 1
        
    Globals.tree.pack(side='top', fill='both', expand=True)
        
    
''' Function will allow user to change where the files get saved. 
    This will also need to update the fileTree. '''
def updateCWD():
    Globals.cwd = Globals.optionsEntry.get()
    Globals.tree.destroy()
    fileTree()
    return 
        
    
    
    
''' Function creates second window with all the options for a run. '''    
def launch():
    Globals.secondWindow = Toplevel()
    Globals.secondWindow.title("MagScreen Testing")
    Globals.secondWindow.geometry('650x375')
    
    ''' Create main containers '''
    topFrame = Frame(Globals.secondWindow, width=500, height=75, pady=10, padx=10)
    secondFrame = Frame(Globals.secondWindow, width=500, height=50, pady=10, padx=10)
    middleFrame = Frame(Globals.secondWindow, width=500, height=275, pady=10, padx=10)     
    bottomFrame = Frame(Globals.secondWindow, width=500, height=100, pady=10, padx=10)
    bottomFrame2 = Frame(Globals.secondWindow, width=500, height=50, pady=10, padx=10)
    
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
    
def initializeGUI():
    Globals.root = Tk()
    Globals.root.geometry('675x400')
    Globals.root.title("MagScreen")
    
    ''' Create main window. '''
    mainWindow = Frame(Globals.root, bg='red', width=600, height=350, pady=10, padx=10)
    
    ''' Place main window. '''
    mainWindow.pack(fill='both', expand=True)
    
    ''' Create subcontainers. '''
    Globals.treeContainer = Frame(mainWindow, bg='blue', width=150, height=375, pady=10, padx=10)
    topContainer = Frame(mainWindow, bg='cyan', width=500, height=75, pady=10, padx=10)
    midContainer = Frame(mainWindow, bg='yellow', width=500, height=225, pady=10, padx=10)
    bottomContainer = Frame(mainWindow, bg='black', width=500, height=75, pady=10, padx=10)
    
    ''' Place subcontainers in main window. '''
    Globals.treeContainer.grid(row=0, column=0, rowspan=3)
    topContainer.grid(row=0, column=1, columnspan=3)
    midContainer.grid(row=1, column=1, columnspan=3)
    bottomContainer.grid(row=2, column=1, columnspan=3)
    
    
    ''' Create the widgets for top container. New run button right now. '''
    newRunButton = Button(topContainer, text='New Run', command=launch)
    welcomeLabel = ttk.Label(topContainer, text='Welcome to MagScreen!', font=("Calibri", 14) )
    
    ''' Place the widgets in top container. New run button. '''
    newRunButton.pack(side='right', expand=True, fill='both', padx=70, pady=10)
    welcomeLabel.pack(side='left', expand=True, fill='both', padx=40, pady=10)
    
    ''' Create options entry and button for user to change where the files are saved. Will 
    go in treeContainer.'''
    Globals.optionsEntry = ttk.Entry(Globals.treeContainer, text=os.getcwd())
    
    
    changeButton = ttk.Button(Globals.treeContainer, text='Change', command=updateCWD)
    
    ''' Place options entry and change button into tree container. '''
    Globals.optionsEntry.pack(side='bottom', fill='x', expand=True, padx=20, pady=50)
    changeButton.pack(side='bottom', fill='x', expand=True, padx=20, pady=10)
    
    
def GUI():
    initializeGUI()
    
    ''' Create and place the widgets for tree container'''
    fileTree()
    
    
    Globals.root.mainloop()