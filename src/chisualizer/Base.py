import logging
import yaml
import os

from chisualizer.util import Rectangle

# A registry of all visualization descriptors (map from tag name to class)
# which can be instantiated.
tag_registry = {}
def tag_register(tag_name=None):
  def wrap(cls):
    assert tag_name not in tag_registry
    tag_registry[tag_name] = cls
    logging.debug("Registered tag '%s'" % tag_name)
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
    
    def create_obj_constructor(tag_name):
      def obj_constructor(loader, node):
        return ParsedElement(tag_name, loader.construct_mapping(node),
                             filename)
      return obj_constructor
    
    for tag_name in tag_registry:
      loader.add_constructor("!" + tag_name, create_obj_constructor(tag_name))
      
    for tag_name in desugar_registry:
      loader.add_constructor("!" + tag_name, create_obj_constructor(tag_name))
    
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
  An intermediate representation for parsed visualizer descriptor objects -
  essentially a dict of the element attributes and list of children.
  """
  def parse_error(self, message, exc_cls=VisualizerParseError):
    """Helper function to throw a fatal error, indicating the broken element
    along with filename and line number.
    """
    raise exc_cls("Error parsing %s '%s' (%s:%i): %s" % 
                  (self.tag, self.ref, self.xml_filename,
                   self.xml_element.sourceline, message))
  
  def __init__(self, tag_name, attr_map, filename):
    self.tag = tag_name
    self.attrs = attr_map
    
    self.filename = filename
          
  def instantiate(self, parent, valid_subclass=None):
    assert valid_subclass is not None
    if self.tag not in tag_registry:
      self.parse_error("Unknown tag '%s'" % self.tag,
                       exc_cls=VisualizerParseTagError)
      
    rtn_cls = tag_registry[self.tag]
    if not issubclass(rtn_cls, valid_subclass):
      self.parse_error("Expected to be a subclass of %s" %
                       valid_subclass.__name__,
                       exc_cls=VisualizerParseTagError)
        
    logging.debug("Instantiating %s (%s:%s)" % 
                  (rtn_cls.__name__, self.tag, self.ref))
    
    assert False #TODO IMPLEMENT ME
    
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
                     exc_cls=VisualizerParseAttributeNotFound)

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
