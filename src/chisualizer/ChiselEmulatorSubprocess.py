import logging
import subprocess
import string

from chisualizer.ChiselApi import ChiselApi

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

class ChiselSubprocessEmulatorWire:
  def __init__(self, api, node_path):
    assert isinstance(api, ChiselEmulatorSubprocess)
    assert api.has_node(node_path)
    self.api = api
    self.node_path = node_path
    
  def __str__(self):
    return "%s: %s" % (self.__class__.__name__, self.node_path)
    
  def get_type(self):
    raise NotImplementedError("Node types not yet implemented")

  def get_width(self):
    return result_to_int(self.api.command('wire_width', self.node_path))
  
  def get_depth(self):
    raise ValueError("Cannot get depth of wire")

  def get_value(self):
    return result_to_int(self.api.command('wire_peek', self.node_path))

  def set_value(self, value):
    return result_to_bool(self.api.command('wire_poke', self.node_path, value))

  def get_subscript_reference(self, subscript):
    raise NotImplementedError("Wire subscripting not yet implemented")
  
  def get_child_reference(self, child_name):
    raise ValueError("Cannot get child of wire")

class ChiselSubprocessEmulatorMem:
  def __init__(self, api, node_path):
    assert isinstance(api, ChiselEmulatorSubprocess)
    assert api.has_node(node_path)
    self.api = api
    self.node_path = node_path
    self.depth = self.get_depth()
    
  def __str__(self):
    return "%s: %s" % (self.__class__.__name__, self.node_path)

  def get_type(self):
    raise NotImplementedError("Memory types not yet implemented")

  def get_width(self):
    return result_to_int(self.api.command('mem_width', self.node_path))
  
  def get_depth(self):
    return result_to_int(self.api.command('mem_depth', self.node_path))
  
  def get_value(self):
    raise ValueError("Cannot peek entire memory array")
    
  def set_value(self, value):
    raise ValueError("Cannot poke entire memory array")  

  def get_subscript_reference(self, subscript):
    assert subscript < self.depth
    return ChiselSubprocessEmulatorMemElement(self, subscript)
  
  def get_child_reference(self, child_name):
    raise ValueError("Cannot get child of wire")

class ChiselSubprocessEmulatorMemElement:
  def __init__(self, parent, subscript):
    assert isinstance(parent, ChiselSubprocessEmulatorMem)
    assert isinstance(subscript, int)
    self.api = parent.api
    self.parent = parent
    self.array_path = parent.array_path
    self.element_num = subscript
    
  def __str__(self):
    return "%s: %s" % (self.__class__.__name__, self.node_path)
    
  def get_type(self):
    raise NotImplementedError("Node types not yet implemented")

  def get_width(self):
    return self.parent.get_width()
  
  def get_depth(self):
    raise ValueError("Memory element has no depth")

  def get_value(self):
    return result_to_int(self.api.command('mem_peek',
                                          self.array_path, self.element_num))

  def set_value(self, value):
    return result_to_bool(self.api.command('mem_poke',
                                           self.array_path, self.element_num,
                                           value))

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
    raise NotImplementedError
  
  def reset(self, cycles):
    self.command("reset", cycles)
  
  def clock(self, cycles):
    self.command("clock", cycles)
  
  def get_node_reference(self, node):
    if node in self.wires:
      return ChiselSubprocessEmulatorWire(self, node)
    elif node in self.mems:
      return ChiselSubprocessEmulatorMem(self, node)
    else:
      raise NotImplementedError("Unknown node '%s'" % node)
