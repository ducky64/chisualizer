import logging

from Common import *

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
      if not isinstance(val, list):
        attr_map[attr] = [val] 
    return attr_map
  
  def instantiate(self, parent, valid_subclass=None, **kwargs):
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
    rtn = rtn_cls(accessor, parent, **kwargs)
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
  
class ElementAccessor(object):
  """Accessor object for ParsedElement. Provides a method to track accesses,
  to ensure all attributes specified in the descriptors are actually used.
  """
  def parse_error(self, *args, **kwargs):
    self.parent.parse_error(*args, **kwargs)
  
  def __init__(self, parent_element):
    self.parent = parent_element
    self.accessed_attrs = set()
  
  def get_ref(self):
    return self.parent.ref
  
  def attrs_not_accessed(self):
    return self.parent.get_all_attrs() - self.accessed_attrs
  
  def get_attr_list(self, attr):
    self.accessed_attrs.add(attr)
    return self.parent.get_attr_list(attr)
  