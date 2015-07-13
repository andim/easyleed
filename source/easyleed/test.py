from __future__ import division

from functools import partial
import itertools
import collections
import math
import logging
import time

import numpy as np
np.seterr(all="ignore")
import scipy.optimize

from .base import *

logging.basicConfig(level=logging.INFO)

#### background_funcs ####
class Background:
    """ Wraps a background function for easier construction and speeds things up for constant background"""
    def __init__(self, func, size, is_constant=False):
        self.is_constant = is_constant
        func = partial(func, size)
        if self.is_constant:
            self.image = func()
        else:
            self.func = func
    def __call__(self):
        if self.is_constant:
            return self.image.copy()
        else:
            return self.func()

def back_uniform(size, level=0):
    return np.ones(size) * level
    
def back_poisson(size, mu=1):
    return np.random.poisson(mu, size)

def back_normal(size, mu=2, sigma=1):
    return abs(sigma * np.random.randn(*size) + mu)

BACKGROUND_NORMAL = Background(partial(back_normal, mu=4, sigma=3), (400, 400), False)
#########################


#### intensity_funcs ####
def constant_factory(value, *args, **kwargs):
    return eat_args(next(itertools.repeat(value)))

def eat_args(func):
    def new(*args, **kwargs):
        return func()
    return new

def step_function(x, step_x = 100, value=1000):
    """ Heavyside step function making the step at step_x"""
    if x < step_x:
        return value
    else:
        return 0.0

def sine_intensity(x, freq=10, value=1000):
    omega = 2 * np.pi / freq
    return (0.5 * np.cos(omega * x) + 0.5) * value
#########################

#### energy_funcs ####
def linear(x, m=1.0, b=0.0):
    return m * x + b
#######################

def draw_gauss(x_spot, y_spot, sigma, npimage , integral = 1, multiplicator = None, sigma_cutoff = 4):
    """ Draw an gaussian spot at x_spot, y_spot with width sigma and integral intensity."""
    if multiplicator is None:
        multiplicator = integral / (2 * sigma**2 * np.pi)
    npimage += gaussian2d_rot(multiplicator, x_spot, y_spot, sigma)(*np.indices(npimage.shape))

class Spot:
    def __init__(self, start_point, end_point, energy, intensity_func=constant_factory(1000), size=3, variable_size=False, energy_func=float):
        """ start_points, end_point: array-like
            variable_size: indicates whether to change the size of the spot.
            energy_func to distort used energy
        """
        self.end_point = np.asarray(end_point)
        start_point = np.asarray(start_point)
        self.direction = (start_point - end_point).astype(float)
        distance = np.linalg.norm(self.direction)
        self.direction /= distance
        # distance scaling constant
        self.c = distance * energy**0.5
        self.intensity_func = intensity_func
        self.energy_func = energy_func
        self.sigma = size
        self.variable_size = variable_size
        if self.variable_size:
            # size scaling constant
            self.c_size = energy * self.sigma

    def compute_position(self, energy):
        energy = self.energy_func(energy)
        distance = self.c / energy**0.5
        result = distance * self.direction + self.end_point
        return result[0], result[1]

    def draw(self, npimage, energy):
        """ Draw an gaussian spot with integrated intensity from intensity_func."""
        x_spot, y_spot = self.compute_position(energy)
        if self.variable_size:
            self.sigma = self.c_size / energy
        draw_gauss(x_spot, y_spot, self.sigma, npimage, integral=self.intensity_func(energy))

class ImageGenerator:
    """ Generate test images."""
    def __init__(self, inputDir = "",
                 background = Background(np.zeros, (500, 500), True),
                 energies=range(75, 125),
                 spots = [Spot((30.0, 30.0), (200, 200), 75, constant_factory(1000))]):
        """ input dir only for compatibility with ImageLoader,
        """
        self.energies = sorted(energies)
        self.spots = spots
        self.background = background
    def __iter__(self):
        for energy in self.energies:
            npimage = self.background()
            for spot in self.spots:
                spot.draw(npimage, energy)
            yield npimage, energy

class TestTracking:
    def __init__(self):
        size = (200, 200)
        end_point = (200, 200)
        self.radii = collections.defaultdict(constant_factory(10))
        default_range = range(60, 140)

        self.kwarg_dict = {}
        self.kwarg_dict["minimal"] = \
            dict(background = Background(partial(back_uniform, level=0), size, is_constant=True),
            energies = default_range,
            spots = [Spot((100, 50), end_point, default_range[0], intensity_func=constant_factory(1000))])

        # backgrounds
        self.kwarg_dict["back_uniform"] = \
            dict(background = Background(partial(back_uniform, level=4), size, is_constant=True),
            energies = default_range,
            spots = [Spot((30, 30), end_point, default_range[0], intensity_func=constant_factory(1000))])
        self.kwarg_dict["back_poisson"] = \
            dict(background = Background(partial(back_poisson, mu=4), size, is_constant=False),
            energies = default_range,
            spots = [Spot((30, 30), end_point, default_range[0], intensity_func=constant_factory(1000))])
        self.kwarg_dict["back_normal"] = \
            dict(background = Background(partial(back_normal, mu=4, sigma=3), size, is_constant=False),
            energies = default_range,
            spots = [Spot((30, 30), end_point, default_range[0], intensity_func=constant_factory(1000))])

        # intensities
        self.kwarg_dict["intensity_step"] = \
            dict(background = Background(partial(back_normal, mu=4, sigma=3), size, is_constant=False),
            energies = default_range,
            spots = [Spot((30, 30), end_point, default_range[0], intensity_func = partial(step_function, step_x=100))])
        self.kwarg_dict["intensity_sine"] = \
            dict(background = Background(partial(back_normal, mu=4, sigma=3), size, is_constant=False),
            energies = default_range,
            spots = [Spot((30, 30), end_point, default_range[0], intensity_func = partial(sine_intensity, 5))])
        
        # energy
#        self.kwarg_dict["eV_stepsize"] = dict(background = Background(partial(back_normal, mu=4, sigma=3), size, is_constant=False),
#                                         energies = range(75, 125, 2),
#                                         spots = [Spot((30, 30), end_point, 75, intensity_func=partial(constant, value=1000))])
        self.kwarg_dict["eV_uncalibrated"] = dict(background = Background(partial(back_normal, mu=4, sigma=3), size, is_constant=False),
                                             energies = default_range,
                                             spots = [Spot((30, 30), end_point, default_range[0], intensity_func=constant_factory(1000),
                                                energy_func=partial(linear, m=1.01, b=1.0))])

        # point
        self.kwarg_dict["point_light"] = \
            dict(background = Background(partial(back_normal, mu=4, sigma=3), size, is_constant=False),
            energies = default_range,
            spots = [Spot((30, 30), end_point, default_range[0], intensity_func=constant_factory(250))])
        self.kwarg_dict["point_two"] = \
            dict(background = Background(partial(back_normal, mu=4, sigma=3), size, is_constant=False),
            energies = default_range,
            spots = [Spot((30, 30), end_point, default_range[0], intensity_func=constant_factory(1000), size=2),
                Spot((38, 38), end_point, default_range[0], intensity_func=constant_factory(1000), size=2)])
#        self.kwarg_dict["points_scaling"] = \
#            dict(background = Background(partial(back_normal, mu=4, sigma=3), size, is_constant=False),
#            energies = default_range,
#            spots = [Spot((30, 30), end_point, default_range[0], intensity_func=partial(constant, value=1000), variable_size=True)])
        self.kwarg_dict["point_small"] = \
            dict(background = Background(partial(back_normal, mu=4, sigma=3), size, is_constant=False),
            energies = default_range,
            spots = [Spot((30, 30), end_point, default_range[0], intensity_func=constant_factory(250), size=1)])
        self.radii["point_small"] = 5

        self.xss = []
        self.yss = []
        self.intensitiess = []
    
    def run_all(self, output="full"):
        """ output in ["summary", "full", None] """
        for key in sorted(self.kwarg_dict.keys()):
            if output == "full":
                print()
                print(key)
            # this is a hack as run is now an iterator for display
            [item for item in self.run(key)]
            if output == "full":
                self.print_error(-1)

    def run(self, name, output=False):
        imageGenerator = ImageGenerator(**self.kwarg_dict[name])
        npimage, energy = iter(imageGenerator).next()
        trackers = []
        energy = imageGenerator.energies[0]
        for spot in imageGenerator.spots:
            x, y = spot.compute_position(energy)
            trackers.append((Tracker(x, y, self.radii[name], energy), spot))
        images = iter(imageGenerator)
        xs = []
        ys = []
        intensities = []
        for image in images:
            if output:
                xs_out = []
                ys_out = []
            for tracker, spot in trackers:
                x, y, intensity, energy, radius = tracker.feed_image(image)
                if output:
                    xs_out.append(x)
                    ys_out.append(y)
                x_true, y_true = spot.compute_position(image[1])
                intensity_true = spot.intensity_func(image[1])
                xs.append((x, x_true))
                ys.append((y, y_true))
                intensities.append((intensity, intensity_true))
            if output:
                yield image[0], xs_out, ys_out
        self.xss.append(xs)
        self.yss.append(ys)
        self.intensitiess.append(intensities)

    def print_error(self, index, round_=4):
        bias_pos = (compute_bias(self.xss[index])**2 + compute_bias(self.yss[index])**2)**0.5
        stddev_pos = (compute_stddev(self.xss[index])**2 + compute_stddev(self.yss[index])**2)**0.5
        print_bias_stddev(bias_pos, stddev_pos, "position")
        print_bias_stddev(compute_bias(self.intensitiess[index]), compute_stddev(self.intensitiess[index]), "intensity")

class TestIdentification:
    def __init__(self, x, y, intensity, size, sigma_back, runs = 100):
        self.background = partial(back_normal, (10, 10), mu=10, sigma=sigma_back)
        self.spot = partial(draw_gauss, x, y, size, multiplicator=intensity)
        self.runs = runs

    def __iter__(self):
        for i in range(self.runs):
            npimage = self.background()
            self.spot(npimage)
            yield npimage

#### test helper ####
def compute_bias(values):
    measured, true = zip(*values)
    return np.mean(measured) - np.mean(true)

def compute_stddev(values):
    diff = [(measured - true)**2 for measured, true in values]
    return np.mean(diff)**0.5

def print_bias_stddev(bias, stddev, prefix="", round_=4):
    if not prefix == "":
        prefix = prefix + " "
    print(prefix + "bias %s, sigma %s" % (round(bias, round_), round(stddev, round_)))
######################

#### main methods ####
def tracking(test=None):
    tester = TestTracking()
    if test is None:
        tester.run_all()
    else:
        [item for item in tester.run(test)]

def identification(sys_args):
    x_true, y_true = 5, 5
    sigma_back = 1
    nRuns = 100
    for intensity in np.arange(10, 1, -1):
        print(intensity / sigma_back),
        tester = TestIdentification(x_true, y_true, intensity, 3, sigma_back, nRuns)
        xs = []
        ys = []
        xerr = np.zeros((nRuns))
        snr = np.zeros((nRuns))
        for i, image in enumerate(tester):
            try:
                z, pcov = guess_from_Gaussian(image, x_true, y_true, 10)
                x, y = z
                xerr[i] = (pcov[0, 0] + pcov[1, 1])**.5
                snr[i] = signal_to_noise(image, x, y, 3)
                xs.append((x, x_true))
                ys.append((y, y_true))
            except:
                print(i, "failed")
        bias_pos = (compute_bias(xs)**2 + compute_bias(ys)**2)**0.5
        stddev_pos = (compute_stddev(xs)**2 + compute_stddev(ys)**2)**0.5
        print_bias_stddev(bias_pos, stddev_pos)
        print(np.mean(xerr), np.mean(snr))

def calc_v(z_r, z_c, z_dev, z_c_dev, E, dE):
    # make sure the state variables are numpy array
    z_r, z_c, z_dev, z_c_dev = np.asarray(z_r), np.asarray(z_c), np.asarray(z_dev), np.asarray(z_c_dev)
    # calculate the distance vector = real coordinate - centrum coordinate
    z = z_r - z_c
    z_dev = (z_dev**2 + z_c_dev**2)**.5
    v = - 0.5 * z / E 
    v_dev = - 0.5 * z_dev / E 
    return v[0], v[1], v_dev[0], v_dev[1]

def bootstrap(data, axis = 0, n = 10000):
    return np.mean(np.asarray([simple_bootstrap(data, axis = axis, n = 100) for i in range(int(n/100))]), axis = 0)

def simple_bootstrap(data, axis = 0, n = 100):
    this_data = data[np.random.randint(data.shape[axis], size = (data.shape[axis], n))]
    bootstrap_means = np.mean(this_data, axis = axis)
    return np.std(bootstrap_means, axis = axis, ddof = 1)

def display(sys_args):
    import gobject
    import gtk

    import matplotlib
    matplotlib.use('GTKAgg')
    import matplotlib.cm as cm

    import matplotlib.pyplot as plt

    fig = plt.figure(1)
    ax = fig.add_subplot(111)

    def animate():
        tester = TestTracking()
        tester_run = tester.run(sys_args[2], output=True)
        image, xs, ys = tester_run.next()
        im = ax.imshow(image, cmap=cm.gray, interpolation="nearest")
        plot = ax.plot(ys, xs, "go")
        for image, xs, ys in tester_run:
            ax.set_xlim(0, 200)
            ax.set_ylim(0, 200)
            time.sleep(0.1)
            im.set_data(image)
            plot[0].set_data(ys, xs)
            fig.canvas.draw()
        raise SystemExit

    gobject.idle_add(animate)
    plt.show()

def profile(sys_args):
    import cProfile
    tester = TestTracking() 
    command = """tester.run_all()"""
    cProfile.runctx(command, globals(), locals(), "profile.dat")
#######################

if __name__ == "__main__":
    import sys

    sys.stderr = open("errs.log", "w")
    
    #TODO: There must be a better way to do this!

    if len(sys.argv) == 1:
        print("not enough arguments")

    elif sys.argv[1] == "tracking":
        if len(sys.argv) == 3:
            tracking(sys.argv[2])
        else:
            tracking()
    
    elif sys.argv[1] == "kalman":
        kalman(sys.argv)

    elif sys.argv[1] == "identification":
        identification(sys.argv)

    elif sys.argv[1] == "display":
        display(sys.argv)
    
    elif sys.argv[1] == "profile":
        profile(sys.argv)

    else:
        print("unknown command")
