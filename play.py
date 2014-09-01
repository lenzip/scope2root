#!/usr/bin/env python

from ROOT import *
import sys, time
import numpy

from waveform import Waveform

class Analyzer(object):
  def __init__(self,work,drawEvery=10):
    self._work = work
    self.chains = []
    self.drawEvery = drawEvery
    for channel in work.keys():
      print channel
      chain = TChain("tree")
      for filename in work[channel]["files"]:
        chain.Add(filename)
      self.chains.append(chain)  

    self.mainchain = self.chains[0]
    for ichain in range(1,len(self.chains)):
      alias="tree"+str(ichain)
      self.mainchain.AddFriend(self.chains[ichain], alias)  

    self.mainchain.Print("all")  

  def play(self): #, profileC3):
    
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
          theampl = eval("event."+channel+"_ampl")
          thetime = eval("event."+channel+"_time")
          wf = Waveform(thetime, theampl, channel)
          wf.setBaselineLimits(self._work[channel]["baseline"]["limit_low"], self._work[channel]["baseline"]["limit_high"])
          wf.setMaxCalculatorLimits(self._work[channel]["maximum"]["limit_low"], self._work[channel]["maximum"]["limit_high"])
          wf.setAreaCalculatorLimits(self._work[channel]["area"]["limit_low"], self._work[channel]["area"]["limit_high"])
          waveforms[channel] = wf
        
        plots_refs = []
        for i,channel in enumerate(self._work.keys()):
          if self._work[channel]["scaleBy"]!=None:
            waveforms[channel].scaleBy(self._work[channel]["scaleBy"])
          if self._work[channel]["scaleTo"]!="":
            waveforms[channel].scaleTo(waveforms[self._work[channel]["scaleTo"]])
          waveforms[channel].computeAll()
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

      except KeyboardInterrupt:
        a=raw_input("hit a key to continue...")  

    #profile.Draw()
    #return profile

  


work = {#"C2":{      "files": ["C2_Misura 2_ -30 degree_00000.trc.root"],
        #            "scaleBy": 1.,
        #            "scaleTo": "",
        #            "graph": {"ymin": -0.04, "ymax": 0.005},
        #            "histograms":[{"name": "C2_ampl", "nbins": 100, "xmin": 0., "xmax":0.05, "what": "amplitude"}],
        #            "baseline": {'limit_low': 0.1e-6, "limit_high": 0.4e-6},
        #            "maximum": {'limit_low': -20e-9, "limit_high": 20e-9},
        #            "area": {'limit_low': -20e-9, "limit_high": 20e-9}
        #          },
        #"C3":{      "files": ["C3_Misura 2_ -30 degree_00000.trc.root"],
        #            "scaleBy": 1.,
        #            "scaleTo": "",
        #            "graph": {"ymin": -0.5, "ymax": 0.005},
        #            "histograms":[{"name": "C3_ampl", "nbins": 100, "xmin": 0., "xmax":0.5, "what": "amplitude"}],
        #            "baseline": {'limit_low': 0.1e-6, "limit_high": 0.4e-6},
        #            "maximum": {'limit_low': -20e-9, "limit_high": 20e-9},
        #            "area": {'limit_low': -20e-9, "limit_high": 20e-9}
        #          },
         "C4":{     "files": ["C4_Misura BaF_ 90 degree_00000.trc.root"],
                    "scaleBy": 1.,
                    "scaleTo": "",
                    "graph": {"ymin": -5, "ymax": 0.1},
                    "histograms":[#{"name": "C4_area", "nbins": 1000, "xmin": -0.6e-7, "xmax":1e-8, "what": "area"},
                                  {"name": "C4_ampl", "nbins": 1000, "xmin": 0., "xmax":10, "what": "amplitude"}],
                    "baseline": {'limit_low': -0.20e-6, "limit_high": -0.1e-6},
                    "maximum": {'limit_low': -0.1e-6, "limit_high": 4e-6},
                    "area": {'limit_low': -0.1e-6, "limit_high": 4e-6},
                  }          
                  
       }

        

ana=Analyzer(work)
ana.play()


a=raw_input("hit a key to exit...")

