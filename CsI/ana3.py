#!/bin/env python

from ROOT import *
import sys
from array import array
import math

def fit(hist, color, pos=True, modelname='full', fitres=None):
  r=RooRealVar("r", "r", -1, 1)
  r.setBins(40)
  data = RooDataHist(hist.GetName(), hist.GetName(), RooArgList(r), hist)
  sigma = RooRealVar("sigma", "sigma", 0, 1)
  mu = RooRealVar("mu", "mu", -1, 1)
  mubg = RooRealVar("mubg", "mubg", -1, 1)
  sigma2 = RooRealVar("sigma2", "sigma2", 0.1, 2)
  if pos:
    alpha = RooRealVar("alpha", "alpha", 0, 1)
  else:
    alpha = RooRealVar("alpha", "alpha", -1, 0)
  n = RooRealVar("n", "n", 0, 100)
  f = RooRealVar("f", "f", 0, 1)
  bg = RooCBShape("bif", "bif", r, mubg, sigma2, alpha, n)
  ga = RooGaussian("g", "g", r, mu, sigma)
  if fitres != None:
    parameters = fitres.floatParsFinal()
    mu.setVal(parameters.at(parameters.index("mu")).getVal())
    mu.setConstant()
    sigma.setVal(parameters.at(parameters.index("sigma")).getVal())
    sigma.setConstant()
    print "*******SETTING CONSTANT PARAMETERS***********"
  if modelname=='full':
    model = RooAddPdf("model", "model", bg, ga, f)
  elif modelname=='gauss':
    model = ga
  else:
    model = bg
  res = model.fitTo(data, RooFit.Save(True), RooFit.PrintLevel(-1))
  #fu = model.asTF(RooArgList(r), RooArgList(sigma, mu, mubg, sigma2, alpha, f, n))
  #print fu
  maximumat = 0#fu.GetMaximumX()
  print "maximum at", maximumat
  plot = r.frame(RooFit.Name("frame"+hist.GetName()))
  plot.SetAxisRange(0.001, 0.3, "Y")
  data.plotOn(plot, 
  RooFit.Rescale(1./hist.Integral()), 
  RooFit.MarkerColor(color),  RooFit.LineColor(color), RooFit.RefreshNorm())
  model.plotOn(plot, RooFit.LineColor(color), RooFit.Normalization(1.,RooAbsReal.NumEvent))
  plot.GetYaxis().SetTitle("1/n dn/dr")
  #print f.Clone().GetMaximum()
  #model.paramOn(plot, RooFit.Parameters(RooArgSet(mu)))
  return (plot, model, data, res, mu, mubg, r, maximumat, f)


files = ['m60deg.root', 'm30deg.root', '0deg.root',  '10deg.root',  '20deg.root',  '30deg.root',  '40deg.root',  '50deg.root',  '60deg.root']
#files = ['0deg.root',  '30deg.root',  '60deg.root']
#angle = [0,             30,            60]
angle = [-60,           -30,           0,             10,            20,            30,            40,            50,            60]
color = [9,             4,             1,             2,             3,             4,             8,             6,             9]

selection='abs(C2_peak_timecross-C1_timecross)<5e-9 && abs(C2_peak_timecross-C1_timecross)<5e-9'
selectionPeak = "C2_peak_area<-0.02e-9 && C3_peak_area<-0.02e-9"
selectionTail = "C2_tail_area<-0.02e-9 && C3_tail_area<-0.02e-9"

variable_peak='(C2_peak_area-C3_peak_area)/(C2_peak_area+C3_peak_area)'
variable_tail='(C2_tail_area-C3_tail_area)/(C2_tail_area+C3_tail_area)'
binning = [40, -1, 1]

out=TFile("ciao.root", "recreate")
out.cd()

histosPeak=[]
histosTail=[]
for i,file in enumerate(files):
  f = TFile(file)
  tree = f.Get("summary")
  hPeakName = "hPeak"+str(angle[i])+"deg"
  hTailName = "hTail"+str(angle[i])+"deg"
  out.cd()
  histosPeak.append(TH1F(hPeakName, hPeakName, binning[0], binning[1], binning[2]))
  histosTail.append(TH1F(hTailName, hTailName, binning[0], binning[1], binning[2]))
  tree.Draw(variable_peak+">>"+hPeakName, selection+" && "+selectionPeak)
  tree.Draw(variable_tail+">>"+hTailName, selection+" && "+selectionTail)

results=[]
x  = array("d", angle)
y  = array("d", angle)
ex = array("d", angle)
ey = array("d", angle)
cTail=TCanvas()
cTail.cd()
legTail=TLegend(0.5, 0.7, 0.83, 0.95)
legTail.SetFillStyle(0)
legTail.SetBorderSize(0)
for i in range(len(files)):
  histosTail[i].SetLineColor(color[i])
  histosTail[i].SetMarkerColor(color[i])
  histosTail[i].SetLineWidth(2)
  legTail.AddEntry(histosTail[i], str(angle[i])+"#circ on peak", "l")
  res = fit(histosTail[i], color[i], angle[i]>=0, 'gauss')
  ex.insert(i, 0.)
  if i==0:
    res[0].Draw()
    #histosTail[i].DrawNormalized()
  else:
    res[0].Draw("sames")
    #histosTail[i].DrawNormalized("sames")
  print "Results for "+histosTail[i].GetName()
  res[3].Print()
  y.insert(i, res[7])
  results.append(res[3])
legTail.Draw("sames")
gTail = TGraph(len(angle), x, y)
c3=TCanvas()
c3.cd()
gTail.Draw("AP")

x  = array("d", angle)
y  = array("d", angle)
ex = array("d", angle)
ey = array("d", angle)
yf = array("d", angle)
eyf= array("d", angle)
cPeak=TCanvas()
cPeak.cd()
legPeak=TLegend(0.5, 0.7, 0.83, 0.95)
legPeak.SetFillStyle(0)
legPeak.SetBorderSize(0)
for i in range(len(files)):
  histosPeak[i].SetLineColor(color[i])
  histosPeak[i].SetMarkerColor(color[i])
  histosPeak[i].SetLineWidth(2)
  legPeak.AddEntry(histosPeak[i], str(angle[i])+"#circ on peak", "l")
  res = fit(histosPeak[i], color[i], angle[i]>=0, 'full', results[i])
  x.insert(i, math.radians(angle[i]))
  ex.insert(i, 0.)
  if i==0:
    res[0].Draw()
    #histosPeak[i].DrawNormalized()
  else:
    res[0].Draw("sames")
    #histosPeak[i].DrawNormalized("sames")
  print "Results for "+histosPeak[i].GetName()
  res[3].Print()

  print "mubg", res[5].getVal()
  y.insert(i, res[5].getVal())
  ey.insert(i, res[5].getError())
  yf.insert(i, res[8].getVal())
  eyf.insert(i, res[8].getError())
legPeak.Draw("sames")
gPeak = TGraphErrors(len(angle), x, y, ex, ey)
c2=TCanvas()
c2.cd()
gPeak.Draw("AP")
gPeak.GetYaxis().SetTitle("peak r value")
gPeak.Draw("AP")
#f = TF1("f", "tan(x)/tan([0])", -0.5, 0.5)
#f.SetParameter(0, 0.98)


gPeakF = TGraphErrors(len(angle), x, yf, ex, eyf)
c3=TCanvas()
c3.cd()
gPeakF.Draw("AP")
gPeakF.GetYaxis().SetTitle("fraction of Cherenkov in the peak")
gPeakF.Draw("AP")


#f = TF1("f", "(-max(1/(cos(x)+sin(x)*(1/tan([0]+x))), 0)+max(1/(cos(x)+sin(x)*(-1/tan([0]-x))), 0))/(max(1/(cos(x)+sin(x)*(1/tan([0]+x))), 0)+max(1/(cos(x)+sin(x)*(-1/tan([0]-x))), 0))", math.radians(-30), math.radians(30))
#f.SetParameter(0, 0.98)
#f = TF1("f", "((1-[1])*cos(x)+(1+[1])*tan(x)/tan([0]))/((1+[1])*cos(x)+(1-[1])*tan(x)/tan([0]))"
f = TF1("f", "tan(x)/tan([0])", -0.5, 0.5)
f.SetParameter(0, 0.98)

gPeak.Fit(f, "R")


a=raw_input("press any key to exit")
