"""
easyleed.qt
------------

A Qt API selector that can be used to switch between PyQt and PySide wrappers.

Thanks to Liam Deacon for this workaround.
"""

import sys
import os

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
# This will be passed on to new versions of matplotlib
os.environ['QT_API'] = variant

if variant == 'pyside':
    from PySide import QtCore, QtGui
    QtCore.QT_VERSION_STR = QtCore.__version__
    QtCore.QT_VERSION = tuple(int(c) for c in QtCore.__version__.split('.'))    
elif variant == 'pyqt4':
    from PyQt4 import QtCore, QtGui
elif variant == 'pyqt5': 
    from PyQt5 import QtCore, QtGuiQtWidgets
elif variant == 'pyqt':
    try:
        from PyQt5 import QtCore, QtGui, QtWidgets
        variant = 'pyqt5'
    except:
        from PyQt4 import QtCore, QtGui
        variant = 'pyqt4'
else:
    raise ImportError("Qt variant not specified")

sys.modules[__name__ + '.QtCore'] = QtCore
sys.modules[__name__ + '.QtGui'] = QtGui
sys.modules[__name__ + '.widgets'] = QtGui if variant == 'pyqt4' else QtWidgets
QtCore.QString = str

def get_qt_binding_name():
    return variant

__all__ = [QtGui, QtCore, get_qt_binding_name]
