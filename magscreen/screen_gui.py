# -*- coding: utf-8 -*-
"""
Created on Mon Jun  6 08:43:18 2022

@author: jonpe
"""
import math
import numpy as np
import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tkinter.messagebox import showerror, showwarning, showinfo
from tkinter import filedialog as fd
from PIL import Image, ImageTk
from tkhtmlview import HTMLLabel
import os


''' This class will represent the default values helping manage our global
    variables'''
class Globals:
    
    root = None 
    mainFrame = None
    topFrame = None
    window = None 
    default_num_sensors = 8
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
    midContainer = None
    tree = None
    cwd = os.getcwd()
    optionsEntry = None
    
    scrollable_frame = None
    sensor_list = []
    color_list = []
    color_canvas = None
    
    so = []
    
    colors = ['papaya whip', 'blanched almond', 'bisque', 'peach puff',
          'navajo white', 'lemon chiffon', 'mint cream', 'azure', 'alice blue', 'lavender',
          'lavender blush', 'dark slate gray', 'dim gray', 'slate gray',
          'gray', 'midnight blue', 'navy', 'cornflower blue', 'dark slate blue',
          'slate blue', 'medium slate blue', 'light slate blue', 'medium blue', 'royal blue',  'blue',
          'dodger blue', 'deep sky blue', 'sky blue', 'light sky blue', 'steel blue', 'light steel blue',
          'light blue', 'powder blue', 'pale turquoise', 'dark turquoise', 'medium turquoise', 'turquoise',
          'cyan', 'light cyan', 'cadet blue', 'aquamarine', 'dark green', 'dark olive green',
          'dark sea green', 'sea green', 'medium sea green', 'light sea green', 'pale green', 'spring green',
          'lawn green', 'medium spring green', 'green yellow', 'lime green', 'yellow green',
          'forest green', 'olive drab', 'dark khaki', 'pale goldenrod',
          'light yellow', 'yellow', 'gold', 'light goldenrod', 'goldenrod', 'dark goldenrod', 'rosy brown',
          'indian red', 'saddle brown', 'sandy brown',
          'dark salmon', 'salmon', 'light salmon', 'orange', 'dark orange',
          'coral', 'light coral', 'tomato', 'orange red', 'red', 'hot pink', 'deep pink', 'pink', 'light pink',
          'pale violet red', 'maroon', 'medium violet red', 'violet red']
    
    
class sensor:
    def __init__(self, serial, radii, color, state=0):
        self.serial = serial
        self.radii = radii
        self.color = color
        self.state = state

class sensorFrame(ttk.Frame):
    def __init__(self, container):
        super().__init__(container)
        
        ''' Create and place sensor combobox. '''
        self.serial = tk.StringVar()
        self.sensor_cb = ttk.Combobox(self, width=10, textvariable=self.serial)
        self.sensor_cb["values"] = (Globals.sensor_A, Globals.sensor_B, Globals.sensor_C)
        self.sensor_cb['state'] = 'disable'
        self.sensor_cb.pack(side='left', fill='both', padx=30, pady=10)
        
        ''' Create and place radii entry. '''
        self.radius = tk.IntVar()
        self.radii = ttk.Entry(self, width=5, textvariable=self.radius)
        self.radii['state'] = 'disable'
        self.radii.pack(side='left', fill='both', padx=30, pady=10)
        
        ''' Get random color from list colors. Add the color to the list of colors being used. Create and place color label. '''
        self.color = Globals.colors[np.random.choice(range(len(Globals.colors)))]
        Globals.color_list.append(self.color)
        self.color_label = Label(self, bg=self.color, width=2)
        self.color_label.pack(side='left', padx=7, pady=10)
    
        ''' Create and place checkbutton. Command function is enableDisable. '''
        self.checkbox = ttk.Checkbutton(self, command=lambda: enableDisable(self.winfo_children()))
        self.checkbox.pack(side='left', fill='both', padx=15, pady=10)
        
        # show frame
        self.pack(side='top', fill='x')
        
    
    
''' Function changes current working directory. Calls function to remake tree.'''    
def select_directory():
    Globals.cwd = fd.askdirectory()
    updateCWD()
    return

''' Function enables and disables the sensor combobox and radii entry widget corresponding to the check button clicked.'''
def enableDisable(children):    
    combobox = children[0]
    entry = children[1]
    if ('normal' in str(combobox['state'])):
        combobox.configure(state='disable')
        entry.configure(state='disable')
        
    else:
        combobox.configure(state='normal')
        entry.configure(state='normal')
    return

''' Function adds new sensor serial number entry, check box, and entry for radii. '''
def add_new_sensor():
    
    s = sensorFrame(Globals.scrollable_frame)
    Globals.so.append(s)
    

    return

''' Funcation removes sensor serial entry, checkbox, and entry for radii. Updates Globals sensor list. '''
def remove_sensor():
    if len(Globals.so) < 3:
        # showinfo(title='Error', message='This is the minimum number of sensors allowed.')
        return
    else:
        last_sensor = Globals.so[-1]
        last_sensor.destroy()
        Globals.so = Globals.so[:-1]
        Globals.color_list = Globals.color_list[:-1]
        return 
    
''' Function to create image of the sensor set up from the software's perspective. '''
def create_set_up():
    Globals.color_canvas.delete("all")
    Globals.color_canvas.create_oval(79, 71, 197, 189, fill='light gray')
    Globals.color_canvas.create_oval(139, 131, 137, 129, fill='black')
    
    centerX = 138
    centerY = 130
    radii_list = []
    clr = []
    for sensor in Globals.so:
        radii_entry = sensor.radii
        if ('normal' in str(radii_entry['state'])):
            radii_list.append(radii_entry.get())
            clr.append(sensor.color)
            
            
    print(radii_list)
    
    pi = math.pi
    theta = 0
    incr = (2*pi) / len(radii_list)
    for i in range(len(radii_list)):
        shifty = 5.3*int(radii_list[i])*math.sin(theta)
        shiftx = 5.3*int(radii_list[i])*math.cos(theta)
        
        if (theta == 0 or theta == pi or theta == 2*pi):
            x1 = (-12) + centerX + shiftx
            y1 = (5) + centerY + shifty
            x2 = (12) + centerX + shiftx 
            y2 = (-5) + centerY + shifty
        
            lPts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
            
        elif (theta > (3*pi/2)):
            angle = theta - (3*pi/2)
            phi = (pi/2) - angle
            
            x1 = centerX + shiftx
            y1 = centerY + shifty
            
            delta_x1 = 10*math.sin(phi)
            delta_y1 = 10*math.cos(phi)
            delta_x2 = 24*math.sin(angle)
            delta_y2 = 24*math.cos(angle)
            
            p1 = (x1, y1)
            p2 = ((x1 - delta_x1), (y1 - delta_y1))
            p3 = ((p2[0] + delta_x2), (p2[1] - delta_y2))
            p4 = ((x1 + delta_x2), (y1 - delta_y2))
            
            lPts = [p1, p2, p3, p4]
            
        elif (theta > pi):
            angle = theta - (pi)
            phi = (pi/2) - angle
            
            x1 = centerX + shiftx
            y1 = centerY + shifty
            
            delta_x1 = 10*math.sin(angle)
            delta_y1 = 10*math.cos(angle)
            delta_x2 = 24*math.sin(phi)
            delta_y2 = 24*math.cos(phi)
            
            p1 = (x1, y1)
            p2 = ((x1 + delta_x1), (y1 - delta_y1))
            p3 = ((p2[0] - delta_x2), (p2[1] - delta_y2))
            p4 = ((x1 - delta_x2), (y1 - delta_y2))
            
            lPts = [p1, p2, p3, p4]
            
        elif (theta > (pi/2)):
            angle = theta - (pi/2)
            phi = (pi/2) - angle
            
            x1 = centerX + shiftx
            y1 = centerY + shifty
            
            delta_x1 = 10*math.sin(phi)
            delta_y1 = 10*math.cos(phi)
            delta_x2 = 24*math.sin(angle)
            delta_y2 = 24*math.cos(angle)
            
            p1 = (x1, y1)
            p2 = ((x1 + delta_x1), (y1 + delta_y1))
            p3 = ((p2[0] - delta_x2), (p2[1] + delta_y2))
            p4 = ((x1 - delta_x2), (y1 + delta_y2))
            
            lPts = [p1, p2, p3, p4]
            
        elif (theta < (pi/2)):
            phi = (pi/2) - theta
            
            x1 = centerX + shiftx
            y1 = centerY + shifty
            
            delta_x1 = 10*math.sin(theta)
            delta_y1 = 10*math.cos(theta)
            delta_x2 = 24*math.sin(phi)
            delta_y2 = 24*math.cos(phi)
            
            p1 = (x1, y1)
            p2 = ((x1 - delta_x1), (y1 + delta_y1))
            p3 = ((p2[0] + delta_x2), (p2[1] + delta_y2))
            p4 = ((x1 + delta_x2), (y1 + delta_y2))
            
            lPts = [p1, p2, p3, p4]
            
        elif (theta == (3*pi/2) or theta == pi/2):
            y1 = (-12) + centerX + shiftx
            x1 = (5) + centerY + shifty
            y2 = (12) + centerX + shiftx 
            x2 = (-5) + centerY + shifty
            
            lPts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
          
        Globals.color_canvas.create_polygon(lPts, fill=clr[i])
        
        # rotate the rectangle
        theta = theta + incr
		
	
        
    
        
    
''' Function will create file tree of directories.'''
def fileTree():
    listOfDirs = os.listdir(Globals.cwd)
    dirName = os.path.split(Globals.cwd)    

    # Now create the tree.
    height1 = Globals.treeContainer.winfo_screenheight() - 20
    Globals.tree = ttk.Treeview(Globals.treeContainer, height=height1)
    # print(Globals.tree.configure().keys())
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
        
    Globals.tree.pack(side='top', fill='y', expand=True)
        
    
''' Function will allow user to change where the files get saved. 
    This will also need to update the fileTree. '''
def updateCWD():
    # Globals.cwd = Globals.optionsEntry.get()
    Globals.tree.destroy()
    fileTree()
    return 

''' Function to initialize the main window. Can update later to show 
    different things based on first run or not.'''
def mainPage():
    
    ''' Create two subcontainers within the midContainer. '''
    # leftFrame = Frame(Globals.midContainer, width=240, height=225)
    rightFrame = Frame(Globals.midContainer, width=280, height=225)
    
    ''' Place the left and right frame withing the midContainer. '''
    # leftFrame.pack(side='left', fill='both', expand=True)
    rightFrame.pack(side='left', fill='both', expand=True)
    
    ''' Place image for now in left frame.'''
    main_label = HTMLLabel(rightFrame, html="""
        <p>Magnetic cleanliness screening is the process of determining the
        magnetic properties of various parts before they are added to 
        instrumentation that measures magnetic fields. The properties of interest
        are the stray field and dipole moment. Typically a full field 
        characterization is unnecessary. A simple pass/fail measurement of the 
        worst possible magnetic field distortion created by an object is typically good enough for
        instrument construction purposes. This software is intended for use with an apparatus that 
        rotates the part to be screened at a constant rate while the 3-axis magnetic field is regularly 
        sampled at 2-N locations in space near the part. Magscreen was written using the TwinLeaf VMR 
        sensors for thier simple serial interface, though it easily could be adapted for other equipment.</p>
                   <img src="mag_screen_apperatus.jpg">                
    """)
                           
    main_label.pack(pady=20, padx=20, fill='both', expand=True)
    
    
''' Function creates second window with all the options for a run. '''    
def launch():
    if (Globals.secondWindow != None):
        Globals.secondWindow.deiconify()
        return
    Globals.secondWindow = Toplevel()
    Globals.secondWindow.title("MagScreen Testing")
    Globals.secondWindow.geometry('650x510')
    
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
   
    part_label = ttk.Label(topFrame, text="Part:", font=('Calibri', 12))
    part = ttk.Entry(topFrame)
    part.insert(0, Globals.default_part)
   
    system_label = ttk.Label(topFrame, text="System:", font=("Calibri", 12))
    system = ttk.Entry(topFrame)
    system.insert(0, Globals.default_system)
   
    ''' Placing the widgets in the top frame. '''
    tech_label.pack(fill='x', side='left')
    tech.pack(fill='x', side='left', padx=10)
    
    system_label.pack(fill='x', side='left', padx=10)
    system.pack(fill='x', side='left', padx=5)
   
    part_label.pack(fill='x', side='left', padx=10)
    part.pack(fill='x', side='left', padx=5)
   
    ''' Create widgets for second frame. This is the combobox for number of sensors 
       being used. '''
    # num_sensors_label = ttk.Label(secondFrame, text='Number of Sensors:')
    # Globals.selected_num_sensors = tk.IntVar()
    # num_sensors_chosen = ttk.Combobox(secondFrame, width=5)
    # num_sensors_chosen["values"] = (2, 3, 4, 5)
    # num_sensors_chosen.state(["readonly"])
    # num_sensors_chosen.set(Globals.num_sensors)      # default number of sensors
    # num_sensors_chosen.bind('<<Combobox Selected>>', ***Need function here to change number of sensors***)
    
    # s = sensorStuff(Globals.scrollable_frame)
    
    addSensorButton = ttk.Button(secondFrame, text='Add New Sensor', width = 20, command=add_new_sensor)
   
    removeSensorButton = ttk.Button(secondFrame, text='Remove Sensor', width=20, command=remove_sensor)
    
    ''' Placing the combobox in the second frame. '''
    # num_sensors_label.pack(side='left')
    # num_sensors_chosen.pack(fill='x', side='left', padx=10)
    
    addSensorButton.pack(side='left', padx=10, pady=10)
    
    removeSensorButton.pack(side='left', padx=15, pady=10)
   
    ''' Create widgets for middle frame. This will be the label for serial numbers,
       comboboxes for serial numbers, label for radii, and entries for radii. Planning
       to use five, but will provide NA for comboboxes not used and 0 for entries not
       used.'''
       
    # Create canvas for middle frame. This will have a frame and scrollbar within it.
    # Within this frame in the canvas, we will add the new sensor combobox, checkbox, and entry.
    canvas = Canvas(middleFrame, width=320)
    scrollbar = ttk.Scrollbar(middleFrame, orient='vertical', command=canvas.yview)
    Globals.scrollable_frame = ttk.Frame(canvas)
    Globals.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    
    canvas.create_window((0,0), window=Globals.scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side='left', fill="both")
    scrollbar.pack(side='left', fill='y')
    
    label_frame = ttk.Frame(Globals.scrollable_frame)
    label_frame.pack(side='top', fill='x')
    
    sensor_serials_label = ttk.Label(label_frame, text="Sensor Serial Numbers:")
    sensor_serials_label.pack(side='left', fill='y', padx=10, pady=10)
    
    #blank_label = ttk.Label(label_frame, text=' ')
    #blank_label.pack(side='left', fill='y', padx=120, pady=10)
    
    radii_label = ttk.Label(label_frame, text="Radii [cm]:")
    radii_label.pack(side='left', fill='y', padx=18, pady=10)
        
    
    i = 0
    while (i < Globals.default_num_sensors):
        add_new_sensor()
        i= i + 1
        
    ''' Create image of set up based on softwares perspective. Users can use this to confirm this looks like
    their set up or make changes to the program options to ensure it is correct. Start by creating a canvas. '''
    Globals.color_canvas = Canvas(middleFrame, width=275, bg='white')
    Globals.color_canvas.pack(side='left', fill='both', padx=5)
    Globals.color_canvas.create_oval(79, 71, 197, 189, fill='light gray')
    Globals.color_canvas.create_oval(139, 131, 137, 129, fill='black')
    
    ''' Have a function called to create the figures representing set up. '''
    # create_set_up()
   
    ''' Create widgets for bottom frame. This will be rate label and entry, 
       options button, and reset all button. '''
    rate_label = ttk.Label(bottomFrame, text="Rate [Hz]:")
    rate = ttk.Entry(bottomFrame, width='10')
    rate.insert(0, Globals.default_rate)
    
    options = ttk.Button(bottomFrame, text='Options', width=15)        # Need to create funtion and add command for Option button  
    ready = ttk.Button(bottomFrame, text='Ready', width=15, command=create_set_up)
   
    ''' Place widgets into bottom frame. '''
    rate_label.pack(side='left', padx=25, pady=5)
    rate.pack(side='left', padx=25, pady=5)
   
    options.pack(side='left', fill='both', expand=True, padx=25, pady=5)
    ready.pack(side='left', fill='both', expand=True, padx=25, pady=5)
   
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
	    
    Globals.secondWindow.protocol("WM_DELETE_WINDOW", hide)
    return

def hide():
	Globals.secondWindow.withdraw()
	return
    
def initializeGUI():
    Globals.root = Tk()
    Globals.root.geometry('840x400')
    Globals.root.title("MagScreen")
    
    ''' Create main window. '''
    mainWindow = Frame(Globals.root, width=600, height=350, pady=10, padx=10)
    
    ''' Place main window. '''
    mainWindow.pack(fill='both', expand=True)
    mainWindow.columnconfigure(1, weight=1)
    mainWindow.rowconfigure(1, weight=1)
    
    ''' Create menu bar for main window. '''
    menubar = Menu(Globals.root)
    Globals.root.config(menu=menubar)
    
    ''' Create file menu. '''
    file_menu = Menu(menubar, tearoff=0)
    
    ''' Add commands to file_menu. '''
    file_menu.add_command(label='New Run', command=launch)
    file_menu.add_separator()
    
    file_menu.add_command(label='Exit', command=Globals.root.destroy)
    
    ''' Add file_menu to menubar. '''
    menubar.add_cascade(label="File", menu=file_menu, underline=0)
    
    ''' Create view menu. '''
    view_menu = Menu(menubar, tearoff=0)
    
    ''' Add commands to view menu. '''
    view_menu.add_command(label='Recent')
    
    ''' Add view menu to menubar. '''
    menubar.add_cascade(label='View', menu=view_menu, underline=0)
    
    ''' Create Help menu. '''
    help_menu = Menu(menubar, tearoff=0)
    
    ''' Add commands to help menu. '''
    help_menu.add_command(label='Help', command=lambda: showinfo(title='Help', message='Press NEW RUN for new run. \nPress BROWSE to change file location. \nPress FILE, EXIT to close MagScreen.'))
    
    ''' Add help menu to menubar.'''
    menubar.add_cascade(label='Help', menu=help_menu, underline=0)
    
    ''' Create subcontainers. '''
    Globals.treeContainer = Frame(mainWindow, width=150, height=375, pady=10, padx=10)
    topContainer = Frame(mainWindow, width=500, height=75, pady=10, padx=20)
    Globals.midContainer = Frame(mainWindow, width=500, height=225, pady=10, padx=10)
    bottomContainer = Frame(mainWindow, width=500, height=75, pady=10, padx=20)
    
    ''' Place subcontainers in main window. '''
    Globals.treeContainer.grid(row=0, column=0, rowspan=2, sticky=N+S)
    topContainer.grid(row=0, column=1, sticky=E+W+N+S)
    Globals.midContainer.grid(row=1, column=1, sticky=E+W+N+S)
    bottomContainer.grid(row=2, column=1, sticky=E+W+N+S)
    
    
    ''' Create the widgets for top container. New run button right now. '''
    newRunButton = Button(topContainer, text='New Run', font=('Book Antiqua', 10), command=launch)
    welcomeLabel = ttk.Label(topContainer, text='Welcome to MagScreen!', font=('Book Antiqua', 16) )
    blankLabel = ttk.Label(topContainer, text=' ')
    
    ''' Place the widgets in top container. New run button. '''
    newRunButton.pack(side='right', padx=40, pady=10)
    welcomeLabel.pack(side='left', padx=10, pady=10)
    blankLabel.pack(side='left', padx=80, pady=10)
    
    
    ''' Create options entry and button for user to change where the files are saved. Will 
    go in treeContainer.'''
    # Globals.optionsEntry = ttk.Entry(Globals.treeContainer, text=os.getcwd())
    browseButton = ttk.Button(Globals.treeContainer, text='Browse', command=select_directory)
    
    ''' Place options entry and change button into tree container. '''
    # Globals.optionsEntry.pack(side='bottom', fill='x', expand=True, padx=10, pady=10)
    browseButton.pack(side='bottom', fill='x', expand=True, padx=10, pady=10)
    
    
def GUI():
    initializeGUI()
    fileTree()
    mainPage()
    Globals.root.mainloop()