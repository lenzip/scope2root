#!/usr/bin/env python

from ROOT import *
import numpy as n
import sys

import lecroy

def treeFromFile(filename, branchroot, treename, timemin=-9999999999, timemax=+999999999):
  basename = filename.rstrip('.txt')
  basenamesplit = basename.split('/')
  basename = basenamesplit[-1] 
  outfile = TFile(basename+'.root', "RECREATE")
  outfile.cd()
  tree = TTree(treename, treename);
  time = vector('float')()
  ampl = vector('float')()

  # create the branches and assign the fill-variables to them
  tree.Branch(branchroot+'_time', time) #, 'time/D')
  tree.Branch(branchroot+'_ampl', ampl) #, 'ampl/D')
  
  #f = open(filename)
  converted = lecroy.read_timetrace(filename)
  lasttime = -9999999999999999999
  eventnumber = 1
  for thewaveform in converted:
    #print thewaveform
    #print converted[0]
    eventnumber += 1
    if eventnumber%100 == 0:
      print "-->read event", eventnumber
    for thetime, theampl in n.nditer([thewaveform[0], thewaveform[1]]):  
      if thetime > timemin and thetime < timemax:
        time.push_back(thetime)
        ampl.push_back(theampl)
    tree.Fill()
    time.clear() 
    ampl.clear()
  print "==== Read",eventnumber-1, "events ===="       
  outfile.Write()

if len(sys.argv) < 3 or sys.argv[1] == "--help" or sys.argv[1] == "-h":
  print "help: python scope2root.py <txt file name> <string to prepend to each branch name> "
  sys.exit(1)

timemin = -9999999999
timemax = +9999999999
if len(sys.argv)>3:
  timemin = float(sys.argv[3])
if len(sys.argv)>4:
  timemax = float(sys.argv[4])
  
treeFromFile(sys.argv[1], sys.argv[2], "tree", timemin, timemax)        

