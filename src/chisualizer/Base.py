# a registry of all visualization descriptors which can be instantiated
# indexed by name which it can be instantiated under.
xml_registry = {}
def xml_register(name=None):
  def wrap(cls):
    local_name = name
    if local_name == None:
      local_name = cls.__name__
    if local_name in xml_registry:
      raise NameError("Attempting to re-register a XML visualizer descriptor: "
                      + local_name)
    xml_registry[local_name] = cls
    return cls
  return wrap

class Base(object):
  """Abstract base class for visualizer descriptor objects."""
  @classmethod
  def from_xml(cls, parent, node):
    """Initializes this descriptor from a XML etree Element."""
    raise NotImplementedError() #todo fixme get from xml_registry
    new = cls()
    return new
