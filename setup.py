from distutils.core import setup, Extension
import os, sys, glob

__version__ = '0.1'

setup(name = 'mts',
      version = __version__,
      description = 'Interfaces to KAT-7 Correlator Test System',
      license = 'GPL',
      author = 'Ruby van Rooyen',
      requires=['valon_synth', 'serial', 'iniparse', 'inspect', 'signal', 'optparse', 'numpy'],
      provides=['mts'],
      package_dir = {'mts':'mts'},
      packages = ['mts'],
      scripts=glob.glob('scripts/*'),
      data_files=[('/etc/mts',['etc/mts_default', 'etc/cw_calib_table.data', 'etc/noise_calib_table.data'])]
)
