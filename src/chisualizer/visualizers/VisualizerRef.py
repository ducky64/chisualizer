import chisualizer.Base as Base
from VisualizerBase import AbstractVisualizer

@Base.xml_register('VisualizerRef')
class VisualizerRef(AbstractVisualizer):
  """Lazy initialized reference to another visualizer"""
  def __init__(self, element, parent):
    super(VisualizerRef, self).__init__(element, parent)
    target = element.get_attr_string('target')
    self.target = self.root.get_ref(target).instantiate(self, valid_subclass=AbstractVisualizer)
  
  def layout_cairo(self, cr):
    return self.target.layout_cairo(cr)
    
  def draw_cairo(self, cr, rect, depth):
    return self.target.draw_cairo(cr, rect, depth)
        
  def wx_prefix(self):
    return self.target.wx_prefix()
    
  def wx_defaultaction(self):
    self.target.wx_defaultaction()
        
  def wx_popupmenu_populate(self, menu):
    return self.target.wxpopupmenu_populate(menu)
  