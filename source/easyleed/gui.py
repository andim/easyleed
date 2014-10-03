"""
easyleed.gui
-------------

Various classes for providing a graphical user interface.
"""


import logging
import webbrowser
import pickle

from PyQt4.QtCore import (QPoint, QRectF, QPointF, Qt, SIGNAL, QTimer, QObject)
from PyQt4.QtGui import (QApplication, QMainWindow, QGraphicsView,
    QGraphicsScene, QImage, QWidget, QHBoxLayout, QPen, QSlider,
    QVBoxLayout, QPushButton, QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsItem,
    QGraphicsSimpleTextItem, QToolButton,
    QPainter, QKeySequence, QAction, QIcon, QFileDialog, QProgressBar, QAbstractSlider,
    QBrush, QFrame, QLabel, QRadioButton, QGridLayout, QSpinBox, QDoubleSpinBox, QCheckBox,
    QComboBox, QLineEdit, QMessageBox, QPixmap)
import numpy as np

from . import config
from . import __version__
from . import __author__
from base import *
from io import *

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT

logging.basicConfig(filename = config.loggingFilename, level=config.loggingLevel)

class QGraphicsMovableItem(QGraphicsItem):
    """ Provides an QGraphicsItem that can be moved with the arrow keys.

        Pressing Shift at the same time allows fine adjustments. """

    def __init__(self, parent=None):
        super(QGraphicsMovableItem, self).__init__(parent)
        self.setFlags(QGraphicsItem.ItemIsMovable)

    def keyPressEvent(self, event):
        """ Handles keyPressEvents.

            The item can be moved using the arrow keys. Applying Shift
            at the same time allows fine adjustments.
        """
        if event.key() == Qt.Key_Right:
            if event.modifiers() & Qt.ShiftModifier:
                self.moveRight(config.QGraphicsMovableItem_smallMove)
            else:
                self.moveRight(config.QGraphicsMovableItem_bigMove)
        elif event.key() == Qt.Key_Left:
            if event.modifiers() & Qt.ShiftModifier:
                self.moveLeft(config.QGraphicsMovableItem_smallMove)
            else:
                self.moveLeft(config.QGraphicsMovableItem_bigMove)
        elif event.key() == Qt.Key_Up:
            if event.modifiers() & Qt.ShiftModifier:
                self.moveUp(config.QGraphicsMovableItem_smallMove)
            else:
                self.moveUp(config.QGraphicsMovableItem_bigMove)
        elif event.key() == Qt.Key_Down:
            if event.modifiers() & Qt.ShiftModifier:
                self.moveDown(config.QGraphicsMovableItem_smallMove)
            else:
                self.moveDown(config.QGraphicsMovableItem_bigMove)

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

    def onPositionChange(self, point):
        """ Handles incoming position change request."""
        self.setPos(point)

class QGraphicsSpotItem(QGraphicsEllipseItem, QGraphicsMovableItem):
    """ Provides an QGraphicsItem to display a Spot on a QGraphicsScene. """

    def __init__(self, point, radius, parent=None):
        super(QGraphicsSpotItem, self).__init__(parent)
        offset = QPointF(radius, radius)
        self.setRect(QRectF(-offset, offset))
        self.setPen(QPen(Qt.blue))
        self.setPos(point)
        self.setFlags(self.flags() |
                      QGraphicsItem.ItemIsSelectable|
                      QGraphicsItem.ItemIsFocusable)

    def keyPressEvent(self, event):
        """ Handles keyPressEvents.


            The circles radius can be changed using the plus and minus keys.
        """

        if event.key() == Qt.Key_Plus:
            self.changeSize(config.QGraphicsSpotItem_spotSizeChange)
        elif event.key() == Qt.Key_Minus:
            self.changeSize(-config.QGraphicsSpotItem_spotSizeChange)
        else:
            super(QGraphicsSpotItem, self).keyPressEvent(event)

    def onRadiusChange(self, radius):
        """ Handles incoming radius change request."""
        self.changeSize(radius - self.radius())


    def radius(self):
        return self.rect().width() / 2.0


    def changeSize(self, inc):
        """ Change radius by inc.
        
            inc > 0: increase
            inc < 0: decrease
        """

        inc /= 2**0.5 
        self.setRect(self.rect().adjusted(-inc, -inc, +inc, +inc))

class QGraphicsCenterItem(QGraphicsRectItem, QGraphicsMovableItem):
    """ Provides an QGraphicsItem to display the center position on a QGraphicsScene. """
    
    def __init__(self, point, size, parent=None):
        super(QGraphicsCenterItem, self).__init__(parent)
        offset = QPointF(size, size)
        self.setRect(QRectF(-offset, offset))
        self.setPen(QPen(Qt.red))
        self.setPos(point)
        self.setFlags(self.flags() |
                      QGraphicsItem.ItemIsSelectable|
                      QGraphicsItem.ItemIsFocusable)

class QSpotModel(QObject):
    """ Wraps a SpotModel to offer signals.

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
        self.spots = []
        self.center = None
    
    def mousePressEvent(self, event):
        """ Processes mouse events through either            
              - propagating the event
            or 
              - instantiating a new Circle (on left-click)
              - instantiating a new Center (on right-click)
        """
       
        if self.itemAt(event.scenePos()):
            super(GraphicsScene, self).mousePressEvent(event)
        elif event.button() == Qt.LeftButton:
            item = QGraphicsSpotItem(event.scenePos(),
                         config.GraphicsScene_defaultRadius)
            self.clearSelection()
            self.addItem(item)
            item.setSelected(True)
            self.setFocusItem(item)
            #print item.scenePos()
            self.spots.append(item)
        elif event.button() == Qt.RightButton:
            if self.center is None:
                item = QGraphicsCenterItem(event.scenePos(),
                        config.QGraphicsCenterItem_size)
                self.clearSelection()
                self.addItem(item)
                item.setSelected(True)
                self.setFocusItem(item)
                #print item.scenePos()
                self.center = item
            else:
                print "failure: center already defined"


    def keyPressEvent(self, event):
        """ Processes key events through either            
              - deleting the focus item
            or   
              - propagating the event

        """

        item = self.focusItem()
        if item:
            if event.key() == Qt.Key_Delete:
                if type(item) is QGraphicsSpotItem:
                    self.spots.remove(item)
                else:
                    self.center = None
                self.removeItem(item)
                del item
            else:
                super(GraphicsScene, self).keyPressEvent(event)

    def drawBackground(self, painter, rect):
        """ Draws image in background if it exists. """
        if hasattr(self, "image"):
            painter.drawImage(QPoint(0, 0), self.image)

    def setBackground(self, image, labeltext):
        """ Sets the background image. """
        if not hasattr(self, 'imlabel'):
            self.imlabel = QGraphicsSimpleTextItem(labeltext)
            self.imlabel.setBrush(QBrush(Qt.white))
            #self.imlabel.setPen(QPen(Qt.white))
            self.imlabel.setPos(5, 5)
            self.addItem(self.imlabel)
        self.imlabel.setText(labeltext)
        self.image = image
        self.update()
    
    def removeAll(self):
        """ Remove all items from the scene (leaves background unchanged). """
        for item in self.items():
            self.removeItem(item)
        self.spots = []
        self.center = None

class GraphicsView(QGraphicsView):
    """ Custom GraphicsView to display the scene. """
    def __init__(self, parent=None):
        super(GraphicsView, self).__init__(parent)
        self.setRenderHints(QPainter.Antialiasing)
    
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
        self.label = QLabel("<qt>Contacts: <a href = mailto:andisspam@gmail.com>andisspam@gmail.com</a>, <a href = mailto:feranick@hotmail.com> feranick@hotmail.com</a></qt>", self)
        self.label.setOpenExternalLinks(True);
        self.verticalLayout.addWidget(self.label)
        self.label = QLabel("More details: ", self)
        self.verticalLayout.addWidget(self.label)
        self.label = QLabel("<qt><a href = http://dx.doi.org/10.1016/j.cpc.2012.02.019>A Mayer, H Salopaasi, K Pussi, RD Diehl. Comput. Phys. Commun. 183, 1443-1447 (2012)</a>", self)
        self.label.setWordWrap(True)
        self.label.setOpenExternalLinks(True);
        self.verticalLayout.addWidget(self.label)

class PlotWidget(QWidget):
    """ Custom PyQt widget canvas for plotting """

    def __init__(self):
        super(PlotWidget, self).__init__()
        self.setWindowTitle("I(E)-curve")
        self.create_main_frame()
    
    def create_main_frame(self):       
        """ Create the mpl Figure and FigCanvas objects. """
        # 5x4 inches, 100 dots-per-inch
        self.setGeometry(700, 450, 600, 400)
        self.dpi = 100
        self.fig = Figure((5.0, 4.0), dpi=self.dpi)
        self.axes = self.fig.add_subplot(111)

        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        
        # Create the navigation toolbar, tied to the canvas
        self.mpl_toolbar = NavigationToolbar2QT(self.canvas, self)

        # Add checkbox for average
        self.averageCheck = QCheckBox("Average")
        self.averageCheck.setChecked(config.GraphicsScene_plotAverage)

        # Layout
        vbox = QVBoxLayout()
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.averageCheck)
        self.setLayout(vbox)

        # Define events for checkbox
        QObject.connect(self.averageCheck, SIGNAL("clicked()"), self.updatePlot)

    def setupPlot(self, worker):
        # Setup axis, labels, lines, ...
        if config.GraphicsScene_intensTimeOn == False:
            self.axes.set_xlabel("Energy [eV]")
        else:
            self.axes.set_xlabel("Frame")
        self.axes.set_ylabel("Intensity")
        # removes the ticks from y-axis
        self.axes.set_yticks([])
        self.worker = worker
        self.lines_map = {}
        for spot in self.worker.spots_map:
            self.lines_map[spot], = self.axes.plot([], [])
        # show line at y = 0
        self.axes.axhline(0.0)
        # try to auto-adjust plot margins (might not be available in all matplotlib versions)
        try:
            self.fig.tight_layout()
        except:
            pass
        self.updatePlot()
        self.show()

    def updatePlot(self):
        """ Basic Matplotlib plotting I(E)-curve """
        # update data
        for spot, line in self.lines_map.iteritems():
            line.set_data(self.worker.spots_map[spot][0].m.energy, self.worker.spots_map[spot][0].m.intensity)
        if self.averageCheck.isChecked():
            if not hasattr(self, 'averageLine'):
                self.averageLine, = self.axes.plot([], [], 'k', lw = 2, label = 'Average')
            intensity = np.zeros(self.worker.numProcessed())
            for model, tracker in self.worker.spots_map.itervalues():
                intensity += model.m.intensity
            intensity /= len(self.worker.spots_map)
            self.averageLine.set_data(model.m.energy, intensity)
        # ... axes limits
        self.axes.relim()
        self.axes.autoscale_view(True,True,True)
        # and show the new plot
        self.canvas.draw()

    def close(self):
        self.axes.cla()
        super(PlotWidget, self).close()

    def save(self):
        """ Saving the plot """
        # savefile prompt
        filename = str(QFileDialog.getSaveFileName(self, "Save the plot to a file"))
        if filename:
            self.fig.savefig(filename)

class ParameterSettingWidget(QWidget): 
    """PyQt widget for setting tracking parameters"""
 
    
    def __init__(self):
        super(ParameterSettingWidget, self).__init__()
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
        
        self.intensTime = QCheckBox("Extract I(time) - fixed energy")
        self.intensTime.setChecked(config.GraphicsScene_intensTimeOn)

        self.spotIdentification = QComboBox(self)
        self.spotIdentification.addItem("guess_from_Gaussian")
        self.siLabel = QLabel("Spot identification algorithm", self)

        self.fnLabel = QLabel("Kalman tracker process noise Q", self)
        self.processNoisePosition = QDoubleSpinBox(self)
        self.processNoisePosition.setSingleStep(0.1)
        self.processNoisePosition.setValue(config.Tracking_processNoisePosition)
        self.processNoisePositionLabel = QLabel("Position", self)
        self.processNoiseVelocity = QDoubleSpinBox(self)
        self.processNoiseVelocity.setSingleStep(0.1)
        self.processNoiseVelocity.setValue(config.Tracking_processNoiseVelocity)
        self.processNoiseVelocityLabel = QLabel("Velocity", self)

        self.saveButton = QPushButton('&Save', self)
        self.loadButton = QPushButton('&Load', self)
        self.defaultButton = QPushButton('&Default', self)
        self.wrongLabel = QLabel(" ", self)
        self.applyButton = QPushButton('&Apply', self)
        self.cancelButton = QPushButton('&Cancel', self)

        self.vertLine = QFrame()
        self.vertLine.setFrameStyle(QFrame.HLine)
        self.horLine = QFrame()
        self.horLine.setFrameStyle(QFrame.HLine)

        #Layouts
        self.setGeometry(700, 0, 300, 150)
        self.setWindowTitle('Set acquisition parameters')
     
        #base grid
        self.gridLayout = QGridLayout()
        self.setLayout(self.gridLayout)

        #vertical line layout
        self.vlineLayout = QVBoxLayout()
        self.vlineLayout.addWidget(self.vertLine)

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
        self.rvLayout.addWidget(self.intensTime)
        self.rvLayout.addWidget(self.horLine)
        self.rvLayout.addWidget(self.siLabel)
        self.rvLayout.addWidget(self.spotIdentification)
        self.rvLayout.addWidget(self.fnLabel)
        self.hpLayout = QHBoxLayout()
        self.rvLayout.addWidget(self.processNoisePositionLabel)
        self.rvLayout.addWidget(self.processNoisePosition)
        self.rvLayout.addWidget(self.processNoiseVelocityLabel)
        self.rvLayout.addWidget(self.processNoiseVelocity)

        #horizontal layout left
        self.hLayout = QHBoxLayout()
        self.hLayout.addWidget(self.saveButton)
        self.hLayout.addWidget(self.loadButton)
        self.hLayout.addWidget(self.defaultButton)
        self.hLayout.addWidget(self.wrongLabel)

        #horizontal layout right
        self.h2Layout = QHBoxLayout()
        self.h2Layout.addWidget(self.applyButton)
        self.h2Layout.addWidget(self.cancelButton)

        #adding layouts to the grid
        self.gridLayout.addLayout(self.lvLayout, 0, 0)
        self.gridLayout.addLayout(self.rvLayout, 0, 2)
        self.gridLayout.addLayout(self.hpLayout, 3, 1)
        self.gridLayout.addLayout(self.hLayout, 3, 0)
        self.gridLayout.addLayout(self.h2Layout, 3, 2)
        self.gridLayout.addLayout(self.vlineLayout, 0,1,3,1)

        QObject.connect(self.applyButton, SIGNAL("clicked()"), self.applyParameters)
        QObject.connect(self.defaultButton, SIGNAL("clicked()"), self.defaultValues)
        QObject.connect(self.saveButton, SIGNAL("clicked()"), self.saveValues)
        QObject.connect(self.loadButton, SIGNAL("clicked()"), self.loadValues)

    def applyParameters(self):
        """Parameter setting control"""
        config.Tracking_inputPrecision = self.inputPrecision.value()
        config.Tracking_windowScalingOn = self.integrationWindowScale.isChecked()
        config.Tracking_minWindowSize = self.integrationWindowRadius.value()
        config.GraphicsScene_defaultRadius = self.integrationWindowRadiusNew.value()
        config.Tracking_minWindowSize = self.integrationWindowRadius.value()
        config.Tracking_guessFunc = self.spotIdentification.currentText()
        config.Tracking_gamma = self.validationRegionSize.value()
        config.Tracking_minRsq = self.determinationCoefficient.value()
        config.Processing_backgroundSubstractionOn = self.backgroundSubstraction.isChecked()
        config.GraphicsScene_livePlottingOn = self.livePlotting.isChecked()
        config.GraphicsScene_intensTimeOn = self.intensTime.isChecked()
        config.Tracking_processNoisePosition = self.processNoisePosition
        config.Tracking_processNoiseVelocity = self.processNoiseVelocity

    def defaultValues(self):
        """Reload config-module and get the default values"""
        reload(config)
        self.inputPrecision.setValue(config.Tracking_inputPrecision)
        self.integrationWindowRadiusNew.setValue(config.GraphicsScene_defaultRadius)
        self.integrationWindowRadius.setValue(config.Tracking_minWindowSize)
        self.validationRegionSize.setValue(config.Tracking_gamma)
        self.determinationCoefficient.setValue(config.Tracking_minRsq)
        self.integrationWindowScale.setChecked(config.Tracking_windowScalingOn)
        self.backgroundSubstraction.setChecked(config.Processing_backgroundSubstractionOn)
        self.processNoisePosition.setValue(self.Tracking_processNoisePosition)
        self.processNoiseVelocity.setValue(self.Tracking_processNoiseVelocity)
        self.livePlotting.setChecked(config.GraphicsScene_livePlottingOn)

    def saveValues(self):
        """ Basic saving of the set parameter values to a file """
        pass
#        filename = str(QFileDialog.getSaveFileName(self, "Save the parameter configuration to a file"))
#        if filename:
#            output = open(filename, 'w')
#            writelist = [self.inputPrecision.value(), self.integrationWindowScale.isChecked(), self.integrationWindowRadius.value(), self.spotIdentification.currentText(), self.validationRegionSize.value(), self.determinationCoefficient.value(), self.backgroundSubstraction.isChecked(), backgroundsublist,self.livePlotting.isChecked()]
#            pickle.dump(writelist, output)

    def loadValues(self):
        """ Load a file of set parameter values that has been saved with the widget """
        pass
        #namefile = str(QFileDialog.getOpenFileName(self, 'Open spot location file'))
        #try:
        #    loadput = open(namefile, 'r')
        #    loadlist = pickle.load(loadput)
        #    self.inputPrecision.setValue(loadlist[0])
        #    self.integrationWindowScale.setChecked(loadlist[1])
        #    self.integrationWindowRadius.setValue(loadlist[2])
        #    self.spotIdentification.setCurrentIndex(self.spotIdentification.findText(loadlist[3]))
        #    self.validationRegionSize.setValue(loadlist[4])
        #    self.determinationCoefficient.setValue(loadlist[5])
        #    self.backgroundSubstraction.setChecked(loadlist[6])
        #    self.value1.setText(str(loadlist[7][0]))
        #    self.value2.setText(str(loadlist[7][1]))
        #    self.value3.setText(str(loadlist[7][2]))
        #    self.value4.setText(str(loadlist[7][3]))
        #    self.livePlotting.setChecked(loadlist[8])
        #except:
        #    print "Invalid file"

class MainWindow(QMainWindow):
    """ EasyLEED's main window. """
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("EasyLEED %s" % __version__)

        #### setup central widget ####
        self.aboutwid = AboutWidget()
        self.plotwid = PlotWidget()
        self.parametersettingwid = ParameterSettingWidget()
        self.scene = GraphicsScene(self)
        self.view = GraphicsView()
        self.view.setScene(self.scene)
        self.view.setMinimumSize(660, 480)
        self.setGeometry(10, 10, 660, 480)
        self.setCentralWidget(self.view)
        global sliderCurrentPos
        sliderCurrentPos = 1
        global processRemoveSpot
        
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

        processPlotOptions = self.createAction("&Plot...", self.plot,
                QKeySequence("Ctrl+d"), None,
                "Plot Intensities.")
        processSetParameters = self.createAction("&Set Parameters", self.parametersettingwid.show,
                None, None,
                "Set tracking parameters.")
        processRemoveSpot = self.createAction("&Remove Spot", self.removeLastSpot,
                None, None,
                "Remove Last Spot.")

        self.processActions = [processNextAction, processPreviousAction, None, processRunAction, processStopAction, processRestartAction, None, processPlotOptions, None, processRemoveSpot]
        fileOpenAction = self.createAction("&Open...", self.fileOpen,
                QKeySequence.Open, None,
                "Open a directory containing the image files.")
        self.fileSaveAction = self.createAction("&Save intensities...", self.saveIntensity,
                QKeySequence.Save, None,
                "Save the calculated intensities to a text file.")
                
        # actions to "File" menu
        self.fileSavePlotAction = self.createAction("&Save plot...", self.plotwid.save,
                QKeySequence("Ctrl+a"), None,
                "Save the plot to a pdf file.")
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
        self.aboutAction = self.createAction("&About", self.aboutwid.show,
                None, None,
                "About EasyLEED")
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
        self.toolBarActions = [self.fileQuitAction, None, fileOpenAction, None, processRunAction, None, processStopAction, None, processPlotOptions, None, processSetParameters, None, processRemoveSpot, None, processRestartAction]
        self.addActions(toolBar, self.toolBarActions)
        
        #### Create status bar ####
        self.statusBar().showMessage("Ready", 5000)

        ### Create previous and next buttons
        self.prevButton = QToolButton(self)
        self.prevButton.setArrowType(Qt.LeftArrow)
        self.nextButton = QToolButton(self)
        self.nextButton.setArrowType(Qt.RightArrow)
        self.prevButton.setEnabled(False)
        self.nextButton.setEnabled(False)
        
        ### Create slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        
        ### Create "next" and "previous" buttons.
        self.statusBar().addPermanentWidget(self.prevButton)
        self.statusBar().addPermanentWidget(self.nextButton)
        self.statusBar().addPermanentWidget(self.slider)
    
        ### Create event connector for slider
        QObject.connect(self.slider, SIGNAL("sliderMoved(int)"), self.slider_moved)
        QObject.connect(self.prevButton, SIGNAL("clicked()"), self.prevBtnClicked)
        QObject.connect(self.nextButton, SIGNAL("clicked()"), self.nextBtnClicked)
    

    def slider_moved(self, sliderNewPos):
        """
        This function tracks what to do with a slider movement.
            
        """
        global sliderCurrentPos
        self.worker = Worker(self.scene.spots, self.scene.center, self.current_energy, parent=self)

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
        self.worker = Worker(self.scene.spots, self.scene.center, self.current_energy, parent=self)
        self.previous()
        self.worker.process(self.loader.this())

    def nextBtnClicked(self):
        self.worker = Worker(self.scene.spots, self.scene.center, self.current_energy, parent=self)
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
        """ Delete stored plot information and start fresh """
        self.scene.removeAll()
        self.loader.restart()
        self.setImage(self.loader.next())
        self.plotwid.close()
        sliderCurrentPos = self.slider.setValue(1)

    def setImage(self, image):
        npimage, energy = image
        qimage = npimage2qimage(npimage)
        self.view.setSceneRect(QRectF(qimage.rect()))
        if config.GraphicsScene_intensTimeOn == False:
            labeltext = "Energy: %s eV" % energy
        else:
            labeltext = "Frame: %s" % energy
        self.scene.setBackground(qimage, labeltext)
        self.current_energy = energy

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
            # Set Slider boundaries.
            self.slider.setRange(1, len(files)+1)
            try:
                self.loader = filetype.loader(files, config.IO_energyRegex)
                self.setImage(self.loader.next())
                self.enableProcessActions(True)
                self.prevButton.setEnabled(True)
                self.nextButton.setEnabled(True)
                self.slider.setEnabled(True)
                self.fileSaveScreenAction.setEnabled(True)
                sliderCurrentPos = self.slider.setValue(1)
            except IOError, err:
                self.statusBar().showMessage('IOError: ' + str(err), 5000)

    def removeLastSpot(self):
        if len(self.scene.items(0)) > 1:
            self.scene.spots.remove(self.scene.spots[-1])
            self.scene.removeItem(self.scene.items(0)[-1])

    def stopProcessing(self):
        self.stopped = True

    def plot(self): 
        self.plotwid.setupPlot(self.worker)
        # can save the plot now
        self.fileSavePlotAction.setEnabled(True)

    def run(self):
        global sliderCurrentPos

        if len(self.scene.spots) == 0:
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
            processRemoveSpot.setEnabled(False)
            self.scene.clearSelection()
            self.worker = Worker(self.scene.spots, self.scene.center, self.current_energy, parent=self)
            self.fileSaveAction.setEnabled(True)
            self.fileSaveSpotsAction.setEnabled(True)

            if config.GraphicsScene_livePlottingOn == True:
                self.plot()
            
            for image in self.loader:
                if self.stopped:
                    break
                progress.setValue(int(image[1]))
                QApplication.processEvents()
                self.setImage(image)
                self.worker.process(image)
                QApplication.processEvents()
                if config.GraphicsScene_livePlottingOn == True:
                    self.plotwid.updatePlot()
                sliderCurrentPos = sliderCurrentPos + 1
                self.slider.setValue(sliderCurrentPos)

            self.view.setInteractive(True)
            self.slider.setEnabled(True)
            processRemoveSpot.setEnabled(True)
            print "Total time acquisition:", time.time() - time_before, "s"
            self.statusBar().removeWidget(statusWidget)

    def disableInput(self):
        for item in self.scene.spots:
            item.setFlag(QGraphicsItem.ItemIsSelectable, False)
            item.setFlag(QGraphicsItem.ItemIsFocusable, False)
            item.setFlag(QGraphicsItem.ItemIsMovable, False)

    def helpBoxShow(self):
        webbrowser.open("http://andim.github.io/easyleed/userdoc.html")


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
        """Saves the spot locations to a file, uses workers saveloc-function"""
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
                item = QGraphicsSpotItem(point, radius[i][0])
                # adding the item to the gui
                self.scene.clearSelection()
                self.scene.addItem(item)
                item.setSelected(True)
                self.scene.setFocusItem(item)
            
class Worker(QObject):
    """ Worker that manages the spots."""

    def __init__(self, spots, center, energy, parent=None):
        super(Worker, self).__init__(parent)
        # spots_map:
        # - key: spot
        # - value: SpotModel, Tracker
        self.spots_map = {}
        for spot in spots:
            pos = spot.scenePos()
            if center:
                tracker = Tracker(pos.x(), pos.y(), spot.radius(), energy, center.x(), center.y(),
                            input_precision = config.Tracking_inputPrecision,
                            window_scaling = config.Tracking_windowScalingOn)
            else:
                tracker = Tracker(pos.x(), pos.y(), spot.radius(), energy,
                            input_precision = config.Tracking_inputPrecision,
                            window_scaling = config.Tracking_windowScalingOn)
            self.spots_map[spot] = (QSpotModel(self), tracker)

        for view, tup in self.spots_map.iteritems():
            # view = QGraphicsSpotItem, tup = (QSpotModel, tracker) -> tup[0] = QSpotModel
            self.connect(tup[0], SIGNAL("positionChanged"), view.onPositionChange)
            self.connect(tup[0], SIGNAL("radiusChanged"), view.onRadiusChange)

    def process(self, image):
        for model, tracker in self.spots_map.itervalues():
            tracker_result = tracker.feed_image(image)
            # feed_image returns x, y, intensity, energy and radius
            model.update(*tracker_result)

    def numProcessed(self):
        """ Return the number of processed images. """
        return len(self.spots_map.itervalues().next()[0].m.energy)

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
    
