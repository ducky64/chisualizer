from chisualizer.Base import Base

# a global registry for stock display objects
display_registry = {}

# this instantiates display classes into objects that can be referenced
# inside visualizer descriptors
def display_instantiate(name, **kwds):
  def wrap(cls):
    local_name = name
    if local_name in display_registry:
      raise NameError("Attempting to re-register a display: '%s'" % local_name)
    display_registry[local_name] = cls(**kwds)
    return cls
  return wrap

def registry_get_display(display_name):
  if display_name in display_registry:
    return display_registry[display_name]
  else:
    raise NameError("No display in registry: '%s'" % display_name)

class DisplayBase(Base):
  """Abstract base class for Chisel visualizer displays
  (objects that node visualizer properties based on input data)."""
  def apply(self, node_ref):
    """Returns a dict of key->value mappings applied by this modifier based
    on the input data. It is up to the calling visualizer (or perhaps
    higher-level display) to use this data accordingly.
    node_ref is a chisualizer.ChiselApi.ChiselApiNode object
    The returned dict should be mutable."""
    return {}
  
  def get_longest_text(self, node_ref):
    """Returns a list of text strings which contains the longest (by rendered
    size, for an arbitrary font and sizes) possible string if this display
    modifies the text field. This is used to size visualizers displaying text
    properly so their size does not change according to data values.
    This assumes the size and font stays constant. If this assumption is not
    true, then sizing artifacts may occur. Basically, this prevents
    combinatorial explosion caused by an unlikely use case. If this isn't the
    case, this decision may be revisited.
    This may make Chisel API calls to get the type / bitwidth of a node, but
    should not alter the emulator state.
    """
    return []

  def set_from_text(self, node_ref, in_text):
    """Sets the node's value from the input text. The specific translation from
    input text to integer value is dependent on the display, with the general
    idea being that you should be able to type in what text is shown.
    Returns True if set correctly, and False if the input was not able to be
    parsed. This should be chain-called, trying the base displays first.
    The default implementation attempts Python's built-in integer parsing.
    """
    try:
      val = int(in_text, 0)
      node_ref.set_value(val)
      return True
    except ValueError:
      return False
    