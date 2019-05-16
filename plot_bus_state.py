#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu May 16 17:19:48 2019

@author: pedro
"""

import csv
import matplotlib.pyplot

import bus

filename = 'bus-state.tsv'
with open (filename, 'r') as fd:
    reader = csv.reader (fd, delimiter = '\t', quoting = csv.QUOTE_NONNUMERIC)
    data = [row for row in reader]
    figure = matplotlib.pyplot.figure (dpi = 300)
    axes = figure.add_subplot (111)
    mintime = data [0][0]
    maxtime = data [-1][0]
    rngtime = maxtime - mintime
    xs = [row [5] for row in data]
    ys = [row [6] for row in data]
    cs = [
            (0.25, 0, (row [0] - mintime) / rngtime)
            for row in data]
    axes.scatter (xs, ys, c = cs)
    xs = [row [5] for row in data if row [7] == bus.STATE_ENTER_DROP_PASSENGERS]
    ys = [row [6] for row in data if row [7] == bus.STATE_ENTER_DROP_PASSENGERS]
    axes.scatter (xs, ys, c = 'red', marker = 'x')
    figure.show ()
