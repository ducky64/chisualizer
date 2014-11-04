import chisualizer.Base as Base
from VisualizerBase import VisualizerBase

@Base.xml_register('VisualizerRef')
class VisualizerRef(VisualizerBase):
  """Lazy initialized reference to another visualizer"""
  def __init__(self, element, parent):
    super(VisualizerRef, self).__init__(element, parent)
    target = element.get_attr_string('target')
    self.target = self.root.get_ref(target).instantiate(self)
  
  def layout_cairo(self, cr):
    return self.target.layout_cairo(cr)
    
  def draw_cairo(self, cr, rect, depth):
    return self.target.draw_cairo(cr, rect, depth)
        
  def wx_popupmenu_populate(self, menu):
    return False
  