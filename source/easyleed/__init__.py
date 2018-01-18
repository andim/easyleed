"""
The EasyLEED package is divided into several subpackages:

- base: Core functionality (fitting procedures, Tracker class, etc.)
- kalman: Implementation of Kalman filter classes
- io: Input/Output functionality (reading FITS, PIL, and IMG files)
- gui: Graphical User Interface

.. automodule:: easyleed.base
    :members:

.. automodule:: easyleed.kalman
    :members:

.. automodule:: easyleed.io
    :members:

.. automodule:: easyleed.gui
    :members:

"""

__version__ = "2.5.1"
__author__ = "Andreas Mayer, Hanna Salopaasi, Nicola Ferralis"

from .defaultconfig import *
import os.path

config = Configuration()
if os.path.isfile(config.configFile) is False:
    print("Configuration file does not exist: Creating one.")
    config.createConfig()
config.readConfig(config.configFile)

import logging
logging.basicConfig(filename=config.loggingFilename, level=int(config.loggingLevel))
logger = logging.getLogger()

from . import defaultconfig
from . import gui

from . import kalman
from . import io
from . import base
from . import test
from . import qt
from . import gui
