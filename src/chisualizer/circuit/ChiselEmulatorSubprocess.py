import logging
import subprocess
import string
import atexit

from Common import Circuit, CircuitNode, CircuitView, TemporalNode
from ValueDictView import ValueDictView

def result_to_list(res):
  if not res:
    return []
  return string.split(res)

def result_to_int(res):
  try:
    return int(res, 0)
  except ValueError:
    raise ValueError("Expected int, got '%s'" % res)

def result_to_bool(res):
  if res == "true":
    return True
  elif res == "false":
    return False
  else:
    raise ValueError("Expected int, got '%s'" % res)

def result_ok(res):
  if res == "ok":
    return True
  else:
    return False

class ChiselEmulatorSubprocess(Circuit):
  def __init__(self, emulator_path, reset=True):
    """Starts the emulator subprocess."""
    super(ChiselEmulatorSubprocess, self).__init__()
    
    self.p = subprocess.Popen(emulator_path,
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
    atexit.register(self.p.terminate)

    self.wires = result_to_list(self.command("list_wires"))
    self.mems =  result_to_list(self.command("list_mems"))
    logging.debug("Found wires: %s" % self.wires)
    logging.debug("Found mems: %s" % self.mems)
    
    if reset:
      self.reset(1)
      logging.debug("Reset circuit")
      
    self.temporal_nodes_count = 0
    self.temporal_node = self.create_temporal_node(0)

  def command(self, op, *args):
    """Sends a command to the emulator, and returns the output string."""
    # sanity check - extra newlines will break the protocol
    assert isinstance(op, basestring)
    cmd = op
    for arg in args:
      cmd += ' ' + str(arg)
    if cmd.find('\n') != -1:
      raise ValueError("Command contains unexpected newline: '%s'" % cmd)
        
    self.p.stdin.write(cmd + '\n')
    self.p.stdin.flush();
    out = self.p.stdout.readline().strip()
    if out.startswith('error'):
      raise ValueError("Command '%s' returned error: '%s'" % (cmd, out))
    logging.debug("API: '%s' -> '%s'", cmd, out)
    return out;
  
  def has_node(self, node):
    return node in self.wires or node in self.mems

  def get_nodes_list(self):
    out = []
    out.extend(self.wires)
    out.extend(self.mems)
    return out

  def create_temporal_node(self, cycle):
    self.temporal_nodes_count += 1
    return ChiselTemporalNode(self.current_to_value_dict(),
                              self.temporal_nodes_count, 
                              cycle)

  def update_temporal_node(self):
    self.snapshot_save(self.temporal_node.get_snapshot_state())
    self.temporal_node.update(self.current_to_value_dict())

  def get_current_temporal_node(self):
    return self.temporal_node

  def do_modified_callback(self):
    # TODO: This can probably be made more efficient
    self.update_temporal_node()
    if self.temporal_node.get_next_time() is not None:
      prev_temporal_node = self.temporal_node
      self.temporal_node = self.create_temporal_node(self.temporal_node.cycle)
      self.temporal_node.prev_mod = prev_temporal_node
      if prev_temporal_node.get_next_mod() is not None:
        self.temporal_node.next_mod = prev_temporal_node.next_mod
        prev_temporal_node.next_mod.prev_mod = self.temporal_node 
      prev_temporal_node.next_mod = self.temporal_node 
    super(ChiselEmulatorSubprocess, self).do_modified_callback()
    
  def navigate_next_mod(self):
    if self.temporal_node.get_next_mod() is not None:
      self.update_temporal_node()
      self.temporal_node = self.temporal_node.get_next_mod()
      self.snapshot_restore(self.temporal_node.get_snapshot_state())
    else:
      logging.warn("No next mod")
  
  def navigate_prev_mod(self):
    if self.temporal_node.get_prev_mod() is not None:
      self.update_temporal_node()
      self.temporal_node = self.temporal_node.get_prev_mod()
      self.snapshot_restore(self.temporal_node.get_snapshot_state())
    else:
      logging.warn("No prev mod")

  def navigate_back(self):
    if self.temporal_node.get_prev_time() is not None:
      self.update_temporal_node()
      self.temporal_node = self.temporal_node.get_prev_time()
      self.snapshot_restore(self.temporal_node.get_snapshot_state())
    else:
      logging.warn("No snapshots to revert")

  def navigate_fwd(self, cycles=None):
    if cycles is None:
      self.navigate_step()
    else:
      self.navigate_to_cycle(self.temporal_node.cycle + cycles)

  def navigate_step(self):
    self.update_temporal_node()
    if self.temporal_node.get_next_time() is None:
      self.navigate_to_cycle(self.temporal_node.cycle + 1)
    else:
      self.temporal_node = self.temporal_node.get_next_time()
      self.snapshot_restore(self.temporal_node.get_snapshot_state())

  def navigate_to_cycle(self, target_cycle):
    self.update_temporal_node()
    curr_temporal_node = self.temporal_node
    while True:
      next_temporal_node = curr_temporal_node.get_next_time()
      if next_temporal_node is None or next_temporal_node.cycle > target_cycle:
        self.temporal_node = curr_temporal_node
        self.snapshot_restore(self.temporal_node.get_snapshot_state())
        self.clock(target_cycle - curr_temporal_node.cycle)
        return
      elif next_temporal_node.cycle == target_cycle:
        self.temporal_node = next_temporal_node
        self.snapshot_restore(self.temporal_node.get_snapshot_state())
        return        
      curr_temporal_node = next_temporal_node
      
  def reset(self, cycles):
    self.temporal_nodes_count = 0
    self.temporal_node = self.create_temporal_node(0)
    return result_to_int(self.command("reset", cycles))
  
  def clock(self, cycles):
    cycles = result_to_int(self.command("clock", cycles)) 
    prev_temporal_node = self.temporal_node
    self.temporal_node = self.create_temporal_node(self.temporal_node.cycle + cycles)
    self.temporal_node.prev_time = prev_temporal_node
    if prev_temporal_node.get_next_time() is not None:
      assert prev_temporal_node.get_next_time().cycle > self.temporal_node.cycle
      self.temporal_node.next_time = prev_temporal_node.next_time
      prev_temporal_node.next_time.prev_time = self.temporal_node
    prev_temporal_node.next_time = self.temporal_node
    return cycles

  def current_to_value_dict(self):
    rtn = {}
    for node_name in self.wires:
      rtn[node_name] = result_to_int(self.command('wire_peek', node_name))
    return rtn

  def snapshot_save(self, name):
    self.command("referenced_snapshot_save", name)
  
  def snapshot_restore(self, name):
    self.command("referenced_snapshot_restore", name)
    
  def get_historical_view(self):
    width_dict = {}
    for node_name in self.wires:
      width_dict[node_name] = result_to_int(self.command('wire_width', node_name))
    return ValueDictView(self, width_dict)
  
  def get_current_view(self):
    return ChiselCircuitView(self)
    
  def close(self):
    self.command("quit")

class ChiselCircuitView(CircuitView):
  def __init__(self, parent):
    self.parent = parent
    
  def get_root_node(self):
    return ChiselNodePlaceholder(self.parent, "")
  
class ChiselNode(CircuitNode):
  def __str__(self):
    return "%s: %s" % (self.__class__.__name__, self.path)
  
  def __init__(self, api, path):
    assert isinstance(api, ChiselEmulatorSubprocess)
    self.api = api
    self.path = path
  
  def get_node_by_path(self, path):
    if self.api.has_node(path):
      if path in self.api.mems: # TODO more generalized solution
        return ChiselMem(self.api, path)
      else:
        return ChiselWire(self.api, path)
    else:
      return ChiselNodePlaceholder(self.api, path)

  def get_child_reference(self, child_path):
    if not child_path:
      return self
    return self.get_node_by_path(self.join_path(self.path, child_path))

class ChiselNodePlaceholder(ChiselNode):
  def has_value(self):
    return False
  
  def can_set_value(self):
    return False

class ChiselWire(ChiselNode):
  def __init__(self, api, path):
    super(ChiselWire, self).__init__(api, path)
    assert api.has_node(path)
        
  def get_type(self):
    raise NotImplementedError("Node types not yet implemented")

  def get_width(self):
    return result_to_int(self.api.command('wire_width', self.path))
  
  def get_depth(self):
    raise ValueError("Cannot get depth of wire")

  def has_value(self):
    return True
  
  def can_set_value(self):
    return True

  def get_value(self):
    return result_to_int(self.api.command('wire_peek', self.path))

  def set_value(self, value):
    rtn = (result_ok(self.api.command('wire_poke', self.path, value))
           and result_ok(self.api.command('propagate')))
    self.api.do_modified_callback()
    return rtn
  
  def get_subscript_reference(self, subscript):
    raise NotImplementedError("Cannot subscript wire.")

class ChiselMem(ChiselNode):
  def __init__(self, api, path):
    super(ChiselMem, self).__init__(api, path)
    self.depth = self.get_depth() # optimization to prevent spamming the API

  def get_type(self):
    raise NotImplementedError("Memory types not yet implemented")

  def get_width(self):
    return result_to_int(self.api.command('mem_width', self.path))
  
  def get_depth(self):
    return result_to_int(self.api.command('mem_depth', self.path))
  
  def has_value(self):
    return False
  
  def can_set_value(self):
    return False
  
  def get_value(self):
    raise ValueError("Cannot peek entire memory array")
    
  def set_value(self, value):
    raise ValueError("Cannot poke entire memory array")  

  def get_subscript_reference(self, subscript):
    assert subscript < self.depth
    return ChiselMemElement(self, subscript)

class ChiselMemElement(ChiselNode):
  def __init__(self, parent, subscript):
    assert isinstance(parent, ChiselMem)
    assert isinstance(subscript, int)
    super(ChiselMemElement, self).__init__(parent.api,
                                                             "%s[%i]" % (parent.path, subscript))
    self.parent = parent
    self.element_num = subscript
    
  def get_type(self):
    raise NotImplementedError("Node types not yet implemented")

  def get_width(self):
    return self.parent.get_width()
  
  def get_depth(self):
    raise ValueError("Memory element has no depth")

  def has_value(self):
    return True
  
  def can_set_value(self):
    return True

  def get_value(self):
    return result_to_int(self.api.command('mem_peek',
                                          self.parent.path, self.element_num))

  def set_value(self, value):
    rtn = (result_ok(self.api.command('mem_poke',
                                      self.parent.path, self.element_num,
                                      value))
           and result_ok(self.api.command('propagate')))
    self.api.do_modified_callback()
    return rtn

class ChiselTemporalNode(TemporalNode):
  """A node associated with a particular state in time."""
  def __init__(self, value_dict, snapshot, cycle):
    self.update(value_dict)
    self.snapshot = snapshot
    self.cycle = cycle
    self.prev_time = None
    self.next_time = None
    self.prev_mod = None
    self.next_mod = None
    
  def update(self, value_dict):
    self.value_dict = value_dict
    
  def get_historical_state(self):
    return self.value_dict
  
  def get_snapshot_state(self):
    return self.snapshot
  
  def get_label(self):
    return str(self.cycle)
  
  def get_prev_time(self):
    return self.prev_time

  def get_next_time(self):
    return self.next_time

  def get_prev_mod(self):
    return self.prev_mod
  
  def get_next_mod(self):
    return self.next_mod
