#!/usr/bin/env python3

# -*- coding: utf-8 -*-
"""
Created on Wed Jul 28 13:52:56 2021

@author: cjdorman
"""

import tldevice
vmr = tldevice.Device('COM5')
file = open('log.tsv','w')
for row in vmr.data.stream_iter():
  rowstring = "\t".join(map(str,row))+"\n"
  print(rowstring)
  file.write(rowstring)
