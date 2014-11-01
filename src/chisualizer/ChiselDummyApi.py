class ChiselDummyApiNode:
  """Node reference abstract base class. This provides the methods in the Chisel
  API (below) for a particular node, and possibly at a higher speed because
  of referencing."""
  def get_type(self):
    """Returns the Chisel type of a node."""
    raise NotImplementedError

  def get_width(self):
    """Returns the bit-width of a node. Raises a ValueError for non-node types
    (like modules).
    """
    return 32
  
  def get_depth(self):
    """Returns the depth of a node for subscriptable nodes (like memories).
    Raises a ValueError for non-subscriptable nodes.
    """
    return 1

  def get_value(self):
    """Returns the current value of a node in the circuit as a integer type.
    This can be used to access an memory array by subscripting the address
    in brackets.
    """
    return 0

  def set_value(self):
    """Sets a node's value, and propagates it through the circuit.
    Only meaningful on registers, as other values will be overridden when
    propagation occurs.
    Value may either be an integer type or a string representation of an 
    integer (which will be parsed).
    """
    pass

  def get_subscript_reference(self, subscript):
    return ChiselDummyApiNode()
  
  def get_child_reference(self, child_name):
    return ChiselDummyApiNode()

class ChiselDummyApi:
  """
  API definition to interface with running Chisel RTL.
  Subclass this for particular implementations to interface with, like the
  emulator over stdin/stdout.
  """
  def has_node(self, node):
    """Returns whether node is API-accessible in the host."""
    return True
    
  def get_nodes_list(self):
    """Returns a list of API-accessible nodes in the circuit.
    Depending on the optimization level during synthesis, some nodes may not
    be accessible.
    """
    return []
  
  def reset(self, cycles):
    """Hold circuit in reset for some cycles."""
    pass
  
  def clock(self, cycles):
    """Clocks circuit for some cycles."""
    pass
  
  def get_node_reference(self, node):
    """Returns a ChiselApiNode reference for the given node. The reference
    object allows all the operations in the API, but possibly at a higher
    speed (and more convenient format) due to referencing."""
    return ChiselDummyApiNode()
  
  def snapshot_save(self, name):
    """Saves a snapshot of the current state under name"""
    pass
  
  def snapshot_restore(self, name):
    """Restores a previously saved snapshot under name to the current state.
    Raises an exception if not successful."""
    pass
  
  def close(self):
    """Closes the connection to the API host. If this is the only user of the
    host, the host should terminate."""
    pass
  