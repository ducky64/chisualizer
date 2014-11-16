import math

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
    try:
      val = int(in_text, 0)
      visualizer.get_node_ref.set_value(val)
      return True
    except ValueError:
      return False
    
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
    width = visualizer.get_node().get_width()
    digits = int(math.ceil(math.log(2 ** width - 1, self.radix)))
    return [self.prefix + self.charmap[0]*digits]
  