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
    new.step = element.get('step', 'row')
    if new.step not in ['row', 'col']: new.parse_error("step must be 'row' or 'col', got '%s'" % new.step) 
    
    if len(element) != 1:
      new.parse_error("MemoryArray must have exactly 1 child")
    new.cell_elt = element[0]

    # TODO: allow dynamic cell instantiation by changing offsets
    def instantiate_cell(num):
      inst = Base.Base.from_xml(new.cell_elt, new)
      inst.set_node(new.node.get_subscript_reference(num))
      inst.path_component += "[%i]" % num
      inst.path += "[%i]" % num
      if inst.label is None: inst.label = str(num)
      return inst

    new.cells = []  # list of cols of cells (each element is a list of cells)
    element_num = new.offset
    for col in xrange(new.cols):
      new.cells.append([])
    if new.step == 'row':
      for _ in xrange(new.rows):
        for col in xrange(new.cols):
          new.cells[col].append(instantiate_cell(element_num))
          element_num += 1
          if element_num >= new.node.get_depth(): break
    elif new.step == 'col':
      for col in xrange(new.cols):
        for _ in xrange(new.rows):
          new.cells[col].append(instantiate_cell(element_num))
          element_num += 1
          if element_num >= new.node.get_depth(): break

    return new

  def layout_element_cairo(self, cr):
    # for now, assume the cell size is constant
    # TODO: FIXME
    self.cell_x = 0
    self.cell_y = 0
    for x_col_ary in self.cells:
      for cell in x_col_ary:
        cell_x, cell_y = cell.layout_cairo(cr)
        self.cell_x = max(self.cell_x, cell_x)
        self.cell_y = max(self.cell_y, cell_y)
        
    self.total_x = self.cell_x * self.cols
    self.total_y = self.cell_y * self.rows
    return (self.total_x, self.total_y) 
        
  def draw_element_cairo(self, cr, rect, depth):
    origin_x = rect.center_horiz() - self.total_x / 2
    origin_y = rect.center_vert() - self.total_y / 2
    pos_x = origin_x
    pos_y = origin_y
    elements = []

    for x_col_ary in self.cells:
      pos_y = origin_y
      for cell in x_col_ary:
        cell_rect = Rectangle((pos_x, pos_y),
                              (pos_x + self.cell_x, pos_y + self.cell_y))
        elements.extend(cell.draw_cairo(cr, cell_rect, depth + 1))
        pos_y += self.cell_y
      pos_x += self.cell_x

    return elements
  