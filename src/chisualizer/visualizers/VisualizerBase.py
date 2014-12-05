import string

import chisualizer.Base as Base
from chisualizer.descriptor import Common, DataTypes, ParsedElement
from chisualizer.util import Rectangle

import cairo
import wx

@Common.tag_register("Template")
class AbstractVisualizer(Base.Base):
  """Abstract base class for Chisel visualizer objects. Defines interface 
  methods and provides common functionality, like paths."""
  def __init__(self, elt, parent, path_component_override=None,
               node_override=None):
    from chisualizer.display.Modifier import Modifier # TODO dehackify
    super(AbstractVisualizer, self).__init__(elt, parent)
    self.root = parent.root
    
    self.dynamic_attrs = {}

    self.path_component = self.static_attr(DataTypes.StringAttr, 'path').get()    
    if path_component_override is not None:
      self.path_component = path_component_override
    self.path = parent.path + self.path_component
    
    if node_override is not None:
      self.node = node_override
    else:
      self.node = parent.get_circuit_node().get_child_reference(self.path_component)
      
    self.modifiers = []
    modifiers = self.static_attr(DataTypes.ObjectAttr, 'modifiers').get()
    for modifier in modifiers:
      if not isinstance(modifier, ParsedElement.ParsedElement):
        elt.parse_error("Modifier %s not a object")
      self.modifiers.append(modifier.instantiate(self, valid_subclass=Modifier))
    
  def dynamic_attr(self, datatype_cls, attr_name, **kwds):
    """Registers my attributes, so update() will look for and appropriately
    type-convert attribute values."""
    attr_obj = datatype_cls(self, self.elt, attr_name, dynamic=True, **kwds)
    assert attr_name not in self.dynamic_attrs
    self.dynamic_attrs[attr_name] = attr_obj
    return attr_obj
    
  def apply_attr_overloads(self, modifier_obj, modifiers_dict):
    """Apply dynamic attribute overloads."""
    for modify_attr, modify_val in modifiers_dict.iteritems():
      if modify_attr in self.static_attrs:
        modifier_obj.elt.parse_error("Target attr '%s' is static" % modify_attr)
      if modify_attr not in self.dynamic_attrs:
        modifier_obj.elt.parse_error("Target does not have attr '%s'" % modify_attr)
      self.dynamic_attrs[modify_attr].apply_overload(modify_val)
    
  def apply_modifier(self, modifier):
    modifier.elt.parse_error("%s can't apply modifier %s",
                             self.__class__.__name__,
                             modifier.__class__.__name__)
    
  def get_vis_root(self):
    """Returns the visualizer root."""
    return self.root

  def get_circuit_node(self):
    """Returns my associated circuit node or None."""
    return self.node
    
  def update(self):
    """Called once per visualizer update (before the layout phase), refreshing
    my attrs dict based on new circuit values / modifiers / whatever.
    Classes with elements should also have their children update."""
    for dynamic_attr in self.dynamic_attrs.itervalues():
      dynamic_attr.clear_overloads()
    
    self.update_children()
          
    for modifier in self.modifiers:
      self.apply_modifier(modifier)
  
  def update_children(self):
    """Updates my children, if necessary. Called between when this object clears
    its overloads / udpates its attributes and when it applies modifiers."""
    pass
  
  def layout_cairo(self, cr):
    """Computes (and stores) the layout for this object when drawing with Cairo.
    Returns a tuple (width, height) of the minimum size of this object.
    This may differ per frame, and should be called before draw_cairo."""
    raise NotImplementedError()
    
  def draw_cairo(self, cr, rect, depth):
    """Draw this object (with borders and labels) to the Cairo context.
    rect indicates the area allocated for this object.
    Returns a list elements drawn: tuple (depth, rect, visualizer)
    Depth indicates the drawing depth, with a higher number meaning deeper
    (further nested). This is used to calculate UI events, like mouseover 
    and clicks.
    """
    raise NotImplementedError()
     
  def wx_prefix(self):
    """Returns the string prefix for this visualizer when referred to in UI 
    elements."""
    raise NotImplementedError()
      
  def wx_defaultaction(self):
    """Default action when the visualizer is double-clicked."""
    raise NotImplementedError()
          
  def wx_popupmenu_populate(self, menu):
    """Adds items relevant to this visualizer to the argument menu.
    Return True if items were added, False otherwise."""
    return False

@Common.tag_register("FramedBase")
class FramedVisualizer(AbstractVisualizer):
  """Base class for visualizers providing visual framing (borders)."""
  def __init__(self, elt, parent, **kwargs):
    super(FramedVisualizer, self).__init__(elt, parent, **kwargs)

    self.frame_style = self.static_attr(DataTypes.StringAttr, 'frame_style', valid_set=['none', 'frame']).get()
    self.frame_margin = self.static_attr(DataTypes.IntAttr, 'frame_margin', valid_min=0).get()

    
    self.border_style = self.dynamic_attr(DataTypes.StringAttr, 'border_style', valid_set=['none', 'border'])
    self.border_size = self.static_attr(DataTypes.IntAttr, 'border_size', valid_min=1).get()
    self.border_color = self.dynamic_attr(DataTypes.StringAttr, 'border_color')
    
    self.label = self.dynamic_attr(DataTypes.StringAttr, 'label')
    self.label_size = self.static_attr(DataTypes.IntAttr,'label_size', valid_min=1).get()
    self.label_font = self.static_attr(DataTypes.StringAttr,'label_font').get()
    self.label_color = self.dynamic_attr(DataTypes.StringAttr, 'label_color')
        
    self.collapsed = False

  def layout_cairo(self, cr):
    assert isinstance(cr, cairo.Context)
    if self.collapsed:
      self.element_width, self.element_height = (0, 0)
    else:
      self.element_width, self.element_height = self.layout_element_cairo(cr)
    
    if self.frame_style == 'frame':
      cr.select_font_face(self.label_font,
                          cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
      cr.set_font_size(self.label_size)
      if not self.label.get():
        _, _, _, _, self.label_width, _ = cr.text_extents(string.strip(self.path_component, "_. "))
      else:
        # TODO: better labeling so labels don't affect element size
        _, _, _, _, self.label_width, _ = cr.text_extents(self.label.get())
      _, _, _, self.label_height, _, _ = cr.text_extents('X')
      
      width = max(self.element_width, self.label_width)
      self.top_height = self.label_height + self.frame_margin
      return (2 * self.frame_margin + width,
              self.top_height + self.frame_margin + self.element_height)
    elif self.frame_style == 'none':
      return (self.element_width, self.element_height)      
    else:
      assert False
      
  def draw_cairo(self, cr, rect, depth):
    assert isinstance(cr, cairo.Context)
    assert isinstance(rect, Rectangle)
    
    elements = []
    
    if self.frame_style == 'frame':
      element_rect = rect.shrink(self.frame_margin,
                                 self.top_height,
                                 self.frame_margin,
                                 self.frame_margin)
      border_offset = self.frame_margin / 2
      top_offset = self.top_height / 2
      
      
      # draw the border only if indicated
      if self.border_style.get() == 'border':
        cr.set_source_rgba(*self.get_vis_root().get_theme().color(self.border_color.get()))
        cr.set_line_width(self.border_size)
        cr.move_to(rect.left() + self.frame_margin,      # top left, where label begins
                   element_rect.top() - top_offset)
        cr.line_to(element_rect.left() - border_offset,   # top left
                   element_rect.top() - top_offset)
        cr.line_to(element_rect.left() - border_offset,   # bottom left
                   element_rect.bottom() + border_offset)
        cr.line_to(element_rect.right() + border_offset,  # bottom right
                   element_rect.bottom() + border_offset)
        cr.line_to(element_rect.right() + border_offset,  # top right
                   element_rect.top() - top_offset)
        cr.line_to(rect.left() + self.frame_margin + self.label_width,  # top right, where label ends
                   element_rect.top() - top_offset)
        cr.stroke()
        
      # draw the label always
      cr.set_source_rgba(*self.get_vis_root().get_theme().color(self.label_color.get()))
      cr.select_font_face(self.label_font,
                          cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
      cr.set_font_size(self.label_size)
      cr.move_to(rect.left() + self.frame_margin,
                 rect.top() + self.top_height - border_offset)
      if not self.label.get():
        cr.show_text(string.strip(self.path_component, "_. "))
      else:
        cr.show_text(self.label.get())

      if not self.collapsed:
        elements.extend(self.draw_element_cairo(cr, element_rect, depth))
    else:
      elements.extend(self.draw_element_cairo(cr, rect, depth))
      
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
    prefix = string.strip(self.path_component, "_. ")
    if self.label.get():
      prefix += "(%s)" % self.label.get()
    return prefix

  def wx_defaultaction(self):
    #TODO: integrate this with menu so both choose options from common source
    if self.frame_style == 'frame':
      if self.collapsed:
        self.wx_popupmenu_expand(None)
      else:
        self.wx_popupmenu_collapse(None)
          
  def wx_popupmenu_populate(self, menu):
    super_populated = super(FramedVisualizer, self).wx_popupmenu_populate(menu)
    if self.frame_style == 'frame':
      if self.collapsed:
        item = wx.MenuItem(menu, wx.NewId(), "%s: Expand" % self.wx_prefix())
        menu.AppendItem(item)
        menu.Bind(wx.EVT_MENU, self.wx_popupmenu_expand, item)
      else:
        item = wx.MenuItem(menu, wx.NewId(), "%s: Collapse" % self.wx_prefix())
        menu.AppendItem(item)
        menu.Bind(wx.EVT_MENU, self.wx_popupmenu_collapse, item)
      return True
    else:
      return super_populated

  def wx_popupmenu_expand(self, evt):
    self.collapsed = False
    
  def wx_popupmenu_collapse(self, evt):
    self.collapsed = True
