from collections import namedtuple
import logging

from Verilog_VCD.Verilog_VCD import parse_vcd

from Common import Circuit, CircuitNode, CircuitView, TemporalNode
from ValueDictView import ValueDictView

VcdNode = namedtuple('VcdNode', ['vcd_key', 'tv_list', 'size'])

def vcd_val_to_int(vcd_val_str):
  assert isinstance(vcd_val_str, basestring)
  return int(vcd_val_str, 2)

class VcdCircuit(Circuit):
  def __init__(self, vcd_filename):
    super(VcdCircuit, self).__init__()
    self.parsed_vcd = parse_vcd(vcd_filename)
  
    self.nodes = {}
    
    for vcd_key, nets_tv_dict in self.parsed_vcd.iteritems():
      for net_dict in nets_tv_dict['nets']:
        node_name = net_dict['hier'] + '.' + net_dict['name']
        assert node_name not in self.nodes
        self.nodes[node_name] = VcdNode(vcd_key=vcd_key,
                                        tv_list=nets_tv_dict['tv'],
                                        size=int(net_dict['size'], 10))

    self.initial_temporal_node = self.create_initial_temporal_node()
    self.current_temporal_node = self.initial_temporal_node

    self.width_dict = {}
    for node_name, vcd_node in self.nodes.iteritems():
      self.width_dict[node_name] = vcd_node.size

    self.current_view = ValueDictView(self, self.width_dict)
    self.historical_view = ValueDictView(self, self.width_dict)
    self.current_view.set_view(self.current_temporal_node.get_historical_state())

  def create_initial_temporal_node(self):
    # TODO: refactor so they reference common data structure instead of two
    # dicts (for efficiency reasons - constant term savings).
    tv_positions = {}
    state = {}
    for node_name, vcd_node in self.nodes.iteritems():
      state[node_name] = vcd_val_to_int(vcd_node.tv_list[0][1])
      tv_positions[node_name] = 0
    return VcdTemporalNode(self, None, 0, tv_positions, state)

  def get_current_temporal_node(self):
    return self.current_temporal_node
      
  def get_current_view(self):
    return self.current_view
      
  def get_historical_view(self):
    return self.historical_view
  
  def navigate_next_mod(self):
    logging.warn("No modifiable state in VCDs")
    pass
  
  def navigate_prev_mod(self):
    logging.warn("No modifiable state in VCDs")
    pass

  def navigate_back(self):
    if self.current_temporal_node.get_prev_time():
      self.current_temporal_node = self.current_temporal_node.get_prev_time()
    else:
      logging.warn("Can't navigate back any further")
    self.current_view.set_view(self.current_temporal_node.get_historical_state())
      
  def navigate_fwd(self, cycles=None):
    if cycles is None:
      cycles = 1
    while cycles > 0:
      self.current_temporal_node = self.current_temporal_node.get_next_time()
      assert self.current_temporal_node is not None
      cycles -= 1
    self.current_view.set_view(self.current_temporal_node.get_historical_state())

  def reset(self, cycles):
    self.current_temporal_node = self.initial_temporal_node()
    self.current_view.set_view(self.current_temporal_node.get_historical_state())

class VcdTemporalNode(TemporalNode):
  def __init__(self, circuit, prev_node, cycle, tv_positions, state):
    self.circuit = circuit
    self.prev_node = prev_node
    self.next_node = None
    
    self.cycle = cycle
    self.tv_positions = tv_positions
    self.state = state
  
  def get_historical_state(self):
    return self.state
  
  def get_snapshot_state(self):
    return self.state
  
  def get_label(self):
    return str(self.cycle)
  
  def get_prev_time(self):
    return self.prev_node

  def get_next_time(self):
    if self.next_node is None:
      self.next_node = self.generate_next_node()
    return self.next_node

  def generate_next_node(self):
    new_tv_positions = {}
    new_state = {}
    new_cycle = self.cycle + 1
    for node_name, vcd_node in self.circuit.nodes.iteritems():
      tv_index = self.tv_positions[node_name] 
      if tv_index+1 < len(vcd_node.tv_list):
        assert vcd_node.tv_list[tv_index+1][0] >= new_cycle  
        if vcd_node.tv_list[tv_index+1][0] == new_cycle:
          tv_index = tv_index + 1
      new_tv_positions[node_name] = tv_index
      new_state[node_name] = vcd_val_to_int(vcd_node.tv_list[tv_index][1])
    return VcdTemporalNode(self.circuit, self, new_cycle, new_tv_positions, 
                           new_state)

  def get_prev_mod(self):
    return None
  
  def get_next_mod(self):
    return None
  