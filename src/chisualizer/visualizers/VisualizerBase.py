from chisualizer.Base import Base

import wx.lib.wxcairo
import cairo

class VisualizerBase(Base):
  """Abstract base class for Chisel visualizer objects."""
  
  class Rectangle:
    def __init__(self, point1, point2):
      self.top = max(point1[1], point2[1])
      self.bottom = min(point1[1], point2[1])
      self.left = min(point1[0], point2[0])
      self.right = max(point1[0], point2[0])
  
    def top(self):
      return self.top
  
    def bottom(self):
      return self.bottom
  
    def left(self):
      return self.left
    
    def right(self):
      return self.right
    
    def center_horiz(self):
      return (self.left() + self.right()) / 2
    
    def center_vert(self):
      return (self.bottom() + self.top()) / 2
    
    def height(self):
      return abs(self.top() - self.bottom())
    
    def width(self):
      return abs(self.right() - self.left())
  
  @classmethod
  def from_xml_cls(cls, element, parent=None, **kwargs):
    new = super(VisualizerBase, cls).from_xml_cls(element, **kwargs)
    new.parent = parent
    new.path_component = element.get('path', '')
    if parent:
      new.root = parent.root
      new.path = parent.path + new.path_component
    else:
      new.root = new
      new.path = new.path_component
    return new
  
  def instantiate(self, new_parent):
    """Instantiates this visualizer template by cloning the template and
    resolving all references. Acts as clone (to a new parent) if called by an
    already-instantiated object.
    """
    cloned = self.__class__()
    cloned.container = new_parent.container
    cloned.root = new_parent.root
    cloned.parent = new_parent
    cloned.path_component = self.path_component
    cloned.path = new_parent.path + cloned.path_component
    return cloned
  
  def get_chisel_api(self):
    """Returns the ChiselApi object used to access node values.
    Returns None if not available or if this visualizer wasn't properly
    instantiated."""
    if not self.root:
      return None
    return self.root.get_chisel_api()
  
  def draw_cairo(self, rect, cr):
    """Draw this object to the Cairo context.
    The point (0, 0) is the parent's anchor point for this object.
    rect indicates how much space was allocated for this object, in the
    coordinates of the given Cairo context.
    """
    assert isinstance(cr, cairo.Context)
    assert isinstance(rect, self.Rectangle)
    # future implementations may have more stuff in the base class, like
    # drawing labels or borders
    # subclasses should make sure to chain-call the draw functions of their
    # superclasses
    cr.set_source.rgb(0.25, 0.25, 0.25)
    cr.rectangle(rect.left(), rect.bottom(), rect.right(), rect.top())
    cr.stroke()
    
    size_x, size_y = self.calculate_cairo_minimum_size(cr)
    cr.set_source.rgb(0.25, 0.25, 0.25)
    cr.rectangle(rect.center_horiz()-size_x/2, rect.center_vert()-size_y/2,
                 rect.center_horiz()+size_x/2, rect.center_vert()+size_y/2)
    cr.stroke()
    pass
  
  def calculate_cairo_minimum_size(self, cr):
    """Returns a tuple (x, y) of the minimum size of this object when drawing
    with pyCairo."""
    assert isinstance(cr, cairo.Context)
    raise NotImplementedError()
