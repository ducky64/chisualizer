import chisualizer.visualizers.Base as Base
import chisualizer.visualizers.Data as Data

@Base.visualizer_register('DataText')
class DataText(Data.Data):
  """Visualizer for data represented as text."""
  @classmethod
  def from_xml(cls, parent, node):
    new = super(DataText, cls).from_xml(parent, node)
    return new
  
  def clone(self, new_parent):
    cloned = super(DataText, self).clone(new_parent)
    return cloned
