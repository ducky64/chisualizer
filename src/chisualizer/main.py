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
from chisualizer.circuit.VcdCircuit import VcdCircuit
from chisualizer.descriptor.YamlDescriptor import YamlDescriptor

from chisualizer.ui.Manager import ChisualizerManager

def run():
  if not haveWxCairo:
    print "Chisualizer requires wxPython, PyCairo, and wxCairo to run."
    sys.exit(1)
    
  parser = argparse.ArgumentParser(description="Chisualizer, a block-diagram-style RTL visualizer")
  parser.add_argument('--emulator', '-e',
                      help="Command to invoke the Chisel API compliant emulator with (or 'dummy').")
  parser.add_argument('--emulator_args', '-a', nargs='*',
                      help="Arguments to pass into the emulator.")
  parser.add_argument('--vcd',
                      help="VCD file to view.")
  parser.add_argument('--vcd_start_cycle', type=int, default=0,
                      help="VCD start cycle (post-scaling).")
  parser.add_argument('--vcd_timescale', type=int, default=1,
                      help="Divide all VCD times by this amount.")
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
    
  if args.emulator and args.vcd:
    raise ValueError("Cannot specify both a VCD and emulator")
  elif args.emulator:
    if args.emulator == "dummy":  
      circuit = DummyCircuit()
    else:
      emulator_cmd_list = [args.emulator]
      if args.emulator_args:
        emulator_cmd_list.extend(args.emulator_args)
        print emulator_cmd_list
      circuit = ChiselEmulatorSubprocess(emulator_cmd_list, reset=args.emulator_reset)
  elif args.vcd:
    circuit = VcdCircuit(args.vcd, timescale_divisor=args.vcd_timescale,
                         start_cycle=args.vcd_start_cycle) 
  else:
    raise ValueError("Must specify either emulator executable path or VCD file")
  
  vis_descriptor = YamlDescriptor()
  vis_descriptor.read_descriptor(os.path.dirname(__file__) + "/vislib.yaml")
  vis_descriptor.read_descriptor(args.visualizer_desc)

  ChisualizerManager(vis_descriptor, circuit).run()

if __name__ == "__main__":
  run()
  