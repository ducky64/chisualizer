class Base(object):
  """Abstract base class for visualizer descriptor objects."""
  def __init__(self, element, parent):
    self.parent = parent
    self.elt = element
    self.ref = element.get_ref()
    self.static_attrs = {}
    
  def static_attr(self, datatype_cls, attr_name, **kwds):
    """Registers my attributes, so update() will look for and appropriately
    type-convert attribute values."""
    new_attr = datatype_cls(self, self.elt, attr_name, dynamic=False, **kwds)
    assert attr_name not in self.static_attrs
    self.static_attrs[attr_name] = new_attr
    return new_attr
