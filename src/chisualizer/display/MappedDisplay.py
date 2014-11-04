import copy
import logging

import chisualizer.Base as Base
from DisplayBase import DisplayBase

@Base.xml_register('MappedDisplay')
class MappedDisplay(DisplayBase):
  def __init__(self, element, parent):
    super(MappedDisplay, self).__init__(element, parent)
    self.mappings = {}
    for child in element.get_children():
      if child.tag != 'Mapping':
        child.parse_error("Unexpected tag '%s' as child" % child.tag)
      mapping_key = child.get_attr_int('key')
      mapping_val = {}
      
      for attr in child.get_all_attrs():
        if attr != "key":
          mapping_val[attr] = child.get_attr_string(attr)
      self.mappings[mapping_key] = mapping_val

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
   
    # allow case sensitive compare to take priority 
    case_insensitive_val = None
    # TODO: detect ambiguous parse
    
    for mapping_key, mapping_val in self.mappings.iteritems():
      if 'text' in mapping_val:
        if mapping_val['text'] == in_text:
          node_ref.set_value(mapping_key)
          return True
        elif mapping_val['text'].lower() == in_text.lower():
          case_insensitive_val = mapping_key
    if case_insensitive_val is not None:
      node_ref.set_value(case_insensitive_val)
      return True
    
    return False
      