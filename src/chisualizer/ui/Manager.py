import wx

from ChisualizerFrame import ChisualizerFrame

class ChisualizerManager(object):
  def __init__(self, visualizer_descriptor, circuit):
    self.visualizer_descriptor = visualizer_descriptor
    self.circuit = circuit
    
  def run(self):
    app = wx.App(False)
    ChisualizerFrame(None, "Chisualizer", self.circuit, self.visualizer_descriptor)
    app.MainLoop()
    