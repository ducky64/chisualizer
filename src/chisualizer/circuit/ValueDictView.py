from Common import CircuitNode, HistoricalCircuitView

class ValueDictView(HistoricalCircuitView):
  """
  View circuit state based on a value dict (from node paths to values
  """
  def __init__(self, circuit, width_dict, mem_depth_dict=None):
    self.value_dict = {}
    self.circuit = circuit
    self.width_dict = width_dict
    self.mem_depth_dict = mem_depth_dict

  def set_view(self, state):
    self.value_dict = state
  
  def get_root_node(self):
    return ValueDictNode(self, "")

  def get_current_temporal_node(self):
    return self.circuit.get_current_temporal_node()

class ValueDictNode(CircuitNode):
  def __init__(self, view, path):
    self.view = view
    self.path = path
    
  def get_type(self):
    raise NotImplementedError("Node types not yet implemented")

  def get_width(self):
    assert self.path in self.view.width_dict
    return self.view.width_dict[self.path]
  
  def get_depth(self):
    return self.view.mem_depth_dict[self.path]

  def has_value(self):
    return self.path in self.view.value_dict
  
  def can_set_value(self):
    return False

  def get_value(self):
    return self.view.value_dict[self.path]
  
  def get_subscript_reference(self, subscript):
    # TODO make this better
    return ValueDictNode(self.view, self.path + "[" + str(subscript) + "]")
  
  def get_child_reference(self, child_path):
    return ValueDictNode(self.view, self.join_path(self.path, child_path))
  