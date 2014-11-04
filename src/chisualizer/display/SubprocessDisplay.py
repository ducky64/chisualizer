import logging
import subprocess

from chisualizer.Base import xml_register
from DisplayBase import DisplayBase

@xml_register('SubprocessDisplay')
class SubprocessDisplay(DisplayBase):
  def __init__(self, element, parent):
    super(SubprocessDisplay, self).__init__(element, parent)
    self.subprocess = element.get_attr_string('subprocess')
    try:
      #TODO: avoid creating duplicate subprocesses of the same name
      self.p = subprocess.Popen(self.subprocess,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
      #TODO: gracefully close subprocesses somewhere?
    except OSError as e:
      element.parse_error("Can't open subprocess %s: %s" % (self.subprocess, e))
    
    self.length = element.get_attr_int('length', 1)

    self.cmd_to_text = element.get_attr_string('cmd_to_text')
    self.cmd_from_text = element.get_attr_string('cmd_from_text')

  def command(self, cmd):
    """Sends a command to the subprocess, and returns the output string.
    The expected protocol is that each command ends with a newline, and
    each response ends with a newline 
    """
    # sanity check - extra newlines will break the protocol
    assert isinstance(cmd, basestring)
    if cmd.find('\n') != -1:
      raise ValueError("Command contains unexpected newline: '%s'" % cmd)
        
    self.p.stdin.write(cmd + '\n')
    self.p.stdin.flush();
    out = self.p.stdout.readline().strip()
    logging.debug("SubprocessDisplay: '%s' -> '%s'", cmd, out)
    return out;
  
  def apply(self, node):
    if self.cmd_to_text:
      value = node.get_value()
      return {'text': self.command(self.cmd_to_text % value)} 
    else:
      return {}
  
  def set_from_text(self, node_ref, in_text):
    if self.cmd_from_text:
      ret = self.command(self.cmd_from_text % in_text)
      try:
        val = int(ret, 0)
        node_ref.set_value(val)
        return True
      except ValueError:
        pass
    super(SubprocessDisplay, self).set_from_text(node_ref, in_text)
  
  def get_longest_text(self, node_ref):
    return ['x'*self.length]
  