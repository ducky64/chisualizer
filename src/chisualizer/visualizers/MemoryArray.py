import sys
import logging

import chisualizer.Base as Base
from VisualizerBase import Rectangle
from Data import Data

@Base.xml_register('MemoryArray')
class MemoryArray(Data):
  """A grid of cells, each pointing to a memory element."""
  def __init__(self, element, parent):
    super(MemoryArray, self).__init__(element, parent)
    self.step = element.get_attr_string('step', valid_set=['row', 'col'])
        
    self.offset = element.get_attr_int('offset', valid_min=0)
    self.offset_anchor = element.get_attr_float('offset_anchor',
                                                valid_min=0, valid_max=1)
    self.rows = element.get_attr_int('rows', valid_min=1)
    self.cols = element.get_attr_int('cols', valid_min=1)
    self.cells_count = self.rows * self.cols
    
    if len(element.get_children()) != 1:
      element.parse_error("Must have exactly one child")
      
    self.cell_elt = element.get_children()[0]
    
    self.cells_min = -1
    self.cells_max = -1
    self.cells = []

  def update_cells(self):
    def instantiate_cell(addr):
      inst = self.cell_elt.instantiate(self)
      inst.set_node(self.node.get_subscript_reference(addr))
      # TODO: dehackify
      inst.path_component += "[%i]" % addr
      inst.path += "[%i]" % addr
      if inst.label is None: inst.label = str(addr)
      return inst
    
    def instantiate_cells(inst_min, inst_max):
      ary = []
      assert inst_min <= inst_max
      for i in xrange(inst_min, inst_max+1):
        ary.append(instantiate_cell(i))
      assert len(ary) == inst_max - inst_min + 1
      return ary
    
    render_min = self.offset - int(self.offset_anchor * self.cells_count)
    render_max = render_min + self.cells_count - 1
    
    if render_min < 0:
      render_max += 0 - render_min
      render_min = 0
    if render_max >= self.node.get_depth():
      render_min += render_max - (self.node.get_depth()-1)
      render_max = self.node.get_depth() - 1
    if render_min < 0:
      render_min = 0
      
    if render_max == self.cells_max and render_min == self.cells_min:
      # If rendering range exactly the same, nothing needs to be done.
      return
    elif render_max >= self.cells_min or render_min <= self.cells_max:
      # If rendering range overlaps, fix the edges
      pre = []
      post = []
      if render_min < self.cells_min:
        # rendering range overlaps with current, but need extra before
        pre = instantiate_cells(render_min, self.cells_min - 1)
      if render_max > self.cells_max:
        # rendering range overlaps with current, but need extra after
        post = instantiate_cells(self.cells_max + 1, render_max)
                
      if self.cells_max > render_max:
        # currently too many cells after
        for _ in xrange(self.cells_max - render_max):
          self.cells.pop(-1)
      if self.cells_min > render_min:
        # currently too many cells after
        for _ in xrange(self.cells_min - render_min):
          self.cells.pop(-1)        
      self.cells[:0] = pre
      self.cells.extend(post)
    else:
      # If rendering range completely disjoint, nuke it from orbit.
      self.cells = instantiate_cells(render_min, render_max)
    
    self.cells_min = render_min
    self.cells_max = render_max
    assert len(self.cells) == self.cells_count
    assert len(self.cells) == self.cells_max - self.cells_min + 1
    
    
  def layout_element_cairo(self, cr):
    self.update_cells()
    
    self.cell_x = 0
    self.cell_y = 0
    for cell in self.cells:
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

    minor_pos = 0
    cells = []

    for element in self.cells:
      cell_rect = Rectangle((pos_x, pos_y),
                            (pos_x + self.cell_x, pos_y + self.cell_y))
      cells.extend(element.draw_cairo(cr, cell_rect, depth + 1))
      
      if self.step == "row":
        pos_x += self.cell_x
        minor_pos += 1
        if minor_pos == self.cols:
          pos_x = origin_x
          pos_y += self.cell_y
          minor_pos = 0
      elif self.step == "col":
        pos_y += self.cell_y
        minor_pos += 1
        if minor_pos == self.rows:
          pos_y = origin_y
          pos_x += self.cell_x
          minor_pos = 0
      else:
        assert False
        
    return cells
  