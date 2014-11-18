import chisualizer.Base as Base
from VisualizerBase import AbstractVisualizer, FramedVisualizer, Rectangle

@Base.tag_register('LineGrid')
class LineGrid(FramedVisualizer):
  """A single line of elements, either in a row or column."""
  def __init__(self, element, parent):
    super(LineGrid, self).__init__(element, parent)
    self.dir = self.attr(Base.StringAttr, 'dir', valid_set=['row', 'col']).get_static()
    cell_attr = self.attr(Base.ObjectAttr, 'cells')
    self.cells = []
    for cell in cell_attr.get_static():
      if not isinstance(cell, Base.ParsedElement):
        cell_attr.parse_error("Expected list of Visualizers, got a %s"
                              % cell.__class__.__name__)
      self.cells.append(cell.instantiate(self, valid_subclass=AbstractVisualizer))

  def update(self):
    super(LineGrid, self).update()
    for cell in self.cells:
      cell.update()

  def layout_element_cairo(self, cr):
    x_size = 0
    y_size = 0
    
    self.cell_sizes = []
    
    for cell in self.cells:
      cell_x, cell_y = cell.layout_cairo(cr)
      if self.dir == 'row':    # cells along x-dir
        x_size += cell_x
        y_size = max(y_size, cell_y)
      elif self.dir == 'col':  # cells along y-dir
        x_size = max(x_size, cell_x)
        y_size += cell_y
      else:
        assert False
      self.cell_sizes.append((cell_x, cell_y))

    self.x_size = x_size
    self.y_size = y_size
      
    return (x_size, y_size) 
        
  def draw_element_cairo(self, cr, rect, depth):
    if self.dir == 'row':    # cells along x-dir
      step_pos = rect.center_horiz() - self.x_size / 2
      center_pos = rect.center_vert()
    elif self.dir == 'col':  # cells along y-dir
      center_pos = rect.center_horiz()
      step_pos = rect.center_vert() - self.y_size / 2
    
    elements = []  
    for cell, cell_size in zip(self.cells, self.cell_sizes):
      if self.dir == 'row':
        elements.extend(cell.draw_cairo(cr,
                                        Rectangle((step_pos, center_pos-cell_size[1]),
                                                  (step_pos+cell_size[0], center_pos+cell_size[1])),
                                        depth+1))
        step_pos += cell_size[0]
      elif self.dir == 'col':
        elements.extend(cell.draw_cairo(cr,
                                        Rectangle((center_pos-cell_size[0], step_pos),
                                                  (center_pos+cell_size[0], step_pos+cell_size[1])),
                                        depth+1))
        step_pos += cell_size[1]
        
    return elements
