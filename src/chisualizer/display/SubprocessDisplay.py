import logging
import subprocess

from chisualizer.Base import xml_register
from DisplayBase import DisplayBase

@xml_register('SubprocessDisplay')
class SubprocessDisplay(DisplayBase):
  @classmethod
  def from_xml_cls(cls, element, parent):
    new = super(SubprocessDisplay, cls).from_xml_cls(element, parent)
    new.subprocess = element.get('subprocess', None)
    if not new.subprocess:
      new.parse_error("No subprocess specified")
    try:
      #TODO: avoid creating duplicate subprocesses of the same name
      new.p = subprocess.Popen(new.subprocess,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
      #TODO: gracefully close subprocesses somewhere?
    except OSError as e:
      new.parse_error("Failed to open subprocess %s: %s" % (new.subprocess, e))
    
    new.length = new.parse_element_int(element, 'length', 0)
    
    new.cmd_to_text = element.get('cmd_to_text', None)
    new.cmd_from_text = element.get('cmd_from_text', None)
    
    return new
  
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
  