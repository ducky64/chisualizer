import logging

import cairo 
import wx

import chisualizer.Base as Base

from Data import Data

@Base.xml_register('DataText')
class DataText(Data):
  """Visualizer for data represented as text."""
  @classmethod
  def from_xml_cls(cls, element, parent):
    new = super(DataText, cls).from_xml_cls(element, parent)
    display_ref = element.get('display', 'hexadecimal')
    new.display = new.get_ref(display_ref)
    
    new.display_size = new.parse_element_int(element, 'display_size', 14)
    new.display_font = element.get('display_font', 'Mono')
    
    new.node = None
    return new
  
  def instantiate(self, new_parent, **kwargs):
    cloned = super(DataText, self).instantiate(new_parent, **kwargs)
    cloned.display = self.display
    cloned.display_size = self.display_size
    cloned.display_font = self.display_font
    cloned.node = None
    return cloned

  def get_node(self):
    """Returns the Chisel API node reference object for this visualizer's target
    node.
    self.node is lazy-initialized because the API is not ready at instantiation
    time.
    TODO: FIX THIS DIRTY HACK
    """
    if not self.node:
      self.node = self.get_chisel_api().get_node_reference(self.path)
    return self.node    

  def draw_element_cairo(self, cr, rect, depth):
    cr.set_source_rgb(1, 1, 1)
    cr.set_line_width (1)
    cr.select_font_face(self.display_font,
                        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(self.display_size)
    
    modifiers = self.display.apply(self.get_node())
    if 'text' in modifiers:
      text = modifiers['text']
      del modifiers['text']
    else:
      logging.warn("%s (%s): no 'text' in modifiers: %s", self.path, self.__class__.__name__, modifiers)
      text = "err"
      cr.set_source_rgb(1, 0, 0)
    
    if 'color' in modifiers:
      cr.set_source_rgb(*modifiers['color'])
      del modifiers['color']
    
    if modifiers:
      logging.warn("%s (%s): unprocessed modifiers: %s", self.path, self.__class__.__name__, modifiers)
             
    cr.move_to(rect.left(), rect.center_vert() + self.text_max_height / 2)
    cr.show_text(text)
    
    return []
  
  def layout_element_cairo(self, cr):
    texts = self.display.get_longest_text(self.get_node())
    self.text_max_width = 0
    cr.set_line_width (1)
    cr.select_font_face(self.display_font,
                        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(self.display_size)
    for text in texts:
      _, _, text_width, _, _, _ = cr.text_extents(text)
      self.text_max_width = max(self.text_max_width, text_width)
    _, _, _, self.text_max_height, _, _ = cr.text_extents('X')
    return (self.text_max_width, self.text_max_height)
  
  def wx_popupmenu_populate(self, menu):
    item = wx.MenuItem(menu, wx.NewId(), "%s: Set" % self.wx_prefix())
    menu.AppendItem(item)
    menu.Bind(wx.EVT_MENU, self.wx_popupmenu_set, item)
    
    super(DataText, self).wx_popupmenu_populate(menu)
    
    return True
    
  def wx_popupmenu_set(self, evt):
    curr_value = ""
    modifiers = self.display.apply(self.get_node())
    if 'text' in modifiers:
      curr_value = modifiers['text']
      
    dlg = wx.TextEntryDialog(None, self.path, 'New Value', curr_value)
    while True:
      ret = dlg.ShowModal()
      if ret != wx.ID_OK:
        return
      curr_value = dlg.GetValue()
      if self.display.set_from_text(self.get_node(), curr_value):
        logging.info("Set '%s' to '%s'" % (self.path, curr_value))
        return
    