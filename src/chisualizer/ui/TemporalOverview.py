import logging
import time

import wx
import wx.lib.wxcairo
import cairo

# TODO: MAJOR REFACTORING

from chisualizer.visualizers.VisualizerBase import AbstractVisualizer
from chisualizer.visualizers.Theme import LightTheme, DarkTheme

class TemporalOverview(wx.Frame):
  def __init__(self, parent, manager, title, circuit_view, vis_root):
    wx.Frame.__init__(self, parent, title="Chisualizer: " + title + " (Temporal Overview)", size=(400,800))
    self.canvas = TemporalOverviewPanel(self, manager, title, circuit_view, vis_root)
    self.Show()

  def vis_refresh(self):
    self.canvas.vis_refresh()

class TemporalOverviewPanel(wx.Panel):
  def __init__(self, parent, manager, title, circuit_view, vis_root):
    wx.Panel.__init__(self, parent, style=wx.BORDER_SIMPLE)
    self.Bind(wx.EVT_PAINT, self.OnPaint)
    self.Bind(wx.EVT_SIZE, self.OnSize)
    self.Bind(wx.EVT_CHAR, self.OnChar)
    self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
    self.Bind(wx.EVT_MOTION, self.OnMouseMotion)
    self.Bind(wx.EVT_RIGHT_UP, self.OnMouseRight)
    self.Bind(wx.EVT_LEFT_DCLICK, self.OnMouseLeftDClick)
    
    self.manager = manager
    self.title = title
    self.circuit_view = circuit_view
    self.vis_root = vis_root
    
    self.scale = 1
    self.mouse_vis = (0, 0)   # mouse position, in visualizer coords
    
    self.need_visualizer_refresh = True
    self.elements = []

  def vis_refresh(self):
    self.need_visualizer_refresh = True
    self.Refresh()

  def OnChar(self, evt):
    char = evt.GetKeyCode()
    if char == ord('r'):
      self.manager.circuit_reset()
    elif char == wx.WXK_LEFT:
      self.manager.circuit_prev_mod()
    elif char == wx.WXK_RIGHT:
      self.manager.circuit_next_mod()
    elif char == wx.WXK_UP:
      self.manager.circuit_back()
    elif char == wx.WXK_DOWN:
      self.manager.circuit_fwd()
    elif char == ord('s'):
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
      self.manager.circuit_fwd(cur_val)
    elif char == ord('p'):
      self.save_svg("%s_%s_%s.svg" % (self.title,
                                      self.manager.get_circuit_cycle(),
                                      time.strftime("%y%m%d_%H%M%S")))
    elif char == ord('q'):
      self.manager.exit()

  def OnSize(self, evt):
    self.vis_refresh()

  def OnMouseWheel(self, evt):
    delta = evt.GetWheelRotation() / evt.GetWheelDelta()
    scale_factor = 1.2 ** delta
    self.scale = self.scale * scale_factor
    self.vis_refresh()

  def OnMouseMotion(self, evt):
    self.mouse_vis = self.device_to_visualizer_coordinates((evt.GetX(), evt.GetY()))
    self.Refresh()

  def OnMouseRight(self, evt):
    x, y = self.device_to_visualizer_coordinates(evt.GetPosition())
    elements = self.get_mouseover_elements(x, y)
    elements = sorted(elements, key = lambda element: element[0], reverse=True)
    
    menu = wx.Menu()
    populated = False
    for element in elements:
      assert isinstance(element[1], AbstractVisualizer)
      this_populated = element[1].wx_popupmenu_populate(menu)
      populated = populated or this_populated
    if populated:
      self.PopupMenu(menu, evt.GetPosition())
    menu.Destroy()
    
    # TODO: make this event-driven from AbstractVisualizer
    self.vis_refresh()
    
  def OnMouseLeftDClick(self, evt):
    x, y = self.device_to_visualizer_coordinates(evt.GetPosition())
    elements = self.get_mouseover_elements(x, y)
    if not elements:
      return
    elements = sorted(elements, key = lambda element: element[0], reverse=True)

    assert isinstance(elements[0][1], AbstractVisualizer)
    elements[0][1].wx_defaultaction()
    
    # TODO: make this event-driven from AbstractVisualizer
    self.vis_refresh()
    
  def OnPaint(self, evt):
    dc = wx.PaintDC(self)
    width, height = self.GetClientSize()
    dc.Blit(0, 0, width, height, 
            self.get_visualizer_dc(self.GetClientSize()), 
            0, 0)

    # Per-frame elements
    cr = wx.lib.wxcairo.ContextFromDC(dc)
    cr.set_source_rgba(*self.vis_root.get_theme().default_color())
    cr.select_font_face('Mono',
                        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(10)
    cr.move_to(0, height - 50)
    cr.show_text("Scale: %.2f" % self.scale)
    cr.move_to(0, height - 40)
    cr.show_text("Mouse: %.1f, %.1f" % self.mouse_vis)
    cr.move_to(0, height - 30)
    elements = self.get_mouseover_elements(*self.mouse_vis)
    elements = map(lambda element: element[1].path, elements)
    cr.show_text(str(elements))

  def device_to_visualizer_coordinates(self, pos):
    x, y = pos
    width, height = self.GetClientSize()
    x = x - width / 2
    y = y - height / 2
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
      self.vis_root.set_theme(DarkTheme())
      
      width, height = size
      dc = wx.MemoryDC(wx.EmptyBitmap(width, height))
      cr = wx.lib.wxcairo.ContextFromDC(dc)
    
      cr.set_source_rgba(*self.vis_root.get_theme().background_color())
      cr.rectangle(0, 0, width, height)
      cr.fill()
    
      cr.translate(0.5, 0.5)
      cr.save()
      cr.translate(width/2, height/2)
      cr.scale(self.scale, self.scale)
      
      timer_draw = time.time()
      self.draw_visualizer(cr)
      timer_draw = time.time() - timer_draw

      cr.restore()
      
      cr.set_source_rgba(*self.vis_root.get_theme().default_color())
      cr.select_font_face('Mono',
                          cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
      cr.set_font_size(10)
      cr.move_to(0, height - 15)
      cr.show_text("Cycle %s, render: %.2f ms" %
                   (self.manager.get_circuit_cycle(), timer_draw*1000))
      cr.move_to(0, height - 5)
      cr.show_text(u"(\u25B2) back one cycle, (\u25BC) forward one cycle, (s) variable cycle step, (r) cycle in reset, (mousewheel) zoom, (p) save to SVG")
      
      self.visualizer_dc = dc
      self.need_visualizer_refresh = False
      
    return self.visualizer_dc

  def draw_visualizer(self, cr):
    timers = [0, 0, 0]
    left_x = right_x = bot_y = top_y = 0
    current_temporal_node = self.circuit_view.get_current_temporal_node()
    self.elements = []
    
    def draw_visualizer_at(temporal_node, layout_process_fn, green=False):  # TODO DEHACKIFY
      self.circuit_view.set_view(temporal_node.get_historical_state())
      
      timer = time.time()
      self.vis_root.update()
      timers[0] += time.time() - timer
      self.vis_root.visualizer.apply_attr_overloads(None, {"label": str(temporal_node.get_label())})
      if green:
        self.vis_root.visualizer.apply_attr_overloads(None, {"label_color": "green"})
        self.vis_root.visualizer.apply_attr_overloads(None, {"border_color": "green"})
      
      timer = time.time()
      layout = layout_process_fn(self.vis_root.layout_cairo(cr).centered_origin())
      timers[1] += time.time() - timer
        
      timer = time.time()
      self.elements.extend(self.vis_root.draw_cairo(cr, layout))
      timers[2] += time.time() - timer
      
      return layout
    
    def iter_draw(iterations, next_node_fn, start_coord, layout_process_fn_fn, coord_increment_fn):
      temporal_node = next_node_fn(current_temporal_node)
      while iterations > 0 and temporal_node is not None:
        layout = draw_visualizer_at(temporal_node, layout_process_fn_fn(start_coord))
        start_coord = coord_increment_fn(start_coord, layout)
        temporal_node = next_node_fn(temporal_node)
        iterations -= 1
    
    center_layout = draw_visualizer_at(current_temporal_node, lambda layout: layout, green=True)
    
    # Draw nodes, prev by time
    iter_draw(10,
              lambda node: node.get_prev_time(),
              center_layout.top(),
              lambda coord: lambda layout: layout.aligned_bottom(coord),
              lambda coord, layout: coord - layout.height())
    
    # Draw nodes, next by time
    iter_draw(10,
              lambda node: node.get_next_time(),
              center_layout.bottom(),
              lambda coord: lambda layout: layout.aligned_top(coord),
              lambda coord, layout: coord + layout.height())
    
    # Draw nodes, prev by mod
    iter_draw(1,
              lambda node: node.get_prev_mod(),
              center_layout.left(),
              lambda coord: lambda layout: layout.aligned_right(coord),
              lambda coord, layout: coord - layout.width())
    
    # Draw nodes, next by mod
    iter_draw(1,
              lambda node: node.get_next_mod(),
              center_layout.right(),
              lambda coord: lambda layout: layout.aligned_left(coord),
              lambda coord, layout: coord + layout.width())
    
    logging.debug("draw_visualizer: layout time: %.2f ms, draw time: %.2f ms" %
                 (timers[1]*1000, timers[2]*1000))
    
  def save_svg(self, filename):
    # TODO: refactor to avoid calling desc.layout here
    self.vis_root.set_theme(LightTheme())
      
    f = file(filename, 'w')
    surface_test = cairo.SVGSurface(f, 1, 1)  # dummy surface to get layout size
    # TODO make cross platform, 
    cr_test = cairo.Context(surface_test)
    self.vis_root.visualizer.apply_attr_overloads(None, {"label": str("1")})
    self.vis_root.update()
    layout = self.vis_root.layout_cairo(cr_test)
    surface_test.finish()
    
    f = file(filename, 'w')
    surface = cairo.SVGSurface(f, layout.width()+2, layout.height()*7+2)
    cr = cairo.Context(surface)
    
    cr.set_source_rgba(*self.vis_root.get_theme().background_color())
    cr.rectangle(0, 0, layout.width()+2, layout.height()*7+2)
    cr.fill()
    
    cr.translate(1, 1)
    cr.translate(layout.width()/2, layout.height()*3.5)
    cr.save()
    #self.vis_root.draw_cairo(cr, layout)
    self.draw_visualizer(cr)
    
    surface.finish()
    f.close()
    
    logging.info("Rendered visualizer to SVG '%s'" % filename)
