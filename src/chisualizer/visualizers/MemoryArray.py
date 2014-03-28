import chisualizer.Base as Base
from VisualizerBase import Rectangle
from Data import Data

@Base.xml_register('MemoryArray')
class MemoryArray(Data):
  """A grid of elements, each pointing to a memory element."""
  @classmethod
  def from_xml_cls(cls, element, parent):
    new = super(MemoryArray, cls).from_xml_cls(element, parent)
    
    new.offset = new.parse_element_int(element, 'offset', 0)
    new.rows = new.parse_element_int(element, 'rows', 1)
    new.cols = new.parse_element_int(element, 'cols', 1)
    
    new.cell = None # cell visualizer, as a template to populate cells with
    for child_vis in element:
      if new.cell:
        new.parse_warning("duplicate cell, overwriting")
      new.cell = Base.Base.from_xml(child_vis, new)
    if not new.cell:
      new.parse_error("MemoryArray missing cell")

    new.cells = []  # list of rows of cells (each element is a list of cells)

    return new
  
  def instantiate(self, new_parent):
    cloned = super(MemoryArray, self).instantiate(new_parent)
    cloned.offset = self.offset
    cloned.rows = self.rows
    cloned.cols = self.cols
    cloned.cell = self.cell
    cloned.cells = []
    cloned.instantiate_cells(self.offset, self.rows, self.cols, self.cell)
    return cloned
  
  def instantiate_cells(self, offset, rows, cols, cell):
    self.cells = []
    element_num = 0
    for col in xrange(cols):
      self.cells.append([])
      for row in xrange(rows):
        inst = cell.instantiate(self)
        inst.set_node(self.node.get_subscript_reference(element_num))
        if inst.label is None: inst.label = str(element_num)
        self.cells[col].append(inst)
        element_num = element_num + 1    
  
  def layout_element_cairo(self, cr):
    # for now, assume the cell size is constant
    self.cell_x = 0
    self.cell_y = 0
    for x_col in xrange(self.cols):
      for y_row in xrange(self.rows):
        cell_x, cell_y = self.cells[x_col][y_row].layout_cairo(cr)
        self.cell_x = max(self.cell_x, cell_x)
        self.cell_y = max(self.cell_y, cell_y)
        
    # TODO: FIXME
    self.total_x = self.cell_x * self.cols
    self.total_y = self.cell_y * self.rows
    return (self.total_x, self.total_y) 
        
  def draw_element_cairo(self, cr, rect, depth):
    origin_x = rect.center_horiz() - self.total_x / 2
    origin_y = rect.center_vert() - self.total_y / 2
    pos_x = origin_x
    pos_y = origin_y
    elements = []
    
    #TODO consistent rows/cols with instantiation
    for y_row in xrange(self.rows):
      pos_x = origin_x
      for x_col in xrange(self.cols):
        cell_rect = Rectangle((pos_x, pos_y),
                              (pos_x + self.cell_x, pos_y + self.cell_y))
        elements.extend(self.cells[x_col][y_row].draw_cairo(cr, cell_rect,
                                                              depth + 1))
        pos_x += self.cell_x
      pos_y += self.cell_y
    
    return elements
  