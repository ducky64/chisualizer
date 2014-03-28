from VisualizerBase import VisualizerBase

class Data(VisualizerBase):
  """Abstract base class for visualizer objects depending on node values."""
  @classmethod
  def from_xml_cls(cls, element, parent):
    new = super(Data, cls).from_xml_cls(element, parent)
    new.node = None
    return new
  
  def instantiate(self, new_parent):
    cloned = super(Data, self).instantiate(new_parent)
    if self.node:
      cloned.node = self.node()
    else:
      cloned.node = self.get_chisel_api().get_node_reference(cloned.path)
    return cloned
  