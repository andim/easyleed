from distutils.core import setup

setup(
    name='EasyLEED',
    packages=['easyleed'],
    requires=['numpy', 'matplotlib', 'scipy', 'pillow', 'pyqt4'],
    scripts=['easyleed.pyw'],
    version='2.1',
    description='Automated extraction of intensity-energy spectra from low-energy electron diffraction patterns',
    long_description= """
EasyLEED facilitates data analysis of images obtained by low-energy electron diffraction, a common technique in surface science. It aims to automate the process of extracting intensity-energy spectra from a series of diffraction patterns acquired at different beam energies. At its core a tracking algorithm exploiting the specifics of the underlying physics (see `paper <http://dx.doi.org/10.1016/j.cpc.2012.02.019>`_) allows to link the position of the diffraction maxima between subsequent images.

For more info please see https://andim.github.io/easyleed/ or contact the authors via Email (andisspam@gmail.com) or Twitter (https://twitter.com/andisspam)
""",
    author='Andreas Mayer, Hanna Salopaasi, Nicola Ferralis',
    author_email='andisspam@gmail.com',
    url='https://andim.github.io/easyleed/',
    download_url='https://github.com/andim/easyleed/archive/2.1.tar.gz',
    keywords=['LEED', 'surface science', 'image analysis', 'I(E) spectra', 'spot tracking'],
    license='GPLv2',
    platforms='any',
    classifiers=[
     'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
     'Development Status :: 5 - Production/Stable',
     'Programming Language :: Python :: 2.7',
     'Intended Audience :: Science/Research',
     'Topic :: Scientific/Engineering :: Chemistry',
     'Topic :: Scientific/Engineering :: Physics',
     ],
)
