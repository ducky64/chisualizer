from chisualizer.descriptor import Common, DataTypes, ParsedElement
from VisualizerBase import AbstractVisualizer, FramedVisualizer, Rectangle

@Common.tag_register('LineGrid')
class LineGrid(FramedVisualizer):
  """A single line of elements, either in a row or column."""
  def __init__(self, element, parent, **kwargs):
    super(LineGrid, self).__init__(element, parent, **kwargs)
    self.dir = self.static_attr(DataTypes.StringAttr, 'dir', valid_set=['row', 'col']).get()
    cell_attr = self.static_attr(DataTypes.ObjectAttr, 'cells')
    self.cells = []
    for cell in cell_attr.get():
      if not isinstance(cell, DataTypes.ParsedElement):
        cell_attr.parse_error("Expected list of Visualizers, got %s"
                              % cell)
      self.cells.append(cell.instantiate(self, valid_subclass=AbstractVisualizer))

  def update_children(self):
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
      center_low = rect.bottom()
      center_high = rect.top()
    elif self.dir == 'col':  # cells along y-dir
      center_low = rect.left()
      center_high = rect.right()
      step_pos = rect.center_vert() - self.y_size / 2
    
    elements = []  
    for cell, cell_size in zip(self.cells, self.cell_sizes):
      if self.dir == 'row':
        elements.extend(cell.draw_cairo(cr,
                                        Rectangle((step_pos, center_low),
                                                  (step_pos+cell_size[0], center_high)),
                                        depth+1))
        step_pos += cell_size[0]
      elif self.dir == 'col':
        elements.extend(cell.draw_cairo(cr,
                                        Rectangle((center_low, step_pos),
                                                  (center_high, step_pos+cell_size[1])),
                                        depth+1))
        step_pos += cell_size[1]
        
    return elements

@Common.desugar_tag("MultiLineGrid")
def desugar_multilinegrid(parsed_element, registry):
  parsed_element.tag = "LineGrid"
  if parsed_element.get_attr_list('dir')[0] == 'row':
    new_dir = 'col'
  else:
    new_dir = 'row'
  # A bit of a hack: other conditions not checked here because value will be
  # validated during instantiation
  
  replacements = []
  for idx, elt in enumerate(parsed_element.get_attr_list('cells')):
    if isinstance(elt, list):
      new_attr_map = {'cells': elt, 'dir': new_dir, 'frame_style': 'none'}
      new_elt = ParsedElement.ParsedElement('LineGrid', new_attr_map,
                                            parsed_element.filename,
                                            parsed_element.lineno)
      registry.apply_default_template(new_elt)
      desugar_multilinegrid(new_elt, registry)
      replacements.append((idx, new_elt))
  for idx, new_elt in replacements:
    parsed_element.attr_map['cells'][idx] = new_elt
  