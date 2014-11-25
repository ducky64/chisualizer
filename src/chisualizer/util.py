class Rectangle:
  def __init__(self, point1, point2):
    self._left = min(point1[0], point2[0])
    self._right = max(point1[0], point2[0])
    self._top = min(point1[1], point2[1])
    self._bottom = max(point1[1], point2[1])

  def top(self):
    return self._top

  def bottom(self):
    return self._bottom

  def left(self):
    return self._left
  
  def right(self):
    return self._right
  
  def center_horiz(self):
    return (self.left() + self.right()) / 2
  
  def center_vert(self):
    return (self.bottom() + self.top()) / 2
  
  def height(self):
    return abs(self.top() - self.bottom())
  
  def width(self):
    return abs(self.right() - self.left())

  def centered_origin(self):
    return Rectangle((self.left() - self.center_horiz(),
                      self.top() - self.center_vert()),
                     (self.right() - self.center_horiz(),
                     self.bottom() - self.center_vert()))

  def aligned_bottom(self, coord):
    return self.translated(0, -self.bottom() + coord)

  def aligned_top(self, coord):
    return self.translated(0, -self.top() + coord)

  def aligned_left(self, coord):
    return self.translated(-self.left() + coord, 0)

  def aligned_right(self, coord):
    return self.translated(-self.right() + coord, 0)

  def translated(self, dx, dy):
    return Rectangle((self.left() + dx, self.top() + dy),
                     (self.right() + dx, self.bottom() + dy))

  def shrink(self, left, top, right, bottom):
    return Rectangle((self.left() + left,
                      self.top() + top),
                     (self.right() - right,
                      self.bottom() - bottom))

  def contains(self, point_x, point_y):
    if (self._left <= point_x and self._right >= point_x and 
        self._top <= point_y and self._bottom >= point_y):
      return True
    else:
      return False 
