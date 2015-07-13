"""
easyleed.base
-------------

Base class providing common functionality for analyzing Leed patterns.

"""

import logging
logger = logging.getLogger("leedbase")

import numpy as np
from scipy import optimize
import math

from . import config
from . import kalman

class SpotModel:
    """ Data model for a Spot that stores all the information in various lists.
    """

    def __init__(self):
        self.x = []
        self.y = []
        self.intensity = []
        self.energy = []
        self.radius = []

    def update(self, x, y, intensity, energy, radius):
        self.x.append(x)
        self.y.append(y)
        self.intensity.append(intensity)
        self.energy.append(energy)
        self.radius.append(radius)

class Tracker:
    """ Tracks spots through intensity information and velocity prediction. """
    def __init__(self, x_in, y_in, radius, energy, x_c = None, y_c = None,
            input_precision = 1, window_scaling = False):
        """ x_in, y_in: start position of spot """
        self.radius = radius
        if x_c and y_c:
            x, y = x_in - x_c, y_in - y_c 
            r = (x**2 + y**2)**.5
            v = - 0.5 * r / energy
            # calculate std. dev. of velocity guess
            # by propagation of uncertainty from the input precision
            v_precision = 2**.5 * 0.5 * input_precision / energy
            phi = np.arctan2(y, x)
            cov_input = np.diag([input_precision, input_precision, v_precision, v_precision])**2
            self.kalman = kalman.PVKalmanFilter2(x_in, y_in, cov_input, energy, vx_in = v * np.cos(phi), vy_in = v * np.sin(phi))
        else:
            cov_input = np.diag([input_precision, input_precision, 1000, 1000])
            self.kalman = kalman.PVKalmanFilter2(x_in, y_in, cov_input, energy)

        self.window_scaling = window_scaling
        if self.window_scaling:
            self.c_size = energy**0.5 * self.radius

    def feed_image(self, image):
        npimage, energy = image
        if config.GraphicsScene_intensTimeOn == False:
            if self.window_scaling:
                self.radius = self.c_size / energy**0.5
        if self.radius < config.Tracking_minWindowSize:
            self.radius = config.Tracking_minWindowSize
        if config.GraphicsScene_intensTimeOn == False:
            processNoise = np.diag([config.Tracking_processNoisePosition, config.Tracking_processNoisePosition,
                    config.Tracking_processNoiseVelocity, config.Tracking_processNoiseVelocity])
            self.kalman.predict(energy, processNoise)
        x_p, y_p = self.kalman.get_position()
        guess = guesser(npimage, x_p, y_p, self.radius)
        if guess is not None:
            x_th, y_th, guess_cov = guess
            # spot in validation region?  (based on residual covariance)
            if self.kalman.measurement_distance((x_th, y_th), guess_cov) > config.Tracking_gamma:
                print(" no spot in validation gate")
            else:
                self.kalman.update([x_th, y_th], guess_cov)
        x, y = self.kalman.get_position()
        intensity = calc_intensity(npimage, x, y, self.radius, background_substraction = config.Processing_backgroundSubstractionOn)
        return x, y, intensity, energy, self.radius

def guess_from_Gaussian(image, *args, **kwargs):
    """ Guess position of spot from a Gaussian fit. """
    # construct circle where data is fit
    radius = 0.5 * min(image.shape)
    distances = calc_distances(image.shape, radius - 0.5, radius - 0.5, radius)
    circle = distances <= radius**2

    # generate good guesses for the Gaussian distribution
    background = np.min(image)
    params = moments(image-background)
    params.append(background)
    errfunc = lambda p: np.ravel(gaussian2d(*p)(*np.indices(image.shape))[circle] - image[circle])
    # fit Gaussian
    try:
        output = optimize.leastsq(errfunc, params, full_output=True, maxfev=200)
    except:
      return None
    p_opt = output[0]
    p_cov = output[1]
    infodict = output[2]
    if infodict["nfev"] >= 150 or p_cov is None:
        print(" fit failed")
        return None
    # residual sum of squares sum (x_i - f_i)^2
    sum_of_squares_regression = (errfunc(p_opt)**2).sum()
    # variance of the data sum (x_i - <x>)^2
    sum_of_squares_total = ((image-np.mean(image))**2).sum()
    # calculate R^2
    Rsq = 1 - sum_of_squares_regression / sum_of_squares_total
    if Rsq < config.Tracking_minRsq:
        print(" Rsq to low")
        return None
    # estimate sigma^2 from a chi^2 equivalent
    s_sq = sum_of_squares_regression/(len(image.flatten())-len(params))
    p_cov *= s_sq
    p_cov = p_cov[1:3, 1:3]
    x_res = p_opt[1]
    y_res = p_opt[2]
    return (x_res, y_res), p_cov

def guesser(npimage, x_in, y_in, radius, func = eval(config.Tracking_guessFunc), fit_region_factor = config.Tracking_fitRegionFactor):
    def failure(reason):
        logger.info(" no guess, because " + reason)
        print(reason)
        return None

    # try to get patch from image around estimated position
    try:
        x_min, x_max, y_min, y_max = adjust_slice(npimage, x_in - fit_region_factor * radius, x_in + fit_region_factor * radius + 1,
                                     y_in - fit_region_factor * radius, y_in + fit_region_factor * radius + 1)
    except IndexError:
       return failure(" position outside image")
    image = npimage[y_min : y_max, x_min : x_max]

    result = func(image, x_mid = x_in - x_min, y_mid = y_in - y_min, size = radius)
    if result is None:
        return failure(" fit failed")
    pos, cov = result
    y_res, x_res = pos
    x_res += x_min
    y_res += y_min

    return x_res, y_res, cov
    
def gaussian2d(height, center_x, center_y, width_x, width_y = None,
                offset=0):
    """Returns a two dimensional gaussian function with the given parameters"""
    if width_y is None:
        width_y = width_x
    return lambda x, y: np.asarray(height * np.exp(-(((center_x - x) / width_x)**2 + \
                        ((center_y - y) / width_y)**2) / 2)) + \
                        offset

def moments(data):
    """ Calculates the moments of 2d data.
    Returns [height, x, y, width_x, width_y]
    the gaussian parameters of a 2D distribution by calculating its
    moments. """
    total = data.sum()
    X, Y = np.indices(data.shape)
    x = (X*data).sum()/total
    y = (Y*data).sum()/total
    if math.isnan(x) == True:
        x = 0
    if math.isnan(y) == True:
        y = 0
    col = data[:, int(y)]
    width_x = np.sqrt(abs((np.arange(col.size)-y)**2*col).sum()/col.sum())
    row = data[int(x), :]
    width_y = np.sqrt(abs((np.arange(row.size)-x)**2*row).sum()/row.sum())
    height = data.max()
    return [height, x, y, width_x, width_y]

def adjust_slice(image, x_sl_min, x_sl_max, y_sl_min, y_sl_max):
    """
    Adjusts slice if it is trying to get pieces outside the image.

    >>> image = np.ones((2, 2))
    >>> adjust_slice(image, 0, 1.5, 0, 2)
    (0, 1, 0, 2)
    >>> adjust_slice(image, -5.5, 2, -0.5, 10)
    (0, 2, 0, 2)
    """

    ymax, xmax = image.shape
    adjusted = False
    indices = [int(x_sl_min), int(x_sl_max), int(y_sl_min), int(y_sl_max)]
    for i, value in enumerate(indices):
        if value < 0:
            indices[i] = 0
            adjusted = True
    for i, value in enumerate(indices):
        if i < 2:
            if value > xmax:
                indices[i] = xmax
                adjusted = True
        else:
            if value > ymax:
                indices[i] = ymax
                adjusted = True
    if adjusted:
        logger.warning(" slice had to be adjusted to fit image.")
    if not int(indices[0] - indices[1]) or not int(indices[2] - indices[3]):
        raise IndexError()
    return tuple(indices)

def calc_distances(shape, x, y, squared = True):
    """
    Helper function that returns an array of distances to x, y.
    This array can be useful for fancy indexing of numpy arrays.

    squared: return the squared distance (default: True)
    """
    yind, xind = np.indices(shape)
    distSquare = ((yind - y)**2 + (xind - x)**2)
    if not squared:
        return distSquare**.5
    return distSquare

def signal_to_background(npimage, x, y, radius):
    distSquare = calc_distances(npimage.shape, x, y)
    signal = np.mean(npimage[distSquare <= radius**2])
    # average background intensity over annulus with equal area
    background = np.mean(npimage[np.logical_and(distSquare >= radius**2, distSquare <= 2 * radius**2)])
    return signal/background
  
def calc_intensity(npimage, x, y, radius, background_substraction=config.Processing_backgroundSubstractionOn):
    """ Calculates the intensity of a spot.
        
        npimage: numpy array of intensity values
        x, y: position of the spot
        radius: radius of the spot
        background_substraction: boolean to turn substraction on/off
    """
    distSquare = calc_distances(npimage.shape, x, y, squared = True)
    intensities = npimage[distSquare <= radius**2]
    intensity = np.sum(intensities)
    if background_substraction:
        # average background intensity over annulus with approximately equal area
        background_intensities = npimage[np.logical_and(distSquare >= radius**2, distSquare <= 2 * radius**2)]
        area = len(intensities)
        intensity -= np.mean(background_intensities) * area
    return intensity
