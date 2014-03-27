import logging
import string

from chisualizer.Base import Base

import cairo

import wx

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

  def contains(self, point_x, point_y):
    if (self._left <= point_x and self._right >= point_x and 
        self._top <= point_y and self._bottom >= point_y):
      return True
    else:
      return False 

class VisualizerParseError(BaseException):
  pass

class VisualizerBase(Base):
  """Abstract base class for Chisel visualizer objects."""
  def parse_warning(self, msg):
    """Emits a warning message for XML parsing, automatically prepending
    the class name and reference."""
    logging.warning("Parsing warning for %s: '%s': %s" % 
                    (self.__class__.__name__, self.ref, msg))
  def parse_error(self, msg):
    """Emits an error message for XML parsing, automatically prepending
    the class name and reference and throwing an exception"""
    logging.warning("Parsing ERROR for %s: '%s': %s" % 
                    (self.__class__.__name__, self.ref, msg))
    raise VisualizerParseError(msg) 
    
  def parse_element_int(self, element, param, default):
    got = element.get(param, None)
    if got is None:
      return default
    try:
      return int(got, 0)
    except ValueError:
      self.parse_warning("unable to convert %s='%s' to int, default to %s" %
                         (param, got, default))
      return default
  
  def __init__(self):
    self.collapsed = False
  
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
    new.border_size = new.parse_element_int(element, 'border_size', 1)
    new.border_margin = new.parse_element_int(element, 'border_margin', 6)
    new.label = element.get('label', None)
    new.label_size = new.parse_element_int(element, 'label_size', 10)
    new.label_font = element.get('label_font', 'Mono')
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
    cloned.label = self.label
    cloned.label_font = self.label_font
    cloned.label_size = self.label_size
    
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
    return self.draw_cairo(cr, rect, 0)
  
  def layout_cairo(self, cr):
    """Computes (and stores) the layout for this object when drawing with Cairo.
    Returns a tuple (width, height) of the minimum size of this object.
    This may differ per frame, and should be called before draw_cairo."""
    assert isinstance(cr, cairo.Context)
    if self.collapsed:
      self.element_width, self.element_height = (0, 0)
    else:
      self.element_width, self.element_height = self.layout_element_cairo(cr)
    
    cr.select_font_face(self.label_font,
                        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(self.label_size)
    if self.label is None:
      _, _, self.label_width, _, _, _ = cr.text_extents(string.strip(self.path_component, "_. "))
    else:
      _, _, self.label_width, _, _, _ = cr.text_extents(self.label)
    _, _, _, self.label_height, _, _ = cr.text_extents('X')
    
    width = max(self.element_width, self.label_width)
    self.top_height = self.label_height + self.border_margin
    return (2 * self.border_margin + width,
            self.top_height + self.border_margin + self.element_height)
  
  def draw_cairo(self, cr, rect, depth):
    """Draw this object (with borders and labels) to the Cairo context.
    rect indicates the area allocated for this object.
    Returns a list elements drawn: tuple (depth, rect, visualizer)
    Depth indicates the drawing depth, with a higher number meaning deeper
    (further nested). This is used to calculate UI events, like mouseover 
    and clicks.
    """
    assert isinstance(cr, cairo.Context)
    assert isinstance(rect, Rectangle)
    
    element_rect = rect.shrink(self.border_margin,
                               self.top_height,
                               self.border_margin,
                               self.border_margin)
    border_offset = self.border_margin / 2
    top_offset = self.top_height / 2
    
    cr.set_source_rgb(0, 0.4, 0.5)
    cr.set_line_width(self.border_size)
    cr.rectangle(element_rect.left() - border_offset,
                 element_rect.top() - top_offset,
                 element_rect.width() + 2 * border_offset,
                 element_rect.height() + border_offset + top_offset)
    cr.stroke()
    
    cr.set_source_rgb(0, 0, 0)
    cr.rectangle(rect.left() + self.border_margin,
                 rect.top() + border_offset,
                 self.label_width,
                 self.label_height)
    cr.fill()
    
    cr.set_source_rgb(0, 0.4, 0.5)
    cr.select_font_face(self.label_font,
                        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(self.label_size)
    cr.move_to(rect.left() + self.border_margin,
               rect.top() + self.top_height - border_offset)
    if self.label is None:
      cr.show_text(string.strip(self.path_component, "_. "))
    else:
      cr.show_text(self.label)
    
    if self.collapsed:
      elements = []
    else:
      elements = self.draw_element_cairo(cr, element_rect, depth)
    elements.append((depth, rect, self))
    return elements
  
  def layout_element_cairo(self, cr):
    """Computes (and stores) the layout for this object when drawing with Cairo.
    Returns a tuple (width, height) of the minimum size of this object.
    This may differ per frame, and should be called before draw_cairo."""
    raise NotImplementedError()
  
  def draw_element_cairo(self, cr, rect, depth):
    """Draw this object to the Cairo context.
    rect indicates the area allocated for this object.
    Returns the same as draw_cairo.
    """
    raise NotImplementedError()

  def wx_prefix(self):
    prefix = self.path
    if self.label:
      prefix = "%s (%s)" % (prefix, self.label)
    return prefix
      
  def wx_popupmenu_populate(self, menu):
    """Adds items relevant to this visualizer to the argument menu.
    Return True if items were added, False otherwise."""
    if self.collapsed:
      item = wx.MenuItem(menu, wx.NewId(), "%s: Expand" % self.wx_prefix())
      menu.AppendItem(item)
      menu.Bind(wx.EVT_MENU, self.wx_popupmenu_expand, item)
    else:
      item = wx.MenuItem(menu, wx.NewId(), "%s: Collapse" % self.wx_prefix())
      menu.AppendItem(item)
      menu.Bind(wx.EVT_MENU, self.wx_popupmenu_collapse, item)

    return True

  def wx_popupmenu_expand(self, evt):
    self.collapsed = False
    
  def wx_popupmenu_collapse(self, evt):
    self.collapsed = True
    