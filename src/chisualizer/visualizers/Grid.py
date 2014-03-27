import chisualizer.Base as Base
from VisualizerBase import VisualizerBase, Rectangle

@Base.xml_register('Grid')
class Grid(VisualizerBase):
  """Grid containing other visualizers."""
  @classmethod
  def from_xml_cls(cls, element, parent):
    new = super(Grid, cls).from_xml_cls(element, parent)
    new.cells = {}  # mapping of (x_col, y_row) to VisualizerBase-derived object
    for child_cell in element:
      if child_cell.tag != "Cell":
        new.parse_error("Grid children must be 'Cell', got '%s'" % child_cell.tag)
      x_col = child_cell.get('col', None)
      y_row = child_cell.get('row', None)
      if x_col is None: new.parse_error("cell missing col (x) position")
      if y_row is None: new.parse_error("cell missing row (y) position")
      x_col = int(x_col)
      y_row = int(y_row)
      for child_vis in child_cell:
        vis = Base.Base.from_xml(child_vis, parent=new)
        if (x_col, y_row) in new.cells:
          new.parse_warning("duplicate cell in (%s, %s), overwriting" %
                            (x_col, y_row))
        new.cells[(x_col, y_row)] = vis
    
    new.x_col_sizes = {}
    new.y_row_sizes = {}
    
    return new
  
  def instantiate(self, new_parent, **kwargs):
    cloned = super(Grid, self).instantiate(new_parent, **kwargs)
    cloned.cells = {}
    for coords, vis in self.cells.iteritems():
      cloned.cells[coords] = vis.instantiate(cloned)
    cloned.x_col_sizes = {}
    cloned.y_row_sizes = {}
    return cloned
  
  def layout_element_cairo(self, cr):
    self.x_col_sizes = {}
    self.y_row_sizes = {}
    for coords, vis in self.cells.iteritems():
      x_col, y_row = coords
      vis_x, vis_y = vis.layout_cairo(cr)
      if x_col not in self.x_col_sizes:
        self.x_col_sizes[x_col] = 0
      if y_row not in self.y_row_sizes:  
        self.y_row_sizes[y_row] = 0
      self.x_col_sizes[x_col] = max(self.x_col_sizes[x_col], vis_x)
      self.y_row_sizes[y_row] = max(self.y_row_sizes[y_row], vis_y)
      
    self.x_total = reduce(lambda x, y: x+y, self.x_col_sizes.itervalues(), 0)
    self.y_total = reduce(lambda x, y: x+y, self.y_row_sizes.itervalues(), 0)
    return (self.x_total, self.y_total)
        
  def draw_element_cairo(self, cr, rect, depth):
    origin_x = rect.center_horiz() - self.x_total / 2
    origin_y = rect.center_vert() - self.y_total / 2
    pos_x = origin_x
    pos_y = origin_y
    elements = []
    for y_row, y_size in sorted(self.y_row_sizes.iteritems()):
      pos_x = origin_x
      for x_col, x_size in sorted(self.x_col_sizes.iteritems()):
        if (x_col, y_row) in self.cells:
          cell_rect = Rectangle((pos_x, pos_y),
                                (pos_x + x_size, pos_y + y_size))
          elements.extend(self.cells[(x_col, y_row)].draw_cairo(cr, cell_rect,
                                                                depth + 1))
        pos_x += x_size
      pos_y += y_size
    return elements