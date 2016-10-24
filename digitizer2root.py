#!/usr/bin/env python

from ROOT import *
import numpy as n
import sys


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
  
  filein = open(filename)
  iev=0
  lasttime = -9999999999999999999
  eventnumber = 1
  for line in filein:
    if "Record Length" in line:
      iev += 1
      if iev%1000 == 0:
         print "-->read event", iev
      first=False
      if not first:
        tree.Fill()
        time.clear()
        ampl.clear()
      isamp = 0.
      nsamples = float(line.split()[2])
      eventStarted=True
      filein.next()
      filein.next()
      filein.next()
      filein.next()
      filein.next()
      filein.next()
    else:
      time.push_back(isamp)
      ampl.push_back(float(line.rstrip()))
      isamp = isamp + 1 


  print "==== Read",iev-1, "events ===="       
  outfile.Write()

if len(sys.argv) < 3 or sys.argv[1] == "--help" or sys.argv[1] == "-h":
  print "help: python digitizer2root.py <txt file name> <string to prepend to each branch name> "
  sys.exit(1)

timemin = -9999999999
timemax = +9999999999
if len(sys.argv)>3:
  timemin = float(sys.argv[3])
if len(sys.argv)>4:
  timemax = float(sys.argv[4])
  
treeFromFile(sys.argv[1], sys.argv[2], "tree", timemin, timemax)        

