class Circuit(object):
  """
  Interface definition for a circuit. Consists of a current circuit view (what
  would be displayed in a "main panel" along with optional state history.
  """
  def __init__(self):
    self.modified_callback_fns = []
  
  def has_node(self, node):
    """Returns whether node is API-accessible in the host."""
    raise NotImplementedError
    
  def get_nodes_list(self):
    """Returns a list of API-accessible nodes in the circuit.
    Depending on the optimization level during synthesis, some nodes may not
    be accessible.
    """
    raise NotImplementedError
  
  def register_modified_callback(self, callback_fn):
    self.modified_callback_fns.append(callback_fn)
  
  def do_modified_callback(self):
    for callback_fn in self.modified_callback_fns:
      callback_fn()
      
  def get_current_view(self):
    """Returns a CircuitView object viewing the circuit state at the current
    timestep."""
    raise NotImplementedError
      
  def get_historical_view(self):
    """Returns a HistoricalCircuitView object with the ability to view
    circuit state in the past."""
    raise NotImplementedError

  def reset(self, cycles):
    """Hold circuit in reset for some cycles."""
    raise NotImplementedError
  
  def clock(self, cycles):
    """Clocks circuit for some cycles."""
    raise NotImplementedError

  def current_to_value_dict(self):
    """Returns the current circuit state as a value dict, which can be loaded
    into a ValueDictView."""
    raise NotImplementedError

  def snapshot_save(self, name):
    """Saves a snapshot of the current state under name"""
    raise NotImplementedError
  
  def snapshot_restore(self, name):
    """Restores a previously saved snapshot under name to the current state.
    Raises an exception if not successful."""
    raise NotImplementedError
  
  def close(self):
    """Closes the connection to the API host. If this is the only user of the
    host, the host should terminate."""
    raise NotImplementedError

class CircuitView(object):
  """
  Interface definition for a circuit view - provides access (read at least, 
  write if applicable) to the state of the circuit at some time step.
  """  
  def get_root_node(self):
    """Returns a CircuitNode reference to the root node. Likely, that node
    will be a dummy path holder.
    """
    raise NotImplementedError
  
class HistoricalCircuitView(CircuitView):
  def set_view(self, state):
    """Sets this view to some (historical) circuit state. State currently
    can be anything.
    """
    raise NotImplementedError
  
class CircuitNode(object):
  """
  Interface definition for a circuit node (wire/register/memory/whatever) tied
  to a particular CircuitView.
  """
  @staticmethod
  def join_path(base_path, child_path):
    """Joins a base path and a child path, handling special functionality (like
    .__up__), and returning the combined path as a string,
    """
    # TODO: make this more general, allowing __up__ anywhere within child?
    while child_path.startswith(".__up__"):
      child_path = child_path[7:]
      base_path = base_path[:base_path.rindex(".")]
    return base_path + child_path  
  
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

  def has_value(self):
    """Returns True if this node has a value."""
    raise NotImplementedError
  
  def can_set_value(self):
    """Returns True if this node can set its value."""
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
    """Returns a ChiselApiNode of this node's child at some subscript. Used
    mainly for accessing memory elements.
    TODO: merge with get_child_reference?
    """
    raise NotImplementedError
  
  def get_child_reference(self, child_path):
    """Returns a ChiselApiNode of some subpath under this node.
    """
    raise NotImplementedError