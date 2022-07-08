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
		
		# Create menu bar
		self.menubar = Menubar(self)
		self.config(menu=self.menubar)
		
		
	# select_directory function
	def select_directory(self):
		self.cwd = fd.askdirectory()
		self.updateCWD()
		return
		
		


if __name__ == "__main__":
    app = App()
    app.mainloop()