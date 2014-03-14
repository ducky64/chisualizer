import logging
import string

from chisualizer.Base import Base

import wx.lib.wxcairo
import cairo

class Rectangle:
  def __init__(self, point1, point2):
    self._left = min(point1[0], point2[0])
    self._right = max(point1[0], point2[0])
    self._top = min(point1[1], point2[1])
    self._bottom = max(point1[1], point2[1])

  def top(self):
    return self._top

  def bottom(self):
    return self._bottom

  def left(self):
    return self._left
  
  def right(self):
    return self._right
  
  def center_horiz(self):
    return (self.left() + self.right()) / 2
  
  def center_vert(self):
    return (self.bottom() + self.top()) / 2
  
  def height(self):
    return abs(self.top() - self.bottom())
  
  def width(self):
    return abs(self.right() - self.left())

  def shrink(self, left, top, right, bottom):
    return Rectangle((self.left() + left,
                      self.top() + top),
                     (self.right() - right,
                      self.bottom() - bottom))

class VisualizerBase(Base):
  """Abstract base class for Chisel visualizer objects."""
  
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
    new.api = None
    
    def parse_element_int(param, default):
      got = element.get(param, None)
      if got is None:
        return default
      try:
        return int(got, 0)
      except ValueError:
        logging.error("Unable to parse %s='%s' into integer in %s: '%s'",
                      param, got, new.__class__.__name__, new.ref)
        return default
    new.border_size = parse_element_int('border_size', 1)
    new.border_margin = parse_element_int('border_margin', 5)
    new.border_label = element.get('border_label', None)
    new.border_label_size = parse_element_int('border_label_size', 10)
    new.border_label_font = element.get('border_label_font', 'Sans')
    return new
  
  def instantiate(self, new_parent, path_prefix=''):
    """Instantiates this visualizer template by cloning the template and
    resolving all references. Acts as clone (to a new parent) if called by an
    already-instantiated object.
    """
    cloned = self.__class__()
    cloned.parent = new_parent
    cloned.path_component = path_prefix + self.path_component
    cloned.container = self.container
    if new_parent:
      cloned.root = new_parent.root
      cloned.path = new_parent.path + cloned.path_component
    else:
      cloned.root = cloned
      cloned.path = cloned.path_component
    cloned.api = None
    
    cloned.border_size = self.border_size
    cloned.border_margin = self.border_margin
    cloned.border_label = self.border_label
    cloned.border_label_font = self.border_label_font
    cloned.border_label_size = self.border_label_size
    
    return cloned
  
  def set_chisel_api(self, api):
    self.api = api
  
  def get_chisel_api(self):
    """Returns the ChiselApi object used to access node values.
    Returns None if not available or if this visualizer wasn't properly
    instantiated."""
    return self.root.api
  
  def layout_and_draw_cairo(self, cr):
    size_x, size_y = self.layout_cairo(cr)
    rect = Rectangle((0, 0), (size_x, size_y))
    self.draw_cairo(cr, rect)
  
  def layout_cairo(self, cr):
    """Computes (and stores) the layout for this object when drawing with Cairo.
    Returns a tuple (width, height) of the minimum size of this object.
    This may differ per frame, and should be called before draw_cairo."""
    assert isinstance(cr, cairo.Context)
    self.element_width, self.element_height = self.layout_element_cairo(cr)
    
    cr.select_font_face(self.border_label_font,
                        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(self.border_label_size)
    if self.border_label is None:
      _, _, self.label_width, _, _, _ = cr.text_extents(string.strip(self.path_component, "_. "))
    else:
      _, _, self.label_width, _, _, _ = cr.text_extents(self.border_label)
    _, _, _, self.label_height, _, _ = cr.text_extents('X')
    
    width = max(self.element_width, self.label_width)
    self.top_height = max(self.border_margin, self.label_height)
    return (2 * self.border_margin + width,
            self.top_height + self.border_margin + self.element_height)
  
  def draw_cairo(self, cr, rect):
    """Draw this object (with borders and labels) to the Cairo context.
    rect indicates the area allocated for this object.
    """
    assert isinstance(cr, cairo.Context)
    assert isinstance(rect, Rectangle)
    
    element_rect = rect.shrink(self.border_margin,
                               self.top_height,
                               self.border_margin,
                               self.border_margin)
    border_offset = self.border_margin / 2
    
    cr.set_source_rgb(0, 0.4, 0.5)
    cr.set_line_width(self.border_size)
    cr.rectangle(element_rect.left() - border_offset,
                 element_rect.top() - border_offset,
                 element_rect.width() + 2 * border_offset,
                 element_rect.height() + 2 * border_offset)
    cr.stroke()
    
    cr.set_source_rgb(0, 0, 0)
    cr.rectangle(rect.left() + self.border_margin,
                 rect.top(),
                 self.label_width,
                 self.label_height)
    cr.fill()
    
    cr.set_source_rgb(0, 0.4, 0.5)
    cr.select_font_face(self.border_label_font,
                        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(self.border_label_size)
    cr.move_to(rect.left() + self.border_margin,
               rect.top() + self.top_height)
    if self.border_label is None:
      cr.show_text(string.strip(self.path_component, "_. "))
    else:
      cr.show_text(self.border_label)
      
    
    self.draw_element_cairo(cr, element_rect)
  
  def layout_element_cairo(self, cr):
    """Computes (and stores) the layout for this object when drawing with Cairo.
    Returns a tuple (width, height) of the minimum size of this object.
    This may differ per frame, and should be called before draw_cairo."""
    raise NotImplementedError()
  
  def draw_element_cairo(self, cr, rect):
    """Draw this object to the Cairo context.
    rect indicates the area allocated for this object.
    """
    raise NotImplementedError()
    