import logging

import cairo 

import chisualizer.Base as Base
import chisualizer.display.DisplayBase as DisplayBase

from Data import Data

@Base.xml_register('DataText')
class DataText(Data):
  """Visualizer for data represented as text."""
  @classmethod
  def from_xml_cls(cls, element, **kwargs):
    new = super(DataText, cls).from_xml_cls(element, **kwargs)
    display_ref = element.get('display', 'hexadecimal')
    new.display = new.container.get_ref(display_ref)
    
    new.display_size = new.parse_element_int(element, 'display_size', 14)
    new.display_font = element.get('display_font', 'Sans')
    
    new.node = None
    return new
  
  def instantiate(self, new_parent, **kwargs):
    cloned = super(DataText, self).instantiate(new_parent, **kwargs)
    cloned.display = self.display
    cloned.display_size = self.display_size
    cloned.display_font = self.display_font
    cloned.node = None
    return cloned

  def draw_element_cairo(self, cr, rect):
    if not self.node:
      self.node = self.get_chisel_api().get_node_reference(self.path)
    
    cr.set_source_rgb(1, 1, 1)
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
      cr.set_source_rgb(*modifiers['color'])
      del modifiers['color']
    
    if modifiers:
      logging.warn("%s (%s): unprocessed modifiers: %s", self.path, self.__class__.__name__, modifiers)
             
    cr.move_to(rect.left(), rect.center_vert() + self.text_max_height / 2)
    cr.show_text(text)
    
  def layout_element_cairo(self, cr):
    if not self.node:
      self.node = self.get_chisel_api().get_node_reference(self.path)
    texts = self.display.get_longest_text(self.node)
    self.text_max_width = 0
    cr.set_line_width (1)
    cr.select_font_face(self.display_font,
                        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(self.display_size)
    for text in texts:
      _, _, text_width, text_height, _, _ = cr.text_extents(text)
      self.text_max_width = max(self.text_max_width, text_width)
    _, _, _, self.text_max_height, _, _ = cr.text_extents('X')
    return (self.text_max_width, self.text_max_height)
