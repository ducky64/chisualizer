class ChiselDummyApiNode:
  def get_type(self):
    raise NotImplementedError

  def get_width(self):
    return 32
  
  def get_depth(self):
    return 16

  def get_value(self):
    return 0

  def set_value(self):
    pass

  def get_subscript_reference(self, subscript):
    return ChiselDummyApiNode()
  
  def get_child_reference(self, child_name):
    return ChiselDummyApiNode()

class ChiselDummyApi:
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
  
  def get_node_reference(self, node):
    return ChiselDummyApiNode()
  
  def snapshot_save(self, name):
    pass
  
  def snapshot_restore(self, name):
    pass
  
  def close(self):
    pass
  