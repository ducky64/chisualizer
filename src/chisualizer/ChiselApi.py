class ChiselApiNode:
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
    raise NotImplementedError
  
  def get_depth(self):
    """Returns the depth of a node for subscriptable nodes (like memories).
    Raises a ValueError for non-subscriptable nodes.
    """
    raise NotImplementedError

  def get_value(self):
    """Returns the current value of a node in the circuit as a integer type.
    This can be used to access an memory array by subscripting the address
    in brackets.
    """
    raise NotImplementedError

  def set_value(self):
    """Sets a node's value, and propagates it through the circuit.
    Only meaningful on registers, as other values will be overridden when
    propagation occurs.
    Value may either be an integer type or a string representation of an 
    integer (which will be parsed).
    """
    raise NotImplementedError

  def get_subscript_reference(self, subscript):
    raise NotImplementedError
  
  def get_child_reference(self, child_name):
    raise NotImplementedError

class ChiselApi:
  """
  API definition to interface with running Chisel RTL.
  Subclass this for particular implementations to interface with, like the
  emulator over stdin/stdout.
  """
  def has_node(self, node):
    """Returns whether node is API-accessible in the host."""
    raise NotImplementedError
    
  def get_nodes_list(self):
    """Returns a list of API-accessible nodes in the circuit.
    Depending on the optimization level during synthesis, some nodes may not
    be accessible.
    """
    raise NotImplementedError
  
  def reset(self, cycles):
    """Hold circuit in reset for some cycles."""
    raise NotImplementedError
  
  def clock(self, cycles):
    """Clocks circuit for some cycles."""
    raise NotImplementedError
  
  def get_node_reference(self, node):
    """Returns a ChiselApiNode reference for the given node. The reference
    object allows all the operations in the API, but possibly at a higher
    speed (and more convenient format) due to referencing."""
    raise NotImplementedError
  