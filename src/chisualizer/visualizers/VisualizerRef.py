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
  
  def instantiate(self, new_parent, **kwargs):
    """Instantiates this visualizer template by cloning the template and
    resolving all references. Acts as clone (to a new parent) if called by an
    already-instantiated object.
    """
    target_obj = self.get_ref(self.target)
    if not isinstance(target_obj, VisualizerBase):
      raise ValueError("VisualizerRef does not point to VisualizerBase-derived object: ref '%s'" % self.ref)
    
    path_prefix = self.path
    if 'path_prefix' in kwargs:
      path_prefix = self.path + kwargs['path_prefix']
    
    new_obj = target_obj.instantiate(new_parent, path_prefix=path_prefix, **kwargs)
    
    return new_obj
