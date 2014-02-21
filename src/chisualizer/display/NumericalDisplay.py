from chisualizer.Base import xml_register
from chisualizer.display.DisplayBase import DisplayBase, display_instantiate

@display_instantiate('binary', prefix='0b', radix=2)
@display_instantiate('decimal', prefix='', radix=10)
@display_instantiate('hexadecimal', prefix='0x', radix=16)
@xml_register('NumericalDisplay')
class NumericalDisplay(DisplayBase):
  def __init__(self, prefix='', radix=0):
    if radix <= 0:
      raise ValueError("Invalid radix for NumericalDisplay: " + str(radix))
    self.prefix = prefix
    self.radix = radix
  
  @classmethod
  def from_xml(cls, parent, node):
    # TODO IMPLEMENT ME
    raise NotImplementedError()
