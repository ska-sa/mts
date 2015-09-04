import iniparse

## Script for easy parsing of mts_default config file

class conf:
  def __init__(self, config_file):
    self.cp = iniparse.INIConfig(open(config_file, 'rb'))
  def get_param(self, section, parameter):
    return self.cp[section][parameter]
  def get_float(self, section, parameter):
    return float(self.get_param(section, parameter))
  def get_int(self, section, parameter):
    return int(self.get_param(section, parameter))
  def get_str(self, section, parameter):
    return self.get_param(section, parameter).strip('\'')

# -fin-
