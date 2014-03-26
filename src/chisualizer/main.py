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
from chisualizer.ChiselEmulatorSubprocess import *

logging.getLogger().setLevel(logging.DEBUG)
api = ChiselEmulatorSubprocess('../../tests/gcd/emulator/GCD-emulator')
desc = Base.VisualizerDescriptor('../../tests/gcd/gcd.xml', api)

class MyFrame(wx.Frame):
  def __init__(self, parent, title):
    wx.Frame.__init__(self, parent, title=title, size=(640,480))
    self.canvas = CairoPanel(self)
    self.Show()

class CairoPanel(wx.Panel):
  def __init__(self, parent):
    wx.Panel.__init__(self, parent, style=wx.BORDER_SIMPLE)
    self.Bind(wx.EVT_PAINT, self.OnPaint)
    self.Bind(wx.EVT_CHAR, self.OnChar)
    self.text = 'Hello World!'

  def OnChar(self, evt):
    char = evt.GetKeyCode()
    if char == ord('s'):
      node_name = ""
      while not api.has_node(node_name):
        dlg = wx.TextEntryDialog(None,'Set node','Node name', node_name)
        ret = dlg.ShowModal()
        if ret != wx.ID_OK:
          return
        node_name = dlg.GetValue()
      dlg = wx.TextEntryDialog(None,'Set value','Value', '')
      ret = dlg.ShowModal()
      if ret != wx.ID_OK:
        return
      try:
        node_value = int(dlg.GetValue(), 0)
      except ValueError:
        return
      logging.info("Set '%s' to '%s'" % (node_name, node_value))
      api.set_node_value(node_name, node_value)
    elif char == ord('r'):
      logging.info("Reset circuit")
      api.reset(1)
    elif char == wx.WXK_RIGHT:
      logging.info("Clock circuit")
      api.clock(1)
    self.Refresh()

  def OnPaint(self, evt):
    dc = wx.PaintDC(self)
    width, height = self.GetClientSize()
    cr = wx.lib.wxcairo.ContextFromDC(dc)

    cr.set_source_rgb(0, 0, 0)
    cr.rectangle(0, 0, width, height)
    cr.fill()
    
    cr.translate(0.5, 0.5)
    desc.draw_cairo(cr)

def run():
  if haveCairo:
    app = wx.App(False)
    theFrame = MyFrame(None, 'Chisualizer')
    app.MainLoop()
  else:
    print "Chisualizer requires PyCairo and wxCairo to run."

run()
