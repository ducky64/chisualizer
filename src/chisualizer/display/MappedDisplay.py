import copy
import logging

import chisualizer.Base as Base
from DisplayBase import DisplayBase, display_instantiate

@display_instantiate('bool', mappings={0: {'text':'false', 'color':(1, .7, .7)},
                                       1: {'text':'true',  'color':(.7, 1, .7)},
                                       })
@Base.xml_register('MappedDisplay')
class MappedDisplay(DisplayBase):
  colormap={'red': (1, 0, 0),
            'yellow': (1, 1, 0),
            'green': (0, 1, 0),
            'cyan': (0, 1, 1),
            'blue': (0, 0, 1),
            'pink': (1, 0, 1),
            }
  def __init__(self, mappings=None):
    self.mappings = mappings

  def parse_color(self, color_str):
    if color_str in self.colormap:
      return self.colormap[color_str]
    else:
      logging.error("Unknown color '%s' in %s: '%s",
                    color_str, self.__class__.__name__, self.ref)
    
  @classmethod
  def from_xml_cls(cls, element, **kwargs):
    new = super(MappedDisplay, cls).from_xml_cls(element, **kwargs)
    new.mappings = {}
    for child in element:
      if child.tag != 'Mapping':
        logging.error("Unknown child '%s' in %s: '%s'",
                      child.tag, new.__class__.__name__, new.ref)
      mapping_key = child.get('key', None)
      mapping_val = {}
      if mapping_key is None:
        logging.error("%s: '%s': Mapping missing key",
                      new.__class__.__name__, new.ref)
        continue
      try:
        mapping_key = int(mapping_key, 0)
      except ValueError:
        logging.error("%s: '%s': Mapping key '%s' not a number",
                      new.__class__.__name__, new.ref, mapping_key)
      for key in child.keys():
        if key != 'key':
          if key == 'color':
            mapping_val[key] = new.parse_color(child.get(key))
          else:
            mapping_val[key] = child.get(key)
      new.mappings[mapping_key] = mapping_val
    return new
  
  def apply(self, node_ref):
    value = node_ref.get_value()
    if value in self.mappings:
      return copy.deepcopy(self.mappings[value])
    else:
      logging.warn("MappedDisplay: no mapping for '%s' in %s" % (value, node_ref))
      return {}
  
  def get_longest_text(self, node_ref):
    text_list = []
    for _, mapping in self.mappings.iteritems():
      if 'text' in mapping:
        text_list.append(mapping['text'])
    return text_list
  
  def set_from_text(self, node_ref, in_text):
    if super(MappedDisplay, self).set_from_text(node_ref, in_text):
      return True
    
    for mapping_key, mapping_val in self.mappings.iteritems():
      if 'text' in mapping_val and mapping_val['text'] == in_text:
        node_ref.set_value(mapping_key)
        return True
      
    return False
      