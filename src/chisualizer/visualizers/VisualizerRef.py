import chisualizer.Base as Base
from VisualizerBase import VisualizerBase

@Base.xml_register('VisualizerRef')
class VisualizerRef(VisualizerBase):
  """Lazy initialized reference to another visualizer"""
  @classmethod
  def from_xml_cls(cls, element, parent):
    target = element.get('target', None)
    if not target:
      raise ValueError("VisualizerRef must have 'target' attribute")
    container = super(VisualizerRef, cls).from_xml_cls(element, parent)
    container.target = Base.Base.from_xml(parent.root.get_ref(target), container)
  
    return container
    
  def layout_cairo(self, cr):
    return self.target.layout_cairo(cr)
    
  def draw_cairo(self, cr, rect, depth):
    return self.target.draw_cairo(cr, rect, depth)
        
  def wx_popupmenu_populate(self, menu):
    return False
  