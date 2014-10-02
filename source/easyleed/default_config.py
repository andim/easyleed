# how much information shall be logged
import logging
loggingLevel = logging.INFO
loggingFilename = "easyleed.log"

import numpy as np

#### IO related ####
####################

# regular expression to extract energy from filename (not used for img files)
# match floating point number, followed by a point e.g. filename3.5.img or filename3.jpg
IO_energyRegex = "[0-9]*\.?[0-9]+(?=\.)"

####################
####################

#### GUI related ####
#####################

## GraphicsScene ##
# default radius of a new spot
GraphicsScene_defaultRadius = 20

## QGraphicsItem ##
# change in radius of the spot per key press (+/-) in pixel
QGraphicsItem_spotSizeChange = 1
# change in position per key press (Arrow keys)
QGraphicsItem_bigMove = 1
# change in position per key press if Ctrl pressed
QGraphicsItem_smallMove = 0.1

# Live IV plotting during acquisition
GraphicsScene_livePlottingOn = True

# Acquire I(time) at fixed energy
GraphicsScene_intensTimeOn = False

# Plot averages
GraphicsScene_plotAverage = False

######################
######################

#### Tracking related ####
##########################

# precision of the user input (standard deviation in pixel)
Tracking_inputPrecision = 5
# scale the integration window with changing energy
Tracking_windowScalingOn = True
# minimal radius of the integration window (in pixel)
Tracking_minWindowSize = 0
# function for spot identification
Tracking_guessFunc = "guess_from_Gaussian"
# Kalman tracker process noise
Tracking_processNoise = np.diag([4e-2, 4e-2, 0, 0])
# size of validation region
# Ideal assumptions D_M^2 ~ Chi^2 with two degrees of freedom
# cdf Chi^2 with two degrees of freedom is 1 - exp(-x/2)
Tracking_gamma = 8
# Minimal coefficient of determination R^2 for fit
Tracking_minRsq = 0.8

##########################
##########################

#### Processing related ####
############################

# substract the background from the intensity measurements
Processing_backgroundSubstractionOn = True
