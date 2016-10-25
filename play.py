#!/usr/bin/env python

from ROOT import *
import sys, time
import numpy
import simplejson 
import timeit
import optparse

from waveform import Waveform

class Analyzer(object):
  def __init__(self,work,outfilename, first, last, batch, drawEvery=5):
    self._work = work
    self._out = TFile(outfilename, "RECREATE")
    self._summarytree = TTree("summary", "summary")
    self._channels = {}
    self._first = first
    self._last = last
    self.drawEvery = drawEvery
    self._batch = batch
    
    self.chains = []
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
          


    if not self._batch:
      c=TCanvas();
      c.Divide(maxhistos+1,len(work.keys()));
    read=0
    for event in self.mainchain:
    #for event in self.mainchain:
      try:
        if read < self._first:
          read += 1 
          #print "moving forward"
          continue
        if self._last != -1 and read >= self._last:
          break
        if read%100== 0:
          print "-->read event", read
        waveforms = {}
        for channel in self._work.keys():
          theampl = eval("event."+self._work[channel]['branch_prefix']+"_ampl")
          thetime = eval("event."+self._work[channel]['branch_prefix']+"_time")
          waveforms[channel] = None
          if len(thetime) > 0:
            wf = Waveform(thetime, theampl, channel, 1, self._batch)
            wf.setBaselineLimits(self._work[channel]["baseline"]["limit_low"], self._work[channel]["baseline"]["limit_high"])
            wf.setMaxCalculatorLimits(self._work[channel]["maximum"]["limit_low"], self._work[channel]["maximum"]["limit_high"])
            wf.setAreaCalculatorLimits(self._work[channel]["area"]["limit_low"], self._work[channel]["area"]["limit_high"])
            #wf.setCrossingThresholdSlope(0.5, 'down')
            waveforms[channel] = wf
          del theampl
          del thetime
          
        plots_refs = []
        for i,channel in enumerate(self._work.keys()):
          if waveforms[channel] == None:
            continue
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
        if not self._batch:
          if read%self.drawEvery == 0:    
            for i,channel in enumerate(self._work.keys()): 
              c.cd(i+i*maxhistos+1)
              if waveforms[channel] == None:
                continue;
              o=waveforms[channel].draw(gPad, self._work[channel]["graph"]["ymin"], self._work[channel]["graph"]["ymax"], "h"+str(read))
              plots_refs.append(o)
              for ip, plot in enumerate(self._work[channel]["histograms"]):
                c.cd(i+i*maxhistos+ip+2)
                plots[channel][plot["name"]].Draw()
            c.Update()
        for i,channel in enumerate(self._work.keys()):  
          if waveforms[channel] != None:
            waveforms[channel].clear()
            del waveforms[channel]
        read+=1
        self._summarytree.Fill()

      except KeyboardInterrupt:
        self._out.cd()
        self._summarytree.Write()
        a=raw_input("hit a key to continue...")  

  
       
    self._out.cd()
    self._summarytree.Write()
    if not self._batch:
      a=raw_input("hit a key to continue...")

  
usage="""
  help: python [options] play.py <jsonfile> <outfilename.root>

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


parser = optparse.OptionParser(usage)
parser.add_option('-f', dest='first', help="first event", default=0, action='store', type='int')
parser.add_option('-l', dest='last', help="last event", default=-1, action='store', type='int')
parser.add_option('-b', dest='batch', help="run in batch mode", default=False, action='store_true')
parser.add_option('-p', dest='polarity', help="signal polarity (pos, neg) default pos", default="pos", action='store')

(opt, args) = parser.parse_args()
if len(args)<2 :
  parser.print_help()
  sys.exit(1)


data=open(args[0])
work = simplejson.loads(data.read())
print work
a=simplejson.dumps(work)
ana=Analyzer(work, args[1], opt.first, opt.last, opt.batch)
ana.play()


#a=raw_input("hit a key to exit...")

