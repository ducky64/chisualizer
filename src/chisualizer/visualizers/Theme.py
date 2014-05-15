class Theme(object):
  """Returns the background (fill) color.
  """
  def background_color(self):
    return (0, 0, 0, 0)
    
  """Returns the default foreground color - which should provide a good
  visible contrast with the background fill. 
  """
  def default_color(self):
    return (0.5, 0.5, 0.5, 1)
  
  """Resolves a color map from a description to the actual color. Where
  possible, this should map colors taking into account the theme style.
  This should only be used for foreground colors.
  """
  def color(self, desc):
    theme_dict = {'default': self.default_color(),
                  'text': self.default_color(),
                  'border': self.default_color(),
                  
                  'black': (0, 0, 0, 1),
                  'red': (1, 0, 0, 1),
                  'yellow': (1, 1, 0, 1),
                  'green': (0, 1, 0, 1),
                  'cyan': (0, 1, 1, 1),
                  'blue': (0, 0, 1, 1),
                  'pink': (1, 0, 1, 1),
                  'white': (1, 1, 1, 1),
                  'grey': (.5, .5, .5, 1),
                       
                  'bool_0': (1, 0, 0, 1),
                  'bool_1': (0, 1, 0, 1),
                  }
    if desc in theme_dict:
      return theme_dict[desc]
    else:
      return self.default_color()
     
class DarkTheme(Theme):
  """Theme for use with black backgrounds."""
  def background_color(self):
    return (0, 0, 0, 1)
  
  def default_color(self):
    return (1, 1, 1, 1)
  
  def color(self, desc):
    theme_dict = {'border': (0, 0.4, 0.6),
                  
                  'bool_0': (1, .7, .7, 1),
                  'bool_1': (.7, 1, .7, 1),
                  }
    if desc in theme_dict:
      return theme_dict[desc]
    else:
      return super(DarkTheme, self).color(desc)
    
class LightTheme(Theme):
  """Theme for use with white backgrounds."""
  def background_color(self):
    return (1, 1, 1, 1)
  
  def default_color(self):
    return (0, 0, 0, 1)
  
  def color(self, desc):
    theme_dict = {'border': (.2, .5, .8),
                  
                  'bool_0': (.7, 0, 0, 1),
                  'bool_1': (0, .7, 0, 1),
                  }
    if desc in theme_dict:
      return theme_dict[desc]
    else:
      return super(LightTheme, self).color(desc)
    