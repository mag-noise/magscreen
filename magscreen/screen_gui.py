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
from os.path import join as pjoin
import json
import sys
import argparse    
import signal
import threading     # Mostly waiting on I/O so simple threads are okay
import time          # if the data rate needs to go up significantly we
import datetime      # will need to rewrite using the multiprocess module.
import getpass       # Username
import platform      # Hostname
import glob
import magscreen.common as common # Local modules
import magscreen.tlvmr as tlvmr
import magscreen.semcsv as semcsv
import magscreen.plot as plot
import magscreen.summary as summary

import matplotlib.pyplot as plt 

g_sVersion = "magscreen-0.3"

# Global variable and signal handler to halt main data collection loop
g_lCollectors = []
g_display = None
g_bSigInt = False


''' This class will represent the default values helping manage our global
	variables'''
class Globals:
	
	root = None 
	mainFrame = None
	topFrame = None
	window = None 
	default_num_sensors = 5
	selected_num_sensors = None
	sensor_A = 'DT04H6OX'
	sensor_B = 'DT04H6NY'
	sensor_C = 'DT04H6OF'
	sensors = []
	no_sensor = 'N/A'
	default_tech = 'Your name'
	default_part = 'Enter part name'
	default_system = 'Enter system name'
	default_rate = 10
	rate = None
	tech = None
	system = None
	part = None
	
	options = None
	duration = None 
	dur_var = None 
	summary = None 
	sum_var = None
	msg = None 
	msg_var = None
	rate_var = None
	
	progress_bar = None
	
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
	active_so = []
	
	colors = [ 'bisque', 'peach puff', 'azure', 'alice blue', 'lavender',
	       'dim gray', 'slate gray',
		  'gray', 'midnight blue', 'navy', 'cornflower blue', 'dark slate blue',
		  'slate blue','medium blue', 'royal blue',  'blue',
		  'dodger blue', 'sky blue','steel blue',
		  'light blue', 'powder blue', 'turquoise',
		  'cyan','cadet blue', 'aquamarine', 'dark green',
		  'dark sea green', 'sea green', 'medium sea green', 'light sea green','spring green',
          'lime green', 'forest green', 'dark khaki', 'yellow', 'gold', 'goldenrod', 'saddle brown', 'salmon', 
		  'orange', 'dark orange', 'coral', 'red', 'pink', 'maroon', 'violet red']
	


class sensorFrame(ttk.Frame):
	def __init__(self, container):
		super().__init__(container)
		
		''' Create and place sensor combobox. '''
		self.serial = tk.StringVar()
		# self.sensor_cb = ttk.Combobox(self, width=10, textvariable=self.serial, validate="focusout", validatecommand=self.check_cb)
		self.sensor_cb = ttk.Combobox(self, width=10, textvariable=self.serial)
		if len(Globals.sensors) > 1:
			self.sensor_cb["values"] = Globals.sensors
		else:
			self.sensor_cb["values"] = (Globals.sensor_A, Globals.sensor_B, Globals.sensor_C)
		self.sensor_cb['state'] = 'disable'
		self.sensor_cb.pack(side='left', fill='both', padx=30, pady=10)
		
		''' Create and place radii entry. '''
		self.radius = tk.IntVar()
		self.radii = ttk.Entry(self, width=5, textvariable=self.radius,  validate="focusout", validatecommand=self.callback)
		self.radii['state'] = 'disable'
		self.radii.pack(side='left', fill='both', padx=30, pady=10)
		
		''' Get random color from list colors. Add the color to the list of colors being used. Create and place color label. '''
		self.color = Globals.colors[np.random.choice(range(len(Globals.colors)))]
		Globals.color_list.append(self.color)
		self.color_label = Label(self, bg=self.color, width=2)
		self.color_label.pack(side='left', padx=7, pady=10)
	
		''' Create and place checkbutton. Command function is enableDisable. '''
		self.checkbox = ttk.Checkbutton(self, command=lambda: enableDisable(self.winfo_children(), self))
		self.checkbox.pack(side='left', fill='both', padx=15, pady=10)
		
		# show frame
		self.pack(side='top', fill='x')
		
	def callback(sensor_frame):
		if sensor_frame.radius.get() < 0:
			showerror(title='Error', message='Please enter a value greater than 0.')
		else:
			Globals.active_so.append(sensor_frame)
			create_set_up()
		return True

class homepage(ttk.Frame):
	def __init__(self, container):
		super().__init__(container)
		
		self.leftFrame = Frame(container, width=280, height=225, bg='red')
		self.leftFrame.pack(side='left', fill='both', expand=True)
		self.leftFrame.pack_forget()
		
		
		self.rightFrame = Frame(container, width=280, height=225)
		self.rightFrame.pack(side='left', fill='both', expand=True)
		
		self.main_label = HTMLLabel(self.rightFrame, html="""
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
 						   
		self.main_label.pack(pady=20, padx=20, fill='both', expand=True)

	def hide_right(self, frame):
		frame.pack_forget()
		self.leftFrame.pack(side='left', fill='both', expand=True)
		return

class args:
	def __init__(self, duration, radii, serials, message, summary, system, part):
		gmt = time.gmtime(math.ceil(time.time()))
		self.sOutDir = Globals.cwd + '{}{}'.format(os.sep, system) + '{}{}'.format(os.sep, part) + '{}{}-{}-{}T{}-{}-{}'.format(os.sep, gmt[0], gmt[1], gmt[2], gmt[3], gmt[4], gmt[5]) 
		self.sOutDir = self.sOutDir.replace('/','\\')
		self.sRate = int(Globals.rate.get())
		self.sDuration = duration
		self.sRadii = radii
		self.sUarts = serials
		self.sMsg = message
		self.sSummary = summary
		self.PART = part
			
def load():
	# open and load app data
	if (sys.platform == 'win32'):
		
		filename = pjoin(os.environ['APPDATA'], 'magscreen.json')
		
	else:
		
		filename = pjoin(os.environ['HOME'], '.config', 'magscreen.json')
		
	# check to see if file exists
	if not os.path.isfile(filename):
		# dictionary for app data
		data = {}
	
		# get all app data
		data['technician'] = Globals.default_tech
		data['system'] = Globals.default_system
		data['part'] = Globals.default_part
		data['numSensors'] = Globals.default_num_sensors
		data['cwd'] = Globals.cwd
		data['rate'] = Globals.default_rate
		sensors = []
		data['sensors'] = sensors
		data['secondwindow'] = None
	
		if (sys.platform == 'win32'):
			
			filename = pjoin(os.environ['APPDATA'], 'magscreen.json')
			
		else:
				
			filename = pjoin(os.environ['HOME'], '.config', 'magscreen.json')
	
		# write to file 'mydata.json' the dictionary with all current info
		with open(filename, 'w') as f:
			json.dump(data, f)
		
	# open file
	f = open(filename)
	data = json.load(f)
	
	Globals.default_num_sensors = data['numSensors']
	Globals.sensors = []
	for i in data['sensors']:
		Globals.sensors.append(i)
	Globals.rate = data['rate']
	Globals.cwd = data['cwd']
	Globals.default_tech = data['technician']
	Globals.default_system = data['system']
	Globals.default_part = data['part']
	Globals.secondWindow = data['secondwindow']
	
	# close file
	f.close()
	
	return

def save():
	# dictionary for app data
	data = {}
	
	# get all app data
	data['technician'] = Globals.tech.get()
	data['system'] = Globals.system.get()
	data['part'] = Globals.part.get()
	if len(Globals.so) > 2:
		data['numSensors'] = len(Globals.so)
	else:
		data['numSensors'] = Globals.default_num_sensors
		
	for i in Globals.so:
		sensor_serial = i.sensor_cb.get()
		if sensor_serial not in Globals.sensors:
			Globals.sensors.append(sensor_serial)
		
	data['sensors'] = Globals.sensors
	data['cwd'] = Globals.cwd
	data['rate'] = Globals.rate.get()
	data['secondwindow'] = None
	
	if (sys.platform == 'win32'):
		
		filename = pjoin(os.environ['APPDATA'], 'magscreen.json')
		
	else:
		
		filename = pjoin(os.environ['HOME'], '.config', 'magscreen.json')
	
	# write to file 'mydata.json' the dictionary with all current info
	with open(filename, 'w') as f:
		json.dump(data, f)
	
	# quit app
	Globals.root.destroy()
	return 
	
def setDone():
	"""Function triggered by a timer alarm that is setup in main()"""
	global g_lCollectors
	for col in g_lCollectors:
		col.stop()
		col.close()
	if g_display != None:
		print('gui stop')
		g_display.stop()
	print('setDone is workin')

def setQuit():
	"""Signal handler for CTRL+C from the keyboard"""
	global g_bSigInt
	g_bSigInt = True      # Indicates early exit
	print('setQuit is workin')
	setDone()
	
def _test_properties(sPart, sComments=None):
	"""Return a dictionary of basic properties for a screening test"""
	d = {
		'Part':sPart,
		'Timestamp': time.strftime('%Y-%m-%dT%H:%M:%S%z'), # Use ISO 8601 local times
		'User': getpass.getuser(),
		'Host': platform.node().lower(),
		'Version':g_sVersion
	}

	if sComments: d['Note'] = sComments.replace('"',"'")
	return d		

''' Function changes current working directory. Calls function to remake tree.'''	
def select_directory():
	Globals.cwd = fd.askdirectory()
	updateCWD()
	return

''' Function enables and disables the sensor combobox and radii entry widget corresponding to the check button clicked.'''
def enableDisable(children, sensor):	
	combobox = children[0]
	entry = children[1]
	if ('normal' in str(combobox['state'])):
		combobox.configure(state='disable')
		entry.configure(state='disable')
		i = Globals.active_so.index(sensor)
		del Globals.active_so[i]
		
	else:
		combobox.configure(state='normal')
		entry.configure(state='normal')
		
	create_set_up()
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
		
		if last_sensor in Globals.active_so:
			i = Globals.active_so.index(last_sensor)
			del Globals.active_so[i]
			
		last_sensor.destroy()
		Globals.so = Globals.so[:-1]
		Globals.color_list = Globals.color_list[:-1]
		
		create_set_up()
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
		shifty = int(5.3*int(radii_list[i])*math.sin(theta))
		shiftx = int(5.3*int(radii_list[i])*math.cos(theta))
		
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
			
		elif (theta == (3*pi/2)):
			y1 = (-12) + centerY + shifty
			x1 = (5) + centerX + shiftx
			y2 = (12) + centerY + shifty
			x2 = (-5) + centerX + shiftx
			
			lPts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
			
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
			
		elif (theta == (pi/2)):
			y1 = (-12) + centerY + shifty
			x1 = (5) + centerX + shiftx
			y2 = (12) + centerY + shifty
			x2 = (-5) + centerX + shiftx
			
			lPts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
		  
		Globals.color_canvas.create_polygon(lPts, fill=clr[i])
		
		# rotate the rectangle
		theta = theta + incr
	return 
	
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

	
''' Messing around with a rerun function. Will be called in the runFunc to prepare run window for new run. '''
def rerun():
	create_set_up()
	print(page.rightFrame)
	page.hide_right(page.rightFrame)
	
	return
	
''' Function calls screen.py and passes in params.'''
def runFunc():
	global g_lCollectors
	# sDuration, sMsg, and sSummary all need to be set up. Using defaults currently
	
	if (Globals.msg == None) or (Globals.msg.get() == ''):
		defaultMessage = 'This will be a one lined string to be saved with data.'
	else:
		defaultMessage = Globals.msg.get()
		
	if (Globals.summary == None) or (Globals.summary.get() == ''):
		defaultSummary = "ScreenResults.csv"
	else:
		defaultSummary = Globals.summary.get()
	
	strRadii = ''
	strSerials = ''
	# get radii
	count = 0
	nSensors = 0
	for sensor in Globals.so:
		radii_entry = sensor.radii
		sensor_serial = sensor.sensor_cb
		if ('normal' in str(radii_entry['state'])):
			nSensors += 1 								# See how many sensors we're going to use
			radius = str(radii_entry.get())
			serial = sensor_serial.get()
			if count == 0:
				strRadii = radius
				strSerials = serial
			else:
				strRadii = strRadii + ',' + radius
				strSerials = strSerials + ',' + serial
		count += 1
			
	# int(Globals.duration.get())	
	opts = args(10, strRadii, strSerials, defaultMessage, defaultSummary, Globals.system.get(), Globals.part.get())
	
	duration = int(Globals.duration.get())
	print(duration)
	print('why is this running')
	sRate = int(Globals.rate.get())
	print(sRate)   
	print(type(sRate))
	
	# Since SIGALRM isn't available on Windows, spawn a thread to countdown to
	# the end of the data collection period, check user supplied time
	if duration < 1 or duration > 60*60:
		showerror(title="Error", message="ERROR: Test sDuration must be between 1 second and 1 hour\n")
		return 7
	
	# Set at X samples per second per sensor, should be no more then
	# 10 samples per second so that slow python code can keep up
	if (int(Globals.rate.get()) < 1) or (int(Globals.rate.get()) >= 200):
		showerror(title="Error", message="ERROR: Requested sample rate %d is out of expected range 1 to 200 (Hz)."%int(Globals.rate.get()))
		return 8
	
	# Check how many sensors we're going to use
	lDist = [int(s.strip(),10) for s in opts.sRadii.split(',')]
	if nSensors < 1:
		showerror(title="Error", message="ERROR: At least one measurement distance must be given via -r\n")
		return 9
	
	lSerial = [s.strip() for s in opts.sUarts.split(',')]
	if len(lSerial) < nSensors:
		showerror(title="Error", message="ERROR: %d UARTs are required for measurements at %d distances.\n"%(
			nSensors, nSensors
		))
		return 10
	
	rTime0 = time.time()  # Current unix time in floating point seconds	
	g_bSigInt = False    # Global interrupt flag
	
	print('line 640')
	# Check that our non-empty sensors can be distinguished from each other
	g_lCollectors = []
	for i in range(nSensors):
		lTest = []
		for j in range(nSensors): 
			if (j != i): lTest.append(lSerial[j])
		if lSerial[i] in lTest:
			showerror(title="Error", message="ERROR: UART serial number %s is not unique in %s!\n"%(lSerial[i], opts.sUarts))
			return 13

		try:
			g_lCollectors.append(tlvmr.VMR('%d'%i, lSerial[i], sRate))
		except OSError as e:
			# perr("ERROR: %s\n"%e)
			showinfo(title="HINT", message='HINT:  Sensors can be ignored by requesting data at fewer distances.')
			print(type(e))
			showerror(title="Error", message='Error: {}'.format(e))
			# perr('  Use -h for more info.\n')
			return 15

		g_lCollectors[-1].set_time0(rTime0)
		g_lCollectors[-1].set_dist(lDist[i])

	if len(g_lCollectors) == 0:
		showinfo(title="Information", message='INFO:  No data collection ports specified, successfully did nothing.\n')
		return 0
	
	# Create a display output thread
	showinfo(title="Information", message="Use the 'Quit' button to quit early")
	
	global g_display
	g_display = common.Display("MSG:   Collecting ~%d seconds of data "%duration)
	
	# create an alarm thread to stop taking data
	alarm = threading.Timer(duration + (time.time() - rTime0), setDone)
	print('line 671')
	print(g_lCollectors)
	# Start all the threads
	for collector in g_lCollectors:
		collector.start()
	alarm.start()
	g_display.start()
	
	#start progress bar
	Globals.progress_bar.start()
	
	print('line 679')
	# Wait on all my threads to exit
	for collector in g_lCollectors:
		print('this loop is goin')
		if collector:
			collector.join()
	print('we made it')
	g_display.join()
	
	print('line 686')
	alarm.cancel() # Cancel the alarm if it hasn't gone off
	Globals.progress_bar.stop() 		# stop progress bar
	# perr('\n')
	if g_bSigInt:
		showwarning(title="Warning", message='WARN:  Data collection terminated, no output written\n')
		return 4  # An error return value
	
	# Save raw-data from collectors
	#sFile = pjoin(opts.sOutDir, "%s.csv"%(common.safe_filename(opts.PART)+str(time.strftime('%Y_%m_%dT%H_%M_%S'))))
	
	print(opts.sOutDir)
	sFile = pjoin(opts.sOutDir, "{}.csv".format('timeseries'))
	sTitle = "Magnetic Screening Test, Raw Data"
	tlvmr.write_mag_vecs(
		sFile, g_lCollectors, sTitle, _test_properties(opts.PART, opts.sMsg)
	)

	print('699')
	# Plot time series and PSD of the raw data, as a cross check
	(dProps, lDatasets) = semcsv.read(sFile)
	subSum = pjoin(sFile, sFile.replace('timeseries.csv', 'summary_plot.pdf'))
	subPng = pjoin(sFile, sFile.replace('timeseries.csv', 'summary_plot.png'))
	print(subSum)
	print(subPng)
	plot.screen_plot_pdf(dProps, lDatasets, subSum)
	plot.screen_plot_png(dProps, lDatasets, subPng)
	
	# Open the roll-up info file (or create one if it doesn't exist)
	if os.sep not in opts.sSummary:
		opts.sSummary = pjoin(opts.sOutDir, opts.sSummary)
	
	summary.append(opts.sSummary, dProps, lDatasets)
	showinfo(title="Information", message="INFO:  Summary appended to {}".format(opts.sSummary))
	
	stemp = ("%s%s*p1.png"%(opts.sOutDir, os.sep)).replace('/','\\')
	stemp2 = ("%s%s*p2.png"%(opts.sOutDir, os.sep)).replace('/','\\')
	print(stemp)
	print(stemp2)
	
	lFiles = glob.glob(stemp) 
	lFiles += glob.glob(stemp2)
	dRep={'file1':lFiles[0], 'file2':lFiles[1]}
	
	sDoc = """
	<html>
	<body>
	<pre>
	file://%(file1)s
	</pre>
	<img src="%(file1)s" >
	
	<img src="%(file2)s" >
	
	</body>
	</html>
	"""%dRep
	imageOne = HTMLLabel(page.leftFrame, html=sDoc)
	#imageTwo = HTMLLabel(page.leftFrame, html="""<img src='{}.p2.png'.format(opts.sOutDir)>""")
	imageOne.pack(fill='both', expand=True)
	rerun()
	return 0  # An all-okay return value
	

def runbut():
	threading.Thread(target=runFunc).start()
	return
	
''' Function creates second window with all the options for a run. '''	
def launch():
	if (Globals.options != None):
		Globals.options.deiconify()
	else:
		optionsWindow()
		Globals.options.withdraw()
	
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
	topFrame.grid(row=0, sticky='nsew')
	secondFrame.grid(row=1, sticky='ew')
	middleFrame.grid(row=2, sticky='nsew')
	bottomFrame.grid(row=3, sticky='nsew')
	bottomFrame2.grid(row=4, sticky='ew')
   
	''' Create the widgets for top frame. These include technician label and entry,
	part label and entry, and system label and entry. '''
	tech_label = ttk.Label(topFrame, text="Technician:", font=("Calibri", 12))
	Globals.tech = ttk.Entry(topFrame, textvariable=Globals.default_tech)
	Globals.tech.insert(0, Globals.default_tech)
   
	part_label = ttk.Label(topFrame, text="Part:", font=('Calibri', 12))
	Globals.part = ttk.Entry(topFrame)
	Globals.part.insert(0, Globals.default_part)
   
	system_label = ttk.Label(topFrame, text="System:", font=("Calibri", 12))
	Globals.system = ttk.Entry(topFrame)
	Globals.system.insert(0, Globals.default_system)
   
	''' Placing the widgets in the top frame. '''
	tech_label.pack(fill='x', side='left')
	Globals.tech.pack(fill='x', side='left', padx=10)
	
	system_label.pack(fill='x', side='left', padx=10)
	Globals.system.pack(fill='x', side='left', padx=5)
   
	part_label.pack(fill='x', side='left', padx=10)
	Globals.part.pack(fill='x', side='left', padx=5)
	
   
	''' Create widgets for second frame. This is the combobox for number of sensors 
	   being used. '''
	
	addSensorButton = ttk.Button(secondFrame, text='Add New Sensor', width = 20, command=add_new_sensor)
   
	removeSensorButton = ttk.Button(secondFrame, text='Remove Sensor', width=20, command=remove_sensor)
	
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
	Globals.rate_var = tk.IntVar
	Globals.rate = ttk.Entry(bottomFrame, width='10')
	Globals.rate.insert(0, Globals.default_rate)
	
	options = ttk.Button(bottomFrame, text='Options', width=40, command=optionsWindow)		# Need to create funtion and add command for Option button  
	# ready = ttk.Button(bottomFrame, text='Ready', width=15, command=create_set_up)
   
	''' Place widgets into bottom frame. '''
	rate_label.pack(side='left', padx=25, pady=5)
	Globals.rate.pack(side='left', padx=25, pady=5)
   
	options.pack(side='right', fill='both', padx=25, pady=5)
	# ready.pack(side='left', fill='both', expand=True, padx=25, pady=5)
   
	''' Create widgets for bottomFrame2. This will be progress bar, clear all button, and run button'''
	quitButton = ttk.Button(bottomFrame2, text='Quit', width=15, command=setQuit)	# Need to create funtion and add command for Clear all button
   
	run = ttk.Button(bottomFrame2, text='Run', width=15, command=runbut)		# Need to add command to run button
   
	# Progress bar mode can be set to determinant once I know how to measure relative progress of the program.
	# Could possibly set it so if it takes more than 22 seconds it displays bad run or error???
	Globals.progress_bar = ttk.Progressbar(bottomFrame2, orient='horizontal', length='300', mode='indeterminate')  
   
	''' Place widgets in bottomFrame2. '''
   
	Globals.progress_bar.pack(side='left', padx=25, pady=5)
   
	quitButton.pack(side='left', fill='x', padx=25, pady=5)
   
	run.pack(side='left', fill='x', padx=25, pady=5)
		
	Globals.secondWindow.protocol("WM_DELETE_WINDOW", hide)
	return

''' Function creates options window which houses duration, summary and message options. '''
def optionsWindow():
	if (Globals.options != None):
		Globals.options.deiconify()
		return
	Globals.options = Toplevel()
	# Globals.options.grab_set()
	Globals.options.title('Options')
	Globals.options.geometry('330x150')
	
	# creating frame for options window
	frameOne = Frame(Globals.options, width=280, height=50, padx=10, pady=5)
	frameOne.pack(side='top', fill='x', expand=True)
	
	frameTwo = Frame(Globals.options, width=280, height=50, padx=10, pady=5)
	frameTwo.pack(side='top', fill='x', expand=True)
	
	frameThree = Frame(Globals.options, width=280, height=50, padx=10, pady=5)
	frameThree.pack(side='top', fill='x', expand=True)
	
	# creating widgets for options window
	duration_label = ttk.Label(frameOne, text='Duration [s]:')
	Globals.dur_var = tk.IntVar()
	Globals.duration = ttk.Entry(frameOne, width='10', textvariable=Globals.dur_var)
	Globals.duration.delete(0,'end')
	Globals.duration.insert(0,20) 		# inserting default 20 second duration value 
	
	summary_label = ttk.Label(frameTwo, text='Summary:')
	Globals.sum_var = tk.StringVar()
	Globals.summary = ttk.Entry(frameTwo, width='35', textvariable=Globals.sum_var)
	Globals.summary.insert(0, "ScreenResults.csv") 		# inserting default summary
	
	msg_label = ttk.Label(frameThree, text='Message:')
	Globals.msg_var = tk.StringVar()
	Globals.msg = ttk.Entry(frameThree, width='35', textvariable=Globals.msg_var)
	
	# placing widgets in opionts window frame
	duration_label.pack(side='left', padx=5)
	Globals.duration.pack(side='left', padx=10)
	
	summary_label.pack(side='left', padx=5)
	Globals.summary.pack(side='left', padx=10)
	
	msg_label.pack(side='left', padx=5)
	Globals.msg.pack(side='left', padx=15)
	
	Globals.options.protocol("WM_DELETE_WINDOW", hideOW)
	
	return 
	
''' Function closes or hides Options window. '''
def hideOW():
	Globals.options.withdraw()
	return
	
''' Function closes or hides run window. '''
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
	load()
	fileTree()
	# mainPage()
	page = mp(Globals.midContainer)
	Globals.root.protocol("WM_DELETE_WINDOW", save)
	Globals.root.mainloop()
	
initializeGUI()
load()
fileTree()
# mainPage()
page = homepage(Globals.midContainer)
Globals.root.protocol("WM_DELETE_WINDOW", save)
Globals.root.mainloop()
