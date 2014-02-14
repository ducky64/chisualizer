import subprocess

from ChiselApi import ChiselApi

class ChiselEmulatorSubprocess(ChiselApi):
  def __init__(self, emulator_path):
    """Starts the emulator subprocess."""
    self.p = subprocess.Popen(emulator_path,
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)

  def command(self, cmd):
    """Sends a command to the emulator, and returns the output string."""
    # sanity check - extra newlines will break the protocol
    if cmd.find('\n') != -1:
      raise ValueError("Command contains unexpected newline: " + cmd)
    self.p.stdin.write(cmd.strip() + "\n")
    self.p.stdin.flush();
    out = self.p.stdout.readline().strip()
    return out;
