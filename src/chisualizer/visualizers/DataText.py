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
    new.display = DisplayBase.registry_get_display(display_ref)
    return new
  
  def instantiate(self, new_parent):
    cloned = super(DataText, self).instantiate(new_parent)
    cloned.display = self.display
    return cloned

  def calculate_cairo_minimum_size(self, cr):
    pass

  def draw_cairo(self, rect, cr):
    super(DataText, self).draw_cairo(rect, cr)
    
    pass
  