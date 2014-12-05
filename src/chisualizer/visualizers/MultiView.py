from collections import OrderedDict

import wx

from chisualizer.descriptor import Common, DataTypes
from VisualizerBase import AbstractVisualizer, FramedVisualizer

@Common.tag_register('MultiView')
class MultiView(FramedVisualizer):
  """Allows multiple, selectable visualizers."""
  def __init__(self, element, parent, **kwargs):
    super(MultiView, self).__init__(element, parent, **kwargs)
    views_attr = self.static_attr(DataTypes.ObjectAttr, 'views')
    
    self.view_names = []
    self.views = {}
    self.active_view_index = 0
    
    assert len(views_attr.get()) == 1, "Multiple dicts not supported yet"
    for view_name, view in views_attr.get()[0].iteritems():
      if not isinstance(view, DataTypes.ParsedElement):
        views_attr.parse_error("Expected value to be visualizer, got %s"
                               % view)
      if view_name in self.views:
        views_attr.parse_error("Duplicate view name %s" % view_name)
      self.view_names.append(view_name)
      self.views[view_name] = view.instantiate(self, valid_subclass=AbstractVisualizer)
      
    if not self.view_names:
      views_attr.parse_error("No views found")

    self.active_view = self.views[self.view_names[self.active_view_index]]

  def update_children(self):
    self.active_view.update()

  def layout_element_cairo(self, cr):
    return self.active_view.layout_cairo(cr)
        
  def draw_element_cairo(self, cr, rect, depth):
    return self.active_view.draw_cairo(cr, rect, depth)

  def wx_defaultaction(self):
    self.active_view_index = (self.active_view_index + 1) % len(self.view_names)
    self.active_view = self.views[self.view_names[self.active_view_index]]
  
  def wx_popupmenu_populate(self, menu): 
    for view_index, view_name in enumerate(self.view_names):
      if view_index == self.active_view_index:
        selection = unichr(0x25c9)
      else:
        selection = unichr(0x25cb)
      item = wx.MenuItem(menu, wx.NewId(), "%s: Select view %s %s" 
                         % (self.wx_prefix(), selection, view_name))
      menu.AppendItem(item)
      menu.Bind(wx.EVT_MENU, self.wx_popupmenu_setindex_wrap(view_index), item)
    super(MultiView, self).wx_popupmenu_populate(menu)
    return True
    
  def wx_popupmenu_setindex_wrap(self, view_index):
    def wx_popupmenu_setindex(evt):
      self.active_view_index = view_index % len(self.view_names)
      self.active_view = self.views[self.view_names[self.active_view_index]]
    return wx_popupmenu_setindex
  