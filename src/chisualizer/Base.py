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

class VisualizerDescriptor(object):
  """An visualizer descriptor file."""
  def __init__(self, filename):
    """Initialize this descriptor from a file."""
    self.registry = {}
    self.parse_from_xml(filename)

  def get_ref(self, ref):
    if ref not in self.registry:
      raise NameError("Unknown ref '%s'" % ref)
    return self.registry[ref]

  def parse_from_xml(self, filename):
    """Parse this descriptor from an XML file."""
    root = etree.parse(filename).getroot()
    for child in root:
      elt = Base.from_xml(child, container=self)
      ref = child.get('ref', None)
      if ref:
        if ref not in self.registry:
          self.registry[ref] = elt
          logging.debug("Registered '%s'", ref)
        else:
          raise NameError("Found object with duplicate ref '%s'", ref)
    # last element is the one visualized
    import chisualizer.visualizers.VisualizerBase as VisualizerBase
    if not isinstance(elt, VisualizerBase.VisualizerBase):
      raise TypeError("Last element in XML must be Visualizer subtype.")
    self.visualizer = elt.instantiate(None)
    logging.debug("Instantiated visualizer")

  def draw_cairo(self, cr):
    self.visualizer.layout_and_draw_cairo(cr)

class Base(object):
  """Abstract base class for visualizer descriptor objects."""
  @staticmethod
  def from_xml(element, **kwargs):
    assert isinstance(element, etree.Element)
    if element.tag in xml_registry:
      rtn = xml_registry[element.tag].from_xml_cls(element, **kwargs)
      logging.debug("Loaded %s" % element.tag)
      return rtn
    else:
      raise NameError("Unknown class '%s'" % element.tag)
      
  @classmethod
  def from_xml_cls(cls, element, container=None, **kwargs):
    """Initializes this descriptor from a XML etree Element."""
    assert isinstance(element, etree.Element)
    new = cls()
    assert container, "from_xml_cls must have container"
    new.container = container
    return new
