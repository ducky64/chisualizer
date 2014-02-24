import chisualizer.Base as Base
from VisualizerBase import VisualizerBase

@Base.xml_register('Grid')
class Grid(VisualizerBase):
  """Grid containing other visualizers."""
  @classmethod
  def from_xml_cls(cls, element, **kwargs):
    new = super(Grid, cls).from_xml_cls(element, **kwargs)
    
    return new
  
  def instantiate(self, new_parent):
    cloned = super(Grid, self).instantiate(new_parent)
    return cloned
  
  def draw_cairo(self, rect, context):
    super(Grid, self).draw_cairo(rect, context)