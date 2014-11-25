from chisualizer.circuit.Common import *

class DummyCircuit(Circuit):
  """
  Dummy circuit, when you want to run without the emulator.
  """
  def has_node(self, node):
    return True
    
  def get_nodes_list(self):
    return []
  
  def reset(self, cycles):
    return 1
  
  def clock(self, cycles):
    return 1
  
  def get_current_view(self):
    return DummyCircuitView()

  def get_historical_view(self):
    return DummyCircuitView()
  
  def snapshot_save(self, name):
    pass
  
  def snapshot_restore(self, name):
    pass
  
  def close(self):
    pass

class DummyCircuitView(HistoricalCircuitView):
  def set_view(self, state):
    pass
  
  def get_root_node(self):
    return DummyCircuitNode()

class DummyCircuitNode(CircuitNode):
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
    return DummyCircuitNode()
  
  def get_child_reference(self, child_path):
    return DummyCircuitNode()
