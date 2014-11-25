class VcdCircuit(object):
  def __init__(self, vcd_filename):
    super(VcdCircuit, self).__init__()
  
  def has_node(self, node):
    raise NotImplementedError
    
  def get_nodes_list(self):
    raise NotImplementedError
  
  def get_current_temporal_node(self):
    # TODO: refactor this out?
    raise NotImplementedError
      
  def get_current_view(self):
    raise NotImplementedError
      
  def get_historical_view(self):
    raise NotImplementedError
  
  def navigate_next_mod(self):
    pass  # No modifiable state in VCDs
  
  def navigate_prev_mod(self):
    pass  # No modifiable state in VCDs

  def navigate_back(self):
    pass
  
  def navigate_fwd(self, cycles=None):
    pass

  def reset(self, cycles):
    pass # No modifiable state in VCDs
