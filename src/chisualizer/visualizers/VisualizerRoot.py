import logging

from chisualizer.Base import Base
from chisualizer.visualizers.Theme import DarkTheme

class VisualizerRoot(Base):
  """Visualizer Root, maintains data structures to interface between the
  parsed visualizers and the rest of the system (like the API and the
  VisualizerDescriptor container class."""
  
  def __init__(self, chisel_api):
    super(VisualizerRoot, self).__init__()
    self.chisel_api = chisel_api
    self.visualizer_elements = []
    self.visualizers = []
    self.visualizer = None  # TODO: allow multiple visualizers in own window
    self.parent = self
    self.root = self
    self.registry = {}
    
    self.theme = DarkTheme()
    
    self.path = ""
    
  @classmethod
  def from_xml_cls(cls, element, parent=None):
    raise RuntimeError("Cannot instantiate VisualizerRoot")

  def get_ref(self, ref):
    if ref in self.registry:
      return self.registry[ref]
    raise NameError("Unknown ref '%s'" % ref)
  
  def parse_children(self, xml_root):
    logging.debug("Parsing XML input")
    for child in xml_root: 
      ref = child.get('ref', None)
      if ref:
        if ref in self.registry: raise NameError("Duplicate ref '%s'" % ref)
        self.registry[ref] = child
        logging.debug("Registered '%s'", ref)
      else:
        self.visualizer_elements.append(child)
  
  def instantiate_visualizers(self):
    logging.debug("Instantiating visualizers")
    for visualizer in self.visualizer_elements:
      self.visualizers.append(Base.from_xml(visualizer, self))
    self.visualizer = self.visualizers[-1]
    
    if len(self.visualizers) > 1:
      raise RuntimeError("Multiple visualizers not currently supported")
  
  def get_chisel_api(self):
    return self.chisel_api

  def set_theme(self, theme):
    self.theme = theme
  
  def get_theme(self):
    return self.theme
    