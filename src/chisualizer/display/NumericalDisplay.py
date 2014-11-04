import math

from chisualizer.Base import xml_register
from DisplayBase import DisplayBase

@xml_register('NumericalDisplay')
class NumericalDisplay(DisplayBase):
  def __init__(self, element, parent):
    super(NumericalDisplay, self).__init__(element, parent)
    self.prefix = element.get_attr_string('prefix')
    self.radix = element.get_attr_int('radix', valid_min=1)
    self.charmap = element.get_attr_string('charmap')
    if len(self.charmap) < self.radix:
      element.parse_error("charmap must be longer than radix (%i), got %i" %
                          (self.radix, len(self.charmap)))    
  
  def apply(self, node):
    value = node.get_value()
    value_string = ''
    while value > 0:
      value_string = self.charmap[value % self.radix] + value_string
      value = value / self.radix
    if not value_string:
      value_string = '0'
    value_string = self.prefix + value_string
    return {'text': value_string}
  
  def get_longest_text(self, node_ref):
    width = node_ref.get_width()
    digits = int(math.ceil(math.log(2 ** width - 1, self.radix)))
    return [self.prefix + self.charmap[0]*digits]
  