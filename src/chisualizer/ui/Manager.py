import wx

from ChisualizerFrame import ChisualizerFrame
from chisualizer.visualizers.VisualizerBase import AbstractVisualizer
from chisualizer.visualizers.Theme import DarkTheme

from chisualizer.util import Rectangle

class VisualizerRoot(object):
  """Root of the visualizer descriptor tree."""
  def __init__(self, circuit, vis_descriptor):
    """Initialize this descriptor from a file and given a ChiselApi object."""
    # Hacks to get this to behave as a AbstractVisualizer
    # TODO: FIX, perhaps with guard node
    self.root = self
    self.path = ""
    
    self.api = circuit
    self.node = self.api.get_root_node()
    self.theme = DarkTheme()

    self.visualizer = vis_descriptor.instantiate(self, valid_subclass=AbstractVisualizer)

  def update(self):
    self.visualizer.update()

  def layout_cairo(self, cr):
    # TODO: make entire layout_cairo stack work with rectangles
    return Rectangle((0, 0), self.visualizer.layout_cairo(cr))
  
  def draw_cairo(self, cr, rect):
    return self.visualizer.draw_cairo(cr, rect, 0)

  def get_theme(self):
    # TODO refactor this, probably makes more sense to set themes here
    return self.theme

  def set_theme(self, theme):
    # TODO: is persistent theme state really the best idea?
    self.theme = theme

  def get_api(self):
    return self.circuit

class ChisualizerManager(object):
  def __init__(self, vis_descriptor, circuit):
    self.vis_descriptor = vis_descriptor
    self.circuit = circuit
    
  def run(self):
    app = wx.App(False)
    for elt_name, elt in self.vis_descriptor.get_display_elements().iteritems():
      vis_root = VisualizerRoot(self.circuit, elt)
      ChisualizerFrame(None, elt_name, self.circuit, vis_root)
    app.MainLoop()
    