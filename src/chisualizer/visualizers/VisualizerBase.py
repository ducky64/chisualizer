import string

from chisualizer.Base import Base
from chisualizer.util import Rectangle

import cairo
import wx

class VisualizerBase(Base):
  """Abstract base class for Chisel visualizer objects."""
  def __init__(self):
    self.collapsed = False
  
  @classmethod
  def from_xml_cls(cls, element, parent):
    new = super(VisualizerBase, cls).from_xml_cls(element, parent)
    new.path_component = element.get('path', '')
    new.path = parent.path + new.path_component

    new.border_size = new.parse_element_int(element, 'border_size', 1)
    new.border_margin = new.parse_element_int(element, 'border_margin', 6)
    new.label = element.get('label', None)
    new.label_size = new.parse_element_int(element, 'label_size', 10)
    new.label_font = element.get('label_font', 'Mono')
    return new
  
  def instantiate(self, new_parent):
    """Instantiates this visualizer template by cloning the template and
    resolving all references. Acts as clone (to a new parent) if called by an
    already-instantiated object.
    """
    cloned = self.__class__()
    cloned.parent = new_parent
    cloned.path_component = self.path_component
    cloned.root = new_parent.root
    cloned.path = new_parent.path + cloned.path_component

    cloned.border_size = self.border_size
    cloned.border_margin = self.border_margin
    cloned.label = self.label
    cloned.label_font = self.label_font
    cloned.label_size = self.label_size
    
    return cloned
    
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
      _, _, _, _, self.label_width, _ = cr.text_extents(string.strip(self.path_component, "_. "))
    else:
      _, _, _, _, self.label_width, _ = cr.text_extents(self.label)
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
    
    cr.set_source_rgba(*self.get_theme().color('border'))
    
    # draw border rectangle
    cr.set_line_width(self.border_size)
    cr.move_to(rect.left() + self.border_margin,      # top left, where label begins
               element_rect.top() - top_offset)
    cr.line_to(element_rect.left() - border_offset,   # top left
               element_rect.top() - top_offset)
    cr.line_to(element_rect.left() - border_offset,   # bottom left
               element_rect.bottom() + border_offset)
    cr.line_to(element_rect.right() + border_offset,  # bottom right
               element_rect.bottom() + border_offset)
    cr.line_to(element_rect.right() + border_offset,  # top right
               element_rect.top() - top_offset)
    cr.line_to(rect.left() + self.border_margin + self.label_width,  # top right, where label ends
               element_rect.top() - top_offset)

    cr.stroke()
    
    # draw label text
    cr.select_font_face(self.label_font,
                        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(self.label_size)
    cr.move_to(rect.left() + self.border_margin,
               rect.top() + self.top_height - border_offset)
    if self.label is None:
      cr.show_text(string.strip(self.path_component, "_. "))
    else:
      cr.show_text(self.label)
    
    # draw the actual element
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
      
  def wx_defaultaction(self):
    #TODO: integrate this with menu so both choose options from common source
    if self.collapsed:
      self.wx_popupmenu_expand(None)
    else:
      self.wx_popupmenu_collapse(None)
          
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
    