Intro
=====

The purpose of the Easyleed program is the extraction of intensity-energy spectra from low-energy electron diffraction patterns.

The method implemented in this software combines the knowledge about the movement of the spots with detected spot positions using a Kalman filter. More information about the algorithm can be found in our paper:

A. Mayer et al. A novel method for the extraction of intensity-energy spectra from low-energy electron diffraction patterns. Comput. Phys. Commun. 183, 1443-1447 (2012), `doi:10.1016/j.cpc.2012.02.019 <http://dx.doi.org/10.1016/j.cpc.2012.02.019>`_

Download and Installation
=========================

The newest version of the software can be downloaded as a zip-file:

:download:`Download Easyleed <_static/source.zip>`, last update |today|

After downloading this file extract its content to a directory. If you have already installed the dependencies (see below), you are ready to go and can open the graphical user interface by running ``run-gui.py``.

Easyleed is written in `Python <http://www.python.org/>`_ and relies on a number of libraries. The easiest way is to install the Python distribution `Python(x,y) <http://code.google.com/p/pythonxy/>`_, that contains all the libraries. Of course, you can also manually install everything. Here is a list of Easyleed's dependencies:

- Python >2.6 `<http://www.python.org/>`_
- Qt 4.6 `<http://qt.nokia.com/>`_ and PyQt 4.7 `<http://www.riverbankcomputing.co.uk/>`_
- Numpy >1.5 and Scipy >0.9 `<http://www.scipy.org/>`_
- Matplotlib >0.9 `<http://matplotlib.org/>`_

Depending on your input file type of choice you might need the following library:

- PyFITS, if you intend to use fits-files as an image input format `<http://www.stsci.edu/resources/software_hardware/pyfits/>`_

Documentation
=============

.. toctree::
   :maxdepth: 1
   
   userdoc
   api
