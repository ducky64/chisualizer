import chisualizer.Base as Base
from DisplayBase import DisplayBase, display_instantiate

@display_instantiate('bool', mappings={
                                       0: {'text':'true'},
                                       1: {'text':'false'},
                                       })
@Base.xml_register('MappedDisplay')
class MappedDisplay(DisplayBase):
  def __init__(self, mappings):
    self.mappings = mappings
    
  @classmethod
  def from_xml(cls, element, **kwargs):
    # TODO IMPLEMENT ME
    raise NotImplementedError()
  
  def apply(self, node):
    value = node.get_node_value()
    if value in self.mapping:
      return self.mapping[value]
  
  def get_longest_text(self, chisel_api, node):
    text_list = []
    for _, mapping in self.mappings.iteritems():
      if 'text' in mapping:
        text_list.append(mapping['text'])
    return text_list
  