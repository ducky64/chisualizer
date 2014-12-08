from collections import namedtuple
import logging

from Verilog_VCD.Verilog_VCD import parse_vcd

from Common import Circuit, CircuitNode, CircuitView, TemporalNode
from ValueDictView import ValueDictView

VcdNode = namedtuple('VcdNode', ['vcd_key', 'tv_list', 'size'])

VcdBundle = namedtuple('VcdBundle', ['elements', 'size'])
VcdBundleElem = namedtuple('VcdBundleElem', ['high', 'low', 'node'])

VcdPosition = namedtuple('VcdPosition', ['node', 'bundle'])

def vcd_val_to_int(vcd_val_str):
  assert isinstance(vcd_val_str, basestring)
  if vcd_val_str.find('x') >= 0:
    vcd_val_str = vcd_val_str.replace('x', '0')
  if vcd_val_str.find('z') >= 0:
    vcd_val_str = vcd_val_str.replace('z', '0')
    
  try:
    return int(vcd_val_str, 2)
  except ValueError as e:
    logging.error("Unable to decode VCD value '%s'" % vcd_val_str)
    raise e

def vcd_node_next(cycle, curr_idx, node):
  while curr_idx < len(node.tv_list) - 1:
    if node.tv_list[curr_idx+1][0] > cycle:
      break
    curr_idx += 1
  assert curr_idx == len(node.tv_list) - 1 or node.tv_list[curr_idx+1][0] > cycle 
  return curr_idx, node.tv_list[curr_idx][1]

def vcd_bundle_next(cycle, curr_idx, bundle):
  combined_val = ""
  new_idx = []
  assert len(bundle.elements) == len(curr_idx)
  for elem_idx, elem in zip(curr_idx, bundle.elements):
    new_elem_idx, node_val = vcd_node_next(cycle, elem_idx, elem.node)
    new_idx.append(new_elem_idx)
    combined_val += node_val
  return new_idx, combined_val

def scale_tv_list(tv_list, timescale_divisor):
  assert isinstance(timescale_divisor, int) and timescale_divisor >= 1
  if timescale_divisor > 1:
    new_tv_list = []
    for tv_pair in tv_list:
      assert len(tv_pair) == 2
      new_tv_list.append((tv_pair[0]/timescale_divisor, tv_pair[1]))
    return new_tv_list
  else:
    return tv_list

class VcdCircuit(Circuit):
  def __init__(self, vcd_filename, timescale_divisor=1, start_cycle=0):
    super(VcdCircuit, self).__init__()
    logging.info("Parsing VCD file '%s'..." % vcd_filename)
    self.parsed_vcd = parse_vcd(vcd_filename)
    logging.info("Done parsing '%s'" % vcd_filename)
  
    self.nodes = {}
    working_bundles = {}
    self.memory_depths = {} # TODO: refactor
    
    for vcd_key, nets_tv_dict in self.parsed_vcd.iteritems():
      for net_dict in nets_tv_dict['nets']:
        parsed_node = VcdNode(vcd_key=vcd_key,
                              tv_list=scale_tv_list(nets_tv_dict['tv'],
                                                    timescale_divisor),
                              size=int(net_dict['size'], 10))
        node_name = net_dict['hier'] + '.' + net_dict['name']
        bracket_begin = node_name.rfind('[')
        bracket_end = node_name.rfind(']')
        if bracket_begin >= 0 and bracket_end >= 0 and bracket_begin < bracket_end:
          # This deals with ModelSim VCDs which derp bundles into single bits.
          node_name_stripped = node_name[:bracket_begin]
          
          index = node_name[bracket_begin+1:bracket_end]
          delim = index.find(':')
          # TODO more graceful error handling
          if delim >= 0:
            begin_str = index[:delim]
            end_str = index[delim+1:]
            begin = int(begin_str)
            end = int(end_str)
          else:
            begin = end = int(index)
          
          if begin == end and parsed_node.size > 1:
            # Special case for memory element "wires".
            assert node_name not in self.nodes, "duplicate name: '%s': %s" % (node_name, net_dict)
            self.memory_depths[node_name_stripped] = max(self.memory_depths.get(node_name_stripped, 1), begin+1)
            self.nodes[node_name] = parsed_node
          else:
            if node_name_stripped not in working_bundles:
              working_bundles[node_name_stripped] = {} # map high bit to VcdBundleElem
            bundle = working_bundles[node_name_stripped]
          
            assert begin >= end
            assert begin not in bundle
          
            bundle[begin] = VcdBundleElem(begin, end, parsed_node)
        else:
          assert node_name not in self.nodes, "duplicate name: '%s': %s" % (node_name, net_dict)
          self.nodes[node_name] = parsed_node

    logging.info("%i nodes found", len(self.nodes))
    logging.debug("Nodes found: %s", self.nodes.keys())

    # Post-process bundles
    self.bundles = {}
    for node_name, bundle in working_bundles.iteritems():
      largest = None
      prev = 0
      sorted_elems = []
      for begin_idx, bundle_elem in reversed(sorted(bundle.items())):
        assert begin_idx == bundle_elem.high
        if largest is None:
          largest = bundle_elem.high
        else:
          # Checks to ensure contiguous signals - currently parser can't fill in signals
          assert bundle_elem.high == prev - 1, "prev %i, next high %i" % (prev, bundle_elem.high)
        prev = bundle_elem.low 
        sorted_elems.append(bundle_elem)
      if not prev == 0:
        logging.warn("Incomplete signal: %s (%i:%i), discarding", node_name, largest, prev)
      else:
        bundle = VcdBundle(sorted_elems, largest)
        assert node_name not in self.bundles 
        self.bundles[node_name] = bundle
      
    logging.info("%i bundles found", len(self.bundles))  
    logging.debug("Bundles found: %s", self.bundles.keys())
    
    logging.info("%i memories inferred", len(self.memory_depths))
    
    self.initial_temporal_node = self.create_initial_temporal_node(start_cycle)
    self.current_temporal_node = self.initial_temporal_node

    self.width_dict = {}
    for node_name, vcd_node in self.nodes.iteritems():
      self.width_dict[node_name] = vcd_node.size
    for node_name, vcd_bundle in self.bundles.iteritems():
      assert node_name not in self.width_dict
      self.width_dict[node_name] = vcd_bundle.size
  
    self.current_view = ValueDictView(self, self.width_dict, self.memory_depths)
    self.historical_view = ValueDictView(self, self.width_dict, self.memory_depths)
    self.current_view.set_view(self.current_temporal_node.get_historical_state())

  def create_initial_temporal_node(self, cycle=0):
    # TODO: refactor so they reference common data structure instead of two
    # dicts (for efficiency reasons - constant term savings).
    vcd_position = VcdPosition({}, {})
    state = {}
    for node_name, vcd_node in self.nodes.iteritems():
      position, value = vcd_node_next(cycle, 0, vcd_node)
      state[node_name] = vcd_val_to_int(value)
      vcd_position.node[node_name] = position
    for node_name, vcd_bundle in self.bundles.iteritems():
      position, value = vcd_bundle_next(cycle, [0]*len(vcd_bundle.elements), vcd_bundle)
      state[node_name] = vcd_val_to_int(value)
      vcd_position.bundle[node_name] = position
    return VcdTemporalNode(self, None, cycle, vcd_position, state)

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
    self.current_temporal_node = self.initial_temporal_nodel
    self.current_view.set_view(self.current_temporal_node.get_historical_state())

class VcdTemporalNode(TemporalNode):
  def __init__(self, circuit, prev_node, cycle, vcd_position, state):
    self.circuit = circuit
    self.prev_node = prev_node
    self.next_node = None
    
    self.cycle = cycle
    self.vcd_position = vcd_position
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
    new_cycle = self.cycle + 1
    
    new_position = VcdPosition({}, {})
    new_state = {}
    
    for node_name, vcd_node in self.circuit.nodes.iteritems():
      position, value = vcd_node_next(new_cycle, self.vcd_position.node[node_name], vcd_node)
      new_state[node_name] = vcd_val_to_int(value)
      new_position.node[node_name] = position
    for node_name, vcd_bundle in self.circuit.bundles.iteritems():
      position, value = vcd_bundle_next(new_cycle, self.vcd_position.bundle[node_name], vcd_bundle)
      new_state[node_name] = vcd_val_to_int(value)
      new_position.bundle[node_name] = position

    return VcdTemporalNode(self.circuit, self, new_cycle, new_position, 
                           new_state)

  def get_prev_mod(self):
    return None
  
  def get_next_mod(self):
    return None
  