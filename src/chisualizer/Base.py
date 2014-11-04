import logging
from lxml import etree
import os

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
    vis_root.parse_children(os.path.join(os.path.dirname(__file__),
                                         "vislib.xml"),
                            lib=True)
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
  def __init__(self, element, parent):
    self.parent = parent
    self.root = parent.root
    self.ref = element.get_ref()
  
  def get_chisel_api(self):
    """Returns the ChiselApi object used to access node values.
    Returns None if not available or if this visualizer wasn't properly
    instantiated."""
    return self.root.get_chisel_api()
  
  def get_theme(self):
    """Returns a Theme object, mapping descriptions to numerical colors."""
    return self.root.get_theme()

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

    def parse_error(self, message):
      self.parsed_element.parse_error(message)

    def get_attr_accessed(self, attribute):
      """Marks an attribute as "read"."""
      self.accessed.add(attribute)
  
    def get_unused_attributes(self):
      """Return set of attributes in all of parent's attributes but not accessed
      from this ParsedElementAccessor using the get_attr_* functions."""
      return self.parsed_element.all_attributes.difference(self.accessed)
    
    def get_ref(self):
      return self.parsed_element.ref
    
    def get_attr_string(self, attr, **kwargs):
      self.get_attr_accessed(attr)
      return self.parsed_element.get_attr_string(attr, **kwargs)
    
    def get_attr_int(self, attr, **kwargs):
      self.get_attr_accessed(attr)
      return self.parsed_element.get_attr_int(attr, **kwargs)      
    
    def get_attr_float(self, attr, **kwargs):
      self.get_attr_accessed(attr)
      return self.parsed_element.get_attr_float(attr, **kwargs)      
    
    def get_children(self):
      return self.parsed_element.children
    
  def parse_error(self, message):
    """Helper function to throw a fatal error, indicating the broken element
    along with filename and line number.
    """
    raise ValueError("Error parsing %s '%s' (%s:%i): %s" % 
                     (self.tag, self.ref, self.xml_filename,
                      self.xml_element.sourceline, message))
  
  def __init__(self, xml_element, xml_filename, prev_parsed_dict):
    """Constructor. Initializes this from a XML element, handling inheritance
    and some common parsing."""
    self.xml_element = xml_element
    self.xml_filename = xml_filename
    
    self.tag = xml_element.tag 
    self.ref = '(anon)'
    
    self.parent = None
    if self.tag + "Default" in prev_parsed_dict:
      self.class_parent = prev_parsed_dict[self.tag + "Default"]  # TODO: make this dynamic based on actual instantiated class
    else:
      self.class_parent = None
    
    self.attributes = {}
    for attr_name, attr_value in xml_element.items():
      if attr_name == "template":
        if attr_value not in prev_parsed_dict:
          self.parse_error("No template: '%s'" % attr_value)
        self.parent = prev_parsed_dict[attr_value]
      elif attr_name == "ref":
        self.ref = attr_value 
      else:
        if attr_value in self.attributes:
          self.parse_error("Duplicate attribute: '%s'" % attr_name)
        self.attributes[attr_name] = attr_value
    
    self.children = []
    for child in xml_element.iterchildren(tag=etree.Element):
      # TODO: handle special tags (modifiers?) here
      self.children.append(ParsedElement(child, xml_filename, prev_parsed_dict))
    
    # Build a list of all attributes so we can determine if there are unused
    # attributes during parsing.
    self.all_attributes = set()
    current = self
    while current is not None:
      for attr_name in current.attributes.iterkeys():
        self.all_attributes.add(attr_name)
      current = current.parent
    current = self.class_parent
    while current is not None:
      for attr_name in current.attributes.iterkeys():
        self.all_attributes.add(attr_name)
      current = current.parent
      
  def instantiate(self, parent, valid_subclass=None):
    assert valid_subclass is not None
    if self.tag not in xml_registry:
      self.parse_error("Unknown tag '%s'" % self.tag)
      
    rtn_cls = xml_registry[self.tag]
    if not issubclass(rtn_cls, valid_subclass):
      self.parse_error("Expected to be a subclass of %s" % valid_subclass.__name__)
        
    logging.debug("Instantiating %s (%s:%s)" % 
                  (rtn_cls.__name__, self.tag, self.ref))
    accessor = self.create_accessor()
    rtn = rtn_cls(accessor, parent)
    if accessor.get_unused_attributes():
      self.parse_error("Unused attributes: %s" % accessor.get_unused_attributes())
    return rtn
    
  def create_accessor(self):
    return self.ParsedElementAccessor(self)

  def get_all_attrs(self):
    return self.all_attributes
    
  def get_attr(self, attribute):
    current = self
    while current is not None:
      if attribute in current.attributes:
        return current.attributes[attribute]
      current = current.parent
    current = self.class_parent
    while current is not None:
      if attribute in current.attributes:
        return current.attributes[attribute]
      current = current.parent
    self.parse_error("Cannot find attribute: '%s'" % attribute)

  def get_attr_string(self, attr, valid_set=None):
    got = self.get_attr(attr)
    if valid_set is not None and got not in valid_set:
      self.parse_error("%s='%s' not in valid set: %s" % (attr, got, valid_set))
    return got
  
  def get_attr_int(self, attr, valid_min=None, valid_max=None):
    got = self.get_attr(attr)
    try:
      conv = int(got, 0)
    except ValueError:
      self.parse_error("Unable to convert %s='%s' to int" % (attr, got))
    if valid_min is not None and conv < valid_min:
      self.parse_error("%s=%i < min (%i)" % (attr, conv, valid_min))
    if valid_max is not None and conv > valid_max:
      self.parse_error("%s=%i < max (%i)" % (attr, conv, valid_max))
    return conv        
  
  def get_attr_float(self, attr, valid_min=None, valid_max=None):
    got = self.get_attr(attr)
    try:
      conv = float(got)
    except ValueError:
      self.parse_error("Unable to convert %s='%s' to float" % (attr, got))
    if valid_min is not None and conv < valid_min:
      self.parse_error("%s=%i < min (%i)" % (attr, conv, valid_min))
    if valid_max is not None and conv > valid_max:
      self.parse_error("%s=%i < max (%i)" % (attr, conv, valid_max))
    return conv        
  