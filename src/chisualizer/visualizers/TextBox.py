import logging

import cairo 
import wx

import chisualizer.Base as Base
from chisualizer.visualizers.VisualizerBase import FramedVisualizer

@Base.tag_register('TextBox')
class TextBox(FramedVisualizer):
  """Visualizer for data represented as text."""
  def __init__(self, elt, parent):
    super(TextBox, self).__init__(elt, parent)
    
    self.text_size = self.attr(Base.IntAttr, 'text_size', valid_min=1).get_static()
    self.text_font = self.attr(Base.StringAttr, 'text_font').get_static()

    self.text = self.attr(Base.StringAttr, 'text', dynamic=True)
    self.text_color = self.attr(Base.StringAttr, 'text_color', dynamic=True)

  def draw_element_cairo(self, cr, rect, depth):
    cr.set_source_rgba(*self.get_theme().default_color())
    cr.set_line_width (1)
    cr.select_font_face(self.text_font,
                        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(self.text_size)
    
    text = self.text.get_dynamic()
    cr.set_source_rgba(*self.get_theme().color(self.text_color.get_dynamic()))

    cr.move_to(rect.left(), rect.center_vert() + self.text_max_height / 2)
    cr.show_text(text)
    
    return []
  
  def layout_element_cairo(self, cr):
    texts = self.text.get_longest_strings()
    
    self.text_max_width = 0
    cr.set_line_width (1)
    cr.select_font_face(self.text_font,
                        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(self.text_size)
    for text in texts:
      _, _, _, _, text_width, _ = cr.text_extents(text)
      self.text_max_width = max(self.text_max_width, text_width)
    _, _, _, self.text_max_height, _, _ = cr.text_extents('X')
    return (self.text_max_width, self.text_max_height)
  
  def wx_defaultaction(self):
    if self.node is not None:
      self.wx_popupmenu_set(None)
  
  def wx_popupmenu_populate(self, menu):
    has_node = self.node is not None  
    if has_node:
      item = wx.MenuItem(menu, wx.NewId(), "%s: Set" % self.wx_prefix())
      menu.AppendItem(item)
      menu.Bind(wx.EVT_MENU, self.wx_popupmenu_set, item)
    
    return super(TextBox, self).wx_popupmenu_populate(menu) or has_node
    
  def wx_popupmenu_set(self, evt):
    curr_value = self.text.get_dynamic()
      
    dlg = wx.TextEntryDialog(None, self.path, 'New Value', curr_value)
    while True:
      ret = dlg.ShowModal()
      if ret != wx.ID_OK:
        return
      curr_value = dlg.GetValue()
      if self.text.set_from_string(curr_value):
        logging.info("Set '%s' to '%s'" % (self.path, curr_value))
        return
    