# for display templates, ones that can be instantiated in XML
display_template_registry = {}
def display_template_register(name=None):
  def wrap(cls):
    local_name = name
    if local_name == None:
      local_name = cls.__name__
    if local_name in display_template_registry:
      raise NameError("Attempting to re-register a display template: " + local_name)
    display_template_registry[local_name] = cls
    return cls
  return wrap

# for actual display objects, ones that can be referenced for a display field
# in an XML visualizer description 
display_registry = {}
def display_register(name=None):
  def wrap(cls):
    local_name = name
    if local_name == None:
      local_name = cls.__name__
    if local_name in display_registry:
      raise NameError("Attempting to re-register a display: " + local_name)
    display_registry[local_name] = cls
    return cls
  return wrap

class Base:
  """Abstract base class for Chisel visualizer displays
  (objects that modify visualizer properties based on input data)."""
  def apply(self, visualizer, data):
    """Applies display modifiers to the input visualizer based on input data.
    This uses setattr to modify the visualizer."""
    raise NotImplementedError()
