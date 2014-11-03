from VisualizerBase import VisualizerBase

class Data(VisualizerBase):
  """Abstract base class for visualizer objects depending on node values.
  Provides the node field."""
  def __init__(self, element, parent):
    super(Data, self).__init__(element, parent)
    self.node = self.get_chisel_api().get_node_reference(self.path)

  def set_node(self, node):
    # TODO: remove this special case, currently only used for memory instantiation.
    self.node = node