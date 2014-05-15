import logging
import xml.etree.ElementTree as etree

from chisualizer.util import Rectangle

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
  def __init__(self, filename, api):
    """Initialize this descriptor from a file and given a ChiselApi object."""
    self.api = api
    self.parse_from_xml(filename)

  def parse_from_xml(self, filename):
    """Parse this descriptor from an XML file."""
    from chisualizer.visualizers.VisualizerRoot import VisualizerRoot
    xml_root = etree.parse(filename).getroot()
    vis_root = VisualizerRoot(self.api)
    vis_root.parse_children(xml_root)
    vis_root.instantiate_visualizer()
    self.vis_root = vis_root
    self.visualizer = vis_root.visualizer

  def layout_cairo(self, cr):
    size_x, size_y = self.visualizer.layout_cairo(cr)
    return Rectangle((0, 0), (size_x, size_y))
  
  def draw_cairo(self, cr, rect):
    return self.visualizer.draw_cairo(cr, rect, 0)

  def get_theme(self):
    # TODO refactor this, probably makes more sense to set themes here
    return self.vis_root.get_theme()

  def set_theme(self, theme):
    # TODO: is persisrent theme state really the best idea?
    self.vis_root.set_theme(theme)

class VisualizerParseError(BaseException):
  pass

class Base(object):
  """Abstract base class for visualizer descriptor objects."""
  def parse_warning(self, msg):
    """Emits a warning message for XML parsing, automatically prepending
    the class name and reference."""
    logging.warning("Parsing warning for %s: '%s': %s" % 
                    (self.__class__.__name__, self.ref, msg))
  def parse_error(self, msg):
    """Emits an error message for XML parsing, automatically prepending
    the class name and reference and throwing an exception"""
    logging.warning("Parsing ERROR for %s: '%s': %s" % 
                    (self.__class__.__name__, self.ref, msg))
    raise VisualizerParseError(msg) 
    
  def parse_element_int(self, element, param, default):
    got = element.get(param, None)
    if got is None:
      return default
    try:
      return int(got, 0)
    except ValueError:
      self.parse_warning("unable to convert %s='%s' to int, default to %s" %
                         (param, got, default))
      return default
    
  def get_chisel_api(self):
    """Returns the ChiselApi object used to access node values.
    Returns None if not available or if this visualizer wasn't properly
    instantiated."""
    return self.root.get_chisel_api()
  
  def get_theme(self):
    """Returns a Theme object, mapping descriptions to numerical colors."""
    return self.root.get_theme()
  
  def get_ref(self, ref):
    """Returns the container VisualizerDescriptor object."""
    return self.root.get_ref(ref)
    
  @staticmethod
  def from_xml(element, parent):
    assert isinstance(element, etree.Element)
    if element.tag in xml_registry:
      rtn = xml_registry[element.tag].from_xml_cls(element, parent)
      logging.debug("Loaded %s: '%s'", rtn.__class__.__name__, rtn.ref)
      return rtn
    else:
      raise NameError("Unknown class '%s'" % element.tag)
      
  @classmethod
  def from_xml_cls(cls, element, parent):
    """Initializes this descriptor from a XML etree Element."""
    assert isinstance(element, etree.Element)
    new = cls()
    new.parent = parent
    new.root = parent.root
    new.ref = element.get('ref', '(anon)')
    return new
