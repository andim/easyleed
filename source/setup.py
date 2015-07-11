from distutils.core import setup

setup(
    name='EasyLEED',
    packages=['easyleed'],
    requires=['numpy', 'matplotlib', 'scipy', 'pillow', 'pyqt4'],
    scripts=['easyleed.pyw'],
    version='2.0',
    description='Automated extraction of intensity-energy spectra from low-energy electron diffraction patterns',
    long_description='EasyLEED is a software tool to help extract intensity-energy spectra from images of low-energy electron diffraction patterns. For more info please see https://andim.github.io/easyleed/ or contact the authors via Email (andisspam@gmail.com) or Twitter (https://twitter.com/andisspam)',
    author='Andreas Mayer, Hanna Salopaasi, Nicola Ferralis',
    author_email='andisspam@gmail.com',
    url='https://andim.github.io/easyleed/',
    download_url='https://github.com/andim/easyleed/tarball/2.0',
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
