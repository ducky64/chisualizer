import math
from numbers import Number

import chisualizer.Base as Base

class VisualizerToString(Base.Base):
  """Abstract base class for "functions" converting Chisel node values to
  strings. Provides supporting functionality, like getting the longest possible
  strings (for auto-sizing) and setting the node from text."""
  def get_string(self, visualizer):
    """Returns the string representation of the Chisel node value, given the
    parent visualizer. May access the visualizer's Chisel node and make Chisel
    API calls, but should not alter the circuit state.
    Returns a string, or None if no mapping was found (and to punt to the next
    level, if available).
    """
    return None
  
  def get_longest_strings(self, visualizer):
    """Returns a list of text strings which contains the longest (by rendered
    size, for an arbitrary font and sizes) possible string if this display
    modifies the text field. This is used to size visualizers displaying text
    properly so their size does not change according to data values.
    This assumes the size and font stays constant. If this assumption is not
    true, then sizing artifacts may occur. Basically, this prevents
    combinatorial explosion caused by an unlikely use case. If this isn't the
    case, this decision may be revisited.
    May make Chisel API calls, but should not alter the circuit state.
    """
    return []

  def set_from_string(self, visualizer, in_text):
    """Sets the node's value from the input text. The specific translation from
    input text to integer value is dependent on the display, with the general
    idea being that you should be able to type in what text is shown. The
    specific node to alter is also overloadable, but generally should be the
    parent visualizer's node.
    By default, will accept any integer value.
    Returns True if set correctly, and False if the input was not able to be
    parsed (and to punt to the next level).
    """
    if visualizer.get_node_ref() is None:
      return False
    
    try:
      val = int(in_text, 0)
      visualizer.get_node_ref().set_value(val)
      return True
    except ValueError:
      return False
    
  def can_set_from_string(self, visualizer):
    return visualizer.get_node_ref is not None
    
@Base.tag_register('NumericalString')
class NumericalString(VisualizerToString):
  def __init__(self, element, parent):
    super(NumericalString, self).__init__(element, parent)
    self.prefix = Base.StringAttr(self, element, 'prefix').get_static() 
    self.radix = Base.IntAttr(self, element, 'radix', valid_min=1).get_static()
    self.charmap = Base.StringAttr(self, element, 'charmap').get_static()
    if len(self.charmap) < self.radix:
      element.parse_error("charmap must be longer than radix (%i), got %i" %
                          (self.radix, len(self.charmap)))    
  
  def get_string(self, visualizer):
    if visualizer.get_node_ref() is None:
      return None
    
    value = visualizer.get_node_ref().get_value()
    value_string = ''
    while value > 0:
      value_string = self.charmap[value % self.radix] + value_string
      value = value / self.radix
    if not value_string:
      value_string = self.charmap[0]
    value_string = self.prefix + value_string
    return value_string
  
  def get_longest_strings(self, visualizer):
    if visualizer.get_node_ref() is None:
      return [] 
      
    width = visualizer.get_node_ref().get_width()
    digits = int(math.ceil(math.log(2 ** width - 1, self.radix)))
    return [self.prefix + self.charmap[0]*digits]

@Base.tag_register('DictString')
class DictString(VisualizerToString):
  def __init__(self, element, parent):
    super(DictString, self).__init__(element, parent)
    mapping_attr = Base.ObjectAttr(self, element, 'mapping')
    mapping = mapping_attr.get_static()[0]
    if not isinstance(mapping, dict):
      mapping_attr.parse_error("Expected type dict, got %s"
                               % mapping)
    self.mapping_to_string = {}
    self.mapping_to_int = {}
    self.default = None
    for mapping_key, mapping_val in mapping.iteritems():
      print mapping_key
      if mapping_key == 'default':
        self.default = mapping_val
      else:
        if isinstance(mapping_key, basestring):
          try:
            mapping_key = int(mapping_key, 0)
          except ValueError:
            mapping_attr.parse_error("Expected key '%s' castable to int" 
                                     % mapping_key)
        else:
          mapping_key = int(mapping_key)
          # TODO: better error handling here?

        self.mapping_to_string[mapping_key] = mapping_val
        if mapping_val in self.mapping_to_int:
          mapping_attr.parse_error("Duplicate value '%s'" % mapping_val)
        self.mapping_to_int[mapping_val] = mapping_key
  
  def get_string(self, visualizer):
    if visualizer.get_node_ref() is None:
      return None
    
    value = visualizer.get_node_ref().get_value()
    if value in self.mapping_to_string:
      return self.mapping_to_string[value]
    else:
      return self.default
  
  def get_longest_strings(self, visualizer):
    if visualizer.get_node_ref() is None:
      return []
    
    return list(self.mapping_to_int.iterkeys())
    
  def set_from_string(self, visualizer, in_text):
    if visualizer.get_node_ref() is None:
      return False

    if in_text in self.mapping_to_int:
      visualizer.get_node_ref().set_value(self.mapping_to_int[in_text])
      return True
    else:
      return False