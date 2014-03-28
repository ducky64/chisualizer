import chisualizer.Base as Base
from VisualizerBase import VisualizerBase

@Base.xml_register('VisualizerRef')
class VisualizerRef(VisualizerBase):
  """Lazy initialized reference to another visualizer"""
  @classmethod
  def from_xml_cls(cls, element, parent):
    new = super(VisualizerRef, cls).from_xml_cls(element, parent)
    new.target = element.get('target', None)
    if not new.target:
      raise ValueError("VisualizerRef must have 'target' attribute") 
    return new
  
  def instantiate(self, new_parent):
    """Instantiates this visualizer template by cloning the template and
    resolving all references. Acts as clone (to a new parent) if called by an
    already-instantiated object.
    """
    cloned = super(VisualizerRef, self).instantiate(new_parent)
    
    target_obj = self.get_ref(self.target)
    if not isinstance(target_obj, VisualizerBase):
      raise ValueError("VisualizerRef does not point to VisualizerBase-derived object: ref '%s'" % self.ref)
    
    cloned.target = target_obj.instantiate(cloned)
    
    return cloned

  def layout_element_cairo(self, cr):
    return self.target.layout_element_cairo(cr)
  
  def draw_element_cairo(self, cr, rect, depth):
    return self.target.draw_element_cairo(cr, rect, depth)
  