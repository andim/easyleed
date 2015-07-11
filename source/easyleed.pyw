#! /usr/bin/env python
import sys
from easyleed.qt.QtGui import QApplication
import easyleed

app = QApplication(sys.argv)
form = easyleed.gui.MainWindow()
form.show()
app.exec_()
