import logging
import subprocess
import string

from chisualizer.ChiselApi import ChiselApi

class ChiselSubprocessEmulatorNode:
  def __init__(self, api, node_path):
    assert isinstance(api, ChiselEmulatorSubprocess)
    assert api.has_node(node_path)
    self.api = api
    self.node_path = node_path
    
  def __str__(self):
    return "%s: %s" % (self.__class__.__name__, self.node_path)
    
  def get_type(self):
    return self.api.get_node_type(self.node_path)

  def get_width(self):
    return self.api.get_node_width(self.node_path)
  
  def get_depth(self):
    return self.api.get_node_depth(self.node_path)

  def get_value(self):
    return self.api.get_node_value(self.node_path)

  def set_value(self):
    return self.api.set_node_value(self.node_path)


class ChiselEmulatorSubprocess(ChiselApi):
  def __init__(self, emulator_path):
    """Starts the emulator subprocess."""
    self.p = subprocess.Popen(emulator_path,
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)

    self.wires = self.result_to_list(self.command("list_wires"))
    self.mems =  self.result_to_list(self.command("list_mems"))
    logging.debug("Found wires: %s" % self.wires)
    logging.debug("Found mems: %s" % self.mems)
    
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
    cmd += "\n"
        
    self.p.stdin.write(cmd)
    self.p.stdin.flush();
    out = self.p.stdout.readline().strip()
    if out.startswith('error'):
      raise ValueError("Command '%s' returned error: '%s'" % (cmd, out))
    return out;

  def result_to_list(self, res):
    if not res:
      return []
    return string.split(res)

  def result_to_int(self, res):
    try:
      return int(res, 0)
    except ValueError:
      raise ValueError("Expected int, got '%s'" % res)

  def result_to_bool(self, res):
    if res == "true":
      return True
    elif res == "false":
      return False
    else:
      raise ValueError("Expected int, got '%s'" % res)

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
  
  def get_node_type(self, node):
    raise NotImplementedError
  
  def get_node_width(self, node):
    if node in self.wires:
      return self.result_to_int(self.command('wire_width', node))
    else:
      raise NotImplementedError("Unknown node '%s'" % node)
  
  def get_node_depth(self, node):
    raise NotImplementedError
  
  def get_node_value(self, node):
    if node in self.wires:
      return self.result_to_int(self.command('wire_peek', node))
    else:
      raise NotImplementedError("Unknown node '%s'" % node)
  
  def set_node_value(self, node, value):
    if node in self.wires:
      return self.result_to_bool(self.command('wire_poke', node, value))
    else:
      raise NotImplementedError("Unknown node '%s'" % node)
  
  def get_node_reference(self, node):
    if node in self.wires:
      return ChiselSubprocessEmulatorNode(self, node)
    else:
      raise NotImplementedError("Unknown node '%s'" % node)