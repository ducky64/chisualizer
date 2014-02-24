import xml.etree.ElementTree as etree
import logging

# a registry of all visualization descriptors which can be instantiated
# indexed by name which it can be instantiated under.
xml_registry = {}
def xml_register(name=None):
  def wrap(cls):
    local_name = name
    if local_name == None:
      local_name = cls.__name__
    if local_name in xml_registry:
      raise NameError("Attempting to re-register a XML descriptor '%s'" %
                      local_name)
    xml_registry[local_name] = cls
    logging.debug("Registered XML descriptor class '%s'" % local_name)
    return cls
  return wrap

ref_registry = {}
def ref_register(name, obj):
  if name not in ref_registry:
    ref_registry[name] = obj
    logging.debug("Registered ref '%s'" % name)
  else:
    raise NameError("Attempting to re-register ref '%s'" % name)

class Base(object):
  """Abstract base class for visualizer descriptor objects."""
  @staticmethod
  def from_xml(parent, node):
    assert isinstance(node, etree.Element)
    if node.tag in xml_registry:
      return xml_registry[node.tag].from_xml_cls(parent, node)
    else:
      raise NameError("Unknown class '%s'" % node.tag)
      
  @classmethod
  def from_xml_cls(cls, parent, node):
    """Initializes this descriptor from a XML etree Element."""
    new = cls()
    
    # automatically register nodes with references
    ref = node.get('ref', None)
    if ref:
      ref_register(ref, new)
    
    return new
