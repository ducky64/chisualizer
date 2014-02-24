import chisualizer.Base as Base
from VisualizerBase import VisualizerBase

@Base.xml_register('VisualizerRef')
class VisualizerRef(VisualizerBase):
  """Lazy initialized reference to another visualizer"""
  @classmethod
  def from_xml_cls(cls, parent, node):
    new = super(VisualizerRef, cls).from_xml_cls(parent, node)
    new.target = node.get('target', None)
    if not new.target:
      raise ValueError("VisualizerRef must have 'target' attribute") 
    return new
  
  def instantiate(self, new_parent):
    """Instantiates this visualizer template by cloning the template and
    resolving all references. Acts as clone (to a new parent) if called by an
    already-instantiated object.
    """
    if self.target in Base.ref_registry:
      ref_obj = Base.ref_registry[self.target]
      if not isinstance(ref_obj, VisualizerBase):
        raise ValueError("VisualizerRef does not point to VisualizerBase-derived object: ref '%s'" % self.ref)
      new_obj = ref_obj.instantiate(self, new_parent)
      
      if self.path_component:
        new_obj.path_component = self.path_component + new_obj.path_component
        new_obj.path = new_obj.parent.path + new_obj.path_component
      
      return new_obj
    else:
      raise ValueError("VisualizerRef not found: target '%s'" % self.target)