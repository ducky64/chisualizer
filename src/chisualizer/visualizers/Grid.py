import chisualizer.Base as Base
from VisualizerBase import VisualizerBase

@Base.xml_register('Grid')
class Grid(VisualizerBase):
  """Grid containing other visualizers."""
  @classmethod
  def from_xml_cls(cls, element, **kwargs):
    assert 'container' in kwargs
    
    new = super(Grid, cls).from_xml_cls(element, **kwargs)
    new.cells = {}  # mapping of (x_col, y_row) to VisualizerBase-derived object
    for child_cell in element:
      if child_cell.tag != "Cell":
        raise TypeError("Grid children must be Cell, got '%s'" % child_cell.tag)
      x_col = child_cell.get('col', None)
      y_row = child_cell.get('row', None)
      if x_col is None or y_row is None:
        raise ValueError("Grid Cell must specify both x and y positions")
      x_col = int(x_col)
      y_row = int(y_row)
      for child_vis in child_cell:
        vis = Base.Base.from_xml(child_vis, container=kwargs['container'])
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
  
  def layout_cairo(self, cr):
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
      
    x_total = reduce(lambda x, y: x+y, self.x_col_sizes.itervalues())
    y_total = reduce(lambda x, y: x+y, self.y_row_sizes.itervalues())
    return (x_total, y_total)
        
  def draw_cairo(self, cr, rect):
    super(Grid, self).draw_cairo(cr, rect)
    
    origin_x = rect.left()
    origin_y = rect.top()
    pos_x = origin_x
    pos_y = origin_y
    for y_row, y_size in sorted(self.y_row_sizes.iteritems()):
      print "Y %i => %i" % (y_row, y_size)
      pos_x = origin_x
      for x_col, x_size in sorted(self.x_col_sizes.iteritems()):
        print "X %i => %i" % (x_col, x_size) 
        if (x_col, y_row) in self.cells:
          # TODO !!! do cairo transform
          cell_rect = self.Rectangle((pos_x, pos_y),
                                     (pos_x + x_size, pos_y + y_size))
          print "Rect %i, %i => %i, %i" % (pos_x, pos_y,
                                     pos_x + x_size, pos_y + y_size)
          self.cells[(x_col, y_row)].draw_cairo(cr, cell_rect)
        pos_x += x_size
      pos_y += y_size
    