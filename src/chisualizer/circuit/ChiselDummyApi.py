from chisualizer.circuit.ChiselApi import ChiselApiNode, ChiselApi

class ChiselDummyApiNode(ChiselApiNode):
  def get_type(self):
    raise NotImplementedError

  def get_width(self):
    return 32
  
  def get_depth(self):
    return 16

  def has_value(self):
    return True
  
  def can_set_value(self):
    return False

  def get_value(self):
    return 0

  def set_value(self):
    pass

  def get_subscript_reference(self, subscript):
    return ChiselDummyApiNode()
  
  def get_child_reference(self, child_path):
    return ChiselDummyApiNode()

class ChiselDummyApi(ChiselApi):
  """
  Dummy API, when you want to run without the emulator.
  """
  def has_node(self, node):
    return True
    
  def get_nodes_list(self):
    return []
  
  def reset(self, cycles):
    return 1
  
  def clock(self, cycles):
    return 1
  
  def get_root_node(self):
    return ChiselDummyApiNode()
  
  def snapshot_save(self, name):
    pass
  
  def snapshot_restore(self, name):
    pass
  
  def close(self):
    pass
  