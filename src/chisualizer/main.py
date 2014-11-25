import argparse
import logging
import os
import sys

try:  
  import wx
  import wx.lib.wxcairo
  import cairo
  haveWxCairo = True
except:
  haveWxCairo = False

from chisualizer.circuit.DummyCircuit import DummyCircuit
from chisualizer.circuit.ChiselEmulatorSubprocess import ChiselEmulatorSubprocess
from chisualizer.descriptor.YamlDescriptor import YamlDescriptor

from chisualizer.ui.Manager import ChisualizerManager

def run():
  if not haveWxCairo:
    print "Chisualizer requires wxPython, PyCairo, and wxCairo to run."
    sys.exit(1)
    
  parser = argparse.ArgumentParser(description="Chisualizer, a block-diagram-style RTL visualizer")
  parser.add_argument('--emulator', '-e', required=True,
                      help="Command to invoke the Chisel API compliant emulator with (or 'dummy').")
  parser.add_argument('--emulator_args', '-a', nargs='*',
                      help="Arguments to pass into the emulator.")
  parser.add_argument('--visualizer_desc', '-d', required=True,
                      help="Path to the visualizer descriptor XML file.")
  parser.add_argument('--emulator_reset', metavar='-r', type=bool, default=True,
                      help="Whether or not to reset the emulator circuit on start.")
  parser.add_argument('--log_level', metavar='-l', default="info",
                      choices=['error', 'warning', 'info', 'debug'],
                      help="Logging verbosity level.")
  args = parser.parse_args()
  
  if args.log_level == 'error':
    logging.getLogger().setLevel(logging.ERROR)
  elif args.log_level == 'warning':  
    logging.getLogger().setLevel(logging.WARNING)
  elif args.log_level == 'info':
    logging.getLogger().setLevel(logging.INFO)
  elif args.log_level == 'debug':
    logging.getLogger().setLevel(logging.DEBUG)
  else:
    assert False
    
  if args.emulator == "dummy":  
    api = DummyCircuit()
  else:
    emulator_cmd_list = [args.emulator]
    if args.emulator_args:
      emulator_cmd_list.extend(args.emulator_args)
    api = ChiselEmulatorSubprocess(emulator_cmd_list, reset=args.emulator_reset)
  
  vis_descriptor = YamlDescriptor()
  vis_descriptor.read_descriptor(os.path.dirname(__file__) + "/vislib.yaml")
  vis_descriptor.read_descriptor(args.visualizer_desc)

  ChisualizerManager(vis_descriptor, api).run()

if __name__ == "__main__":
  run()
  