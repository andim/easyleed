"""
easyleed.gui
-------------

Various classes for providing a graphical user interface.
"""

import webbrowser
import pickle
import six
import time

from .qt import get_qt_binding_name, qt_filedialog_convert
from .qt.QtCore import (QPoint, QRectF, QPointF, Qt, QTimer, QObject)
from .qt.QtCore import pyqtSignal as Signal
from .qt.widgets import (QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
                             QWidget, QHBoxLayout, QGraphicsEllipseItem, QGraphicsRectItem,
                             QGraphicsItem,QGraphicsSimpleTextItem, QSlider, QVBoxLayout,
                             QPushButton, QToolButton, QAction, QFileDialog, QProgressBar,
                             QAbstractSlider, QFrame, QLabel, QRadioButton, QGridLayout,
                             QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, QLineEdit, QMessageBox)
from .qt.QtGui import (QImage, QPen, QIcon, QTransform, QImageWriter,
                       QPainter, QBrush, QKeySequence, QPixmap)

from . import config
from . import __version__
from . import __author__
from .base import *
from .io import *

import numpy as np
from scipy import interpolate

from matplotlib.figure import Figure
if get_qt_binding_name() == 'pyqt5':
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt5 import NavigationToolbar2QT
else:
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt4 import NavigationToolbar2QT

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

    intensityChanged = Signal(object)
    positionChanged = Signal(object)
    radiusChanged = Signal(object)

    def __init__(self, parent=None):
        super(QSpotModel, self).__init__(parent)
        self.m = SpotModel()

    def update(self, x, y, intensity, energy, radius):
        self.m.update(x, y, intensity, energy, radius)
        self.intensityChanged.emit(intensity)
        self.positionChanged.emit(QPointF(x, y))
        self.radiusChanged.emit(radius)

class GraphicsScene(QGraphicsScene):
    """ Custom GraphicScene having all the main content."""

    def __init__(self, parent=None):
        super(GraphicsScene, self).__init__(parent)
        self.spots = []
        self.center = None
        self.spotsLabel = []
    
    def mousePressEvent(self, event):
        """ Processes mouse events through either
              - propagating the event
            or 
              - instantiating a new Circle (on left-click)
              - instantiating a new Center (on right-click)
        """
        transform = QTransform()
        if hasattr(self, "image"):
            if self.itemAt(event.scenePos(), transform):
                super(GraphicsScene, self).mousePressEvent(event)
            elif event.button() == Qt.LeftButton:
                item = QGraphicsSpotItem(event.scenePos(),
                        config.GraphicsScene_defaultRadius)
                self.clearSelection()
                self.addItem(item)
                item.setSelected(True)
                self.setFocusItem(item)
                self.spots.append(item)
                self.spotsLabel.append(str(len(self.spots)-1))
                item.setToolTip(self.spotsLabel[-1])
                # Enable spots to be saved when present on the image
                #if len(self.spots) > 0:
                #    self.parent().fileSaveSpotsAction.setEnabled(True)

            elif event.button() == Qt.RightButton:
                if self.center is None:
                    item = QGraphicsCenterItem(event.scenePos(),
                        config.QGraphicsCenterItem_size)
                    self.clearSelection()
                    self.addItem(item)
                    item.setSelected(True)
                    self.setFocusItem(item)
                    self.center = item
                    self.parent().fileSaveCenterAction.setEnabled(True)
                else:
                    print("failure: center already defined")
        else:
            self.parent().statusBar().showMessage("Spots require a loaded image", 5000)

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
                    self.removeItem(item)
                elif type(item) is QGraphicsCenterItem:
                    self.removeCenter()
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
            self.imlabel.setPos(5, 5)
        if not hasattr(self,"image") or len(self.items()) < 1:
            self.addItem(self.imlabel)
        self.imlabel.setText(labeltext)
        self.image = image
        self.update()
    
    def removeAll(self):
        """ Remove all items from the scene (leaves background unchanged). """
        for item in self.items():
            if type(item) == QGraphicsSpotItem:
                self.removeItem(item)
        self.spots = []
        self.removeCenter()

    def removeCenter(self):
        """ Remove all items from the scene (leaves background unchanged). """
        if self.center is not None:
            center = self.center
            self.removeItem(center)
            del center
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

        self.labelTitle = QLabel("<qt><b><big><a href = http://andim.github.io/easyleed/index.html>EasyLEED %s</a></b></big></qt>" % __version__, self);
        self.labelBy = QLabel("by: %s" % __author__, self)
        self.labelContact = QLabel("<qt>Contacts: <a href = mailto:andimscience@gmail.com>andimscience@gmail.com</a>, <a href = mailto:feranick@hotmail.com> feranick@hotmail.com</a></qt>", self)
        self.labelDetails = QLabel("If EasyLEED has been useful in your research please cite: ", self)
        self.labelPaper = QLabel("<qt><a href = http://dx.doi.org/10.1016/j.cpc.2012.02.019>A Mayer, H Salopaasi, K Pussi, RD Diehl. Comput. Phys. Commun. 183, 1443-1447 (2012)</a>", self)
        for label in [self.labelTitle, self.labelBy, self.labelContact, self.labelDetails, self.labelPaper]:
            label.setWordWrap(True)
            label.setOpenExternalLinks(True);
            self.verticalLayout.addWidget(label)

class CustomPlotToolbar(NavigationToolbar2QT):
    # only display the buttons we need
    toolitems = [t for t in NavigationToolbar2QT.toolitems if
                t[0] in ('Home', None,'Pan','Zoom','Save')]
        
    def __init__(self, *args, **kwargs):
        super(CustomPlotToolbar, self).__init__(*args, **kwargs)
        self.layout().takeAt(1)  #or more than 1 if you have more buttons

class PlotWidget(QWidget):
    """ Custom PyQt widget canvas for plotting """

    def __init__(self):
        super(PlotWidget, self).__init__()
        self.setWindowTitle("I(E)-curve")
        self.create_main_frame()
    
    def create_main_frame(self):       
        """ Create the mpl Figure and FigCanvas objects. """
        # 5x4 inches, 100 dots-per-inch
        self.setGeometry(700, 420, 600, 500)
        self.dpi = 100
        self.fig = Figure((5.0, 4.0), dpi=self.dpi)
        self.axes = self.fig.add_subplot(111)

        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        
        # Create the navigation toolbar, tied to the canvas
        self.mpl_toolbar = CustomPlotToolbar(self.canvas, self)

        # Add checkbox for average
        self.averageCheck = QCheckBox("Average")
        self.averageCheck.setChecked(config.GraphicsScene_plotAverage)
        # Add checkbox for smooth average
        self.smoothCheck = QCheckBox("Smooth Average")
        self.smoothCheck.setChecked(config.GraphicsScene_plotSmoothAverage)
        # Add checkbox for hiding legend in plot
        self.legendCheck = QCheckBox("Show Legend")
        self.legendCheck.setChecked(False)
        # Add cButton for clearing plot
        self.clearPlotButton = QPushButton('&Clear Plot', self)
        
        # Layout
        self.gridLayout = QGridLayout()
        self.setLayout(self.gridLayout)
        
        self.gridLayout.addWidget(self.mpl_toolbar, 0, 0, 1, -1)
        self.gridLayout.addWidget(self.canvas, 1, 0, 1, -1)
        self.gridLayout.addWidget(self.averageCheck, 2, 0, 1, 1)
        self.gridLayout.addWidget(self.smoothCheck, 3, 0, 1, 1)
        self.gridLayout.addWidget(self.clearPlotButton, 2, 1, 1, 1)
        self.gridLayout.addWidget(self.legendCheck, 3, 1, 1, 1)

        # Define events for checkbox
        self.averageCheck.clicked.connect(self.onAverageCheck)
        for button in [self.smoothCheck, self.legendCheck, self.clearPlotButton]:
            button.clicked.connect(self.updatePlot)
        
    def initPlot(self):
        # Setup axis, labels, lines, ...
        if config.GraphicsScene_intensTimeOn:
            self.axes.set_xlabel("Frame")
        else:
            self.axes.set_xlabel("Energy [eV]")
        self.axes.set_ylabel("Intensity [a.u.]")
        # removes the ticks from y-axis
        self.axes.set_yticks([])

    def setupPlot(self, worker):
        self.initPlot()
        self.worker = worker
        self.lines_map = {}
        j = 0
        for spot in self.worker.spots_map:
            self.lines_map[spot], = self.axes.plot([], [], label= str(j))
            j+=1
        
        # set up averageLine
        self.averageLine, = self.axes.plot([], [], 'k', lw=2, label='Average')
        # set up averageSmoothLine
        self.averageSmoothLine, = self.axes.plot([], [], 'b', lw=2, label='Smooth Average')
        
        # show dashed line at y = 0
        self.axes.axhline(0.0, color='k', ls='--')
        # try to auto-adjust plot margins (might not be available in all matplotlib versions)
        try:
            self.fig.tight_layout()
        except:
            pass
        self.updatePlot()
        self.axes.legend(fontsize=10)
        self.axes.legend().set_visible(self.legendCheck.isChecked())
        self.show()

    def onAverageCheck(self):
        if self.averageCheck.isChecked():
            self.smoothCheck.setEnabled(True)
        else:
            self.smoothCheck.setEnabled(False)
        self.updatePlot()

    def updatePlot(self):
        """ Basic Matplotlib plotting I(E)-curve """
        for spot, line in six.iteritems(self.lines_map):
            line.set_data(self.worker.spots_map[spot][0].m.energy, self.worker.spots_map[spot][0].m.intensity)
        if self.averageCheck.isChecked():
            intensity = np.zeros(self.worker.numProcessed())
            for model, tracker in six.itervalues(self.worker.spots_map):
                intensity += model.m.intensity
            intensity /= len(self.worker.spots_map)
            self.averageLine.set_data(model.m.energy, intensity)
            
            if self.smoothCheck.isChecked():
                tck = interpolate.splrep(model.m.energy, intensity, s=config.GraphicsScene_smoothSpline)
                xnew = np.arange(model.m.energy[0], model.m.energy[-1],
                                 (model.m.energy[1]-model.m.energy[0])*config.GraphicsScene_smoothPoints)
                ynew = interpolate.splev(xnew, tck, der=0)
                self.averageSmoothLine.set_data(xnew, ynew)
            else:
                self.averageSmoothLine.set_data([], [])
        else:
            self.averageLine.set_data([], [])

        if self.axes.legend() is not None:
            # decide whether to show legend
            self.axes.legend().set_visible(self.legendCheck.isChecked())
            
        # ... axes limits
        self.axes.relim()
        self.axes.autoscale_view(True, True, True)
        # and show the new plot
        self.canvas.draw()

    def clearPlot(self):
        self.axes.cla()
        self.initPlot()
        self.canvas.draw()

    def save(self):
        """ Saving the plot """
        filename = "plot.png"
        filename = qt_filedialog_convert(QFileDialog.getSaveFileName(self,
                                                    "Save the plot to a file",
                                                    filename))
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
        self.dcLabel = QLabel("Minimal R" + chr(0x00B2) + " to accept fit", self)

        self.integrationWindowScale = QCheckBox("Scale integration window with changing energy")
        self.integrationWindowScale.setChecked(config.Tracking_windowScalingOn)

        self.backgroundSubstraction = QCheckBox("Background substraction")
        self.backgroundSubstraction.setChecked(config.Processing_backgroundSubstractionOn)
        
        self.livePlotting = QCheckBox("Plot I(E) intensities during acquisition")
        self.livePlotting.setChecked(config.GraphicsScene_livePlottingOn)
        
        self.intensTime = QCheckBox("Extract I(frame) - fixed energy")
        self.intensTime.setChecked(config.GraphicsScene_intensTimeOn)
        
        self.smoothPoints = QSpinBox(self)
        self.smoothPoints.setWrapping(True)
        self.smoothPoints.setToolTip("Press Enter to update plot")
        self.smoothPoints.setValue(config.GraphicsScene_smoothPoints)
        self.smPoiLabel = QLabel("# points to be rescaled for smoothing", self)
        
        self.smoothSpline = QSpinBox(self)
        self.smoothSpline.setWrapping(True)
        self.smoothSpline.setToolTip("Press Enter to update plot")
        self.smoothSpline.setValue(config.GraphicsScene_smoothSpline)
        self.smSplLabel = QLabel("Amount of smoothing to perform", self)

        self.spotIdentification = QComboBox(self)
        self.spotIdentification.addItem("guess_from_Gaussian")
        self.siLabel = QLabel("Spot ident. algorithm", self)

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

        self.vertLine = QFrame()
        self.vertLine.setFrameStyle(QFrame.VLine)
        self.horLine = QFrame()
        self.horLine.setFrameStyle(QFrame.HLine)
        self.horLine2 = QFrame()
        self.horLine2.setFrameStyle(QFrame.HLine)

        #Layouts
        self.setGeometry(700, 30, 300, 100)
        self.setWindowTitle('Set acquisition parameters')
     
        #base grid
        self.gridLayout = QGridLayout()
        self.setLayout(self.gridLayout)

        #vertical line layout
        self.vlineLayout = QVBoxLayout()
        self.vlineLayout.addWidget(self.vertLine)

        #1st (left) vertical layout
        self.lh1Layout = QHBoxLayout()
        self.lh1Layout.addWidget(self.ipLabel)
        self.lh1Layout.addWidget(self.inputPrecision)
        self.lh2Layout = QHBoxLayout()
        self.lh2Layout.addWidget(self.iwrnLabel)
        self.lh2Layout.addWidget(self.integrationWindowRadiusNew)
        self.lh3Layout = QHBoxLayout()
        self.lh3Layout.addWidget(self.iwrLabel)
        self.lh3Layout.addWidget(self.integrationWindowRadius)
        self.lh4Layout = QHBoxLayout()
        self.lh4Layout.addWidget(self.vrsLabel)
        self.lh4Layout.addWidget(self.validationRegionSize)
        self.lh5Layout = QHBoxLayout()
        self.lh5Layout.addWidget(self.dcLabel)
        self.lh5Layout.addWidget(self.determinationCoefficient)
        self.lh6Layout = QHBoxLayout()
        self.lh6Layout.addWidget(self.smPoiLabel)
        self.lh6Layout.addWidget(self.smoothPoints)
        self.lh7Layout = QHBoxLayout()
        self.lh7Layout.addWidget(self.smSplLabel)
        self.lh7Layout.addWidget(self.smoothSpline)
        self.lh8Layout = QHBoxLayout()
        self.lh8Layout.addWidget(self.horLine)

        #2nd (right) vertical layout
        self.rh1Layout = QHBoxLayout()
        self.rh1Layout.addWidget(self.intensTime)
        self.rh2Layout = QHBoxLayout()
        self.rh2Layout.addWidget(self.integrationWindowScale)
        self.rh3Layout = QHBoxLayout()
        self.rh3Layout.addWidget(self.backgroundSubstraction)
        self.rh4Layout = QHBoxLayout()
        self.rh4Layout.addWidget(self.livePlotting)
        self.rh5Layout = QHBoxLayout()
        self.rh5Layout.addWidget(self.horLine2)
        self.rh6Layout = QHBoxLayout()
        self.rh6Layout.addWidget(self.siLabel)
        self.rh6Layout.addWidget(self.spotIdentification)
        self.rh7Layout = QHBoxLayout()
        self.rh7Layout.addWidget(self.fnLabel)
        self.rh8Layout = QHBoxLayout()
        self.rh8Layout.addWidget(self.processNoisePositionLabel)
        self.rh8Layout.addWidget(self.processNoisePosition)
        self.rh9Layout = QHBoxLayout()
        self.rh9Layout.addWidget(self.processNoiseVelocityLabel)
        self.rh9Layout.addWidget(self.processNoiseVelocity)

        #horizontal layout left
        self.hLayout = QHBoxLayout()
        self.hLayout.addWidget(self.loadButton)
        self.hLayout.addWidget(self.saveButton)
        self.hLayout.addWidget(self.defaultButton)
        self.hLayout.addWidget(self.wrongLabel)
        self.hLayout.addWidget(self.applyButton)

        #adding layouts to the grid
        self.gridLayout.addLayout(self.lh1Layout, 0, 0)
        self.gridLayout.addLayout(self.lh2Layout, 1, 0)
        self.gridLayout.addLayout(self.lh3Layout, 2, 0)
        self.gridLayout.addLayout(self.lh4Layout, 3, 0)
        self.gridLayout.addLayout(self.lh5Layout, 4, 0)
        self.gridLayout.addLayout(self.lh6Layout, 5, 0)
        self.gridLayout.addLayout(self.lh7Layout, 6, 0)
        self.gridLayout.addLayout(self.lh8Layout, 7, 0)
        
        self.gridLayout.addLayout(self.rh1Layout, 0, 2)
        self.gridLayout.addLayout(self.rh2Layout, 1, 2)
        self.gridLayout.addLayout(self.rh3Layout, 2, 2)
        self.gridLayout.addLayout(self.rh4Layout, 3, 2)
        self.gridLayout.addLayout(self.rh5Layout, 4, 2)
        self.gridLayout.addLayout(self.rh6Layout, 5, 2)
        self.gridLayout.addLayout(self.rh7Layout, 6, 2)
        self.gridLayout.addLayout(self.rh8Layout, 7, 2)
        self.gridLayout.addLayout(self.rh9Layout, 8, 2)
        
        self.gridLayout.addLayout(self.hLayout, 8, 0)
        self.gridLayout.addLayout(self.vlineLayout, 0, 1, 9, 1)

        self.applyButton.clicked.connect(self.applyParameters)
        self.defaultButton.clicked.connect(self.defaultValues)
        self.saveButton.clicked.connect(self.saveValues)
        self.loadButton.clicked.connect(self.loadValues)
    
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
        config.Tracking_processNoisePosition = self.processNoisePosition.value()
        config.Tracking_processNoiseVelocity = self.processNoiseVelocity.value()
        config.GraphicsScene_smoothPoints = self.smoothPoints.value()
        config.GraphicsScene_smoothSpline = self.smoothSpline.value()

    def defaultValues(self):
        """Reload config-module and get the default values"""
        reload(config)
        self.inputPrecision.setValue(config.Tracking_inputPrecision)
        self.integrationWindowRadiusNew.setValue(config.GraphicsScene_defaultRadius)
        self.integrationWindowRadius.setValue(config.Tracking_minWindowSize)
        self.validationRegionSize.setValue(config.Tracking_gamma)
        self.determinationCoefficient.setValue(config.Tracking_minRsq)
        self.smoothPoints.setValue(config.GraphicsScene_smoothPoints)
        self.smoothSpline.setValue(config.GraphicsScene_smoothSpline)
        self.intensTime.setChecked(config.GraphicsScene_intensTimeOn)
        self.integrationWindowScale.setChecked(config.Tracking_windowScalingOn)
        self.backgroundSubstraction.setChecked(config.Processing_backgroundSubstractionOn)
        self.livePlotting.setChecked(config.GraphicsScene_livePlottingOn)
        self.processNoisePosition.setValue(config.Tracking_processNoisePosition)
        self.processNoiseVelocity.setValue(config.Tracking_processNoiseVelocity)

    def saveValues(self):
        """ Basic saving of the set parameter values to a file """
        filename = qt_filedialog_convert(QFileDialog.getSaveFileName(self, "Save the parameter configuration to a file"))
        if filename:
            output = open(filename, 'w')
            writelist = [self.inputPrecision.value(), self.integrationWindowRadiusNew.value(),
                         self.integrationWindowRadius.value(), self.validationRegionSize.value(),
                         self.determinationCoefficient.value(), self.smoothPoints.value(),
                         self.smoothSpline.value(), self.intensTime.isChecked(),
                         self.integrationWindowScale.isChecked() , self.backgroundSubstraction.isChecked(),
                         self.livePlotting.isChecked(), self.spotIdentification.currentIndex(),
                         self.processNoisePosition.value(), self.processNoiseVelocity.value()]
            pickle.dump(writelist, output)
            print("Custom settings saved.")

    def loadValues(self):
        """ Load a file of set parameter values that has been saved with the widget """
        filename = qt_filedialog_convert(QFileDialog.getOpenFileName(self, 'Open spot location file'))
        try:
            loadput = open(filename, 'r')
            loadlist = pickle.load(loadput)
            self.inputPrecision.setValue(loadlist[0])
            self.integrationWindowRadiusNew.setValue(loadlist[1])
            self.integrationWindowRadius.setValue(loadlist[2])
            self.validationRegionSize.setValue(loadlist[3])
            self.determinationCoefficient.setValue(loadlist[4])
            self.smoothPoints.setValue(loadlist[5])
            self.smoothSpline.setValue(loadlist[6])
            self.intensTime.setChecked(loadlist[7])
            self.integrationWindowScale.setChecked(loadlist[8])
            self.backgroundSubstraction.setChecked(loadlist[9])
            self.livePlotting.setChecked(loadlist[10])
            self.spotIdentification.setCurrentIndex(loadlist[11])
            self.processNoisePosition.setValue(loadlist[12])
            self.processNoiseVelocity.setValue(loadlist[13])
            print("Custom settings restored.")
        except:
            print("Invalid file")

class MainWindow(QMainWindow):
    """ EasyLEED's main window. """
    
    sliderCurrentPos = 1
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
        self.setGeometry(10, 30, 660, 480)
        self.setCentralWidget(self.view)
        
        #### define actions ####

        ## actions for "Process" menu
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
                QKeySequence("Ctrl+p"), None,
                "Plot Intensities.")
        processSetParameters = self.createAction("&Set Parameters", self.parametersettingwid.show,
                None, None,
                "Set tracking parameters.")
        self.processRemoveSpot = self.createAction("&Remove Spot", self.removeLastSpot,
                None, None,
                "Remove Last Spot.")

        self.processActions = [processNextAction, processPreviousAction, None, processRunAction, processStopAction, processRestartAction, None, processPlotOptions, None, self.processRemoveSpot]
        
        # actions for "File" menu
        self.fileOpenAction = self.createAction("&Open...", self.fileOpen,
                QKeySequence.Open, None,
                "Open a directory containing the image files.")
        self.fileSaveAction = self.createAction("&Save intensities...", self.saveIntensity,
                QKeySequence.Save, None,
                "Save the calculated intensities to a text file.")
        self.fileSavePlotAction = self.createAction("&Save plot...", self.plotwid.save,
                QKeySequence("Ctrl+a"), None,
                "Save the plot to a pdf file.")
        self.fileSaveScreenAction = self.createAction("&Save screenshot...", self.saveScreenShot,
                QKeySequence("Ctrl+d"), None,
                "Save image to a file.")
        self.fileQuitAction = self.createAction("&Quit", self.fileQuit,
                QKeySequence("Ctrl+q"), None,
                "Close the application.")
        self.fileSaveSpotsAction = self.createAction("&Save spot locations...", self.saveSpots,
                QKeySequence("Ctrl+c"), None,
                "Save the spots to a file.")
        self.fileLoadSpotsAction = self.createAction("&Load spot locations...", self.loadSpots,
                QKeySequence("Ctrl+v"), None,
                "Load spots from a file.")
        self.fileSaveCenterAction = self.createAction("&Save center location...", self.saveCenter,
                QKeySequence("Ctrl+n"), None,
                "Save the center to a file.")
        self.fileLoadCenterAction = self.createAction("&Load center location...", self.loadCenter,
                QKeySequence("Ctrl+m"), None,
                "Load center from a file.")
                
        # Disable actions that are not immediately available
        for action in [self.fileSaveAction,
                       self.fileSavePlotAction,
                       self.fileSaveScreenAction,
                       self.fileSaveSpotsAction,
                       self.fileLoadSpotsAction,
                       self.fileSaveCenterAction,
                       self.fileLoadCenterAction]:
            action.setEnabled(False)
            
        self.fileActions = [self.fileOpenAction, None,
                            self.fileLoadSpotsAction, self.fileLoadCenterAction, None,
                            self.fileSaveAction, self.fileSavePlotAction, self.fileSaveScreenAction,
                            self.fileSaveSpotsAction, self.fileSaveCenterAction, 
                            None, self.fileQuitAction]
        
        # actions for "Help" menu
        self.helpAction = self.createAction("&Help", self.helpBoxShow,
                None, None,
                "Show help")
        self.aboutAction = self.createAction("&About", self.aboutwid.show,
                None, None,
                "About EasyLEED")
        self.helpActions = [None, self.helpAction, None, self.aboutAction]

        #### Create menu bar ####
        fileMenu = self.menuBar().addMenu("&File")
        self.addActions(fileMenu, self.fileActions)
        processMenu = self.menuBar().addMenu("&Process")
        self.addActions(processMenu, self.processActions)
        self.enableProcessActions(False)
        helpMenu = self.menuBar().addMenu("&Help")
        self.addActions(helpMenu, self.helpActions)

        #### Create tool bar ####
        toolBar = self.addToolBar("&Toolbar")
        # adding actions to the toolbar, addActions-function creates a separator with "None"
        self.toolBarActions = [self.fileQuitAction, None, self.fileOpenAction, None,
                               processRunAction, None, processStopAction, None,
                               processPlotOptions, None, processSetParameters, None,
                               self.processRemoveSpot, None, processRestartAction]
        self.addActions(toolBar, self.toolBarActions)
        
        #### Create status bar ####
        self.statusBar().showMessage("Ready", 5000)

        ### Create buttons and custom energy button and text in statusbar
        self.prevButton = QToolButton(self)
        self.prevButton.setArrowType(Qt.LeftArrow)
        self.prevButton.setEnabled(False)
        self.prevButton.setToolTip("Previous image")
        self.nextButton = QToolButton(self)
        self.nextButton.setArrowType(Qt.RightArrow)
        self.nextButton.setEnabled(False)
        self.nextButton.setToolTip("Next image")
        self.custEnergyButton = QPushButton("Set eV", self)
        self.custEnergyButton.setCheckable(True)
        self.custEnergyButton.setEnabled(False)
        self.custEnergyButton.setToolTip("Push to set custom energy")
        self.custEnergyText = QLineEdit()
        self.custEnergyText.setToolTip("Press Enter to set")

        ### Create slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        
        ### Add buttons, slider and custom energy button and text in statusbar
        self.statusBar().addPermanentWidget(self.prevButton)
        self.statusBar().addPermanentWidget(self.nextButton)
        self.statusBar().addPermanentWidget(self.slider)
        self.statusBar().addPermanentWidget(self.custEnergyButton)
        self.statusBar().addWidget(self.custEnergyText)

        ### Create event connector for slider and buttons in statusbar
        self.slider.sliderMoved.connect(self.slider_moved)
        self.prevButton.clicked.connect(self.prevBtnClicked)
        self.nextButton.clicked.connect(self.nextBtnClicked)
        self.custEnergyButton.clicked.connect(self.custEnBtnClicked)
        self.custEnergyText.returnPressed.connect(self.setCustEnergy)
    
        ### Create event connector for enabling fast changes to smoothing parameters
        self.parametersettingwid.smoothPoints.editingFinished.connect(self.liveSmoothParameters)
        self.parametersettingwid.smoothSpline.editingFinished.connect(self.liveSmoothParameters)

    def slider_moved(self, sliderNewPos):
        """
        This function tracks what to do with a slider movement.
            
        """
        diff = self.sliderCurrentPos - sliderNewPos
        if diff > 0:
            for i in range(0, diff):
                self.previous()
        else:
            for i in range(diff, 0):
                self.next_()
        self.sliderCurrentPos = sliderNewPos

    def prevBtnClicked(self):
        self.worker = Worker(self.scene.spots, self.scene.center, self.current_energy, parent=self)
        self.previous()
        self.worker.process(self.loader.goto(self.current_energy))
        self.sliderCurrentPos -= 1
        self.slider.setValue(self.sliderCurrentPos)

    def nextBtnClicked(self):
        self.worker = Worker(self.scene.spots, self.scene.center, self.current_energy, parent=self)
        self.next_()
        self.worker.process(self.loader.goto(self.current_energy))
    
    def custEnBtnClicked(self):
        """ Action when custom energy button is clicked"""
        if self.custEnergyButton.isChecked():
            self.custEnergyText.show()
            self.custEnergyText.setText("%s" % self.current_energy)
        else:
            self.setCustEnergy()
            self.custEnergyText.hide()

    def setCustEnergy(self):
        """ Take energy from custom energy text and move the corresponding frame"""
        self.worker = Worker(self.scene.spots, self.scene.center, self.current_energy, parent=self)
        self.goto(float(self.custEnergyText.text()))
        self.worker.process(self.loader.goto(self.current_energy))
    
    def liveSmoothParameters(self):
        """ Real time setting smoothing parameters from Parameter Settings panel into actual smoothed curve """
        config.GraphicsScene_smoothPoints = self.parametersettingwid.smoothPoints.value()
        config.GraphicsScene_smoothSpline = self.parametersettingwid.smoothSpline.value()
        if self.plotwid.smoothCheck.isChecked():
            self.plotwid.updatePlot()

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
            action.triggered.connect(slot)
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
            self.sliderCurrentPos += 1
            self.slider.setValue(self.sliderCurrentPos)

    def previous(self):
        try:
            image = self.loader.previous()
        except StopIteration:
            self.statusBar().showMessage("Reached first picture", 5000)
        else:
            self.setImage(image)
            self.sliderCurrentPos -= 1
            self.slider.setValue(self.sliderCurrentPos)

    def goto(self, energy):
        if energy >= 0:
            try:
                image = self.loader.goto(energy)
            except:
                self.statusBar().showMessage("Outside of energy range", 5000)
            else:
                self.setImage(image)
                self.sliderCurrentPos = self.loader.index
                self.slider.setValue(self.sliderCurrentPos)
        else:
            self.statusBar().showMessage("Energy must be positive", 5000)

    def restart(self):
        """ Delete stored plot information and start fresh """
        self.scene.removeAll()
        self.loader.restart()
        self.setImage(self.loader.next())
        self.plotwid.clearPlot()
        self.sliderCurrentPos = 1
        self.slider.setValue(1)
        self.fileSaveSpotsAction.setEnabled(False)
    
    def setImage(self, image):
        npimage, energy = image
        qimage = npimage2qimage(npimage)
        self.view.setSceneRect(QRectF(qimage.rect()))
        if config.GraphicsScene_intensTimeOn:
            labeltext = "Frame: %s" % energy
        else:
            labeltext = "Energy: %s eV" % energy
        self.scene.setBackground(qimage, labeltext)
        self.current_energy = energy

    def saveIntensity(self):
        filename = 'intensities.csv'
        filename = qt_filedialog_convert(QFileDialog.getSaveFileName(self,
                                                    "Save intensities to a file",
                                                    filename))
        if filename:
            self.worker.saveIntensity(filename)

    def fileOpen(self):
        """ Prompts the user to select input image files."""
        self.scene.removeAll()
        files = qt_filedialog_convert(QFileDialog.getOpenFileNames(self,
                                             "Open LEED images",
                                             filter="Image files (%s)" % (" ".join(AllImageLoader.supported_extensions()))))
        self.slider.setRange(1, len(files)+1)
        try:
            self.loader = AllImageLoader(files, config.IO_energyRegex)
            self.setImage(self.loader.next())
        except IOError as err:
            self.statusBar().showMessage('IOError: ' + str(err), 5000)
        else:
            self.enableProcessActions(True)
            self.prevButton.setEnabled(True)
            self.nextButton.setEnabled(True)
            self.slider.setEnabled(True)
            self.custEnergyButton.setEnabled(True)
            self.fileSaveScreenAction.setEnabled(True)
            self.fileLoadSpotsAction.setEnabled(True)
            self.fileLoadCenterAction.setEnabled(True)
            self.sliderCurrentPos = 1
            self.slider.setValue(self.sliderCurrentPos)

    def removeLastSpot(self):
        for item in self.scene.items():
            if type(item) == QGraphicsSpotItem:
                self.scene.removeItem(item)
                break
        try:
            self.scene.spots.remove(self.scene.spots[-1])
        except IndexError:
            self.statusBar().showMessage('No spots to be removed', 5000)
        if len(self.scene.items(0)) == 1:
            self.fileSaveSpotsAction.setEnabled(False)

    def stopProcessing(self):
        self.stopped = True

    def plot(self): 
        if hasattr(self,'worker'):
            self.plotwid.setupPlot(self.worker)
            # can save the plot now
            self.fileSavePlotAction.setEnabled(True)
        else:
            self.statusBar().showMessage("Please run acquisition first.", 5000)

    def run(self):
        if len(self.scene.spots) == 0:
            self.statusBar().showMessage("No integration window selected.", 5000)
        else:
            time_before = time.time()
            self.initial_energy = self.current_energy
            self.stopped = False
            self.view.setInteractive(False)
            self.slider.setEnabled(False)
            self.processRemoveSpot.setEnabled(False)
            self.scene.clearSelection()
            self.worker = Worker(self.scene.spots, self.scene.center, self.current_energy, parent=self)
            self.fileSaveAction.setEnabled(True)
            self.fileSaveSpotsAction.setEnabled(True)
            self.plotwid.clearPlotButton.setEnabled(False)
            if config.GraphicsScene_livePlottingOn:
                self.plot()
            self.worker.process(self.loader.goto(self.current_energy))
            for image in self.loader:
                if self.stopped:
                    break
                QApplication.processEvents()
                self.setImage(image)
                self.worker.process(image)
                QApplication.processEvents()
                if config.GraphicsScene_livePlottingOn:
                    self.plotwid.updatePlot()
                self.sliderCurrentPos += 1
                self.slider.setValue(self.sliderCurrentPos)
            self.view.setInteractive(True)
            self.plotwid.clearPlotButton.setEnabled(True)
            self.slider.setEnabled(True)
            self.processRemoveSpot.setEnabled(True)
            print("Total time acquisition:", time.time() - time_before, "s")

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
        filename = "screenshot" + str(self.loader.energies[self.loader.index]) + "eV.png"
        filename = qt_filedialog_convert(QFileDialog.getSaveFileName(self,
                                                    "Save the image to a file", filename,
                                                    filter="Image files (*.png *.bmp, *.jpg)"))
        if filename:
            pixMap = QWidget.grab(self.view) if get_qt_binding_name() == 'pyqt5' else QPixmap().grabWidget(self.view)
            pixMap.save(filename)

    def fileQuit(self):
        """Special quit-function as the normal window closing might leave something on the background """
        self.stopProcessing()
        QApplication.closeAllWindows()
        self.plotwid.canvas.close()

    def saveSpots(self):
        """Saves the spot locations to a file, uses workers saveLoc-function"""
        filename = "loc_" + str(self.initial_energy) + "eV.csv"
        filename = qt_filedialog_convert(QFileDialog.getSaveFileName(self,
                                                    "Save the spot locations to a file", filename))
        if filename:
            self.worker.saveLoc(filename)

    def loadSpots(self):
        """Load saved spot positions"""
        # This can probably be done in a better way
        filename = qt_filedialog_convert(QFileDialog.getOpenFileName(self, 'Open spot location file'))
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
                self.scene.spots.append(item)

    def saveCenter(self):
        """Saves the center locations to a file"""
        filename = 'loc_center.pkl'
        filename = qt_filedialog_convert(QFileDialog.getSaveFileName(self,
                                                    "Save the center location to a file",
                                                    filename))
        if filename:
            zipped = list(zip([self.scene.center.x()], [self.scene.center.y()]))
            output = open(filename, 'wb')
            pickle.dump(zipped, output)
            output.close()

    def loadCenter(self):
        """Load saved center position from file"""
        # This can probably be done in a better way
        filename = qt_filedialog_convert(QFileDialog.getOpenFileName(self,
                                                    "Open center location file"))
        if filename:
            if hasattr (self.scene, "center"):
                self.scene.removeCenter()
            # pickle doesn't recognise the file opened by PyQt's openfile dialog as a file so 'normal' file processing
            pkl_file = open(filename, 'rb')
            # loading the zipped info to "location"
            location = pickle.load(pkl_file)
            pkl_file.close()
            # unzipping the "location"
            cLocx, cLocy = zip(*location)
            point = QPointF(cLocx[0], cLocy[0])
            item = QGraphicsCenterItem(point, config.QGraphicsCenterItem_size)
            # adding the item to the gui
            self.scene.clearSelection()
            self.scene.addItem(item)
            item.setSelected(True)
            self.scene.center = item
            self.scene.setFocusItem(item)
            self.fileSaveCenterAction.setEnabled(True)

class Worker(QObject):
    """ Worker that manages the spots.
    
        spots_map:
        - key: spot
        - value: SpotModel, Tracker
    """

    def __init__(self, spots, center, energy, parent=None):
        super(Worker, self).__init__(parent)
        
        self.spots_map = {}
        for spot in spots:
            pos = spot.scenePos()
            if center:
                tracker = Tracker(pos.x(), pos.y(), spot.radius(), energy, center.x(), center.y(),
                            input_precision=config.Tracking_inputPrecision,
                            window_scaling=config.Tracking_windowScalingOn)
            else:
                tracker = Tracker(pos.x(), pos.y(), spot.radius(), energy,
                            input_precision=config.Tracking_inputPrecision,
                            window_scaling=config.Tracking_windowScalingOn)
            self.spots_map[spot] = (QSpotModel(self), tracker)

        for view, tup in six.iteritems(self.spots_map):
            # view = QGraphicsSpotItem, tup = (QSpotModel, tracker) -> tup[0] = QSpotModel
            tup[0].positionChanged.connect(view.onPositionChange)
            tup[0].radiusChanged.connect(view.onRadiusChange)

    def process(self, image):
        if config.GraphicsScene_intensTimeOn:
            print("Current frame: " + str(self.parent().current_energy))
        else:
            print("Current image energy: " + str(self.parent().current_energy) + "eV")
        for model, tracker in six.itervalues(self.spots_map):
            tracker_result = tracker.feed_image(image)
            # feed_image returns x, y, intensity, energy and radius
            model.update(*tracker_result)

    def numProcessed(self):
        """ Return the number of processed images. """
        return len(next(six.itervalues(self.spots_map))[0].m.energy)

    def saveIntensity(self, filename):
        """save intensities"""
        intensities = [model.m.intensity for model, tracker \
                                in six.itervalues(self.spots_map)]
        energy = [model.m.energy for model, tracker in six.itervalues(self.spots_map)]
        zipped = np.asarray(list(zip(energy[0], *intensities)))
        bs = config.Processing_backgroundSubstractionOn
        np.savetxt(filename, zipped,
                   header='energy, intensity 1, intensity 2, ..., [background substraction = %s]' % bs)

        # Save Average intensity (if checkbox selected)
        if self.parent().plotwid.averageCheck.isChecked():
            intensity = np.zeros(self.numProcessed())
            for model, tracker in six.itervalues(self.spots_map):
                intensity += model.m.intensity
            intensity = [i/len(self.spots_map) for i in intensity]
            zipped = list(zip(energy[0], intensity))
            np.savetxt(filename+'_avg', zipped,
                   header='energy, avg. intensity [background substraction = %s]' % bs)

#        # save positions
#        x = [model.m.x for model, tracker \
#                in six.itervalues(self.spots_map)]
#        y = [model.m.y for model, tracker \
#                in six.itervalues(self.spots_map)]
#        x.extend(y)
#        zipped = np.asarray(list(zip(energy[0], *x))
#        np.savetxt(filename, zipped,
#                   header='energy, x, y')
        
    def saveLoc(self, filename):

        # model = QSpotModel object tracker = tracker
        # dict function .itervalues() = return an iterator over the mapping's values
        energy = [model.m.energy for model, tracker in six.itervalues(self.spots_map)]
        locationx = [model.m.x for model, tracker in six.itervalues(self.spots_map)]
        locationy = [model.m.y for model, tracker in six.itervalues(self.spots_map)]
        radius = [model.m.radius for model, tracker in six.itervalues(self.spots_map)]
        locations = [locationx, locationy, radius]
        zipped = list(zip(energy, *locations))
        output = open(filename, 'wb')
        pickle.dump(zipped, output)
        output.close()
