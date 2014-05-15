import logging
import os
import xml.etree.ElementTree as etree
import time

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

logging.getLogger().setLevel(logging.INFO)
logging.getLogger().setLevel(logging.DEBUG)
TARGET="GCD"
#TARGET="rv1s"

if TARGET=="GCD":
  api = ChiselEmulatorSubprocess('../../tests/gcd/emulator/emulator')
  desc = Base.VisualizerDescriptor('../../tests/gcd/gcd.xml', api)
elif TARGET=="rv1s":
  api = ChiselEmulatorSubprocess(['../../../riscv-sodor/emulator/rv32_1stage/emulator',
                                  '+max-cycles=30000',
                                  '+api', 
                                  '+loadmem=../../../riscv-sodor/emulator/rv32_1stage/output/riscv-v1_addi.hex'],
                                  #'+loadmem=../../../riscv-sodor/emulator/rv32_1stage/output/riscv-v2_and.hex'],
                                 reset=False)
  desc = Base.VisualizerDescriptor('../../tests/sodor/riscv_1stage.xml', api)
else:
  raise ValueError("No visualization TARGET")

class MyFrame(wx.Frame):
  def __init__(self, parent, title):
    wx.Frame.__init__(self, parent, title=title, size=(1280,800))
    self.canvas = CairoPanel(self)
    self.Show()

class CairoPanel(wx.Panel):
  def __init__(self, parent):
    wx.Panel.__init__(self, parent, style=wx.BORDER_SIMPLE)
    self.Bind(wx.EVT_PAINT, self.OnPaint)
    self.Bind(wx.EVT_SIZE, self.OnSize)
    self.Bind(wx.EVT_CHAR, self.OnChar)
    self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
    self.Bind(wx.EVT_MOTION, self.OnMouseMotion)
    self.Bind(wx.EVT_RIGHT_UP, self.OnMouseRight)
    
    self.scale = 1
    self.mouse = (0, 0)
    
    self.need_visualizer_refresh = False
    self.elements = []
    
    self.cycle = 0
    self.snapshots = []

  def OnChar(self, evt):
    char = evt.GetKeyCode()
    if char == ord('r'):
      logging.info("Reset circuit")
      api.reset(1)
      self.cycle = 0
      self.snapshots = []
      self.need_visualizer_refresh = True
      
    elif char == wx.WXK_RIGHT:
      logging.info("Clock circuit")
      api.snapshot_save(str(self.cycle))
      self.snapshots.append(self.cycle)
      self.cycle += api.clock(1)
      self.need_visualizer_refresh = True
      
    elif char == wx.WXK_LEFT:
      logging.info("Revert circuit")
      if self.snapshots:
        self.cycle = self.snapshots.pop()
        api.snapshot_restore(str(self.cycle))
        self.need_visualizer_refresh = True
    
    elif char == ord('s'):
      logging.info("Clock circuit")
      cur_val = -1
      dlg = wx.TextEntryDialog(None, 'Step', 'Cycles to step', "1")
      while cur_val < 1:
        ret = dlg.ShowModal()
        if ret != wx.ID_OK:
          return
        dlg_val = dlg.GetValue()
        try:
          cur_val = int(dlg_val)
        except:
          pass
        
      api.snapshot_save(str(self.cycle))
      self.snapshots.append(self.cycle)
      self.cycle += api.clock(cur_val)
      self.need_visualizer_refresh = True
      
    elif char == ord('p'):
      self.save_svg("%s_%i.svg" % (TARGET, self.cycle))
      
    self.Refresh()

  def OnSize(self, evt):
    self.need_visualizer_refresh = True
    self.Refresh()

  def OnMouseWheel(self, evt):
    delta = evt.GetWheelRotation() / evt.GetWheelDelta()
    self.scale = self.scale * (1.2 ** delta)
    self.need_visualizer_refresh = True
    self.Refresh()

  def OnMouseMotion(self, evt):
    self.mouse = self.device_to_visualizer_coordinates((evt.GetX(), evt.GetY()))
    self.Refresh()

  def OnMouseRight(self, evt):
    x, y = self.device_to_visualizer_coordinates(evt.GetPosition())
    elements = self.get_mouseover_elements(x, y)
    elements = sorted(elements, key = lambda element: element[0], reverse=True)
    
    menu = wx.Menu()
    populated = False
    for element in elements:
      assert isinstance(element[1], VisualizerBase.VisualizerBase)
      this_populated = element[1].wx_popupmenu_populate(menu)
      populated = populated or this_populated
    if populated:
      self.PopupMenu(menu, evt.GetPosition())
    menu.Destroy()
    
    self.need_visualizer_refresh = True
    self.Refresh()
    
  def OnPaint(self, evt):
    dc = wx.PaintDC(self)
    width, height = self.GetClientSize()
    dc.Blit(0, 0, width, height, 
            self.get_visualizer_dc(self.GetClientSize()), 
            0, 0)

    # Per-frame elements
    cr = wx.lib.wxcairo.ContextFromDC(dc)
    cr.set_source_rgb(255, 255, 255)
    cr.select_font_face('Mono',
                        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(10)
    cr.move_to(0, height - 35)
    cr.show_text("Scale: %.2f" % self.scale)
    cr.move_to(0, height - 25)
    cr.show_text("Mouse: %d, %d" % self.mouse)
    cr.move_to(0, height - 15)
    elements = self.get_mouseover_elements(*self.mouse)
    elements = map(lambda element: element[1].path, elements)
    cr.show_text(str(elements))

  def device_to_visualizer_coordinates(self, pos):
    x, y = pos
    x = x / self.scale
    y = y / self.scale
    return (x, y) 

  def get_mouseover_elements(self, x, y):
    elements = []
    for (depth, rect, visualizer) in self.elements:
      if rect.contains(x, y):
        elements.append((depth, visualizer))
    return elements

  def get_visualizer_dc(self, size):
    if self.need_visualizer_refresh:
      width, height = size
      dc = wx.MemoryDC(wx.EmptyBitmap(width, height))
      cr = wx.lib.wxcairo.ContextFromDC(dc)
    
      cr.set_source_rgb(0, 0, 0)
      cr.rectangle(0, 0, width, height)
      cr.fill()
    
      cr.translate(0.5, 0.5)
      cr.save()
      cr.scale(self.scale, self.scale)

      timer_draw = time.time()
      self.draw_visualizer(cr)
      timer_draw = time.time() - timer_draw

      cr.restore()
      
      cr.move_to(0, height - 5)
      cr.set_source_rgb(255, 255, 255)
      cr.select_font_face('Mono',
                          cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
      cr.set_font_size(10)
      cr.show_text("Cycle %i, render: %.2f ms" %
                   (self.cycle, timer_draw*1000))
      
      self.visualizer_dc = dc
      
    self.need_visualizer_refresh = False
    return self.visualizer_dc

  def draw_visualizer(self, cr):
    timer_lay = time.time()
    layout = desc.layout_cairo(cr)
    timer_lay = time.time() - timer_lay
    
    timer_draw = time.time()
    self.elements = desc.draw_cairo(cr, layout)
    timer_draw = time.time() - timer_draw
    
    logging.info("draw_visualizer: layout time: %.2f ms, draw time: %.2f ms" %
                 (timer_lay*1000, timer_draw*1000))
    
  def save_svg(self, filename):
    # TODO: refactor to avoid calling desc.layout here
    surface_test = cairo.ImageSurface(cairo.FORMAT_A8, 1, 1)  # dummy surface to get layout size
    cr_test = cairo.Context(surface_test)
    layout = desc.layout_cairo(cr_test)
    
    f = file(filename, 'w')
    surface = cairo.SVGSurface(f, layout.width()+2, layout.height()+2)
    cr = cairo.Context(surface)
    cr.translate(1, 1)
    cr.save()
    self.draw_visualizer(cr)
    
    surface.finish()
    
    logging.info("Rendered visualizer to SVG '%s'" % filename)
    
def run():
  if haveCairo:
    app = wx.App(False)
    MyFrame(None, 'Chisualizer')
    app.MainLoop()
  else:
    print "Chisualizer requires PyCairo and wxCairo to run."

run()

api.close()
logging.info("Done")
