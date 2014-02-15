visualizer_registry = {}
def visualizer_register(cls, name=None):
  if name == None:
    name = cls.__name__
  if name in visualizer_registry:
    raise 

class Base:
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
  def fromXml(cls, parent, node):
    """Initializes this visualizer from a XML etree Element."""
    new = cls()
    new.root = parent.root
    new.parent = parent
    new.path_component = node.get('path', '')
    new.path = parent.path + new.path_component
  
  def clone(self, new_parent):
    """Recursively clones this visualizer to have a new root and parent."""
    cloned = self.__class__()
    cloned.root = new_parent.root
    cloned.parent = new_parent
    cloned.path_component = self.path_component
    cloned.path = new_parent.path + cloned.path_component
  
  def draw_cairo(self, rect, context):
    """Draw this object to the Cairo context.
    The point (0, 0) is the parent's anchor point for this object.
    rect indicates how much space was allocated for this object, in the
    coordinates of the given Cairo context.
    """
    raise NotImplementedError()
  
  def calculate_minimum_size(self):
    """Returns a tuple (x, y) of the minimum size of this object."""
    raise NotImplementedError()

  def get_actual_size(self):
    """Returns a tuple (x, y) of my actual size.
    Only valid after a call to calculate_minimum_size.
    """
    raise NotImplementedError()
  