import logging
from numbers import Number
import yaml
import os

from chisualizer.util import Rectangle

# A registry of all visualization descriptors (map from tag name to class)
# which can be instantiated.
tag_registry = {}
def tag_register(tag_name=None):
  def wrap(cls):
    assert tag_name not in tag_registry, "Duplicate tag '%s'" % tag_name
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
    assert tag_name not in desugar_registry, "Duplicate desugar tag '%s'" % tag_name
    desugar_registry[tag_name] = fun
    logging.debug("Registered desugaring transform for '%s'" % tag_name)
    return fun
  return wrap

@desugar_register("Ref")
def desugar_ref(parsed_element):
  return None

class YAMLVisualizerRegistry():
  def __init__(self):
    self.lib_elements = {}
    self.display_elements = []

  def read_descriptor(self, filename):
    loader = yaml.SafeLoader(file(filename, 'r'))
    
    def create_obj_constructor(tag_name):
      def obj_constructor(loader, node):
        return ParsedElement(tag_name, loader.construct_mapping(node),
                             filename, -1)
        # TODO: add line numbers
      return obj_constructor
    
    for tag_name in tag_registry:
      loader.add_constructor("!" + tag_name, create_obj_constructor(tag_name))
      
    for tag_name in desugar_registry:
      loader.add_constructor("!" + tag_name, create_obj_constructor(tag_name))
    
    yaml_dict = loader.get_data()
    if 'lib' in yaml_dict:
      assert isinstance(yaml_dict['lib'], dict)
      for ref_name, elt in yaml_dict['lib'].iteritems():
        logging.debug("Loaded library element ref='%s'", ref_name)
        elt.set_ref(ref_name)
        self.lib_elements[ref_name] = elt

    if 'display' in yaml_dict:
      assert isinstance(yaml_dict['display'], list)
      for idx, elt in enumerate(yaml_dict['display']):
        elt.set_ref("(display %i)" % idx)
        self.display_elements.append(elt)
      
    # TODO: desugaring pass

class VisualizerRoot(object):
  """An visualizer descriptor file."""
  def __init__(self, filename, api):
    """Initialize this descriptor from a file and given a ChiselApi object."""
    from chisualizer.visualizers.Theme import DarkTheme
    
    # Hacks to get this to behave as a AbstractVisualizer
    # TODO: FIX, perhaps with guard node
    self.root = self
    self.path = ""
    
    self.api = api
    self.theme = DarkTheme()
    self.registry = YAMLVisualizerRegistry()
    self.visualizer = None  # TODO: support multiple visualizers in different windows

    self.registry.read_descriptor(filename)
    
    if not self.registry.display_elements:
      raise VisualizerParseError("No display elements specified.")
    
    if len(self.registry.display_elements) != 1:
      raise VisualizerParseError("Multiple visualizers currently not supported.")
    
    from chisualizer.visualizers.VisualizerBase import AbstractVisualizer
    self.visualizer = self.registry.display_elements[0].instantiate(self, valid_subclass=AbstractVisualizer)

  def update(self):
    self.visualizer.update()

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

  def get_api(self):
    return self.api

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

# TODO: refactor the data types internals to be less janky.
# Code smells: way too large method signature...
class ElementDataType(object):
  """Helper methods for attribute to data type conversions."""
  @classmethod
  def list_to_data(cls, accessor, attr, value_list, static, **kwds):
    """Converts a attribute list to the data type."""
    raise NotImplementedError()
  
  @classmethod
  def dynamic_attr_instantiate(cls, accessor, attr, value_list):
    """When a dynamic attribute is registered, instantiate and/or semantically
    desugar its value list into a usable internal format. This is stored as
    the 'parsed list' in the dynamic_attrs in ElementAccessor.""" 
    new_list = []
    for elt in value_list:
      new_list.append(cls.dynamic_elt_instantiate(accessor, attr, elt))
    return new_list

  @classmethod
  def dynamic_elt_instantiate(cls, accessor, attr, value):
    raise NotImplementedError()

  @classmethod
  def error_if_static(cls, accessor, attr, value, static):
    if static:
      accessor.parent.parse_error("%s='%s' is non-static" 
                                  % (attr, value),
                                  exc_cls=VisualizerParseValidationError)

class SingleElementDataType(ElementDataType):
  """Helper methods for single-value (first in list) attribute to data type
  conversions."""
  @classmethod
  def list_to_data(cls, accessor, attr, value_list, static, **kwds):
    for elt in value_list:
      parsed = cls.elt_to_data(accessor, attr, elt, static, **kwds)
      if parsed is not None:
        return parsed
    accessor.parent.parse_error("Attribute %s has no valid value" % attr)
  
  @classmethod
  def elt_to_data(cls, accessor, attr, value, static):
    raise NotImplementedError

class StringType(SingleElementDataType):
  @classmethod
  def elt_to_data(cls, accessor, attr, value, static, valid_set=[]):
    assert isinstance(value, basestring)
    if valid_set and value not in valid_set:
      accessor.parent.parse_error("%s='%s' not in valid set: %s" 
                                  % (attr, value, valid_set),
                                  exc_cls=VisualizerParseValidationError)
    return value
  
  @classmethod
  def dynamic_elt_instantiate(cls, accessor, attr, value):
    if isinstance(value, basestring):
      return value
    else:
      accessor.parent.parse_error("%s='%s' has invalid type" % attr, value)

class IntType(SingleElementDataType):
  @classmethod
  def elt_to_data(cls, accessor, attr, value, static,
                  valid_min=None, valid_max=None):
    if isinstance(value, basestring):
      conv = cls.string_to_int(accessor, attr, value)
    elif isinstance(value, Number):
      conv = int(value)
    else:
      assert False  # TODO more descriptive error here
      
    if valid_min is not None and conv < valid_min:
      accessor.parent.parse_error("%s=%i < min (%i)" % (attr, conv, valid_min),
                                  exc_cls=VisualizerParseValidationError)
    if valid_max is not None and conv > valid_max:
      accessor.parent.parse_error("%s=%i < max (%i)" % (attr, conv, valid_max),
                                  exc_cls=VisualizerParseValidationError)
    return conv 
  
  @classmethod
  def string_to_int(self, accessor, attr, value):
    assert isinstance(value, basestring)
    try:
      return int(value, 0)
    except ValueError:
      accessor.parent.parse_error("Unable to convert %s='%s' to int" % (attr, value),
                                  exc_cls=VisualizerParseTypeError)
  
  @classmethod
  def dynamic_elt_instantiate(cls, accessor, attr, value):
    if isinstance(value, basestring):
      return value
    else:
      accessor.parent.parse_error("%s='%s' has invalid type" % attr, value)
  
  
class ElementAccessor(object):
  """Accessor object for ParsedElement. Provides type-conversion functions,
  static attribute access & checking, dynamic attribute registration and
  resolution, and checks to ensure all attributes were used.
  The elt_to_* functions are the parse_fn s referred below, provide type
  conversion and validation.
  """
  def __init__(self, parent_element):
    self.parent = parent_element
    self.dynamic_overloads = [] # TODO implement support for this later
    self.accessed_attrs = set()
    self.dynamic_attrs = {} # mapping of attr name to (datatype cls, parsed list, kwds)
  
  def get_ref(self):
    return self.parent.ref
  
  def get_dynamic_attrs(self):
    """Returns a dict of dynamic attrs -> parsed value."""
    rtn = {}
    for attr_name, parse_fn_tuple in self.dynamic_attrs.iteritems():
      
      datatype, parsed_list, parse_fn_kwds = parse_fn_tuple
      parsed = datatype.list_to_data(self, attr_name, parsed_list, static=False,
                                     **parse_fn_kwds)
      rtn[attr_name] = parsed
    return rtn
  
  def attrs_not_accessed(self):
    return self.parent.get_all_attrs() - self.accessed_attrs
  
  def get_attr_list(self, attr):
    # TODO support dynamic overload attrs
    return self.parent.get_attr_list(attr)
  
  def get_static_attr(self, datatype, attr, **kwds):
    assert issubclass(datatype, ElementDataType)
    self.accessed_attrs.add(attr)
    return datatype.list_to_data(self, attr, self.get_attr_list(attr), True)
    
  def register_dynamic_attr(self, datatype, attr, **kwds):
    assert issubclass(datatype, ElementDataType)
    self.accessed_attrs.add(attr)
    assert attr not in self.dynamic_attrs
    
    parsed_list = datatype.dynamic_attr_instantiate(self, attr, 
                                                    self.get_attr_list(attr))
    self.dynamic_attrs[attr] = (datatype, parsed_list, kwds)
  
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
                  (self.tag, self.ref, self.filename, self.lineno, message))
  
  def __init__(self, tag_name, attr_map, filename, lineno):
    self.tag = tag_name
    self.attr_map = self.canonicalize_attr_map(attr_map)
    self.filename = filename
    self.lineno = lineno
    self.ref = '(anon)'
  
  def set_ref(self, ref):
    self.ref = ref
  
  @staticmethod
  def canonicalize_attr_map(attr_map):
    """Canonicalizes the attr map, making everything that isn't a list into a
    list. Modification is done in-place."""
    for attr, val in attr_map.iteritems():
      if val is not list:
        attr_map[attr] = [val] 
    return attr_map
  
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
    
    accessor = ElementAccessor(self)
    rtn = rtn_cls(accessor, parent)
    if accessor.attrs_not_accessed():
      self.parse_error("Unused attributes: %s" % accessor.attrs_not_accessed())
    
    return rtn
    
    
  def get_all_attrs(self):
    return set(self.attr_map.iterkeys())
    
  def get_attr_list(self, attr):
    if attr not in self.attr_map:
      self.parse_error("Cannot find attribute: '%s'" % attr,
                       exc_cls=VisualizerParseAttributeNotFound)
    return self.attr_map[attr]
  