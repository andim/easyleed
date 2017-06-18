#! /usr/bin/env python

import sys
from .qt.widgets import QApplication
from .gui import MainWindow

def main():
    app = QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
