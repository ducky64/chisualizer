import logging
import sys

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

  def get_circuit_node(self):
    return self.node

class ChisualizerManager(object):
  def __init__(self, vis_descriptor, circuit):
    self.vis_descriptor = vis_descriptor
    self.circuit = circuit
    self.circuit.register_modified_callback(self.refresh_visualizers)
    
    self.cycle = 0
    self.snapshots = [] # TODO: generalize with tree
    
    self.frames = []
    
  def run(self):
    app = wx.App(False)
    for elt_name, elt in self.vis_descriptor.get_display_elements().iteritems():
      vis_root = VisualizerRoot(self.circuit, elt)
      vis_frame = ChisualizerFrame(None, self, elt_name, self.circuit, vis_root)
      self.frames.append(vis_frame)
    app.MainLoop()
  
  def exit(self):
    sys.exit()
  
  def refresh_visualizers(self):
    for frame in self.frames:
      frame.vis_refresh()
  
  def get_circuit_cycle(self):
    return self.cycle
  
  def circuit_reset(self, cycles=1):
    logging.info("Reset circuit (%i cycles)", cycles)
    self.circuit.reset(cycles)
    self.cycle = 0
    self.snapshots = []
    self.refresh_visualizers()
    
  def circuit_fwd(self, cycles=1):
    logging.info("Clock circuit (%i cycles)", cycles)
    self.circuit.snapshot_save(str(self.cycle))
    self.snapshots.append(self.cycle)
    self.cycle += self.circuit.clock(cycles)
    self.refresh_visualizers()
    
  def circuit_back(self, cycles=1):
    assert cycles == 1, "TODO generalize to multicycles"
    if self.snapshots:
      logging.info("Revert circuit (%i cycles)", cycles)
      self.cycle = self.snapshots.pop()
      self.circuit.snapshot_restore(str(self.cycle))
      self.refresh_visualizers()
    else:
      logging.warn("No more snapshots to revert")
      
      