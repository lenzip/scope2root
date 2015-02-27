#!/bin/env python

from ROOT import *
import sys
from array import array

def fit(hist, color):
  r=RooRealVar("r", "r", -2, 2)
  r.setBins(80)
  data = RooDataHist(hist.GetName(), hist.GetName(), RooArgList(r), hist)
  sigma = RooRealVar("sigma", "sigma", 0, 1)
  mu = RooRealVar("mu", "mu", -1, 1)
  mubg = RooRealVar("mubg", "mubg", -1, 1)
  sigma2 = RooRealVar("sigma2", "sigma2", 0, 2)
  alpha = RooRealVar("alpha", "alpha", 0, 2)
  n = RooRealVar("n", "n", 0, 3)
  f = RooRealVar("f", "f", 0, 1)
  #bg = RooBifurGauss("bif", "bif", r, mubg, sigmaL, sigmaR)
  #bg = RooGaussian("bif", "bif", r, mubg, sigma2)
  bg = RooCBShape("bif", "bif", r, mubg, sigma2, alpha, n)
  ga = RooGaussian("g", "g", r, mu, sigma)
  model = RooAddPdf("model", "model", bg, ga, f)
  fi = ga.asTF(RooArgList(r), RooArgList(sigma, mu))
  res = model.fitTo(data, RooFit.Save(True), RooFit.PrintLevel(-1))
  fu = model.asTF(RooArgList(r), RooArgList(sigma, mu, mubg, sigma2, alpha, f, n))
  print fu
  maximumat = fu.GetMaximumX()
  print "maximum at", maximumat
  plot = r.frame(RooFit.Name("frame"+hist.GetName()))
  plot.SetAxisRange(0.001, 0.3, "Y")
  data.plotOn(plot, 
  RooFit.Rescale(1./hist.Integral()), 
  RooFit.MarkerColor(color),  RooFit.LineColor(color), RooFit.RefreshNorm())
  model.plotOn(plot, RooFit.LineColor(color), RooFit.Normalization(1.,RooAbsReal.NumEvent))
  #print f.Clone().GetMaximum()
  #model.paramOn(plot, RooFit.Parameters(RooArgSet(mu)))
  return (plot, model, data, res, mu, mubg, r, maximumat)


#files = ['m60deg.root', 'm30deg.root', '0deg.root',  '10deg.root',  '20deg.root',  '30deg.root',  '40deg.root',  '50deg.root',  '60deg.root']
files = ['m60deg.root', '0deg.root',  '30deg.root',  '60deg.root']
angle = [-60,            0,             30,            60]
#angle = [-60,           -30,           0,             10,            20,            30,            40,            50,            60]
#color = [9,             4,             1,             2,             3,             4,             8,             6,             9]
color = [9,              1,             4,             9]

selection='abs(C2_peak_timecross-C1_timecross)<5e-9 && abs(C2_peak_timecross-C1_timecross)<5e-9'
selectionPeak = "C2_peak_area<-0.02e-9 && C3_peak_area<-0.02e-9"
selectionTail = "C2_tail_area<-0.02e-9 && C3_tail_area<-0.02e-9"

variable_peak='(C2_peak_area-C3_peak_area)/(C2_peak_area+C3_peak_area)'
variable_tail='(C2_tail_area-C3_tail_area)/(C2_tail_area+C3_tail_area)'
binning = [80, -2, 2]

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
  histosPeak[i].SetLineColor(color[i])
  histosPeak[i].SetMarkerColor(color[i])
  histosPeak[i].SetLineWidth(2)
  legPeak.AddEntry(histosPeak[i], str(angle[i])+"#circ on peak", "l")
  res = fit(histosPeak[i], color[i])
  ex.insert(i, 0.)
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
  legTail.AddEntry(histosTail[i], str(angle[i])+"#circ off peak", "l")
  res = fit(histosTail[i], color[i])
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
legTail.Draw("sames")
gTail = TGraph(len(angle), x, y)
c3=TCanvas()
c3.cd()
gTail.Draw("AP")

a=raw_input("press any key to exit")
