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
    target_obj = self.get_ref(self.target)
    if not isinstance(target_obj, VisualizerBase):
      raise ValueError("VisualizerRef does not point to VisualizerBase-derived object: ref '%s'" % self.ref)
    
    # TODO: FIXME make this less hacky
    old_path_component = target_obj.path_component 
    target_obj.path_component = self.path_component + target_obj.path_component
    instantiated = target_obj.instantiate(new_parent)
    
    if self.label and instantiated.label:
      instantiated.label = self.label + instantiated.label
    elif self.label:
      instantiated.label = self.label
    
    target_obj.path_component = old_path_component
    
    return instantiated
