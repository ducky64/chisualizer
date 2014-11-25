from collections import OrderedDict
import logging

import yaml

from Common import *
from ParsedElement import *

class YamlDescriptor():
  def __init__(self):
    self.default_templates = OrderedDict()
    self.lib_elements = {}
    self.display_elements = {}
    self.temporal_elements = {}

  def get_display_elements(self):
    return self.display_elements

  def get_temporal_elements(self):
    return self.temporal_elements

  def get_ref(self, ref_name):
    """Returns the referenced ParsedElement or None"""
    return self.lib_elements.get(ref_name, None)

  def process_default_template(self, name, elt):
    """Processes a default template, like inheriting parents (by the 
    corresponding class hierarchy) and doing various sanity checks."""
    if elt.tag != "Template":
      elt.parse_error("Default templates must be Template tag")
    if name not in tag_registry:
      elt.parse_error("Unrecognized tag '%s'" % name)
    cls = tag_registry[name]

    # Ensure no children have already been parsed as defaults.
    for loaded_name in self.default_templates.iterkeys():
      loaded_cls = tag_registry[loaded_name]
      if issubclass(loaded_cls, cls):
        elt.parse_error("Child tag defaults for '%s' loaded before parent '%s'"
                        % (loaded_name, name))
    
    # Find closest parent and apply as template
    for parent_name, parent_elt in reversed(self.default_templates.items()):
      if issubclass(cls, tag_registry[parent_name]):
        apply_template(elt, parent_elt)
        break
      
  def apply_default_template(self, elt):
    """Applies the default template to an element. Should only be run after
    the element has been fully desugared."""
    if elt.tag in self.default_templates:
      apply_template(elt, self.default_templates[elt.tag])

  def read_descriptor(self, filename):
    """Reads in a YAML descriptor."""
    loader = yaml.SafeLoader(open(filename).read())
    
    desugar_queue = []
    
    # https://stackoverflow.com/questions/13319067/parsing-yaml-return-with-line-number
    def compose_node(parent, index):
      line = loader.line
      node = yaml.composer.Composer.compose_node(loader, parent, index)
      node.__line__ = line + 1
      return node
        
    def create_obj_constructor(tag_name):
      def obj_constructor(loader, node):
        elt = ParsedElement(tag_name, loader.construct_mapping(node),
                            filename, node.__line__)
        desugar_queue.append(elt)
        return elt
        
        # TODO: add line numbers
      return obj_constructor
    
    loader.compose_node = compose_node
    
    # Ensure load ordering: https://stackoverflow.com/questions/5121931/in-python-how-can-you-load-yaml-mappings-as-ordereddicts
    _mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG
    def dict_constructor(loader, node):
      return OrderedDict(loader.construct_pairs(node))
    loader.add_constructor(_mapping_tag, dict_constructor)
    
    for tag_name in tag_registry:
      loader.add_constructor("!" + tag_name, create_obj_constructor(tag_name))
      
    for tag_name in desugar_tag_registry:
      loader.add_constructor("!" + tag_name, create_obj_constructor(tag_name))
    
    yaml_dict = loader.get_data()
    if 'defaults' in yaml_dict:
      assert isinstance(yaml_dict['defaults'], dict)
      for tag_name, elt in yaml_dict['defaults'].items():
        self.process_default_template(tag_name, elt)
        logging.debug("Loaded default template tag='%s'", tag_name)
        self.default_templates[tag_name] = elt
    logging.debug("Finished loading default templates")
    
    if 'lib' in yaml_dict:
      assert isinstance(yaml_dict['lib'], dict)
      for ref_name, elt in yaml_dict['lib'].items():
        # Check is a parsedelement
        elt.set_ref(ref_name)
        if ref_name in self.lib_elements:
          elt.parse_error("Duplicate ref")
        logging.debug("Loaded library element ref='%s'", ref_name)
        self.lib_elements[ref_name] = elt
    logging.debug("Finished loading library elements")
    
    if 'display' in yaml_dict:
      assert isinstance(yaml_dict['display'], dict)
      for elt_name, elt in yaml_dict['display'].iteritems():
        elt.set_ref("(display '%s')" % elt_name)
      self.display_elements = yaml_dict['display']
    logging.debug("Finished loading display elements")
      
    if 'temporal' in yaml_dict:
      assert isinstance(yaml_dict['temporal'], dict)
      for elt_name, elt in yaml_dict['temporal'].iteritems():
        elt.set_ref("(temporal '%s')" % elt_name)
      self.temporal_elements = yaml_dict['temporal']
    logging.debug("Finished loading temporal elements")
      
    # Run desugaring pass
    for elt in desugar_queue:
      while elt.tag in desugar_tag_registry:
        old_tag = elt.tag
        desugar_tag_registry[elt.tag](elt, self)
        assert elt.tag != old_tag
        
      for desugar_all_fn in desugar_all_registry:
        desugar_all_fn(elt, self)
      
      self.apply_default_template(elt)
      
    logging.debug("Finished desugaring pass")
    