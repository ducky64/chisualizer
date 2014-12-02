from collections import namedtuple
import logging

from Verilog_VCD.Verilog_VCD import parse_vcd

from Common import Circuit, CircuitNode, CircuitView, TemporalNode
from ValueDictView import ValueDictView

VcdNode = namedtuple('VcdNode', ['vcd_key', 'tv_list', 'size'])

def vcd_val_to_int(vcd_val_str):
  assert isinstance(vcd_val_str, basestring)
  if vcd_val_str.find('x') >= 0:
    logging.warn("Value contains 'x', converting to 0")
    vcd_val_str = vcd_val_str.replace('x', '0')
  if vcd_val_str.find('z') >= 0:
    logging.warn("Value contains 'z', converting to 0")
    vcd_val_str = vcd_val_str.replace('z', '0')
    
  try:
    return int(vcd_val_str, 2)
  except ValueError as e:
    logging.error("Unable to decode VCD value '%s'" % vcd_val_str)
    raise e

class VcdCircuit(Circuit):
  def __init__(self, vcd_filename):
    super(VcdCircuit, self).__init__()
    logging.info("Parsing VCD file '%s'..." % vcd_filename)
    self.parsed_vcd = parse_vcd(vcd_filename)
    logging.info("Done parsing '%s'" % vcd_filename)
  
    self.nodes = {}
    
    for vcd_key, nets_tv_dict in self.parsed_vcd.iteritems():
      for net_dict in nets_tv_dict['nets']:
        node_name = net_dict['hier'] + '.' + net_dict['name']
        assert node_name not in self.nodes, "duplicate name: '%s': %s" % (node_name, net_dict)
        self.nodes[node_name] = VcdNode(vcd_key=vcd_key,
                                        tv_list=nets_tv_dict['tv'],
                                        size=int(net_dict['size'], 10))

    logging.info("%i nodes total", len(self.nodes))

    self.initial_temporal_node = self.create_initial_temporal_node()
    self.current_temporal_node = self.initial_temporal_node

    self.width_dict = {}
    for node_name, vcd_node in self.nodes.iteritems():
      self.width_dict[node_name] = vcd_node.size

    self.current_view = ValueDictView(self, self.width_dict)
    self.historical_view = ValueDictView(self, self.width_dict)
    self.current_view.set_view(self.current_temporal_node.get_historical_state())

  def create_initial_temporal_node(self, cycle=0):
    # TODO: refactor so they reference common data structure instead of two
    # dicts (for efficiency reasons - constant term savings).
    tv_positions = {}
    state = {}
    for node_name, vcd_node in self.nodes.iteritems():
      prev_idx = 0
      for idx, tv_pair in enumerate(vcd_node.tv_list):
        if tv_pair[0] > cycle:
          break
        prev_idx = idx
      
      state[node_name] = vcd_val_to_int(vcd_node.tv_list[prev_idx][1])
      tv_positions[node_name] = prev_idx
    return VcdTemporalNode(self, None, cycle, tv_positions, state)

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
    if cycles == 1:
      self.current_temporal_node = self.current_temporal_node.get_next_time()
      assert self.current_temporal_node is not None
    else:
      target_cyc = self.current_temporal_node.cycle + cycles
      self.current_temporal_node = self.create_initial_temporal_node(target_cyc)
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
  