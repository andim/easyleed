""" 
The EasyLEED package is divided into several subpackages:

- base: Core functionality (fitting procedures, Tracker class, etc.)
- kalman: Implementation of Kalman filter classes
- io: Input/Output functionality (reading FITS and IMG files)

.. automodule:: easyleed.base
    :members:

.. automodule:: easyleed.kalman
    :members:

.. automodule:: easyleed.io
    :members:

"""

__version__ = "1.1dev"
__author__ = "Andreas Mayer, Hanna Salopaasi, Nicola Ferralis"

# import packages
# order of loading is important and should not be changed
try:
    import sys
    sys.path.append('..')
    import config
except:
    import default_config as config
import kalman
import io
import base
import test
import gui
