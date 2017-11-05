'''
configuration
------------------
Class for handling configuration
'''
import configparser, logging, os
import numpy as np
from pathlib import Path
from . import __version__

class Configuration():
    def __init__(self):
        self.home = str(Path.home())+"/"
        self.configFile = str(self.home+"easyleed.ini")
        self.loggingFilename = str("easyleed.log")
        self.conf = configparser.ConfigParser()
        self.conf.optionxform = str
    
    # Create configuration file
    def createConfig(self):
        try:
            self.defineIOConfig()
            self.defineGUIConfig()
            self.defineTrackingConfig()
            self.defineProcessingConfig()
            self.defineSystemConfig()
            with open(self.configFile, 'w') as configfile:
                self.conf.write(configfile)
        except:
            print("Error in creating configuration file")

    # Hadrcoded default definitions for the confoguration file
    def defineIOConfig(self):
        self.conf['IO'] = {
            'IO_energyRegex' : "[0-9]+(\.[0-9]*)?([Ee](|\+|-)[0-9]+)?(?=[^.0-9]*\.[A-Za-z0-9]+$)",
            }
    def defineGUIConfig(self):
        self.conf['GUI'] = {
            'GraphicsScene_defaultRadius' : 40,
            'GraphicsScene_livePlottingOn' : True,
            'GraphicsScene_intensTimeOn' : False,
            'GraphicsScene_plotAverage' : False,
            'GraphicsScene_plotSmoothAverage': False,
            'GraphicsScene_smoothPoints' : 4,
            'GraphicsScene_smoothSpline' : 50,
            'QGraphicsMovableItem_bigMove' : 1,
            'QGraphicsMovableItem_smallMove' : 0.1,
            'QGraphicsSpotItem_spotSizeChange' : 1,
            'QGraphicsCenterItem_size' : 5,
            }
    def defineTrackingConfig(self):
        self.conf['Tracking'] = {
            'Tracking_inputPrecision' : 2,
            'Tracking_windowScalingOn' : True,
            'Tracking_minWindowSize' : 0,
            'Tracking_guessFunc' : "guess_from_Gaussian",
            'Tracking_processNoisePosition' : 0.1,
            'Tracking_processNoiseVelocity' : 0.0,
            'Tracking_gamma' : 8,
            'Tracking_minRsq' : 0.8,
            'Tracking_fitRegionFactor' : 1.5,
            }
    
    def defineProcessingConfig(self):
        self.conf['Processing'] = {
            'Processing_backgroundSubstractionOn' : True,
            }
    
    def defineSystemConfig(self):
        self.conf['System'] = {
            'appVersion' : __version__,
            'loggingLevel' : logging.INFO,
            'loggingFilename' : self.loggingFilename,
            }

    # Read configuration file into usable variables
    def readConfig(self, configFile):
        self.conf.read(configFile)
        self.sysConfig = self.conf['System']
        self.appVersion = self.sysConfig['appVersion']
        if str(self.appVersion).rsplit('.',1)[0] != __version__.rsplit('.',1)[0] :
            print("Configuration file is for an earlier version of the software")
            oldConfigFile = str(os.path.splitext(configFile)[0]+"_"+str(self.appVersion)+".ini")
            print("Old config file backup: ",oldConfigFile)
            os.rename(configFile, oldConfigFile )
            print("Creating a new config file.")
            self.createConfig()
            
        self.IOConfig = self.conf['IO']
        self.GUIConfig = self.conf['GUI']
        self.trackingConfig = self.conf['Tracking']
        self.processingConfig = self.conf['Processing']

        #####################
        #### IO related ####
        ####################
        # regular expression to extract energy from filename (not used for img files)
        # match the last (floating-point) number before file extension
        self.IO_energyRegex = self.IOConfig['IO_energyRegex']

        #####################
        #### GUI related ####
        #####################
        ## GraphicsScene ##
        # default radius of a new spot
        self.GraphicsScene_defaultRadius = eval(self.GUIConfig['GraphicsScene_defaultRadius'])
        # Live IV plotting during acquisition
        self.GraphicsScene_livePlottingOn = eval(self.GUIConfig['GraphicsScene_livePlottingOn'])
        # Acquire I(time) at fixed energy
        self.GraphicsScene_intensTimeOn = eval(self.GUIConfig['GraphicsScene_intensTimeOn'])
        # Plot averages
        self.GraphicsScene_plotAverage = eval(self.GUIConfig['GraphicsScene_plotAverage'])
        # Plot smoothAverages
        self.GraphicsScene_plotSmoothAverage = eval(self.GUIConfig['GraphicsScene_plotSmoothAverage'])
        # Interval of points to be rescaled for smoothing average
        self.GraphicsScene_smoothPoints = eval(self.GUIConfig['GraphicsScene_smoothPoints'])
        # Amount of smoothing to perform during the spline fit.
        # The default value of s is s=m-\sqrt{2m} where m is the number of data-points being fit.
        self.GraphicsScene_smoothSpline = eval(self.GUIConfig['GraphicsScene_smoothSpline'])

        ## QGraphicsMovableItem ##
        # change in position per key press (Arrow keys)
        self.QGraphicsMovableItem_bigMove = eval(self.GUIConfig['QGraphicsMovableItem_bigMove'])
        # change in position per key press if Ctrl pressed
        self.QGraphicsMovableItem_smallMove = eval(self.GUIConfig['QGraphicsMovableItem_smallMove'])

        ## QGraphicsSpotItem ##
        # change in radius of the spot per key press (+/-) in pixel
        self.QGraphicsSpotItem_spotSizeChange = eval(self.GUIConfig['QGraphicsSpotItem_spotSizeChange'])

        ## QGraphicsCenterItem ##
        self.QGraphicsCenterItem_size = eval(self.GUIConfig['QGraphicsCenterItem_size'])

        ##########################
        #### Tracking related ####
        ##########################

        # precision of the user input (standard deviation in pixel)
        self.Tracking_inputPrecision = eval(self.trackingConfig['Tracking_inputPrecision'])
        # scale the integration window with changing energy
        self.Tracking_windowScalingOn = eval(self.trackingConfig['Tracking_windowScalingOn'])
        # minimal radius of the integration window (in pixel)
        self.Tracking_minWindowSize = eval(self.trackingConfig['Tracking_minWindowSize'])
        # function for spot identification
        self.Tracking_guessFunc = self.trackingConfig['Tracking_guessFunc']
        # Kalman tracker process noise
        self.Tracking_processNoisePosition = eval(self.trackingConfig['Tracking_processNoisePosition'])
        self.Tracking_processNoiseVelocity = eval(self.trackingConfig['Tracking_processNoiseVelocity'])
        # size of validation region
        # Ideal assumptions D_M^2 ~ Chi^2 with two degrees of freedom
        # cdf Chi^2 with two degrees of freedom is 1 - exp(-x/2)
        self.Tracking_gamma = eval(self.trackingConfig['Tracking_gamma'])
        # Minimal coefficient of determination R^2 for fit
        self.Tracking_minRsq = eval(self.trackingConfig['Tracking_minRsq'])
        # factor by which the fitted region is bigger than the radius
        self.Tracking_fitRegionFactor = eval(self.trackingConfig['Tracking_fitRegionFactor'])

        ############################
        #### Processing related ####
        ############################
        # substract the background from the intensity measurements
        self.Processing_backgroundSubstractionOn = eval(self.processingConfig['Processing_backgroundSubstractionOn'])
        
        ############################
        #### System related ####
        ############################
        # substract the background from the intensity measurements
        self.loggingLevel = eval(self.sysConfig['loggingLevel'])
        self.loggingLevel = eval(self.sysConfig['loggingLevel'])

    # Save current parameters in configuration file
    def saveConfig(self, configFile):
        #try:
        with open(configFile, 'w') as configfile:
            self.conf.write(configfile)
        #except:
        #    print("Error in saving parameters")
