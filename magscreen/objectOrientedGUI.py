# -*- coding: utf-8 -*-
"""
Created on Fri Jul  8 15:12:14 2022

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

class treeFrame(ttk.Frame):
	def __init__(self, container):
		super().__init__(container)
		
		options = {'width':150, 'height':375, 'pady':10, 'padx':10}
		
		# browse button for changing file directory
		self.browseButton = ttk.Button(self, text='Browse')
		self.browseButton['command'] = self.select_directory
		self.browseButton.pack(side='bottom', fill='x', expand=True, padx=10, pady=10)
		
		# show frame
		self.grid(row=0, column=0, rowspan=2, sticky=N+S)
	
		
	# update current working directory
	def updateCWD(self, newpath):
		self.tree.destroy()
		self.listOfDirs = os.listdir(newpath)
		self.dirName = os.path.split(newpath)
		
		# Now create the tree.
		height1 = treeFrame.winfo_screenheight() - 20
		self.tree = ttk.Treeview(self.treeFrame, height=height1)
		self.tree.heading('#0', text=dirName[0], anchor='w')
		
		# add data
		self.tree.insert('', tk.END, text=self.dirName[1], iid=0, open=True)
		
		# adding children of node
		iidCount = 1
		
		for i in range(len(self.listOfDirs)):
			name = self.listOfDirs[i]
			self.tree.insert('', tk.END, text=name, iid=iidCount, open=False)
			self.tree.move(iidCount, 0, i)
        
			iidCount = iidCount + 1
		
		self.tree.pack(side='top', fill='y', expand=True)
		
		return 
		
class topFrame(ttk.Frame):
	def __init__(self, container):
		super().__init__(container)
		
		options = {'width':500, 'height':75, 'pady':10, 'padx':20}
		
		# run button
		self.newRunButton = Button(self, text='New Run', font=('Book Antiqua', 10), command=launch)
		self.newRunButton.pack(side='right', padx=40, pady=10)
		
		# welcome label
		self.welcomeLabel = ttk.Label(self, text='Welcome to MagScreen!', font=('Book Antiqua', 16) )
		self.welcomeLabel.pack(side='left', padx=10, pady=10)
		
		# spacer
		self.blankLabel = ttk.Label(self, text=' ')
		self.blankLabel.pack(side='left', padx=80, pady=10)
		
		# show frame
		self.grid(row=0, column=1, sticky=E+W+N+S)
		
class middleFrame(ttk.Frame):
	def __init__(self, container):
		super().__init__(container)
		
		options = {'width':500, 'height':225, 'pady':10, 'padx':10}
		
		# home screen text and image
		self.main_label = HTMLLabel(self, html="""
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
		
		# show frame
		self.grid(row=1, column=1, sticky=E+W+N+S)
		
# how do I want to do the run frame class?

class App(tk.Tk):
	def __init__(self):
		super().__init__()
		
		# Configure the root window
		self.title('Magscreen')
		self.geometry('840x400')
		self.resizable(0,0)
		
		# set current working directory
		self.cwd = os.getcwd()
		
		# tree frame
		self.tf = treeFrame
		
		# top frame
		self.tpf = topFrame
		
		# middle frame
		self.mdf = middleFrame
		
		# Create menu bar
		self.menubar = Menubar(self)
		self.config(menu=self.menubar)
		
		# add file to menu bar
		self.file_menu = Menu(self.menubar, tearoff=0)
		self.file_menu.add_command(label='New Run', command=launch)
		self.file_menu.add_separator() 
		self.file_menu.add_command(label='Exit', command=self.destroy)
		self.menubar.add_cascade(label="File", menu=self.file_menu, underline=0)
		
		# add view to menu bar
		self.view_menu.add_command(label='Recent')
		self.menubar.add_cascade(label='View', menu=self.view_menu, underline=0)
		
		# add help to menu bar
		self.help_menu = Menu(self.menubar, tearoff=0)
		self.help_menu.add_command(label='Help', command=lambda: showinfo(title='Help', message="""
																	Press NEW RUN for new run. 
																	\nPress BROWSE to change file location. 
																	\nPress FILE, EXIT to close MagScreen.
																	"""))
		self.menubar.add_cascade(label='Help', menu=self.help_menu, underline=0)
		
		
	# select_directory function
	def select_directory(self):
		self.cwd = fd.askdirectory()
		self.updateCWD()
		return
		
		


if __name__ == "__main__":
    app = App()
    app.mainloop()