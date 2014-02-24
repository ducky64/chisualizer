from chisualizer.Base import Base

class VisualizerBase(Base):
  """Abstract base class for Chisel visualizer objects."""
  
  class rect:
    def __init__(self, point1, point2):
      self.top = max(point1[1], point2[1])
      self.bottom = min(point1[1], point2[1])
      self.left = min(point1[0], point2[0])
      self.right = max(point1[0], point2[0])
  
    def top(self):
      return self.top
  
    def bottom(self):
      return self.bottom
  
    def left(self):
      return self.left
    
    def right(self):
      return self.right
  
  @classmethod
  def from_xml(cls, parent, node):
    new = super(VisualizerBase. self).from_xml(parent, node)
    new.root = parent.root
    new.parent = parent
    new.path_component = node.get('path', '')
    new.path = parent.path + new.path_component
    return new
  
  def instantiate(self, new_parent):
    """Instantiates this visualizer template by cloning the template and
    resolving all references. Acts as clone (to a new parent) if called by an
    already-instantiated object.
    """
    cloned = self.__class__()
    cloned.root = new_parent.root
    cloned.parent = new_parent
    cloned.path_component = self.path_component
    cloned.path = new_parent.path + cloned.path_component
    return cloned
  
  def get_chisel_api(self):
    """Returns the ChiselApi object used to access node values.
    Returns None if not available or if this visualizer wasn't properly
    instantiated."""
    if not self.root:
      return None
    return self.root.get_chisel_api()
  
  def draw_cairo(self, rect, context):
    """Draw this object to the Cairo context.
    The point (0, 0) is the parent's anchor point for this object.
    rect indicates how much space was allocated for this object, in the
    coordinates of the given Cairo context.
    """
    # future implementations may have more stuff in the base class, like
    # drawing labels or borders
    pass
  
  def calculate_minimum_size(self):
    """Returns a tuple (x, y) of the minimum size of this object."""
    raise NotImplementedError()
