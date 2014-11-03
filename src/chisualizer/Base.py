import logging
from lxml import etree

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
    vis_root = VisualizerRoot(self.api)
    vis_root.parse_children("vislib.xml", lib=True)
    vis_root.parse_children(filename)
    vis_root.instantiate_visualizers()
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
  
  @staticmethod
  def from_xml(element, parent):
    assert isinstance(element, etree.Element), "expected: Element, got: %s" % element.__class__.__name__ 
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

class ParsedElement(object):
  """
  An intermediate representation for parsed XML visualizer descriptor objects -
  essentially a dict of the element attributes and list of children. Contains
  logic for resolving inheritance and checking usage. 
  """
  class ParsedElementAccessor():
    """Accessor to the ParsedElement. Tracks attribute accesses to ensure
    everything is used. There should be a unique accessor per 'object' for the
    tracking to work. Provides type conversion (string parsing) and validcation 
    functions.""" 
    def __init__(self, parsed_element):
      self.parsed_element = parsed_element
      self.accessed = set()

    def get(self, attribute):
      rtn = self.parsed_element.get(attribute)
      self.accessed.add(attribute)
      return rtn
  
    def check_attributes_used(self):
      """Return True if all attributes in the ParsedElement have been accessed
      from this ParsedElementAccessor using the get_attr_* functions."""
      return self.accessed == self.parent.all_attributes
    
    def get_attr_string(self, attr):
      pass
    
    def get_attr_int(self, attr):
      pass
  
  def parse_error(self, message):
    """Helper function to throw a fatal error, indicating the broken element
    along with filename and line number.
    """
    raise ValueError("Error parsing %s (%s:%i): %s" % 
                     (self.tag, self.xml_filename,
                      self.xml_element.sourceline, message))
  
  def __init__(self, xml_element, xml_filename, prev_parsed_dict):
    """Constructor. Initializes this from a XML element, handling inheritance
    and some common parsing."""
    self.xml_element = xml_element
    self.xml_filename = xml_filename
    
    self.parent = None
    
    self.tag = xml_element.tag 
    
    self.attributes = {}
    for attr_name, attr_value in xml_element.items():
      if attr_name == "class":
        if attr_value not in prev_parsed_dict:
          self.parse_error("No class: '%s'" % attr_value)
        self.parent = prev_parsed_dict[attr_value]
        
      if attr_value in self.attributes:
        self.parse_error("Duplicate attribute: '%s'" % attr_name)
      self.attributes[attr_name] = attr_value
    
    self.children = []
    for child in xml_element.iterchildren(tag=etree.Element):
      # TODO: handle special tags (modifiers?) here
      self.children.append(ParsedElement(child, xml_filename, prev_parsed_dict))
    
    # Build a list of all attributes so we can determine if there are unused
    # attributes during parsing.
    self.all_atributes = set()
    current = self
    while current:
      for attr_name in current.iterkeys():
        self.all_attributes.add(attr_name)
      current = current.parent
    
  def create_accessor(self):
    return self.ParsedElementAccessor(self)
    
  def get(self, attribute):
    current = self
    while current:
      if attribute in current.attributes:
        return current.attributes[attribute]
      current = current.parent
    self.parse_error("Cannot find attribute: '%s'" % attribute)
