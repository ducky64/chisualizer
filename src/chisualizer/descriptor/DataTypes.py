from numbers import Number

from Common import *
from ParsedElement import *

class ElementAttr(object):
  """Object representing an attribute, handling dynamic values and data type
  conversions."""
  def parse_error(self, message, **kwds):
    self.element.parse_error("Error in attribute %s: %s"
                             % (self.attr_name, message),
                             **kwds)
  
  def __init__(self, parent, element, attr_name, dynamic):
    self.parent = parent
    self.element = element
    self.attr_name = attr_name
    self.attr_values = self.create_value_list(element.get_attr_list(attr_name))
    self.dynamic = dynamic
    self.overloads = []

  def apply_overload(self, overload):
    assert self.dynamic
    self.overloads.insert(0, overload)
  
  def clear_overloads(self):
    assert self.dynamic
    self.overloads = []
    
  def get_value_list(self):
    if self.dynamic and self.overloads:
      overloads_copy = self.create_value_list(copy.copy(self.overloads))
      overloads_copy.extend(self.attr_values)
      return overloads_copy
    else:
      return self.attr_values

  def create_value_list(self, attr_value_list):
    """Parses the attr's value list and returns it in a format suitable for
    internal use. Does type checking here; can raise parsing errors."""
    raise NotImplementedError()

  def get(self):
    """Returns the value for this attribute."""
    raise NotImplementedError()

class ObjectAttr(ElementAttr):
  """Straight pass-through of the attribute value list, for uncommon attribute
  types where a general framework is not worth the trouble."""
  def __init__(self, parent, element, attr_name, dynamic):
    super(ObjectAttr, self).__init__(parent, element, attr_name, dynamic)

  def create_value_list(self, attr_value_list):
    return attr_value_list

  def get(self):
    return self.get_value_list()

class SingleElementAttr(ElementAttr):
  """ElementAttribute subclass for attributes using the first valid element of 
  the value list."""
  def create_value_list(self, attr_value_list):
    parsed_value_list = []
    for attr_value_elt in attr_value_list:
      parsed_value_list.append(self.create_value_elt(attr_value_elt))
    return parsed_value_list
    
  def create_value_elt(self, attr_value_elt):
    """create_value_list becomes a wrapper for this, which handles the case for
    a single value element."""
    raise NotImplementedError()
  
  def value_elt_to_data(self, value_elt, static=False):
    """Converts a value list element to data, or returns None if the element
    cannot produce the relevant data (and to move onto the next element in the
    list. Raises an error if static if False but the element is dynamic."""
    raise NotImplementedError()

  def get_value(self, dynamic):
    for value_elt in self.get_value_list():
      conv = self.value_elt_to_data(value_elt, static=not dynamic)
      if conv is not None:
        return conv
    self.parse_error("No valid value in list",
                     exc_cls=VisualizerParseValidationError)

  def get(self):
    if self.dynamic:
      return self.get_value(True)
    else:
      return self.get_value(False)
  
class StringAttr(SingleElementAttr):
  def __init__(self, parent, element, attr_name, dynamic, valid_set=None):
    super(StringAttr, self).__init__(parent, element, attr_name, dynamic)
    self.valid_set = valid_set
  
  def create_value_elt(self, attr_value_elt):
    if isinstance(attr_value_elt, basestring):
      return attr_value_elt
    elif isinstance(attr_value_elt, ParsedElement):
      from chisualizer.display.VisualizerToString import VisualizerToString
      return attr_value_elt.instantiate(self.parent, 
                                        valid_subclass=VisualizerToString)
    else:
      self.parse_error("Invalid type for '%s': %s"
                       % (attr_value_elt, attr_value_elt.__class__.__name__),
                       exc_cls=VisualizerParseValidationError)
  
  def value_elt_to_data(self, value_elt, static=False):
    from chisualizer.display.VisualizerToString import VisualizerToString # TODO HACKY
    if isinstance(value_elt, basestring):
      conv = value_elt
    elif isinstance(value_elt, VisualizerToString):
      conv = value_elt.get_string()
    else:
      assert False, "Unknown type: %s" % value_elt.__class__.__name__
    
    if self.valid_set is not None and conv not in self.valid_set:
      self.parse_error("%s='%s' not in valid set: %s" 
                       % (self.attr_name, conv, self.valid_set),
                       exc_cls=VisualizerParseValidationError)
      
    return conv

  def get_longest_strings(self):
    from chisualizer.display.VisualizerToString import VisualizerToString # TODO HACKY
    longest_strings = []
    for value_elt in self.get_value_list():
      if isinstance(value_elt, basestring):
        longest_strings.append(value_elt)
      elif isinstance(value_elt, VisualizerToString):
        longest_strings.extend(value_elt.get_longest_strings())
      else:
        assert False, "Unknown type: %s" % value_elt.__class__.__name__
    return longest_strings
  
  def can_set_from_string(self):
    """Returns whether set_from_string can possibly succeed or will always 
    fail."""
    from chisualizer.display.VisualizerToString import VisualizerToString # TODO HACKY
    for value_elt in self.get_value_list():
      if isinstance(value_elt, VisualizerToString):
        if value_elt.can_set_from_string():
          return True
    return False
  
  def set_from_string(self, set_string):
    """Attempt to set the node of the text being displayed using an arbitrary
    input string. Returns True if successful, False otherwise."""
    from chisualizer.display.VisualizerToString import VisualizerToString # TODO HACKY
    for value_elt in self.get_value_list():
      if isinstance(value_elt, VisualizerToString):
        if value_elt.set_from_string(set_string):
          return True
    return False
  
class IntAttr(SingleElementAttr):
  def __init__(self, parent, element, attr_name, dynamic,
               valid_min=None, valid_max=None):
    super(IntAttr, self).__init__(parent, element, attr_name, dynamic)
    self.valid_min = valid_min
    self.valid_max = valid_max
  
  def create_value_elt(self, attr_value_elt):
    if isinstance(attr_value_elt, basestring):
      try:
        return int(attr_value_elt, 0)
      except ValueError:
        self.parse_error("Can't covert '%s' to int" % attr_value_elt,
                         exc_cls=VisualizerParseTypeError)
    elif isinstance(attr_value_elt, Number):
      return int(attr_value_elt)
    elif isinstance(attr_value_elt, ParsedElement):
      from chisualizer.display.VisualizerToInt import VisualizerToInt # TODO: HACKY
      return attr_value_elt.instantiate(self.parent, 
                                        valid_subclass=VisualizerToInt)
    else:
      self.parse_error("Invalid type in '%s': %s"
                       % (attr_value_elt, attr_value_elt.__class__.__name__),
                       exc_cls=VisualizerParseValidationError)
  
  def value_elt_to_data(self, value_elt, static=False):
    from chisualizer.display.VisualizerToInt import VisualizerToInt # TODO: HACKY
    if isinstance(value_elt, int):
      conv = value_elt
    elif isinstance(value_elt, VisualizerToInt):
      conv = value_elt.get_int()
    else:
      assert False, "Unknown type: %s" % value_elt.__class__.__name__ 
    
    if self.valid_min is not None and conv < self.valid_min:
      self.parse_error("%i < min (%i)" % (conv, self.valid_min),
                       exc_cls=VisualizerParseValidationError)
    if self.valid_max is not None and conv > self.valid_max:
      self.parse_error("%i > max (%i)" % (conv, self.valid_max),
                       exc_cls=VisualizerParseValidationError)
            
    return conv  
  