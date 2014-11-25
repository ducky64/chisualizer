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
  
  def get_current_temporal_node(self):
    return DummyTemporalNode()
  
  def get_current_view(self):
    return DummyCircuitView()

  def get_historical_view(self):
    return DummyCircuitView()
  
  def navigate_next_mod(self):
    pass
  
  def navigate_prev_mod(self):
    pass

  def navigate_back(self):
    pass
  
  def navigate_fwd(self, cycles=None):
    pass
  
  def close(self):
    pass

class DummyCircuitView(HistoricalCircuitView):
  def get_current_temporal_node(self):
    return DummyTemporalNode()
  
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

class DummyTemporalNode(TemporalNode):
  def get_historical_state(self):
    return None
  
  def get_snapshot_state(self):
    return None
  
  def get_label(self):
    return "dummy"
  
  def get_prev_time(self):
    return None

  def get_next_time(self):
    return None

  def get_prev_mod(self):
    return None
  
  def get_next_mod(self):
    return None
