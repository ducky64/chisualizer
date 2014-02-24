import math

from chisualizer.Base import xml_register
from DisplayBase import DisplayBase, display_instantiate

@display_instantiate('binary', prefix='0b', radix=2)
@display_instantiate('decimal', prefix='', radix=10)
@display_instantiate('hexadecimal', prefix='0x', radix=16)
@xml_register('NumericalDisplay')
class NumericalDisplay(DisplayBase):
  def __init__(self, prefix='', radix=0, charmap='01234567890abcdefghijklmnopqrstuvwxyz'):
    assert isinstance(prefix, basestring), "prefix must be string"
    assert isinstance(radix, int), "radix must be int"
    assert radix > 0, "radix must be > 0"
    assert isinstance(charmap, basestring), "charmap must be string"  # TODO: allow general indexable of string
    assert len(charmap) >= radix, "len(charmap) must be >= radix"
    
    self.prefix = prefix
    self.radix = radix
    self.charmap = charmap
  
  @classmethod
  def from_xml(cls, parent, node):
    # TODO IMPLEMENT ME
    raise NotImplementedError()
  
  def apply(self, node):
    value = node.get_node_value()
    value_string = ''
    while value > 0:
      value_string = self.charmap[value % self.radix] + value_string
      value = value / self.radix
    value_string = self.prefix + value_string
    return {'text', value_string}
  
  def get_longest_text(self, chisel_api, node):
    width = node.get_node_width()
    digits = int(math.ceil(math.log(width, self.radix)))
    return [self.prefix + self.charmap[0]*digits]