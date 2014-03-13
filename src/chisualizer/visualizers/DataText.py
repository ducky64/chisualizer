import logging

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
    new.node = None
    return new
  
  def instantiate(self, new_parent, **kwargs):
    cloned = super(DataText, self).instantiate(new_parent, **kwargs)
    cloned.display = self.display
    cloned.node = None
    return cloned

  def draw_cairo(self, cr, rect):
    super(DataText, self).draw_cairo(cr, rect)
    
    if not self.node:
      self.node = self.get_chisel_api().get_node_reference(self.path)
    
    logging.warn("DataText::draw_cairo not implemented")
    
    modifiers = self.display.apply(self.node)
    if 'text' not in modifiers:
      logging.warn("%s (%s): no 'text' in modifiers: %s", self.path, self.__class__.__name__, modifiers)
      text = "err"
    else:
      text = modifiers['text']
      del modifiers['text']
    
    if modifiers:
      logging.warn("%s (%s): unprocessed modifiers: %s", self.path, self.__class__.__name__, modifiers)
    
    import cairo
    cr.set_source_rgb(1, 1, 1) #white         
    cr.set_line_width (1)
    cr.select_font_face ("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size (10)
    cr.move_to(rect.center_horiz(), rect.center_vert())
    cr.show_text(text)
    cr.move_to(0, 0)
    cr.stroke ()
    
  def layout_cairo(self, cr):
    return (250, 50)
    
    logging.warn("DataText::layout_cairo not implemented")
