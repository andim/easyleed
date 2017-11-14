
[![License](https://img.shields.io/pypi/l/easyleed.svg)](https://github.com/andim/easyleed/blob/master/LICENSE)
[![Latest release](https://img.shields.io/pypi/v/easyleed.svg)](https://pypi.python.org/pypi/easyleed)
[![Py2.7/3.x](https://img.shields.io/pypi/pyversions/easyleed.svg)](https://pypi.python.org/pypi/easyleed)
![Status](https://img.shields.io/pypi/status/easyleed.svg)


# EasyLEED : Automated extraction of intensity-energy spectra from LEED patterns.

EasyLEED facilitates data analysis of images obtained by low-energy electron diffraction, a common technique in surface science. It aims to automate the process of extracting intensity-energy spectra from a series of diffraction patterns acquired at different beam energies. At its core a tracking algorithm exploiting the specifics of the underlying physics (see [paper](http://dx.doi.org/10.1016/j.cpc.2012.02.019)) allows to link the position of the diffraction maxima between subsequent images.

See also http://andim.github.io/easyleed/. 

## Installation

EasyLEED is on [PyPI](https://pypi.python.org/pypi/easyleed/) so you can install it using `pip install easyleed`.

## Documentation

You can access the documentation [online](http://andim.github.io/easyleed/). If you install from source you can generate a local version by running `make html` from the `doc` directory.

## Support and contributing

For bug reports and enhancement requests use the [Github issue tool](http://github.com/andim/easyleed/issues/new), or (even better!) open a [pull request](http://github.com/andim/easyleed/pulls) with relevant changes. If you have any questions don't hesitate to contact the authors by email (andimscience@gmail.com, feranick@hotmail.com) or Twitter ([@andimscience](http://twitter.com/andimscience)).
