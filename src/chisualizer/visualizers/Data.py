from chisualizer.visualizers.VisualizerBase import VisualizerBase

class Data(VisualizerBase):
  """Abstract base class for visualizer objects depending on node values."""
  def set_node_value(self, value):
    """Sets the value of the associated node."""
    return self.get_chisel_api().set_node_value(self.path, value)
  
  def get_node_value(self):
    """Returns the value of the associated node."""
    return self.get_chisel_api().get_node_value(self.path)
  
  def get_node_width(self):
    """Returns the bitwidth of the associated node."""
    return self.get_chisel_api().get_node_width(self.path)
    
  def get_node_type(self):
    """Returns the type of the associated node, as a string."""
    return self.get_chisel_api().get_node_type(self.path)
  