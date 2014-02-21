from chisualizer.Base import Base
from chisualizer.visualizers.VisualizerBase import VisualizerBase

@Base.xml_register('Grid')
class Grid(VisualizerBase):
  """Grid containing other visualizers."""
  pass
