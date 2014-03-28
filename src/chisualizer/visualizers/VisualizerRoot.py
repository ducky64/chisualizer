import logging
import string

from chisualizer.Base import Base
from chisualizer.visualizers.VisualizerBase import VisualizerBase, Rectangle

import cairo

import wx

class VisualizerRoot(Base):
  """Visualizer Root, maintains data structures to interface between the
  parsed visualizers and the rest of the system (like the API and the
  VisualizerDescriptor container class."""
  
  def __init__(self, chisel_api):
    super(VisualizerRoot, self).__init__()
    self.chisel_api = chisel_api
    self.visualizer = None
    self.parent = self
    self.root = self
    self.registry = {}
    
    self.path = ""
    
  @classmethod
  def from_xml_cls(cls, element, parent=None):
    raise RuntimeError("Cannot instantiate VisualizerRoot")
  
  def instantiate_visualizer(self):
    self.visualizer = self.visualizer.instantiate(self)

  def get_ref(self, ref):
    from chisualizer.display.DisplayBase import display_registry
    if ref in display_registry:
      return display_registry[ref]
    if ref in self.registry:
      return self.registry[ref]
    raise NameError("Unknown ref '%s'" % ref)
  
  def parse_children(self, xml_root):
    elt = None
    for child in xml_root:
      elt = Base.from_xml(child, self)
      ref = child.get('ref', None)
      if ref:
        if ref in self.registry: raise NameError("Duplicate ref '%s'", ref)
        self.registry[ref] = elt
        logging.debug("Registered '%s'", ref)
    self.visualizer = elt
  
  def get_chisel_api(self):
    return self.chisel_api
  
  def layout_and_draw_cairo(self, cr):
    size_x, size_y = self.visualizer.layout_cairo(cr)
    rect = Rectangle((0, 0), (size_x, size_y))
    return self.visualizer.draw_cairo(cr, rect, 0)
  