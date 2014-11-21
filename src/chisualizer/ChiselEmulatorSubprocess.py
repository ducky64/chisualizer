import logging
import subprocess
import string

from chisualizer.ChiselApi import ChiselApiNode, ChiselApi

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

class ChiselSubprocessEmulatorNode(ChiselApiNode):
  def __str__(self):
    return "%s: %s" % (self.__class__.__name__, self.path)
  
  def __init__(self, api, path):
    assert isinstance(api, ChiselEmulatorSubprocess)
    self.api = api
    self.path = path

  def join_path(self, path_base, path_component):
    # TODO: add __up__ here
    return path_base + path_component
  
  def get_node_by_path(self, path):
    if self.api.has_node(path):
      if path in self.api.mems: # TODO more generalized solution
        return ChiselSubprocessEmulatorMem(self.api, path)
      else:
        return ChiselSubprocessEmulatorWire(self.api, path)
    else:
      return ChiselSubprocessEmulatorPlaceholder(self.api, path)

  def get_child_reference(self, child_path):
    if not child_path:
      return self
    return self.get_node_by_path(self.join_path(self.path, child_path))

class ChiselSubprocessEmulatorPlaceholder(ChiselSubprocessEmulatorNode):
  def has_value(self):
    return False
  
  def can_set_value(self):
    return False

class ChiselSubprocessEmulatorWire(ChiselSubprocessEmulatorNode):
  def __init__(self, api, path):
    super(ChiselSubprocessEmulatorWire, self).__init__(api, path)
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
    return (result_ok(self.api.command('wire_poke', self.path, value))
        and result_ok(self.api.command('propagate')))

  def get_subscript_reference(self, subscript):
    raise NotImplementedError("Cannot subscript wire.")

class ChiselSubprocessEmulatorMem(ChiselSubprocessEmulatorNode):
  def __init__(self, api, path):
    super(ChiselSubprocessEmulatorMem, self).__init__(api, path)
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
    return ChiselSubprocessEmulatorMemElement(self, subscript)

class ChiselSubprocessEmulatorMemElement(ChiselSubprocessEmulatorNode):
  def __init__(self, parent, subscript):
    assert isinstance(parent, ChiselSubprocessEmulatorMem)
    assert isinstance(subscript, int)
    super(ChiselSubprocessEmulatorMemElement, self).__init__(parent.api,
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
    return (result_ok(self.api.command('mem_poke',
                                       self.parent.path, self.element_num,
                                       value))
        and result_ok(self.api.command('propagate')))

class ChiselEmulatorSubprocess(ChiselApi):
  def __init__(self, emulator_path, reset=True):
    """Starts the emulator subprocess."""
    self.p = subprocess.Popen(emulator_path,
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)

    self.wires = result_to_list(self.command("list_wires"))
    self.mems =  result_to_list(self.command("list_mems"))
    logging.debug("Found wires: %s" % self.wires)
    logging.debug("Found mems: %s" % self.mems)
    
    if reset:
      self.reset(1)
      logging.debug("Reset circuit")

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
  
  def reset(self, cycles):
    return result_to_int(self.command("reset", cycles))
  
  def clock(self, cycles):
    return result_to_int(self.command("clock", cycles))
  
  def get_root_node(self):
    return ChiselSubprocessEmulatorPlaceholder(self, "")

  def snapshot_save(self, name):
    self.command("referenced_snapshot_save", name)
  
  def snapshot_restore(self, name):
    self.command("referenced_snapshot_restore", name)
    
  def close(self):
    self.command("quit")
    