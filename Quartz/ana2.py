#!/bin/env python

from ROOT import *
import sys
from array import array
import math

def fit(hist, color, pos=True):
  r=RooRealVar("r", "r", -1, 1)
  r.setBins(40)
  data = RooDataHist(hist.GetName(), hist.GetName(), RooArgList(r), hist)
  sigma = RooRealVar("sigma", "sigma", 0, 1)
  mu = RooRealVar("mu", "mu", -1, 1)
  mubg = RooRealVar("mubg", "mubg", -1, 1)
  sigma2 = RooRealVar("sigma2", "sigma2", 0, 2)
  if pos:
    alpha = RooRealVar("alpha", "alpha", 0, 1)
  else:  
    alpha = RooRealVar("alpha", "alpha", -1, 0)
  n = RooRealVar("n", "n", 0, 100)
  f = RooRealVar("f", "f", 0, 1)
  #bg = RooBifurGauss("bif", "bif", r, mubg, sigmaL, sigmaR)
  #bg = RooGaussian("bif", "bif", r, mubg, sigma2)
  bg = RooCBShape("bif", "bif", r, mubg, sigma2, alpha, n)
  ga = RooGaussian("g", "g", r, mu, sigma)
  model = bg #RooAddPdf("model", "model", bg, ga, f)
  fi = ga.asTF(RooArgList(r), RooArgList(sigma, mu))
  res = model.fitTo(data, RooFit.Save(True), RooFit.PrintLevel(-1))
  #fu = model.asTF(RooArgList(r), RooArgList(sigma, mu, mubg, sigma2, alpha, f, n))
  fu = model.asTF(RooArgList(r), RooArgList(mubg, sigma2, alpha, n))
  #print fu
  maximumat = fu.GetMaximumX()
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
  return (plot, model, data, res, mu, mubg, r, maximumat)


files = ['m60deg.root', 'm30deg.root','0deg.root',  '10deg.root',  '20deg.root',  '30deg.root',  '40deg.root',  '50deg.root',  '60deg.root']
#files = ['m30deg.root' ]
#angle = [-30, 0,             10, 40,            60]
angle = [-60,           -30,           0,             10,            20,            30,            40,            50,            60]
color = [9,              4,            1,             2,             3,             4,             8,             6,             9]
#color = [1,             4, 2,             3]

selection='abs(C2_peak_timecross-C3_peak_timecross)<5e-9'
selectionPeak = "C2_peak_area<-0.01e-9 && C3_peak_area<-0.01e-9"
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
  #tree.Draw(variable_tail+">>"+hTailName, selection+" && "+selectionTail)

x  = array("d", angle)
y  = array("d", angle)
ex = array("d", angle)
ey = array("d", angle)
cPeak=TCanvas()
cPeak.cd()
legPeak=TLegend(0.5, 0.7, 0.83, 0.95)
legPeak.SetFillStyle(0)
legPeak.SetBorderSize(0)
for i in range(len(files)):
  print files[i]
  histosPeak[i].SetLineColor(color[i])
  histosPeak[i].SetMarkerColor(color[i])
  histosPeak[i].SetLineWidth(2)
  legPeak.AddEntry(histosPeak[i], str(angle[i])+"#circ on peak", "l")
  res = fit(histosPeak[i], color[i], angle[i]>=0)
  ex.insert(i, 0.)
  x.insert(i, math.radians(angle[i]))
  if i==0:
    res[0].Draw()
    #histosPeak[i].DrawNormalized()
  else:
    res[0].Draw("sames")
    #histosPeak[i].DrawNormalized("sames")
  print "Results for "+histosPeak[i].GetName()
  res[3].Print()
  y.insert(i, res[7])
legPeak.Draw("sames")
gPeak = TGraph(len(angle), x, y)
c2=TCanvas()
c2.cd()
gPeak.Draw("AP")
#f = TF1("f", "((1-[1])*cos(x)+(1+[1])*tan(x)/tan([0]))/((1+[1])*cos(x)+(1-[1])*tan(x)/tan([0]))", math.radians(-10), math.radians(10))
#f = TF1("f", "tan(x)/tan([0])", -1, -1)
f = TF1("f", "(cos(x)*( exp(-(1-sin(x))/[1]) - exp(-(1+sin(x))/[1]) ) + sin(x)*( exp(-(1-sin(x))/[1]) + exp(-(1+sin(x))/[1]))/tan([0]))/(cos(x)*( exp(-(1-sin(x))/[1]) + exp(-(1+sin(x))/[1]) ) + sin(x)*( exp(-(1-sin(x))/[1]) - exp(-(1+sin(x))/[1]))/tan([0]))", -1, 1)
f.SetParameter(0, 0.98)
f.SetParLimits(0, 0.97, 0.98)
f.SetParameter(1, 0.1)
gPeak.Fit("f", "R")
f.Draw("sames")

a=raw_input("press any key to exit")
