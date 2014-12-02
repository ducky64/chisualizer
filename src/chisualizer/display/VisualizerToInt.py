from chisualizer.visualizers.VisualizerBase import AbstractVisualizer
import chisualizer.Base as Base
from chisualizer.descriptor import *

class VisualizerToInt(Base.Base):
  """TODO: WRITE ME."""
  def __init__(self, element, parent):
    assert isinstance(parent, AbstractVisualizer)
    super(VisualizerToInt, self).__init__(element, parent)
    self.path_component = self.static_attr(DataTypes.StringAttr, 'path').get()
    self.visualizer = parent  # TODO: perhaps remove me if useless?
    self.node = parent.get_circuit_node().get_child_reference(self.path_component)
  
  def get_int(self):
    """TODO: WRITE ME
    """
    return None

@Common.tag_register('NumericalInt')
class NumericalInt(VisualizerToInt):
  """Returns the processed value of a node as an int.""" 
  def __init__(self, element, parent):
    super(NumericalInt, self).__init__(element, parent)
    self.value_eval = self.static_attr(DataTypes.StringAttr, 'value_eval').get()     
  
  def get_int(self):
    if not self.node.has_value():
      return None
    
    rtn = eval(self.value_eval, {}, {'x': self.node.get_value()})
    assert isinstance(rtn, int)
    return rtn
    