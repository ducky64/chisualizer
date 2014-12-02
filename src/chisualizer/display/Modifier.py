from chisualizer.visualizers.VisualizerBase import AbstractVisualizer
import chisualizer.Base as Base
from chisualizer.descriptor import *

class Modifier(Base.Base):
  """Modifies the dynamic attributes of target visualizers."""
  def __init__(self, elt, parent):
    super(Modifier, self).__init__(elt, parent)
    modify_attrs_list = self.static_attr(DataTypes.ObjectAttr, 'modify_attrs').get()
    assert len(modify_attrs_list) == 1, "Chained modify_attrs not supported yet"
    self.modify_attrs = modify_attrs_list[0]

  def apply_to(self, target):
    assert isinstance(target, AbstractVisualizer)
    target.apply_attr_overloads(self, self.modify_attrs)

@Common.tag_register('ArrayIndexModifier')
class ArrayIndexModifier(Modifier):
  """A modifier that works on arrays, modifying the child visualizer at some
  index."""
  def __init__(self, elt, parent):
    super(ArrayIndexModifier, self).__init__(elt, parent)
    self.path_component = self.static_attr(DataTypes.StringAttr, 'index_path').get()
    self.index_eval = self.static_attr(DataTypes.StringAttr, 'index_eval').get()    
    self.index_node = parent.get_circuit_node().get_child_reference(self.path_component)
    if not self.index_node.has_value():
      elt.parse_error("index_path node '%s' has no value" % self.index_node)
    
  def get_array_index(self):
    """Returns the array index to modify"""
    index = eval(self.index_eval, {}, {'x': self.index_node.get_value()})
    assert isinstance(index, int)
    return index
  
@Common.tag_register('CondArrayIndexModifier')
class CondArrayIndexModifier(ArrayIndexModifier):
  """Conditional modifier, only applies when some node is not zero."""
  def __init__(self, elt, parent):
    super(CondArrayIndexModifier, self).__init__(elt, parent)
    self.cond_path_component = self.static_attr(DataTypes.StringAttr, 'cond_path').get()    
    self.cond_eval = self.static_attr(DataTypes.StringAttr, 'cond_eval').get()
    self.cond_node = parent.get_circuit_node().get_child_reference(self.cond_path_component)
    if not self.cond_node.has_value():
      elt.parse_error("cond_path node '%s' has no value" % self.cond_node)
  
  def apply_to(self, target):
    cond = eval(self.cond_eval, {}, {'x': self.cond_node.get_value()})
    assert isinstance(cond, bool)
    if cond:
      super(CondArrayIndexModifier, self).apply_to(target)
    