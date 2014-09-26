import sys
import logging
import webbrowser

from PyQt4.QtCore import (QPoint, QRectF, QPointF, Qt, SIGNAL, QTimer, QObject)
from PyQt4.QtGui import (QApplication, QMainWindow, QGraphicsView,
    QGraphicsScene, QImage, QWidget, QHBoxLayout, QPen, QSlider,
    QVBoxLayout, QPushButton, QGraphicsEllipseItem, QGraphicsItem,
    QPainter, QKeySequence, QAction, QIcon, QFileDialog, QProgressBar, QAbstractSlider,
    QBrush, QFrame, QLabel, QRadioButton, QGridLayout, QSpinBox, QDoubleSpinBox, QCheckBox,
    QComboBox, QLineEdit, QMessageBox, QPixmap)
import numpy as np

from . import config
from . import __version__
from . import __author__
from base import *
from io import *

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT
from matplotlib.figure import Figure
import pickle



logging.basicConfig(filename = config.loggingFilename, level=config.loggingLevel)

class QGraphicsSpotView(QGraphicsEllipseItem):
    """ Provides an QGraphicsItem to display a Spot on a QGraphicsScene.
    
        Circle class providing a circle that can be moved by mouse and keys.
        
    """

    def __init__(self, point, radius, parent=None):
        offset = QPointF(radius, radius)
        super(QGraphicsSpotView, self).__init__(QRectF(-offset, offset),  parent)
        self.setPen(QPen(Qt.blue))
        self.setPos(point)
        self.setFlags(QGraphicsItem.ItemIsSelectable|
                      QGraphicsItem.ItemIsMovable|
                      QGraphicsItem.ItemIsFocusable)

    def keyPressEvent(self, event):
        """ Handles keyPressEvents.

            The circle can be moved using the arrow keys. Applying Shift
            at the same time allows fine adjustments.

            The circles radius can be changed using the plus and minus keys.
        """

        if event.key() == Qt.Key_Plus:
            self.changeSize(config.QGraphicsSpotView_spotSizeChange)
        elif event.key() == Qt.Key_Minus:
            self.changeSize(-config.QGraphicsSpotView_spotSizeChange)
        elif event.key() == Qt.Key_Right:
            if event.modifiers() & Qt.ShiftModifier:
                self.moveRight(config.QGraphicsSpotView_smallMove)
            else:
                self.moveRight(config.QGraphicsSpotView_bigMove)
        elif event.key() == Qt.Key_Left:
            if event.modifiers() & Qt.ShiftModifier:
                self.moveLeft(config.QGraphicsSpotView_smallMove)
            else:
                self.moveLeft(config.QGraphicsSpotView_bigMove)
        elif event.key() == Qt.Key_Up:
            if event.modifiers() & Qt.ShiftModifier:
                self.moveUp(config.QGraphicsSpotView_smallMove)
            else:
                self.moveUp(config.QGraphicsSpotView_bigMove)
        elif event.key() == Qt.Key_Down:
            if event.modifiers() & Qt.ShiftModifier:
                self.moveDown(config.QGraphicsSpotView_smallMove)
            else:
                self.moveDown(config.QGraphicsSpotView_bigMove)

    def onPositionChange(self, point):
        """ Handles incoming position change request."""
        self.setPos(point)

    def radius(self):
        return self.rect().width() / 2.0

    def onRadiusChange(self, radius):
        """ Handles incoming radius change request."""
        self.changeSize(radius - self.radius())

    def moveRight(self, distance):
        """ Moves the circle distance to the right."""
        self.setPos(self.pos() + QPointF(distance, 0.0))

    def moveLeft(self, distance):
        """ Moves the circle distance to the left."""
        self.setPos(self.pos() + QPointF(-distance, 0.0))

    def moveUp(self, distance):
        """ Moves the circle distance up."""
        self.setPos(self.pos() + QPointF(0.0, -distance))

    def moveDown(self, distance):
        """ Moves the circle distance down."""
        self.setPos(self.pos() + QPointF(0.0, distance))

    def changeSize(self, inc):
        """ Change radius by inc.
        
            inc > 0: increase
            inc < 0: decrease
        """

        inc /= 2**0.5 
        self.setRect(self.rect().adjusted(-inc, -inc, +inc, +inc))

class QSpotModel(QObject):
    """
    Wraps a SpotModel to offer signals.

    Provides the following signals:
    - intensityChanged
    - positionChanged
    - radiusChanged
    """

    def __init__(self, parent = None):
        super(QSpotModel, self).__init__(parent)
        self.m = SpotModel()
    
    def update(self, x, y, intensity, energy, radius):
        self.m.update(x, y, intensity, energy, radius)
        QObject.emit(self, SIGNAL("positionChanged"), QPointF(x, y))
        QObject.emit(self, SIGNAL("radiusChanged"), radius)
        QObject.emit(self, SIGNAL("intensityChanged"), intensity)

class GraphicsScene(QGraphicsScene):
    """ Custom GraphicScene having all the main content."""

    def __init__(self, parent=None):
        super(GraphicsScene, self).__init__(parent)
    
    def mousePressEvent(self, event):
        """ Processes mouse events through either            
              - propagating the event
            or 
              - instantiating a new Circle (on left-click)
        """
       
        if self.itemAt(event.scenePos()):
            super(GraphicsScene, self).mousePressEvent(event)
        elif event.button() == Qt.LeftButton:
            item = QGraphicsSpotView(event.scenePos(),
                         config.GraphicsScene_defaultRadius)
            self.clearSelection()
            self.addItem(item)
            item.setSelected(True)
            self.setFocusItem(item)

    def keyPressEvent(self, event):
        """ Processes key events through either            
              - deleting the focus item
            or   
              - propagating the event

        """

        item = self.focusItem()
        if item:
            if event.key() == Qt.Key_Delete:
                self.removeItem(item)
                del item
            else:
                super(GraphicsScene, self).keyPressEvent(event)

    def drawBackground(self, painter, rect):
        """ Draws image in background if it exists. """
        if hasattr(self, "image"):
            painter.drawImage(QPoint(0, 0), self.image)

    def setBackground(self, image):
        """ Sets the background image. """
        self.image = image
        self.update()
    
    def removeAll(self):
        """ Remove all items from the scene (leaves background unchanged). """
        for item in self.items():
            self.removeItem(item)

class GraphicsView(QGraphicsView):
    """ Custom GraphicsView to display the scene. """
    def __init__(self, parent=None):
        super(GraphicsView, self).__init__(parent)
        self.setRenderHints(QPainter.Antialiasing)
    
#    def wheelEvent(self, event):
#        factor = 1.41 ** (-event.delta() / 240.0)
#        self.scale(factor, factor)
    
    def resizeEvent(self, event):
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
    
    def drawBackground(self, painter, rect):
        painter.fillRect(rect, QBrush(Qt.lightGray))
        self.scene().drawBackground(painter, rect)

class FileDialog(QFileDialog):
    def __init__(self, **kwargs):
        super(FileDialog, self).__init__(**kwargs)
        self.setFileMode(QFileDialog.ExistingFiles)


class AboutWidget(QWidget):
    """ PyQt widget for About Box Panel """
    
    def __init__(self):
        super(AboutWidget, self).__init__()
        
        self.initUI()
    
    def initUI(self):
        
        self.setGeometry(100, 200, 400, 200)
        self.setWindowTitle('About EasyLEED')
        self.gridLayout = QGridLayout()
        self.setLayout(self.gridLayout)
        self.verticalLayout = QVBoxLayout()
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.label = QLabel("<qt><b><big><a href = http://andim.github.io/easyleed/index.html>EasyLEED %s</a></b></big></qt>" % __version__, self);
        self.label.setOpenExternalLinks(True);
        self.verticalLayout.addWidget(self.label)
        self.label = QLabel("by: %s" % __author__, self)
        self.verticalLayout.addWidget(self.label)
        self.label = QLabel("<qt>Contact: <a href = mailto:andisspam@gmail.com>andisspam@gmail.com</a></qt>", self)
        self.label.setOpenExternalLinks(True);
        self.verticalLayout.addWidget(self.label)
        self.label = QLabel("More details: ", self)
        self.verticalLayout.addWidget(self.label)
        self.label = QLabel("<qt><a href = http://dx.doi.org/10.1016/j.cpc.2012.02.019>Mayer, H. Salopaasi, K. Pussi, R.D. Diehl. Comput. Phys. Commun. 183, 1443-1447 (2012)</a>",self)
        self.label.setWordWrap(True)
        self.label.setOpenExternalLinks(True);
        self.verticalLayout.addWidget(self.label)

class Plot(QWidget):
    """ Custom PyQt widget canvas for plotting """

    def __init__(self):
        super(Plot, self).__init__()
        self.setWindowTitle("I(E)-curve")
        self.create_main_frame()
    
    def create_main_frame(self):       
        """ Create the mpl Figure and FigCanvas objects. """
        # 5x4 inches, 100 dots-per-inch
        self.setGeometry(700, 450, 600, 400)
        self.dpi = 100
        self.fig = Figure((5.0, 4.0), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        
        # Since we have only one plot, we can use add_axes 
        # instead of add_subplot, but then the subplot
        # configuration tool in the navigation toolbar wouldn't
        # work.
        self.axes = self.fig.add_subplot(111)
        
        # Setup axis, labels...
        self.setupPlot()
        
        # Create the navigation toolbar, tied to the canvas
        self.mpl_toolbar = NavigationToolbar2QT(self.canvas, self)

        # Layout
        vbox = QVBoxLayout()
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.canvas)
        
        # Add checkbox for average.
        self.averageCheck = QCheckBox("Show Average")
        self.averageCheck.setChecked(config.GraphicsScene_plotAverage)
        vbox.addWidget(self.averageCheck)
        self.setLayout(vbox)
        
        # Define event for checkbox
        QObject.connect(self.averageCheck, SIGNAL("clicked()"), self.AvCheck)
    
    def AvCheck(self):
        if self.averageCheck.isChecked() == True:
            config.GraphicsScene_plotAverage = True
        else:
            config.GraphicsScene_plotAverage = False

    def setupPlot(self):
        self.axes.set_xlabel("Energy [eV]")
        self.axes.set_ylabel("Intensity")
        # removes the ticks from y-axis
        self.axes.set_yticks([])

class SetParameters(QWidget): 
    """PyQt widget for setting tracking parameters"""
 
    
    def __init__(self):
        super(SetParameters, self).__init__()
        self.initUI()
        
    def initUI(self):
        
        # Buttons/elements
        self.inputPrecision = QSpinBox(self)
        self.inputPrecision.setWrapping(True)
        self.inputPrecision.setValue(config.Tracking_inputPrecision)
        self.ipLabel = QLabel("User input precision", self)
        
        self.integrationWindowRadiusNew = QSpinBox(self)
        self.integrationWindowRadiusNew.setWrapping(True)
        self.integrationWindowRadiusNew.setValue(config.GraphicsScene_defaultRadius)
        self.iwrnLabel = QLabel("Default radius of a new spot", self)

        self.integrationWindowRadius = QSpinBox(self)
        self.integrationWindowRadius.setWrapping(True)
        self.integrationWindowRadius.setValue(config.Tracking_minWindowSize)
        self.iwrLabel = QLabel("Minimal radius of the integration window", self)

        self.validationRegionSize = QSpinBox(self)
        self.validationRegionSize.setWrapping(True)
        self.validationRegionSize.setValue(config.Tracking_gamma)
        self.vrsLabel = QLabel("Size of the validation region", self)

        self.determinationCoefficient = QDoubleSpinBox(self)
        self.determinationCoefficient.setWrapping(True)
        self.determinationCoefficient.setSingleStep(0.01)
        self.determinationCoefficient.setValue(config.Tracking_minRsq)
        self.dcLabel = QLabel("Minimal R^2 to accept fit", self)

        self.integrationWindowScale = QCheckBox("Scale integration window with changing energy")
        self.integrationWindowScale.setChecked(config.Tracking_windowScalingOn)

        self.backgroundSubstraction = QCheckBox("Background substraction")
        self.backgroundSubstraction.setChecked(config.Processing_backgroundSubstractionOn)
        
        self.livePlotting = QCheckBox("Plot I(E) intensities during acquisition")
        self.livePlotting.setChecked(config.GraphicsScene_livePlottingOn)

        self.spotIdentification = QComboBox(self)
        self.spotIdentification.addItem("guess_from_Gaussian")
        self.siLabel = QLabel("Spot identification algorithm", self)


        self.fnLabel = QLabel("Kalman tracker process noise Q", self)
        self.text = QLabel("Sets diagonal values of covariance matrix", self)
        self.value1 = QLineEdit(self)
        self.value1.setText(str(config.Tracking_processNoise.diagonal()[0]))
        self.value2 = QLineEdit(self)
        self.value2.setText(str(config.Tracking_processNoise.diagonal()[1]))
        self.value3 = QLineEdit(self)
        self.value3.setText(str(config.Tracking_processNoise.diagonal()[2]))
        self.value4 = QLineEdit(self)
        self.value4.setText(str(config.Tracking_processNoise.diagonal()[3]))


        self.saveButton = QPushButton('&Save', self)
        self.loadButton = QPushButton('&Load', self)
        self.defaultButton = QPushButton('&Default', self)
        self.wrongLabel = QLabel(" ", self)
        self.acceptButton = QPushButton('&Accept', self)
        self.applyButton = QPushButton('&Apply', self)
        self.cancelButton = QPushButton('&Cancel', self)

        #Layouts
        self.setGeometry(700, 0, 300, 150)
        self.setWindowTitle('Set tracking parameters')
     
        #base grid
        self.gridLayout = QGridLayout()
        self.setLayout(self.gridLayout)

        #1st (left) vertical layout
        self.lvLayout = QVBoxLayout()
        self.lvLayout.addWidget(self.ipLabel)
        self.lvLayout.addWidget(self.inputPrecision)
        self.lvLayout.addWidget(self.iwrnLabel)
        self.lvLayout.addWidget(self.integrationWindowRadiusNew)
        self.lvLayout.addWidget(self.iwrLabel)
        self.lvLayout.addWidget(self.integrationWindowRadius)
        self.lvLayout.addWidget(self.vrsLabel)
        self.lvLayout.addWidget(self.validationRegionSize)
        self.lvLayout.addWidget(self.dcLabel)
        self.lvLayout.addWidget(self.determinationCoefficient)

        #2nd (right) vertical layout
        self.rvLayout = QVBoxLayout()
        self.rvLayout.addWidget(self.integrationWindowScale)
        self.rvLayout.addWidget(self.backgroundSubstraction)
        self.rvLayout.addWidget(self.livePlotting)
        self.rvLayout.addWidget(self.siLabel)
        self.rvLayout.addWidget(self.spotIdentification)
        self.rvLayout.addWidget(self.fnLabel)
        self.rvLayout.addWidget(self.text)
        self.hpLayout = QHBoxLayout()
        self.rvLayout.addWidget(self.value1)
        self.rvLayout.addWidget(self.value2)
        self.rvLayout.addWidget(self.value3)
        self.rvLayout.addWidget(self.value4)

        #horizontal layout left
        self.hLayout = QHBoxLayout()
        self.hLayout.addWidget(self.saveButton)
        self.hLayout.addWidget(self.loadButton)
        self.hLayout.addWidget(self.defaultButton)
        self.hLayout.addWidget(self.wrongLabel)

        #horizontal layout right
        self.h2Layout = QHBoxLayout()
        self.h2Layout.addWidget(self.applyButton)
        self.h2Layout.addWidget(self.acceptButton)
        self.h2Layout.addWidget(self.cancelButton)

        #adding layouts to the grid
        self.gridLayout.addLayout(self.lvLayout, 0, 0)
        self.gridLayout.addLayout(self.rvLayout, 0, 1)
        self.gridLayout.addLayout(self.hpLayout, 4, 1)
        self.gridLayout.addLayout(self.hLayout, 5, 0)
        self.gridLayout.addLayout(self.h2Layout, 5, 1)

class MainWindow(QMainWindow):
    """ easyLeed's main window. """
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("easyLeed %s" % __version__)

        #### setup central widget ####
        self.aboutwid = AboutWidget()
        self.plotwid = Plot()
        self.setparameterswid = SetParameters()
        self.scene = GraphicsScene(self)
        self.view = GraphicsView()
        self.view.setScene(self.scene)
        self.view.setMinimumSize(660, 480)
        self.setGeometry(10, 10, 660, 480)
        self.setCentralWidget(self.view)
        global sliderCurrentPos
        sliderCurrentPos = 1
        
        #### define actions ####
        processRunAction = self.createAction("&Run", self.run,
                QKeySequence("Ctrl+r"), None,
                "Run the analysis of the images.")
        processStopAction = self.createAction("&Stop", self.stopProcessing,
                QKeySequence("Ctrl+w"), None,
                "Stop the analysis of the images.")
        processRestartAction = self.createAction("&Restart", self.restart,
                QKeySequence("Ctrl+z"), None,
                "Reset chosen points and jump to first image.")
        processNextAction = self.createAction("&Next Image", self.next_,
                QKeySequence("Ctrl+n"), None,
                "Open next image.")
        processPreviousAction = self.createAction("&Previous Image", self.previous,
                QKeySequence("Ctrl+p"), None,
                "Open previous image.")
        processPlotAction = self.createAction("&Plot", self.plotting,
                QKeySequence("Ctrl+d"), None,
                "Plot the energy/intensity.")
        processPlotAverageAction = self.createAction("&Plot average", self.plottingAverage,
                QKeySequence("Ctrl+g"), None,
                "Plot the energy/intensity average.")
        processPlotOptions = self.createAction("&Plot...", self.plottingOptions,
                None, None,
                "Plot Intensities.")
        processSetParameters = self.createAction("&Set Parameters", self.setParameters,
                None, None,
                "Set tracking parameters.")


        self.processActions = [processNextAction, processPreviousAction, None, processRunAction, processStopAction, processRestartAction, None, processPlotAction, None, processPlotAverageAction, None]
        fileOpenAction = self.createAction("&Open...", self.fileOpen,
                QKeySequence.Open, None,
                "Open a directory containing the image files.")
        self.fileSaveAction = self.createAction("&Save intensities...", self.saveIntensity,
                QKeySequence.Save, None,
                "Save the calculated intensities to a text file.")
                
        # actions to "File" menu
        self.fileSavePlotAction = self.createAction("&Save plot...", self.savePlot, QKeySequence("Ctrl+a"), None, "Save the plot to a pdf file.")
        # Will only enable plot saving after there is a plot to be saved
        self.fileSavePlotAction.setEnabled(False)
        self.fileSaveScreenAction = self.createAction("&Save screenshot...", self.saveScreenShot,
                QKeySequence("Ctrl+s"), None,
                "Save image to a file.")
        self.fileSaveScreenAction.setEnabled(False)
        self.fileQuitAction = self.createAction("&Quit", self.fileQuit,
                QKeySequence("Ctrl+q"), None,
                "Close the application.")
        self.fileSaveSpotsAction = self.createAction("&Save spot locations...", self.saveSpots,
                QKeySequence("Ctrl+t"), None,
                "Save the spots to a file.")
        # Enables when data to be saved
        self.fileSaveSpotsAction.setEnabled(False)
        self.fileLoadSpotsAction = self.createAction("&Load spot locations...", self.loadSpots,
                QKeySequence("Ctrl+l"), None,
                "Load spots from a file.")
        self.helpAction = self.createAction("&Help", self.helpBoxShow,
                None, None,
                "Show help")
        self.aboutAction = self.createAction("&About", self.aboutBoxShow,
                None, None,
                "About Easyleed")
        self.helpActions = [None, self.helpAction, None, self.aboutAction]
        
        
        self.fileActions = [fileOpenAction, self.fileSaveAction, self.fileSavePlotAction, self.fileSaveScreenAction,
                self.fileSaveSpotsAction, self.fileLoadSpotsAction, None, self.fileQuitAction]

        #### Create menu bar ####
        fileMenu = self.menuBar().addMenu("&File")
        self.fileSaveAction.setEnabled(False)
        self.addActions(fileMenu, self.fileActions)
        processMenu = self.menuBar().addMenu("&Process")
        self.addActions(processMenu, self.processActions)
        self.enableProcessActions(False)
        helpMenu = self.menuBar().addMenu("&Help")
        self.addActions(helpMenu, self.helpActions)

        #### Create tool bar ####
        toolBar = self.addToolBar("&Toolbar")
        # adding actions to the toolbar, addActions-function creates a separator with "None"
        self.toolBarActions = [self.fileQuitAction, None, fileOpenAction, None, processRunAction, None, processStopAction, None, processPlotOptions, None, processSetParameters, None, processRestartAction]
        self.addActions(toolBar, self.toolBarActions)
        
        #### Create status bar ####
        self.statusBar().showMessage("Ready", 5000)
        self.energyLabel = QLabel()
        self.energyLabel.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)


        self.prevButton = QPushButton('&<', self)
        self.nextButton = QPushButton('&>', self)
        self.prevButton.setEnabled(False)
        self.nextButton.setEnabled(False)
        
        ### Create slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        
        ### Create "next" and "previous" buttons.
        self.statusBar().addPermanentWidget(self.prevButton)
        self.statusBar().addPermanentWidget(self.nextButton)
        self.statusBar().addPermanentWidget(self.slider)
        self.statusBar().addPermanentWidget(self.energyLabel)
    
        ### Create event connector for slider
        QObject.connect(self.slider, SIGNAL("sliderMoved(int)"), self.slider_moved)
        QObject.connect(self.prevButton, SIGNAL("clicked()"), self.prevBtnClicked)
        QObject.connect(self.nextButton, SIGNAL("clicked()"), self.nextBtnClicked)
    

    def slider_moved(self, sliderNewPos):
        """
        This function tracks what to do with a slider movement.
            
        """
        global sliderCurrentPos
        self.worker = Worker(self.scene.items(), self.current_energy, parent=self)

        diff = sliderCurrentPos - sliderNewPos
        if diff > 0:
            for i in range(0, diff):
                self.previous()
                self.worker.process(self.loader.this())
        else:
            for i in range(diff, 0):
                self.next_()
                self.worker.process(self.loader.this())
        sliderCurrentPos = sliderNewPos

    def prevBtnClicked(self):
        self.worker = Worker(self.scene.items(), self.current_energy, parent=self)
        self.previous()
        self.worker.process(self.loader.this())

    def nextBtnClicked(self):
        self.worker = Worker(self.scene.items(), self.current_energy, parent=self)
        self.next_()
        self.worker.process(self.loader.this())

    def addActions(self, target, actions):
        """
        Convenience function that adds the actions to the target.
        If an action is None a separator will be added.
        
        """
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)
    
    def createAction(self, text, slot=None, shortcut=None, icon=None,
                     tip=None, checkable=False, signal="triggered()"):
        """ Convenience function that creates an action with the specified attributes. """
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/{0}.png".format(icon)))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action

    def enableProcessActions(self, enable):
        for action in self.processActions:
            if action:
                action.setEnabled(enable)

    def next_(self):
        try:
            image = self.loader.next()
        except StopIteration:
            self.statusBar().showMessage("Reached last picture", 5000)
        else:
            self.setImage(image)

    def previous(self):
        try:
            image = self.loader.previous()
        except StopIteration:
            self.statusBar().showMessage("Reached first picture", 5000)
        else:
            self.setImage(image)

    def restart(self):
        '''Delete stored plot information and start fresh'''
        self.scene.removeAll()
        self.loader.restart()
        self.setImage(self.loader.next())
        self.plotwid.axes.cla()
        self.plotwid.canvas.draw()
        self.plotwid.close()
        sliderCurrentPos = self.slider.setValue(1)

    def setImage(self, image):
        npimage, energy = image
        qimage = npimage2qimage(npimage)
        self.view.setSceneRect(QRectF(qimage.rect()))
        self.scene.setBackground(qimage)
        self.current_energy = energy
        self.energyLabel.setText("Energy: %s eV" % self.current_energy)

    def saveIntensity(self):
        filename = str(QFileDialog.getSaveFileName(self, "Save intensities to a file"))
        if filename:
            self.worker.save(filename)

    def fileOpen(self):
        """ Prompts the user to select input image files."""
        self.scene.removeAll()
        dialog = FileDialog(parent = self,
                caption = "Choose image files", filter= ";;".join(IMAGE_FORMATS))
        if dialog.exec_():
            files = dialog.selectedFiles();
            filetype = IMAGE_FORMATS[str(dialog.selectedNameFilter())]
            files = [str(file_) for file_ in files]
            try:
                self.loader = filetype.loader(files, config.IO_energyRegex)
                self.setImage(self.loader.next())
                self.enableProcessActions(True)
                self.prevButton.setEnabled(True)
                self.nextButton.setEnabled(True)
                self.slider.setEnabled(True)
                self.fileSaveScreenAction.setEnabled(True)
            except IOError, err:
                self.statusBar().showMessage('IOError: ' + str(err), 5000)
        
        # Set Slider boundaries.
        self.slider.setRange(1, len(files)+1)
        sliderCurrentPos = self.slider.setValue(1)
                

    def stopProcessing(self):
        self.stopped = True

    def run(self):
        global sliderCurrentPos
        
        # Added for live plotting
        global xs
        global ys
        global lin
        xs=[]
        ys=[]
        lin = [len(self.scene.items())]
        
        #
        
        if len(self.scene.items()) == 0:
            self.statusBar().showMessage("No integration window selected.", 5000)
        else:
            import time
            time_before = time.time()
        
            self.stopped = False
            progress = QProgressBar()
            stop = QPushButton("Stop", self)
            self.connect(stop, SIGNAL("clicked()"), self.stopProcessing)
            progress.setMinimum(int(self.loader.current_energy()))
            progress.setMaximum(int(self.loader.energies[-1]))
            statusLayout = QHBoxLayout()
            statusLayout.addWidget(progress)
            statusLayout.addWidget(stop)
            statusWidget = QWidget(self)
            statusWidget.setLayout(statusLayout)
            self.statusBar().addWidget(statusWidget)
            self.view.setInteractive(False)
            self.slider.setEnabled(False)
            self.scene.clearSelection()
            self.worker = Worker(self.scene.items(), self.current_energy, parent=self)
       
            self.fileSaveAction.setEnabled(True)
            self.fileSaveSpotsAction.setEnabled(True)
            
            # Added for liveplotting
            
            for plts in range(len(self.scene.items())):
                lin.append(plts)
                lin[plts], = self.plotwid.axes.plot([],[])

            #
            
            for image in self.loader:
                if self.stopped:
                    break
                progress.setValue(int(image[1]))
                QApplication.processEvents()
                self.setImage(image)
                self.worker.process(image)
                QApplication.processEvents()
                if config.GraphicsScene_livePlottingOn == True:
                    self.livePlotting()
                    if config.GraphicsScene_plotAverage == True:
                        self.plottingAverage()
                sliderCurrentPos = sliderCurrentPos + 1
                self.slider.setValue(sliderCurrentPos)

            self.view.setInteractive(True)
            self.slider.setEnabled(True)
            print "Total time acquisition:", time.time() - time_before, "s"
            self.statusBar().removeWidget(statusWidget)

    def disableInput(self):
        for item in self.scene.items():
            item.setFlag(QGraphicsItem.ItemIsSelectable, False)
            item.setFlag(QGraphicsItem.ItemIsFocusable, False)
            item.setFlag(QGraphicsItem.ItemIsMovable, False)

    def helpBoxShow(self):
        webbrowser.open("http://andim.github.io/easyleed/userdoc.html")

    def aboutBoxShow(self):
        self.aboutwid.show()

	## Plotting with matplotlib ##

    def livePlotting(self):
        """ Basic Matplotlib plotting I(E)-curve """

        global xs
        global ys
        global lin
        
        # do only if there's some data to draw the plot from, otherwise show an error message in the statusbar
        try:
            # getting intensities and energy from the worker class
            intensities = [model.m.intensity for model, tracker \
                                in self.worker.spots_map.itervalues()]
            energy = [model.m.energy for model, tracker in self.worker.spots_map.itervalues()]
                           
            # do the plot
            for x in energy:
                for y in intensities:
                    xs.append(x)
                    ys.append(y)
            for plts in range(len(self.scene.items())):
                lin[plts].set_data(xs[:][plts],ys[:][plts])

            self.plotwid.axes.relim()
            self.plotwid.axes.autoscale_view(True,True,True)
            # and show it
            self.plotwid.canvas.draw()
            # try to auto-adjust plot margins (might not be available in all matplotlib versions"
            try:
                self.plotwid.fig.tight_layout()
            except:
                pass
            self.plotwid.show()
            # can save the plot now
            self.fileSavePlotAction.setEnabled(True)
        except AttributeError:
            self.statusBar().showMessage("No plottable data.", 5000)


    def plotting(self):
        """ Basic Matplotlib plotting I(E)-curve """
        self.plotwid.axes.cla()
        self.plotwid.setupPlot()
        # do only if there's some data to draw the plot from, otherwise show an error message in the statusbar
        try:
            # getting intensities and energy from the worker class
            intensities = [model.m.intensity for model, tracker \
                                in self.worker.spots_map.itervalues()]
            energy = [model.m.energy for model, tracker in self.worker.spots_map.itervalues()]

            # do the plot
            for x in energy:
                for y in intensities:
                    self.plotwid.axes.plot(x, y)
            # and show it
            self.plotwid.canvas.draw()
            # try to auto-adjust plot margins (might not be available in all matplotlib versions"
            try:
                self.plotwid.fig.tight_layout()
            except:
                pass
            self.plotwid.show()
            # can save the plot now
            self.fileSavePlotAction.setEnabled(True)
        except AttributeError:
            self.statusBar().showMessage("No plottable data.", 5000)

    def plottingAverage(self):
        """ Mostly the same as normal plotting but plots the average of the calculated intensities """
        try:
            sum_intensity=0
            list_of_average_intensities = []
            intensities = [model.m.intensity for model, tracker \
                                in self.worker.spots_map.itervalues()]
            number_of_pictures = len(intensities[0])
            number_of_points = len(intensities)
            energy = [model.m.energy for model, tracker in self.worker.spots_map.itervalues()]
            intensities = flatten(intensities)
            for i in range(number_of_pictures):
                for j in range(i, len(intensities), number_of_pictures):
                    sum_intensity = sum_intensity + intensities[j]
                average_intensity = sum_intensity/number_of_points
                list_of_average_intensities.append(average_intensity)
                sum_intensity = 0

            self.plotwid.axes.plot(energy[0], list_of_average_intensities,'k-', linewidth=3, label = 'Average')
            
            self.plotwid.axes.relim()
            self.plotwid.axes.autoscale_view(True,True,True)
            
            self.plotwid.canvas.draw()
            self.plotwid.show()
            self.fileSavePlotAction.setEnabled(True)
        except AttributeError:
            self.statusBar().showMessage("No plottable data.", 5000)

    def plottingOptions(self):
        self.plotwid.setupPlot()
        if config.GraphicsScene_plotAverage == True:
            self.plottingAverage()
        else:
            self.plotting()

    def setParameters(self):

        QObject.connect(self.setparameterswid.acceptButton, SIGNAL("clicked()"), self.acceptParameters)
        QObject.connect(self.setparameterswid.applyButton, SIGNAL("clicked()"), self.applyParameters)
        QObject.connect(self.setparameterswid.defaultButton, SIGNAL("clicked()"), self.defaultValues)
        QObject.connect(self.setparameterswid.saveButton, SIGNAL("clicked()"), self.saveValues)
        QObject.connect(self.setparameterswid.loadButton, SIGNAL("clicked()"), self.loadValues)

        self.setparameterswid.show()

    def SetAllParameters(self):
        """Parameter setting control"""
        config.Tracking_inputPrecision = self.setparameterswid.inputPrecision.value()
        config.Tracking_windowScalingOn = self.setparameterswid.integrationWindowScale.isChecked()
        config.Tracking_minWindowSize = self.setparameterswid.integrationWindowRadius.value()
        config.GraphicsScene_defaultRadius = self.setparameterswid.integrationWindowRadiusNew.value()
        config.Tracking_minWindowSize = self.setparameterswid.integrationWindowRadius.value()
        config.Tracking_guessFunc = self.setparameterswid.spotIdentification.currentText()
        config.Tracking_gamma = self.setparameterswid.validationRegionSize.value()
        config.Tracking_minRsq = self.setparameterswid.determinationCoefficient.value()
        config.Processing_backgroundSubstractionOn = self.setparameterswid.backgroundSubstraction.isChecked()
        config.GraphicsScene_livePlottingOn = self.setparameterswid.livePlotting.isChecked()

    def acceptParameters(self):
        """Set user values to the parameters"""
        self.SetAllParameters()
        try:
            self.noiseList = [float(self.setparameterswid.value1.text()), float(self.setparameterswid.value2.text()), float(self.setparameterswid.value3.text()), float(self.setparameterswid.value4.text())]
            config.Tracking_processNoise = np.diag(self.noiseList)
            self.setparameterswid.close()
        except ValueError:
            self.setparameterswid.setText.wrongLabel("Invalid process noise value")

    def applyParameters(self):
        """Set user values to the parameters"""
        self.SetAllParameters()
        try:
            self.noiseList = [float(self.setparameterswid.value1.text()), float(self.setparameterswid.value2.text()), float(self.setparameterswid.value3.text()), float(self.setparameterswid.value4.text())]
            config.Tracking_processNoise = np.diag(self.noiseList)
        except ValueError:
            self.setparameterswid.setText.wrongLabel("Invalid process noise value")

    def defaultValues(self):
        """Reload config-module and get the default values"""
        reload(config)
        self.setparameterswid.inputPrecision.setValue(config.Tracking_inputPrecision)
        self.setparameterswid.integrationWindowRadiusNew.setValue(config.GraphicsScene_defaultRadius)
        self.setparameterswid.integrationWindowRadius.setValue(config.Tracking_minWindowSize)
        self.setparameterswid.validationRegionSize.setValue(config.Tracking_gamma)
        self.setparameterswid.determinationCoefficient.setValue(config.Tracking_minRsq)
        self.setparameterswid.integrationWindowScale.setChecked(config.Tracking_windowScalingOn)
        self.setparameterswid.backgroundSubstraction.setChecked(config.Processing_backgroundSubstractionOn)
        self.setparameterswid.value1.setText(str(config.Tracking_processNoise.diagonal()[0]))
        self.setparameterswid.value2.setText(str(config.Tracking_processNoise.diagonal()[1]))
        self.setparameterswid.value3.setText(str(config.Tracking_processNoise.diagonal()[2]))
        self.setparameterswid.value4.setText(str(config.Tracking_processNoise.diagonal()[3]))
        self.setparameterswid.livePlotting.setChecked(config.GraphicsScene_livePlottingOn)

    def saveValues(self):
        """ Basic saving of the set parameter values to a file """
        filename = str(QFileDialog.getSaveFileName(self, "Save the parameter configuration to a file"))
        if filename:
            output = open(filename, 'w')
            backgroundsublist = [float(self.setparameterswid.value1.text()), float(self.setparameterswid.value2.text()), float(self.setparameterswid.value3.text()), float(self.setparameterswid.value4.text())]
            writelist = [self.setparameterswid.inputPrecision.value(), self.setparameterswid.integrationWindowScale.isChecked(), self.setparameterswid.integrationWindowRadius.value(), self.setparameterswid.spotIdentification.currentText(), self.setparameterswid.validationRegionSize.value(), self.setparameterswid.determinationCoefficient.value(), self.setparameterswid.backgroundSubstraction.isChecked(), backgroundsublist,self.setparameterswid.livePlotting.isChecked()]
            pickle.dump(writelist, output)

    def loadValues(self):
        """ Load a file of set parameter values that has been saved with the widget """
        namefile = str(QFileDialog.getOpenFileName(self, 'Open spot location file'))
        try:
            loadput = open(namefile, 'r')
            loadlist = pickle.load(loadput)
            self.setparameterswid.inputPrecision.setValue(loadlist[0])
            self.setparameterswid.integrationWindowScale.setChecked(loadlist[1])
            self.setparameterswid.integrationWindowRadius.setValue(loadlist[2])
            self.setparameterswid.spotIdentification.setCurrentIndex(self.setparameterswid.spotIdentification.findText(loadlist[3]))
            self.setparameterswid.validationRegionSize.setValue(loadlist[4])
            self.setparameterswid.determinationCoefficient.setValue(loadlist[5])
            self.setparameterswid.backgroundSubstraction.setChecked(loadlist[6])
            self.setparameterswid.value1.setText(str(loadlist[7][0]))
            self.setparameterswid.value2.setText(str(loadlist[7][1]))
            self.setparameterswid.value3.setText(str(loadlist[7][2]))
            self.setparameterswid.value4.setText(str(loadlist[7][3]))
            self.setparameterswid.livePlotting.setChecked(loadlist[8])
        except:
            print "Invalid file"
       
    def savePlot(self):
        """ Saving the plot """
        # savefile prompt
        filename = str(QFileDialog.getSaveFileName(self, "Save the plot to a file"))
        if filename:
		    self.plotwid.fig.savefig(filename)

    def saveScreenShot(self):
        """ Save Screenshot """
        # savefile prompt
        filename = str(QFileDialog.getSaveFileName(self, "Save the image to a file"))
        if filename:
            pixMap = QPixmap().grabWidget(self.view)
            pixMap.save(filename + "_" + str(self.loader.energies[self.loader.index]) + "eV.png")

    def fileQuit(self):
        """Special quit-function as the normal window closing might leave something on the background """
        self.stopProcessing()
        QApplication.closeAllWindows()
        self.plotwid.canvas.close()

    def saveSpots(self):
        """saves the spot locations to a file, uses workers saveloc-function"""
        filename = str(QFileDialog.getSaveFileName(self, "Save the spot locations to a file"))
        if filename:
            self.worker.saveloc(filename)

    def loadSpots(self):
        """Load saved spot positions"""
        # FIXME: this does not work yet
        # This can probably be done in a better way
        filename = QFileDialog.getOpenFileName(self, 'Open spot location file')
        if filename:
            # pickle doesn't recognise the file opened by PyQt's openfile dialog as a file so 'normal' file processing
            pkl_file = open(filename, 'rb')
            # loading the zipped info to "location"
            location = pickle.load(pkl_file)
            pkl_file.close()
            # unzipping the "location"
            energy, locationx, locationy, radius = zip(*location)
            # NEED TO FIGURE OUT HOW TO GET ALL THE SPOTS TO RESPECTIVE ENERGIES, now only loads the first energy's spots
            # improving might involve modifying the algorithm for calculating intensity
            for i in range(len(energy)):
                #for j in range(len(energy[i])):
                # only taking the first energy location, [0] -> [j] for all, but now puts every spot to the first energy
                point = QPointF(locationx[i][0], locationy[i][0])
                item = QGraphicsSpotView(point, radius[i][0])
                # adding the item to the gui
                self.scene.clearSelection()
                self.scene.addItem(item)
                item.setSelected(True)
                self.scene.setFocusItem(item)
            
      
class Worker(QObject):
    """ Worker that manages the spots."""

    def __init__(self, spots, energy, parent=None):
        super(Worker, self).__init__(parent)
        self.spots_map = {}
        for spot in spots:
            pos = spot.scenePos()
            tracker = Tracker(pos.x(), pos.y(), spot.radius(), energy,
                        input_precision = config.Tracking_inputPrecision,
                        window_scaling = config.Tracking_windowScalingOn)
#            tracker = TrackerPhysics(pos.x(), pos.y(), 217, 218, spot.radius(), energy)
            self.spots_map[spot] = (QSpotModel(self), tracker)

        for view, tup in self.spots_map.iteritems():
            # view = QGraphicsSpotView, tup = (QSpotModel, tracker) -> tup[0] = QSpotModel
            self.connect(tup[0], SIGNAL("positionChanged"), view.onPositionChange)
            self.connect(tup[0], SIGNAL("radiusChanged"), view.onRadiusChange)

    def process(self, image):
        for model, tracker in self.spots_map.itervalues():
            tracker_result = tracker.feed_image(image)
            # feed_image returns x, y, intensity, energy and radius
            model.update(*tracker_result)

    def save(self, filename):
        intensities = [model.m.intensity for model, tracker \
                                in self.spots_map.itervalues()]
        energy = [model.m.energy for model, tracker in self.spots_map.itervalues()]
        zipped = zip(energy[0], *intensities)
        
        if config.Processing_backgroundSubstractionOn == True:
            np.savetxt(filename + "_bs.int", zipped)
        else:
            np.savetxt(filename + "_no-bs.int", zipped)
        
        x = [model.m.x for model, tracker \
                in self.spots_map.itervalues()]
        y = [model.m.y for model, tracker \
                in self.spots_map.itervalues()]
        x.extend(y)
        zipped = zip(energy[0], *x)
        np.savetxt(filename + ".pos", zipped)
        
    def saveloc(self, filename):
        # model = QSpotModel object tracker = tracker
        # dict function .itervalues() = return an iterator over the mapping's values
        energy = [model.m.energy for model, tracker in self.spots_map.itervalues()]
        locationx = [model.m.x for model, tracker in self.spots_map.itervalues()]
        locationy = [model.m.y for model, tracker in self.spots_map.itervalues()]
        radius = [model.m.radius for model, tracker in self.spots_map.itervalues()]
        locations = [locationx, locationy, radius]
        zipped = zip(energy, *locations)
        output = open(filename, 'wb')
        pickle.dump(zipped, output)
        output.close()  
    
