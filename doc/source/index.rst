Intro
=====

The intensity of diffraction maxima in low energy electron diffraction patterns changes with the energy of the incident beam. By varying the beam energy and recording the intensity of the maxima at each step, structural information about the analyzed surface can be obtained. The purpose of the EasyLEED program is to facilitate the extraction of intensity-energy spectra from the experimental images. 

The user selects the spots he wants to track and the software then tries to automatically track the spots throughout all beam energies. An algorithm to determine the position of a spot in an image from the intensity information is combined with a dynamical model of the spot movement between successive beam energies to yield superior tracking performance.

.. image:: /_static/illustration.*
    :scale: 75%


Installation
============

Download 
--------

EasyLEED is open-source software licensed under the GPL v2. The software can be downloaded as a zip-file (:download:`Download ZIP-File <_static/source.zip>`, last update |today|). Alternatively the developer version of the code can be obtained by cloning the git repository: `<https://github.com/andim/easyleed/>`_

Dependencies
------------

EasyLEED is written in `Python <http://www.python.org/>`_ and relies on the following libraries:

- Python 2.6 or 2.7 `<http://www.python.org/>`_
- Qt 4.6 `<http://qt.nokia.com/>`_ and PyQt 4.7 `<http://www.riverbankcomputing.co.uk/>`_
- Numpy >1.5 and Scipy >0.9 `<http://www.scipy.org/>`_
- Matplotlib >0.9 `<http://matplotlib.org/>`_ 

Dependent on the file format of your input LEED images, you should also install the following packages:

- Python Imaging Library (for .tif, .png, .jpg) http://www.pythonware.com/products/pil/
- PyFITS (for .fits) `<http://www.stsci.edu/resources/software_hardware/pyfits/>`_

Installing dependencies on Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest way to get all the required python packages at once is to install the Python distribution `Python(x,y) <http://code.google.com/p/pythonxy/>`_.


Installing dependencies on Mac OSX
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All required packages can be obtained through `MacPorts <http://www.macports.org/>`_. After installing macports, individual libraries are installed with the following:

::

    sudo port install py-pyqt4
    sudo port install py-numpy
    sudo port install py-scipy
    sudo port install py-matplotlib
    sudo port install py-pil 


Run
---

After downloading the zip-file extract its content to a directory. If you have already installed the dependencies, you are ready to go and can open the graphical user interface by running ``run-gui.py``. In Unix systems (such as Mac OS X), you can run it from the terminal with the command: python2.7 run-gui.py


Documentation
=============

.. toctree::
   :maxdepth: 1
   
   userdoc
   api

   
Developer Team
===============

Development of EasyLEED was started by Andreas Mayer while working in Renee Diehl's lab (Penn State). Hanna Salopaasi has contributed to the user interface while working in Katariina Pussi's lab (Lappeenranta University of Technology). Further UI and core improvements are currently contributed by Nicola Ferralis (Massachusetts Institute of Technology). We continue to work on facilitating LEED pattern analysis and therefore appreciate any form of user feedback! 

Citing EasyLEED
===============


We have described the algorithm, which is implemented in EasyLEED in the following article (:download:`Download Bibtex-File<easyleed.bib>`):

A. Mayer, H. Salopaasi, K. Pussi, R.D. Diehl. A novel method for the extraction of intensity-energy spectra from low-energy electron diffraction patterns. Comput. Phys. Commun. 183, 1443-1447 (2012)

The paper is available `online <http://dx.doi.org/10.1016/j.cpc.2012.02.019>`_ at the publisher's website. If you are unable to access the paper at your institution, feel free to contact us via email for a preprint.
