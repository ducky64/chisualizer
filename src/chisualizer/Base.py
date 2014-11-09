import logging
import yaml
import os

from chisualizer.util import Rectangle

# A registry of all visualization descriptors (map from tag name to class)
# which can be instantiated.
tag_registry = {}
def tag_register(tag_name=None):
  def wrap(cls):
    local_name = tag_name
    if local_name == None:
      local_name = cls.__name__
    assert local_name not in tag_registry
    tag_registry[local_name] = cls
    logging.debug("Registered tag '%s'" % local_name)
    return cls
  return wrap

# A registry of desugaring structural transforms, a map from the tag name to a
# function which takes in the ParsedElement and returns the desugared version
# (which may or may not be the same. Desugaring runs in the same order as 
# elements were read in. Returned elements may alias with other elements.
# TODO: is aliasing a good idea? should ParsedElements be able to clone()?
# TODO: is the ordering guarantee good enough? better ways to do that?  
desugar_registry = {}
def desugar_register(tag_name):
  def wrap(fun):
    assert tag_name not in desugar_registry
    desugar_registry[tag_name] = fun
    logging.debug("Registered desugaring transform for '%s'" % tag_name)
    return fun
  return wrap

class YAMLVisualizerRegistry():
  def __init__(self):
    self.templates = {}
    self.default_templates = {}
    self.ref_elements = {}

  def read_descriptor(self, filename):
    loader = yaml.SafeLoader(file(filename, 'r'))
    
    def obj_constructor(loader, node):
        value = loader.construct_mapping(node)
        print value.__class__.__name__
        return value
    
    for tag_name in tag_registry:
      loader.add_constructor("!" + tag_name, obj_constructor)
      
    for tag_name in desugar_registry:
      loader.add_constructor("!" + tag_name, obj_constructor)
    
    print loader.get_data()

class VisualizerRoot(object):
  """An visualizer descriptor file."""
  def __init__(self, filename, api):
    """Initialize this descriptor from a file and given a ChiselApi object."""
    from chisualizer.visualizers.Theme import DarkTheme
    
    self.api = api
    self.theme = DarkTheme()
    self.registry = YAMLVisualizerRegistry()
    self.visualizer = None  # TODO: support multiple visualizers in different windows

    self.registry.read_descriptor(filename)

    assert False

  def layout_cairo(self, cr):
    size_x, size_y = self.visualizer.layout_cairo(cr)
    return Rectangle((0, 0), (size_x, size_y))
  
  def draw_cairo(self, cr, rect):
    return self.visualizer.draw_cairo(cr, rect, 0)

  def get_theme(self):
    # TODO refactor this, probably makes more sense to set themes here
    return self.theme

  def set_theme(self, theme):
    # TODO: is persistent theme state really the best idea?
    self.theme = theme

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

class VisualizerParseError(BaseException):
  """Base exception class for errors during visualizer descriptor parsing."""
  pass

class VisualizerParseTypeError(VisualizerParseError):
  """Type conversion (string->?) failed during parsing."""
  pass

class VisualizerParseValidationError(VisualizerParseError):
  """Attribute validation failed during parsing."""
  pass

class VisualizerParseTagError(VisualizerParseError):
  """Something was wrong with the element tag."""
  pass

class VisualizerParseAttributeError(VisualizerParseError):
  """Something was wrong with the attributes."""
  pass

class VisualizerParseAttributeNotFound(VisualizerParseError):
  """A required attribute was not found."""
  pass

class VisualizerParseAttributeNotUsed(VisualizerParseError):
  """A specified attribute was not used."""
  pass

class ParsedElement(object):
  """
  An intermediate representation for parsed XML visualizer descriptor objects -
  essentially a dict of the element attributes and list of children. Contains
  functionality to to type conversion, validation, and check that all attributes
  specified are actually read.
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
    
    def get_attr(self, attr):
      self.get_attr_accessed(attr)
      return self.parsed_element.get_attr_string(attr)
    
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
    
  def parse_error(self, message, exc_cls=VisualizerParseError):
    """Helper function to throw a fatal error, indicating the broken element
    along with filename and line number.
    """
    raise exc_cls("Error parsing %s '%s' (%s:%i): %s" % 
                  (self.tag, self.ref, self.xml_filename,
                   self.xml_element.sourceline, message))
  
  def __init__(self, xml_element, xml_filename):
    """Constructor. Parses an ElementTree element to populate my attributes and
    children."""
    self.xml_element = xml_element
    self.xml_filename = xml_filename
    
    self.tag = xml_element.tag 
    self.ref = '(anon)'
    
    self.attributes = {}
    for attr_name, attr_value in xml_element.items():
      if attr_value in self.attributes:
        self.parse_error("Duplicate attribute: '%s'" % attr_name,
                         exc_cls=VisualizerParseAttributeError)
      self.attributes[attr_name] = attr_value
    
    self.children = []
    """for child in xml_element.iterchildren(tag=etree.Element):
      self.children.append(ParsedElement(child, xml_filename))"""
          
  def instantiate(self, parent, valid_subclass=None):
    assert valid_subclass is not None
    if self.tag not in xml_registry:
      self.parse_error("Unknown tag '%s'" % self.tag,
                       exc_cls=VisualizerParseTagError)
      
    rtn_cls = xml_registry[self.tag]
    if not issubclass(rtn_cls, valid_subclass):
      self.parse_error("Expected to be a subclass of %s" %
                       valid_subclass.__name__,
                       exc_cls=VisualizerParseTagError)
        
    logging.debug("Instantiating %s (%s:%s)" % 
                  (rtn_cls.__name__, self.tag, self.ref))
    accessor = self.create_accessor()
    rtn = rtn_cls(accessor, parent)
    if accessor.get_unused_attributes():
      self.parse_error("Unused attributes: %s" % 
                       accessor.get_unused_attributes(),
                       exc_cls=VisualizerParseAttributeNotUsed)
    return rtn
    
  def create_accessor(self):
    return self.ParsedElementAccessor(self)

  def get_all_attrs(self):
    return self.attributes.iterkeys()
    
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
    self.parse_error("Cannot find attribute: '%s'" % attribute,
                     exc_cls=VisualizerParseAttributeNotFoundError)

  def get_attr_string(self, attr, valid_set=None):
    got = self.get_attr(attr)
    assert isinstance(got, basestring)
    if valid_set is not None and got not in valid_set:
      self.parse_error("%s='%s' not in valid set: %s" % (attr, got, valid_set),
                       exc_cls=VisualizerParseValidationError)
    return got
  
  def get_attr_int(self, attr, valid_min=None, valid_max=None):
    got = self.get_attr(attr)
    assert isinstance(got, basestring)
    try:
      conv = int(got, 0)
    except ValueError:
      self.parse_error("Unable to convert %s='%s' to int" % (attr, got),
                       exc_cls=VisualizerParseTypeError)
    if valid_min is not None and conv < valid_min:
      self.parse_error("%s=%i < min (%i)" % (attr, conv, valid_min),
                       exc_cls=VisualizerParseValidationError)
    if valid_max is not None and conv > valid_max:
      self.parse_error("%s=%i < max (%i)" % (attr, conv, valid_max),
                       exc_cls=VisualizerParseValidationError)
    return conv        
  
  def get_attr_float(self, attr, valid_min=None, valid_max=None):
    got = self.get_attr(attr)
    assert isinstance(got, basestring)
    try:
      conv = float(got)
    except ValueError:
      self.parse_error("Unable to convert %s='%s' to float" % (attr, got),
                       exc_cls=VisualizerParseTypeError)
    if valid_min is not None and conv < valid_min:
      self.parse_error("%s=%i < min (%i)" % (attr, conv, valid_min),
                       exc_cls=VisualizerParseValidationError)
    if valid_max is not None and conv > valid_max:
      self.parse_error("%s=%i < max (%i)" % (attr, conv, valid_max),
                       exc_cls=VisualizerParseValidationError)
    return conv        
   