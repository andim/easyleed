Intro
=====

The intensity of diffraction maxima in low energy electron diffraction patterns changes with the energy of the incident beam. By varying the beam energy and recording the intensity of the maxima at each step, structural information about the analyzed surface can be obtained. The purpose of the Easyleed program is to facilitate the extraction of intensity-energy spectra from the experimental images. 

The user selects the spots he wants to track and the software then tries to automatically track the spots throughout all beam energies. The tracking relies on a method combining the knowledge about the movement of the spots with detected spot positions.

.. image:: /_static/illustration.*
    :scale: 75%

Development of Easyleed was started by Andreas Mayer while working in Renee Diehl's lab (Penn State). Hanna Salopaasi has since continued working on Easyleed in Katariina Pussi's lab (Lappeenranta University of Technology). We continue to work on facilitating LEED pattern analysis and therefore appreciate any form of user feedback! 

Download 
=========
Easyleed is open-source software licensed under the GPL v2. The software can be downloaded as a zip-file (:download:`Download ZIP-File <_static/source.zip>`, last update |today|). Alternatively the developer version of the code can be obtained by cloning the git repository: `<https://github.com/andim/easyleed/>`_

Installation
============

After downloading the zip-file extract its content to a directory. If you have already installed the dependencies, you are ready to go and can open the graphical user interface by running ``run-gui.py``.

Dependencies
============

Easyleed is written in `Python <http://www.python.org/>`_ and relies on the following libraries:

- Python >2.6 `<http://www.python.org/>`_
- Qt 4.6 `<http://qt.nokia.com/>`_ and PyQt 4.7 `<http://www.riverbankcomputing.co.uk/>`_
- Numpy >1.5 and Scipy >0.9 `<http://www.scipy.org/>`_
- Matplotlib >0.9 `<http://matplotlib.org/>`_
- PyFITS, if you intend to use fits-files as an image input format `<http://www.stsci.edu/resources/software_hardware/pyfits/>`_

Under Windows a simple way to get all the required python packages at once is to install the Python distribution `Python(x,y) <http://code.google.com/p/pythonxy/>`_.

Documentation
=============

.. toctree::
   :maxdepth: 1
   
   userdoc
   api
   
Citing Easyleed
===============

We have described the algorithm, which is implemented in Easyleed in the following article (:download:`Download Bibtex-File<easyleed.bib>`):

A. Mayer, H. Salopaasi, K. Pussi, R.D. Diehl. A novel method for the extraction of intensity-energy spectra from low-energy electron diffraction patterns. Comput. Phys. Commun. 183, 1443-1447 (2012)

You can view the paper using this DOI link: `doi:10.1016/j.cpc.2012.02.019 <http://dx.doi.org/10.1016/j.cpc.2012.02.019>`_ 

