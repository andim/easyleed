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
    variant = 'pyqt'
elif env_api in ['pyside', 'pyqt']:
    variant = env_api 
else:
    raise ImportError('unrecognized python Qt bindings')
# This will be passed on to new versions of matplotlib
os.environ['QT_API'] = variant

if variant == 'pyside':
    from PySide import QtCore, QtGui, QtNetwork, QtSvg
    sys.modules[__name__ + '.QtCore'] = QtCore
    sys.modules[__name__ + '.QtGui'] = QtGui
    sys.modules[__name__ + '.QtNetwork'] = QtNetwork
    sys.modules[__name__ + '.QtSvg'] = QtSvg
    try:
        from PySide import QtOpenGL
        sys.modules[__name__ + '.QtOpenGL'] = QtOpenGL
    except ImportError:
        pass
    try:
        from PySide import QtWebKit
        sys.modules[__name__ + '.QtWebKit'] = QtWebKit
    except ImportError:
        pass
    QtCore.QT_VERSION_STR = QtCore.__version__
    QtCore.QT_VERSION = tuple(int(c) for c in QtCore.__version__.split('.'))    
    for attr in ['pyqtSignal', 'pyqtSlot', 'pyqtProperty']:
        if not hasattr(QtCore, attr):
            eval("QtCore.{} = QtCore.{}".format(attr[4:], attr))
    def QtLoadUI(uifile, obj=None):
        from PySide import QtUiTools
        loader = QtUiTools.QUiLoader()
        uif = QtCore.QFile(uifile)
        uif.open(QtCore.QFile.ReadOnly)
        result = loader.load(uif, obj)
        uif.close()
        return result
elif variant == 'pyqt':
    from PyQt4 import QtCore, QtGui, QtNetwork, QtSvg
    sys.modules[__name__ + '.QtCore'] = QtCore
    sys.modules[__name__ + '.QtGui'] = QtGui
    sys.modules[__name__ + '.QtNetwork'] = QtNetwork
    sys.modules[__name__ + '.QtSvg'] = QtSvg
    try:
        from PyQt4 import QtOpenGL
        sys.modules[__name__ + '.QtOpenGL'] = QtOpenGL
    except ImportError:
        pass
    try:
        from PyQt4 import QtWebKit
        sys.modules[__name__ + '.QtWebKit'] = QtWebKit
    except ImportError:
        pass
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot
    QtCore.Property = QtCore.pyqtProperty
    QtCore.QString = str
    def QtLoadUI(uifile, obj=None):
        from PyQt4 import uic
        return uic.loadUi(uifile, obj)
else:
    raise ImportError("Qt variant not specified")

def get_qt_binding_name():
    return variant

__all__ = [QtGui, QtCore, QtLoadUI, get_qt_binding_name]
