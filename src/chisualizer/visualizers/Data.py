from VisualizerBase import VisualizerBase

class Data(VisualizerBase):
  """Abstract base class for visualizer objects depending on node values.
  Provides the node field."""
  @classmethod
  def from_xml_cls(cls, element, parent):
    new = super(Data, cls).from_xml_cls(element, parent)
    new.node = new.get_chisel_api().get_node_reference(new.path)
    return new
