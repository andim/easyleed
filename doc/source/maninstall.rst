Manual Installation
===================

Download 
--------

EasyLEED is open-source software licensed under the GPL v2. The software can be downloaded as a zip-file (:download:`Download ZIP-File <_static/source.zip>`, last update |today|). Alternatively the developer version of the code can be obtained by cloning the git repository: `<https://github.com/andim/easyleed/>`_

Dependencies
------------

EasyLEED is written in `Python <http://www.python.org/>`_ and relies on the following libraries:

- Python 2.7 or 3.5/3.6 `<http://www.python.org/>`_
- Qt4 or Qt5 `<http://qt.nokia.com/>`_, along with either the respective PyQt version `<http://www.riverbankcomputing.co.uk/>`_ or PySide `<https://wiki.qt.io/Category:LanguageBindings::PySide>`_
- Numpy >1.5 and Scipy >0.9 `<http://www.scipy.org/>`_
- Matplotlib >0.9 `<http://matplotlib.org/>`_ 

Dependent on the file format of your input LEED images, you should also install the following packages:

- Pillow (for .tif, .png, .jpg) `<https://python-pillow.github.io/>`_
- PyFITS (for .fits) `<http://www.stsci.edu/resources/software_hardware/pyfits/>`_

Installing dependencies on Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest way to get all the required python packages at once is to install the Python distribution `Anaconda <https://www.continuum.io/downloads/>`_.


Installing dependencies on Mac OSX
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All required packages can be obtained through `MacPorts <http://www.macports.org/>`_. After installing macports, individual libraries are installed with the following:

::

    sudo port install py-pyqt4
    sudo port install py-numpy
    sudo port install py-scipy
    sudo port install py-matplotlib
    sudo port install py-pillow 

Run
---

After downloading the zip-file extract its content to a directory. If you have already installed the dependencies, you are ready to go and can open the graphical user interface by running ``easyleed``.
