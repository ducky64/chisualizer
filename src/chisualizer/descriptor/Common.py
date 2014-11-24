import copy

# A registry of all visualization descriptors (map from tag name to class)
# which can be instantiated.
tag_registry = {}
def tag_register(tag_name=None):
  def wrap(cls):
    assert tag_name not in tag_registry, "Duplicate tag '%s'" % tag_name
    tag_registry[tag_name] = cls
    return cls
  return wrap

# A registry of desugaring structural transforms, a map from the tag name to a
# function which takes in the ParsedElement and desugars it via in-place 
# mutation. The desugared element must have a different tag.
# Desugaring runs in the same order as elements were read in, postorder.
# Returned elements may alias with other elements. 
# TODO: is aliasing a good idea? should ParsedElements be able to clone()?
# TODO: is the ordering guarantee good enough? better ways to do that?  
desugar_tag_registry = {} 
def desugar_tag(tag_name):
  def wrap(fun):
    assert tag_name not in desugar_tag_registry, "Duplicate desugaring tag '%s'" % tag_name
    desugar_tag_registry[tag_name] = fun
    return fun
  return wrap

# A registry of desugaring structural transforms, run on ALL tagged elements.
# Same guarantees and conditions as the tagged version, except the desugared
# version need not have a different tag. Each registered desugaring function
# runs once per ParsedElement, and there are no guarantees on the ordering of
# the degsugaring functions.
desugar_all_registry = []
def desugar_all():
  def wrap(fun):
    assert fun not in desugar_all_registry, "Duplicate desugaring function %s" % fun
    desugar_all_registry.append(fun)
    return fun
  return wrap

@desugar_tag("Ref")
def desugar_ref(parsed_element, registry):
  if len(parsed_element.get_attr_list('ref')) != 1:
    parsed_element.parse_error("Can only have one ref")
  ref_name = parsed_element.get_attr_list('ref')[0]
  assert isinstance(ref_name, basestring) # TODO: more elegant typing in desugaring
  ref = registry.get_ref(ref_name)
  if ref is None:
    parsed_element.parse_error("Ref not found: '%s'" % ref_name)
  assert ref.tag != "Ref" # should have been already desugared
  if 'path' in parsed_element.attr_map:
    path_prefix = parsed_element.get_attr_list('path')[0]
  else:
    path_prefix = None
  
  parsed_element.tag = ref.tag
  parsed_element.attr_map = copy.copy(ref.attr_map)
  
  # TODO: make this mechanism more general?
  if path_prefix is not None:
    if 'path' in parsed_element.attr_map:
      # TODO: should type check things here
      parsed_element.attr_map['path'] = [path_prefix + path_elt
                                         for path_elt 
                                         in parsed_element.attr_map['path']]
    else:
      parsed_element.attr_map['path'] = path_prefix

def apply_template(element, template):
  for template_attr, template_value_list in template.attr_map.iteritems():
    if template_attr not in element.attr_map:
      element.attr_map[template_attr] = []
    element.attr_map[template_attr].extend(template_value_list)
      
@desugar_all()
def desugar_template(parsed_element, registry):
  if 'template' in parsed_element.attr_map:
    # TODO handle multiple templates
    assert len(parsed_element.get_attr_list('template')) == 1, "TODO Generalize me"
    template_name = parsed_element.get_attr_list('template')[0]
    del parsed_element.attr_map['template']
    template = registry.get_ref(template_name)
    if template is None:
      parsed_element.parse_error("Template not found: '%s'" % template_name)
    if template.tag != 'Template':
      # TODO: is this checking too strict?
      parsed_element.parse_error("Not a template: '%s'" % template_name)
    assert "template" not in template.attr_map  # should have already been desugared
    apply_template(parsed_element, template)
