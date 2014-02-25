import chisualizer.Base as Base
from VisualizerBase import VisualizerBase

@Base.xml_register('VisualizerRef')
class VisualizerRef(VisualizerBase):
  """Lazy initialized reference to another visualizer"""
  @classmethod
  def from_xml_cls(cls, element, **kwargs):
    new = super(VisualizerRef, cls).from_xml_cls(element, **kwargs)
    new.target = element.get('target', None)
    if not new.target:
      raise ValueError("VisualizerRef must have 'target' attribute") 
    return new
  
  def instantiate(self, new_parent):
    """Instantiates this visualizer template by cloning the template and
    resolving all references. Acts as clone (to a new parent) if called by an
    already-instantiated object.
    """
    target_obj = self.container.get_ref(self.target)
    if not isinstance(target_obj, VisualizerBase):
      raise ValueError("VisualizerRef does not point to VisualizerBase-derived object: ref '%s'" % self.ref)
    new_obj = target_obj.instantiate(new_parent)
      
    if self.path_component:
      new_obj.path_component = self.path_component + new_obj.path_component
      new_obj.path = new_obj.parent.path + new_obj.path_component
      
    return new_obj
