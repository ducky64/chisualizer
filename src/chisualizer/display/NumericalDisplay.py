import math

from chisualizer.Base import xml_register
from DisplayBase import DisplayBase

@xml_register('NumericalDisplay')
class NumericalDisplay(DisplayBase):
  @classmethod
  def from_xml_cls(cls, element, parent):
    new = super(NumericalDisplay, cls).from_xml_cls(element, parent)
    new.prefix = element.get('prefix', '')
    new.radix = new.parse_element_int(element, 'radix', 10)
    if new.radix <= 0:
      raise ValueError("NumericalDisplay.radix must be > 0, got %i" % new.radix)
    new.charmap = element.get('charmap', '0123456789abcdefghijklmnopqrstuvwxyz')
    if len(new.charmap) < new.radix:
      raise ValueError("NumericalDisplay.charmap must be longer than radix (%i), got %i" % (new.radix, len(new.charmap)))
    return new
  
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
  