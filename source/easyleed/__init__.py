""" 
The Easyleed package is divided into several subpackages:

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

__version__ = "1.0"
__author__ = "Andreas Mayer, Hanna Salopaasi"

# import packages
# order of loading is important and should not be changed
import default_config as config
import kalman
import io
import base
import test
import my_flatten
import gui
