import logging
import os
import xml.etree.ElementTree as etree

import wx
try:
  import wx.lib.wxcairo
  import cairo
  haveCairo = True
except ImportError:
  haveCairo = False

import chisualizer.Base as Base
import chisualizer.visualizers.VisualizerBase as VisualizerBase

from chisualizer.visualizers import *
from chisualizer.display import *

logging.getLogger().setLevel(logging.DEBUG)
desc = Base.VisualizerDescriptor('../../tests/gcd.xml')

class MyFrame(wx.Frame):
  def __init__(self, parent, title):
    wx.Frame.__init__(self, parent, title=title, size=(640,480))
    self.canvas = CairoPanel(self)
    self.Show()

class CairoPanel(wx.Panel):
  def __init__(self, parent):
    wx.Panel.__init__(self, parent, style=wx.BORDER_SIMPLE)
    self.Bind(wx.EVT_PAINT, self.OnPaint)
    self.text = 'Hello World!'

  def OnPaint(self, evt):
    #Here we do some magic WX stuff.
    dc = wx.PaintDC(self)
    width, height = self.GetClientSize()
    cr = wx.lib.wxcairo.ContextFromDC(dc)

    # cr.scale(size, size)
    cr.set_source_rgb(0, 0, 0) #black
    cr.rectangle(0, 0, width, height)
    cr.fill()
    
    desc.draw_cairo(cr)

  #Change what text is shown
  def SetText(self, text):
    self.text = text
    self.Refresh()

if haveCairo:
  app = wx.App(False)
  theFrame = MyFrame(None, 'Chisualizer')
  app.MainLoop()
else:
  print "Chisualizer requires PyCairo and wxCairo to run."
  