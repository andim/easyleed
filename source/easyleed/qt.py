"""
easyleed.qt
------------

A Qt API selector that can be used to switch between PyQt and PySide wrappers.

Thanks to Liam Deacon for this workaround.

See also https://github.com/matplotlib/matplotlib/blob/master/lib/matplotlib/backends/qt_compat.py
"""

import sys
import os
from . import logger

env_api = os.environ.get('QT_API', 'pyqt')
if '--pyside' in sys.argv:
    variant = 'pyside'
elif '--pyqt4' in sys.argv:
    variant = 'pyqt4'
elif '--pyqt5' in sys.argv:
    variant = 'pyqt5'
elif env_api in ['pyside', 'pyqt']:
    variant = env_api 
else:
    raise ImportError('unrecognized python Qt bindings')
# This will be passed on to new versions of matplotlib (name for pyqt4 is simply pyqt)
os.environ['QT_API'] = 'pyqt' if variant == 'pyqt4' else variant
logger.info("The chosen qt variant is %s." % variant)

if variant == 'pyside':
    from PySide import QtCore, QtGui
    QtCore.QT_VERSION_STR = QtCore.__version__
    QtCore.QT_VERSION = tuple(int(c) for c in QtCore.__version__.split('.'))    
elif variant == 'pyqt4':
    from PyQt4 import QtCore, QtGui
elif variant == 'pyqt5': 
    from PyQt5 import QtCore, QtGui, QtWidgets
elif variant == 'pyqt':
    try:
        from PyQt5 import QtCore, QtGui, QtWidgets
        variant = 'pyqt5'
    except:
        from PyQt4 import QtCore, QtGui
        variant = 'pyqt4'
    logger.info("Qt variant specified as pyqt, using %s." % variant)
else:
    raise ImportError("Qt variant not specified")

sys.modules[__name__ + '.QtCore'] = QtCore
sys.modules[__name__ + '.QtGui'] = QtGui
sys.modules[__name__ + '.widgets'] = QtGui if variant == 'pyqt4' else QtWidgets
QtCore.QString = str

def get_qt_binding_name():
    return variant


def qt_filedialog_convert(output):
    try:
        # in qt5 returns are filename and filetype
        filename, filetype = output
    except ValueError:
        # in qt4 returns are filename only
        filename = output
    return filename if isinstance(filename, list) else str(filename)

__all__ = [QtGui, QtCore, get_qt_binding_name, qt_filedialog_convert]
