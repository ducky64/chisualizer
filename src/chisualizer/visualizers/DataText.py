import logging

import cairo 
import wx

import chisualizer.Base as Base

from Data import Data

@Base.xml_register('DataText')
class DataText(Data):
  """Visualizer for data represented as text."""
  def __init__(self, element, parent):
    super(DataText, self).__init__(element, parent)
    
    self.display = self.root.get_ref(element.get_attr_string('display')).instantiate(self)
    self.display_size = element.get_attr_int('display_size', valid_min=1)
    self.display_font = element.get_attr_string('display_font')

  def draw_element_cairo(self, cr, rect, depth):
    cr.set_source_rgba(*self.get_theme().default_color())
    cr.set_line_width (1)
    cr.select_font_face(self.display_font,
                        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(self.display_size)
    
    modifiers = self.display.apply(self.node)
    if 'text' in modifiers:
      text = modifiers['text']
      del modifiers['text']
    else:
      logging.warn("%s (%s): no 'text' in modifiers: %s", self.path, self.__class__.__name__, modifiers)
      text = "err"
      cr.set_source_rgb(1, 0, 0)
    
    if 'color' in modifiers:
      color = modifiers['color']
      if type(color) is tuple:
        cr.set_source_rgba(*color)
      else:
        cr.set_source_rgba(*self.get_theme().color(color))
      del modifiers['color']
    
    if modifiers:
      logging.warn("%s (%s): unprocessed modifiers: %s", self.path, self.__class__.__name__, modifiers)
             
    cr.move_to(rect.left(), rect.center_vert() + self.text_max_height / 2)
    cr.show_text(text)
    
    return []
  
  def layout_element_cairo(self, cr):
    texts = self.display.get_longest_text(self.node)
    self.text_max_width = 0
    cr.set_line_width (1)
    cr.select_font_face(self.display_font,
                        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(self.display_size)
    for text in texts:
      _, _, _, _, text_width, _ = cr.text_extents(text)
      self.text_max_width = max(self.text_max_width, text_width)
    _, _, _, self.text_max_height, _, _ = cr.text_extents('X')
    return (self.text_max_width, self.text_max_height)
  
  def wx_defaultaction(self):
    self.wx_popupmenu_set(None)
  
  def wx_popupmenu_populate(self, menu):
    item = wx.MenuItem(menu, wx.NewId(), "%s: Set" % self.wx_prefix())
    menu.AppendItem(item)
    menu.Bind(wx.EVT_MENU, self.wx_popupmenu_set, item)
    
    super(DataText, self).wx_popupmenu_populate(menu)
    
    return True
    
  def wx_popupmenu_set(self, evt):
    curr_value = ""
    modifiers = self.display.apply(self.node)
    if 'text' in modifiers:
      curr_value = modifiers['text']
      
    dlg = wx.TextEntryDialog(None, self.path, 'New Value', curr_value)
    while True:
      ret = dlg.ShowModal()
      if ret != wx.ID_OK:
        return
      curr_value = dlg.GetValue()
      if self.display.set_from_text(self.node, curr_value):
        logging.info("Set '%s' to '%s'" % (self.path, curr_value))
        return
    