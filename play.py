#!/usr/bin/env python

from ROOT import *
import sys, time
import numpy
import simplejson 
import timeit

from waveform import Waveform

class Analyzer(object):
  def __init__(self,work,outfilename,drawEvery=10):
    self._work = work
    self._out = TFile(outfilename, "RECREATE")
    self._summarytree = TTree("summary", "summary")
    self._channels = {}
    
    self.chains = []
    self.drawEvery = drawEvery
    for channel in work.keys():
      print channel
      chain = TChain("tree")
      for filename in work[channel]["files"]:
        chain.Add(filename)
      self.chains.append(chain)
      self._channels[channel]={}
      self._channels[channel]['maximum'] = numpy.zeros(1, dtype=float)  
      self._channels[channel]['timecross'] = numpy.zeros(1, dtype=float)
      self._channels[channel]['area'] = numpy.zeros(1, dtype=float)
      self._channels[channel]['baseline'] = numpy.zeros(1, dtype=float)

      self._summarytree.Branch(channel+"_maximum", self._channels[channel]['maximum'], channel+"_maximum/D") 
      self._summarytree.Branch(channel+"_timecross", self._channels[channel]['timecross'], channel+"_timecross/D") 
      self._summarytree.Branch(channel+"_area", self._channels[channel]['area'], channel+"_area/D") 
      self._summarytree.Branch(channel+"_baseline", self._channels[channel]['baseline'], channel+"_baseline/D") 



    self.mainchain = self.chains[0]
    for ichain in range(1,len(self.chains)):
      alias="tree"+str(ichain)
      self.mainchain.AddFriend(self.chains[ichain], alias)  

    self.mainchain.Print("all")  

  def play(self): 
    
    maxhistos=0
    plots = {}
    for chan in self._work.keys():
      plots[chan] = {}
      if len(self._work[chan]["histograms"]) > maxhistos:
        maxhistos = len(self._work[chan]["histograms"])
      for plot in self._work[chan]["histograms"]:
        plots[chan][plot["name"]] = TH1F(plot["name"], plot["name"], plot['nbins'], plot['xmin'], plot['xmax'])
          


    c=TCanvas();
    c.Divide(maxhistos+1,len(work.keys()));
    read=0
    for event in self.mainchain:
      try:
        if read%100== 0:
          print "-->read event", read
        waveforms = {}
        for channel in self._work.keys():
          theampl = eval("event."+self._work[channel]['branch_prefix']+"_ampl")
          thetime = eval("event."+self._work[channel]['branch_prefix']+"_time")
          wf = Waveform(thetime, theampl, channel)
          wf.setBaselineLimits(self._work[channel]["baseline"]["limit_low"], self._work[channel]["baseline"]["limit_high"])
          wf.setMaxCalculatorLimits(self._work[channel]["maximum"]["limit_low"], self._work[channel]["maximum"]["limit_high"])
          wf.setAreaCalculatorLimits(self._work[channel]["area"]["limit_low"], self._work[channel]["area"]["limit_high"])
          wf.setCrossingThresholdSlope(0.5, 'down')
          waveforms[channel] = wf

        plots_refs = []
        for i,channel in enumerate(self._work.keys()):
          if self._work[channel]["scaleBy"]!=None:
            waveforms[channel].scaleBy(self._work[channel]["scaleBy"])
          if self._work[channel]["scaleTo"]!="":
            waveforms[channel].scaleTo(waveforms[self._work[channel]["scaleTo"]])
          waveforms[channel].computeAll()
          self._channels[channel]['maximum'][0] = waveforms[channel].content['maximum']['value']
          self._channels[channel]['baseline'][0] = waveforms[channel].content['baseline']['value']
          self._channels[channel]['area'][0] = waveforms[channel].content['area']['value'] 
          self._channels[channel]['timecross'][0] = waveforms[channel].content['crossings']['value']

          for plot in self._work[channel]["histograms"]:
            plots[channel][plot["name"]].Fill(waveforms[channel].content[plot['what']]["value"])
        if read%self.drawEvery == 0:    
          for i,channel in enumerate(self._work.keys()):  
            c.cd(i+i*maxhistos+1)
            o=waveforms[channel].draw(gPad, self._work[channel]["graph"]["ymin"], self._work[channel]["graph"]["ymax"], "h"+str(read))
            plots_refs.append(o)
            for ip, plot in enumerate(self._work[channel]["histograms"]):
              c.cd(i+i*maxhistos+ip+2)
              plots[channel][plot["name"]].Draw()
          c.Update() 
      
        read+=1
        self._summarytree.Fill()

      except KeyboardInterrupt:
        self._out.cd()
        self._summarytree.Write()
        a=raw_input("hit a key to continue...")  



    a=raw_input("hit a key to continue...")
    self._out.cd()
    self._summarytree.Write()
    #profile.Draw()
    #return profile

  



if len(sys.argv) < 3 or sys.argv[1] == "--help" or sys.argv[1] == "-h":
  print """
  help: python play.py <jsonfile> <outfilename.root>

  the json file contains the work to do in a form like
  {
  "C2_peak":{
  "branch_prefix" : "C2",
  "files": ["C2_Misura 3_ 0 degree_00000.trc.root"],
  "baseline": {"limit_low": -60e-9, "limit_high": -20e-9},
  "maximum": {"limit_low": -20e-9, "limit_high": 20e-9},
  "area": {"limit_low": -20e-9, "limit_high": 20e-9},
  "graph": {"ymin": -0.04, "ymax": 0.005},
  "scaleTo": "",
  "histograms":[{"name": "C2_ampl", "nbins": 100, "xmin": 0.0, "xmax":0.05, "what": "amplitude"}],
  "scaleBy": 1.0}
  }
  
  """
  sys.exit(1)


data=open(sys.argv[1])
work = simplejson.loads(data.read())
print work
a=simplejson.dumps(work)
ana=Analyzer(work, sys.argv[2])
ana.play()


a=raw_input("hit a key to exit...")

