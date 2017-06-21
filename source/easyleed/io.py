"""
easyleed.io
-------------

Import routines for different LEED file formats

"""

import numpy as np
from .qt import QtGui as qtgui

# load regular expression package (for parsing of energy from file name)
import re
import os.path

from . import logger

#### load packages for available file types ####
formats_available = ['IMG']
try:
    import pyfits
    formats_available.append("FITS")
except:
    logger.warning("The pyfits package is not installed.")
# try to import PIL in two possible ways (dependent on PIL version)
try:
    from PIL import Image
    formats_available.append("PIL")
except:
    try:
        import Image
        formats_available.append("PIL")
    except:
        logger.warning("The pillow package is not installed.")

class ImageLoader(object):
    """ Abstract base class for a class loading LEED images.

    Subclasses need to provide
        - get_image(image_path)

    Subclasses may override (default: from filename with regex)
        - get_energy(image_path)
    """
    def __init__(self, image_paths, regex):
        # build a dictionary with energy as key and imagePath as value
        self.regex = regex
        self.files = {}
        for image_path in image_paths:
            energy = self.get_energy(image_path)
            self.files[energy] = image_path
        self.energies = sorted(self.files.keys())
        self.restart()

    def get_energy(self, image_path):
        m = re.search(self.regex, image_path)
        if m is None:
            raise IOError('Invalid filename. Check naming policy.')
        return float(m.group())
   
    def current_energy(self):
        """ Get current energy. """
        return self.energies[self.index]

    def __iter__(self):
        return self

    def restart(self):
        """ Start at lowest energy again. """
        self.index = -1

    def previous(self):
        """ Get image at next lower beam energy. """
        if self.index == 0:
            raise StopIteration("there is no previous image")
        else:
            self.index -= 1
            energy = self.energies[self.index]
            return self.get_image(self.files[energy]), energy

    def __next__(self):
        """ Get image at next higher beam energy. """
        if self.index < len(self.energies)-1:
            self.index += 1
            energy = self.energies[self.index]
            return self.get_image(self.files[energy]), energy
        else:
            raise StopIteration()

    next = __next__

    def goto(self, energy):
        """ Get image at given beam energy. """
        self.index = self.energies.index(energy)
        return self.get_image(self.files[energy]), energy

    # FIXME: untested
    def custom_iter(self, energies):
        """ Returns an iterator to iter over the given energies."""
        non_elements = set(energies) - set(self.energies)
        if non_elements:
            raise Exception("ImageLoader doesn't have the following elements: %s" % (list(non_elements)))
        for energy in energies:
            yield self.get_image(energy), energy


class ImgImageLoader(ImageLoader):
    """ Load .img image files (HotLeed format). """

    extensions = ["img"]

    def get_energy(self, image_path):
        with open(image_path, "rb") as f:
            return self.load_header(f)["Beam Voltage (eV)"]
    
    @staticmethod
    def load_header(f):
        # find header length
        line = f.readline()
        while not b"Header length:" in line:
            line = f.readline()
        header_length = int(line.split(b": ")[1].strip())
        # jump back to beginning
        f.seek(0)
        # read in header
        header_raw = f.read(header_length)
        ## process header ##
        # dict containing names of all interesting entrys
        header = {b"Beam Voltage (eV)": 0, b"Date": "", b"Comment": "",
                  b"x1": 0, b"y1": 0, b"x2": 0, b"y2": 0, b"Number of frames": 0,
                  b'length' : header_length}
        headerlines = header_raw.split(b"\n")
        for line in headerlines:
            parts = line.split(b": ")
            if parts[0] in header.keys():
                # convert int entrys
                if type(header[parts[0]]) == type(1):
                    header[parts[0]] = int(parts[1])
                # convert string entrys
                elif type(header[parts[0]]) == type(""):
                    header[parts[0]] = parts[1].strip()
        return header

    @staticmethod
    def get_image(image_path):
        with open(image_path, "rb") as f:
            header = ImgImageLoader.load_header(f) 
            # jump to begin of image
            f.seek(header[b'length'])
            # read in image
            content = f.read()
            # make numpy array from image
            image = np.frombuffer(content, dtype=np.uint16)
            # calculate size of image from header information
            size = (header[b"y2"]-header[b"y1"]+1, header[b"x2"]-header[b"x1"]+1)
            # reshape image as 2d array
            image = image.reshape((size))
            return image


class FitsImageLoader(ImageLoader):
    """ Load .fits image files. """

    extensions = ["fit", "fits"]

    @staticmethod
    def get_image(image_path):
        hdulist = pyfits.open(image_path)
        data = hdulist[0].data
        hdulist.close()
        return data


class PILImageLoader(ImageLoader):
    """ Load image files supported by Python Imaging Library (PIL). """

    extensions = ["tif", "tiff", "png", "jpg", "bmp"]

    @staticmethod
    def get_image(image_path):
        im = Image.open(image_path)
        data = np.asarray(im.convert('L'), dtype=np.uint16)
        return data

class ImageFormat:
    """ Class describing an image format. """
    def __init__(self, abbrev, loader):
        """
        abbrev: abbreviation (e.g. FITS)
        loader: ImageLoader subclass for this format
        """
        self.abbrev = abbrev
        self.loader = loader
        self.extensions = loader.extensions

    def __str__(self):
        return "{0}-Files ({1})".format(self.abbrev, " ".join(self.extensions))

    def extensions_wildcard(self):
        return ['*.%s' % ext for ext in self.extensions]

""" Dictionary of available ImageFormats. """
IMAGE_FORMATS = [format_ for format_ in \
                    [ImageFormat("PIL", PILImageLoader),
                     ImageFormat("FITS", FitsImageLoader),
                     ImageFormat("IMG", ImgImageLoader)] \
                         if format_.abbrev in formats_available]

class AllImageLoader(ImageLoader):

    @staticmethod
    def supported_extensions():
        extensions = []
        for image_format in IMAGE_FORMATS:
            extensions.extend(image_format.extensions_wildcard())
        return extensions

    def get_image(self, image_path):
        extension = os.path.splitext(image_path)[1][1:]
        for image_format in IMAGE_FORMATS:
            loader = image_format.loader
            if extension in loader.extensions:
                return loader.get_image(image_path)
        raise IOError('The filetype is not supported')


def normalize255(array):
    """ Returns a normalized array of uint8."""
    nmin, nmax = array.min(), array.max()
    if nmin:
        array = array - nmin
    scale = 255.0 / (nmax - nmin)
    if scale != 1.0:
        array = array * scale
    return array.astype("uint8")


qtGreyColorTable = [qtgui.qRgb(i, i, i) for i in range(256)]

def npimage2qimage(npimage):
    """ Converts numpy grayscale image to qimage."""
    h, w = npimage.shape
    npimage = normalize255(npimage)
    # second w to avoid problems if image is not 32-bit aligned
    # --> indicates bytesPerLine
    qimage = qtgui.QImage(npimage.data, w, h, w, qtgui.QImage.Format_Indexed8)
    qimage.setColorTable(qtGreyColorTable)
    return qimage
