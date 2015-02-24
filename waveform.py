import numpy as np
from ROOT import * 
import operator

class Calculator(object):
  def __init__(self, waveform, step):
    self._isCached = False
    self._value = None
    self._waveform = waveform
    self._step = step

  def _compute(self):
    pass 
  
  def reset(self):
    self._isCached = False
    self._value = None
    self._time=None

  def value(self):
    if self._isCached:
      #print "Cached"
      return self._value
    else:
      #print "Computing..."
      self._compute()
      return self._value

#computes the baseline as a median
class BaselineCalculator(Calculator):
  def __init__(self, waveform, step, timemin=-float('Inf'), timemax=float('Inf')):
    super(BaselineCalculator, self).__init__(waveform, step)
    self._timemin = timemin
    self._timemax = timemax
  
  def setLimits(self, timemin=-float('Inf'), timemax=float('Inf')):
    self._timemin = timemin
    self._timemax = timemax
    self._isCached = False

  def _compute(self):
    ampls = []
    for i in range(0, len(self._waveform._time), self._step):
      if self._waveform._time[i] > self._timemin and self._waveform._time[i] <self._timemax:
        ampls.append(self._waveform._ampl[i])
    self._value = np.median(ampls)
    self._isCached = True
    
#computes the maximum
class MaxCalculator(Calculator):
  def __init__(self, waveform, step, timemin=-float('Inf'), timemax=float('Inf')):
    super(MaxCalculator, self).__init__(waveform, step)
    self._timemin = timemin
    self._timemax = timemax

  def setLimits(self, timemin=-float('Inf'), timemax=float('Inf')):
    self._timemin = timemin
    self._timemax = timemax
    self._isCached = False

  def _compute(self):
    ampls = []
    times = []
    for i in range(0, len(self._waveform._time), self._step):
      if self._waveform._time[i] > self._timemin and self._waveform._time[i] <self._timemax:
        ampls.append(self._waveform._ampl[i])
        times.append(time)
    self._value = min(ampls)
    
    self._isCached = True

class AreaCalculator(Calculator):
  def __init__(self, waveform, baselineCalc, step, timemin=-float('Inf'), timemax=float('Inf')):
    super(AreaCalculator, self).__init__(waveform, step)
    self._timemin = timemin
    self._timemax = timemax
    self._baselineCalc = baselineCalc

  def setLimits(self, timemin=-float('Inf'), timemax=float('Inf')):
    self._timemin = timemin
    self._timemax = timemax
    self._isCached = False

  def _compute(self):
    self._baselineCalc._compute()
    baseline = self._baselineCalc.value()
    self._value = 0.
    for i in range(self._step, len(self._waveform._time), self._step):
      time = self._waveform._time[i]
      if time > self._timemin and time < self._timemax:
        timebf = self._waveform._time[i-self._step]
        ampl   = self._waveform._ampl[i]-baseline
        amplbf = self._waveform._ampl[i-self._step]-baseline
        timstep = time-timebf
        av_ampl = (ampl+amplbf)/2
        self._value += av_ampl*timstep

class CrossingThresholdCalculator(Calculator):
  def __init__(self, waveform, maxc, step):
    super(CrossingThresholdCalculator, self).__init__(waveform, step)
    self._maxc = maxc

  def setThreshold(self, threshold):
    self._threshold = threshold
    self._isCached=False
  
  def setSlope(self, slope):
    self._slope = slope
    self._isCached=False  

  def _compute(self):
    self._value = float('Nan') 
    self._maxc._compute()
    threshold = self._maxc.value()*self._threshold
    for i in range(self._step, len(self._waveform._time), self._step):
      ampl   = self._waveform._ampl[i]
      amplbf = self._waveform._ampl[i-self._step]
      if self._slope=="up":
        condition = True if ampl > threshold and amplbf < threshold else False
      if self._slope=="down":
        condition = True if ampl < threshold and amplbf > threshold else False
      if condition:
        self._value = self._waveform._time[i]
        self._isCached=True
        break
     
      

class Waveform:
  def __init__(self, time, ampl, name, step=1):
    self._initialize(time, ampl, name)

    self.content["baseline"]={'limit_low': -float('Inf'), "limit_high": float('Inf'), "value": float('Nan')}
    self.content["maximum"]={'limit_low': -float('Inf'), "limit_high": float('Inf'), "value": float('Nan')}
    self.content["area"]={'limit_low': -float('Inf'), "limit_high": float('Inf'), "value": float('Nan')}
    self.content["crossings"]={'threshold': float('Nan'), "slope": "undefined", "value": float('Nan')}
    self.content['amplitude']={'value':float('Nan')}
    self.blc  = BaselineCalculator(self, step)
    self.maxc = MaxCalculator(self, step)
    self.thcl = CrossingThresholdCalculator(self, self.maxc, step)
    self.areac = AreaCalculator(self, self.blc, step)
    self.calculators = [self.blc, self.maxc, self.thcl, self.areac]

  def _initialize(self, time, ampl, name):
    self._time = time
    self._ampl = ampl
    self._name = name
    self._g     = TGraph(len(self._ampl), np.array(self._time), np.array(self._ampl))
    if getattr(self, "content", None) == None:
      self.content = {}
    self.content["graph"] = self._g

  def scaleTo(self, waveform, what, norm=1.):
    scalevalue = waveform.content[what]["value"]/norm
    self.scaleBy(scalevalue)
 
  def scaleBy(self, value):
    #print "inizio"
    #print np.array(self._ampl) 
    newamp =  [x*value for x in self._ampl]
    self._ampl = newamp 
    #print np.array(self._ampl)
    self._initialize(self._time, self._ampl, self._name)
    for calc in self.calculators:
      calc.reset()


  def setBaselineLimits(self, timemin=-float('Inf'), timemax=float('Inf')):
    self.blc.setLimits(timemin, timemax)
    self.blc.reset()
    self.content["baseline"]['limit_low'] = timemin
    self.content["baseline"]['limit_high'] = timemax


  def setMaxCalculatorLimits(self, timemin=-float('Inf'), timemax=float('Inf')):
    self.maxc.setLimits(timemin, timemax)
    self.maxc.reset()
    self.content["maximum"]['limit_low'] = timemin
    self.content["maximum"]['limit_high'] = timemax
  
  def setAreaCalculatorLimits(self, timemin=-float('Inf'), timemax=float('Inf')):
    self.areac.setLimits(timemin, timemax)
    self.areac.reset()
    self.content["area"]['limit_low'] = timemin
    self.content["area"]['limit_high'] = timemax 

  
  def setCrossingThresholdSlope(self, threshold, slope):
    self.thcl.setThreshold(threshold)
    self.thcl.setSlope(slope)
    self.thcl.reset()
    self.content["crossings"]['threshold'] = threshold
    self.content["crossings"]['slope'] = slope

  def computeBaseline(self):
    self.content['baseline']['value'] = self.blc.value()
    return self.content['baseline']['value']

  def computeMax(self):
    self.content["maximum"]['value'] = self.maxc.value()
    return self.content["maximum"]['value'] 
  
  def computeAmplitude(self):
    self.content['amplitude']['value'] = abs(self.computeMax()-self.computeBaseline())
    return self.content['amplitude']['value']

  def computeArea(self):
    self.content['area']['value'] = self.areac.value()
    return self.content['area']['value']

  def computeCrossing(self):
    self.content["crossings"]["value"] = self.thcl.value()
    return self.content["crossings"]["value"]

  def computeAll(self):
    self.computeBaseline()
    self.computeMax()
    self.computeAmplitude()
    self.computeCrossing()
    self.computeArea()
    

  def draw(self, canvas, ymin, ymax, name):
    canvas.cd()
    g=self.content["graph"]
    g.SetNameTitle(name, name)
    g.SetMarkerStyle(1)
    lbl=TLine(self.content["baseline"]["limit_low"], ymin, self.content["baseline"]["limit_low"], ymax)
    lbh=TLine(self.content["baseline"]["limit_high"], ymin, self.content["baseline"]["limit_high"], ymax)
    lbv=TLine(self.content["baseline"]["limit_low"],  self.content["baseline"]['value'], self.content["baseline"]["limit_high"], self.content["baseline"]['value'])
    lbl.SetLineStyle(2)
    lbh.SetLineStyle(2)
    lbl.SetLineColor(2)
    lbh.SetLineColor(2)
    lbv.SetLineStyle(1)
    lbv.SetLineColor(2)
    lbv.SetLineWidth(2)


    lml=TLine(self.content["maximum"]["limit_low"], ymin, self.content["maximum"]["limit_low"], ymax)
    lmh=TLine(self.content["maximum"]["limit_high"], ymin, self.content["maximum"]["limit_high"], ymax)
    lmv=TLine(self.content["maximum"]["limit_low"], self.content["maximum"]['value'], self.content["maximum"]["limit_high"], self.content["maximum"]['value'])
    lml.SetLineStyle(2)
    lmh.SetLineStyle(2)
    lml.SetLineColor(3)
    lmh.SetLineColor(3)
    lmv.SetLineStyle(1)
    lmv.SetLineColor(3)
    lmv.SetLineWidth(2)
    linecross = TLine(self.content["crossings"]["value"], ymin, self.content["crossings"]["value"], ymax)
    linecross.SetLineStyle(3)
    linecross.SetLineColor(4)
    

    mg=TMultiGraph()
    mg.Add(g)
    mg.Draw("A")
    h=mg.GetHistogram()
    h.GetYaxis().SetRangeUser(ymin, ymax)
    h.Draw()
    mg.Draw("pl")
    lbl.Draw("same")
    lbh.Draw('same')
    lbv.Draw('same')

    lml.Draw("same")
    lmh.Draw('same')
    lmv.Draw('same')
    linecross.Draw('sames')
    return [mg, lbl, lbh, lbv, lml, lmh, lmv, linecross]


    

if __name__ == "__main__":

  file = TFile("C2_Misura 2_ 0 degree_00000.trc.root")
  tree = file.Get("tree")
  for event in tree:
    theampl = event.C2_ampl
    thetime = event.C2_time

    waveform = Waveform(thetime, theampl, "C2")
    print waveform.computeBaseline()
    print waveform.computeMax()
    print waveform.computeAmplitude()
    print waveform.computeCrossing()

