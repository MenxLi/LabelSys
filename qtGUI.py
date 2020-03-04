# from PyQt5.QtWidgets import QMainWindow, QWidget, QAction, QFileDialog, QComboBox, QFrame, Qsplitter, QVBoxLayout
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5 import uic
from version import __VERSION__, __DESCRIPTION__
from dicomFileReader import FolderLoader
from pathlib import Path
import os,sys
from vtkClass import VtkWidget
import myFuncs as F
from config import *

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))

class MainWindow(QMainWindow):
    def __init__(self,args):
        super().__init__()
        # load UI
        ui_path = os.path.join(LOCAL_DIR, "mainWindow.ui")
        uic.loadUi(ui_path, self)
        self.args = args
        sys.stdout = EmittingStream(textWritten = self.slotPutOnConsole)
        if self.args.dev: 
            print("Developing mode...")
            self.slotLoadPatients()
        else:
            print("Normal mode")

        self.showMaximized()
        self.setWindowTitle("LabelSys "+__VERSION__)

        self.initMenu()
        self.initPanel()
        # set style sheet
        # https://doc.qt.io/archives/qt-4.8/stylesheet-reference.html#list-of-properties
        #self.setStyleSheet("QTextBrowser { background-color: yellow  }")
        self.tb_console.setStyleSheet("color: white; background-color:black;")
        # self.setStyleSheet("QPushButton { background-color: #616161;\
                #border-radius:10px }")
        #self.setStyleSheet("QWidget { background-color: #3b3b3b; color:white}")

        #raise Exception("Hello")

        # data
        # self.imgs = None # current image series of a patient
        # self.SOPInstanceUIDs = None # SOPInstanceUIDs of self.imgs
        # self.slice_id = None  # current slice id

    def initMenu(self):
        self.act_open.triggered.connect(self.slotLoadPatients)
        self.act_fullscreen.triggered.connect(self.slotChangeScreenMode)

    def slotLoadPatients(self):
        """Load patients folder, and call initPanelAct() to initialize the panel""" 
        if self.args.dev: 
            fname = self.args.file
        else: 
            fname = QFileDialog.getExistingDirectory(self, "Select Directory")
        if fname == "":
            return 1
        file_path = Path(fname)
        self.fl = FolderLoader(file_path)
        self.initImageUI()
        self.__updatePatient()

        #self.initPanel()
        return 0

    def slotChangeScreenMode(self):
        """Change screen mode between Maximized and full screen"""
        pass

    def initPanel(self):
        """Init the whole panel, will be called on loading the patients""" 
        self.combo_series.currentTextChanged.connect(self.slotChangeComboSeries)
        self.combo_label.addItems(LABELS)
        self.combo_label.currentTextChanged.connect(self.slotChangeComboLabels)
        self.btn_next_slice.clicked.connect(self.slotNextSlice)
        self.btn_prev_slice.clicked.connect(self.slotPrevSlice)
        self.btn_next_patient.clicked.connect(self.slotNextPatient)

    def initImageUI(self):
        """Put image on to main window, will be called on loading the patients"""
        self.im_widget = VtkWidget(self.im_frame) 

    def slotChangeComboSeries(self, entry):
        """Triggered when self.combo_series change the entry"""
        self.slice_id = 0
        try:
            # prevent triggering when changing patient
            self.__readSeries()
            self.__updateImg()
        except: pass

    def slotChangeComboLabels(self, entry):
        pass

    def slotNextSlice(self):
        if self.slice_id >= len(self.imgs)-1:
            return 1
        self.slice_id += 1
        self.__updateImg()
        return 0

    def slotPrevSlice(self):
        if self.slice_id <= 1:
            return 1
        self.slice_id -= 1
        self.__updateImg()
        return 0

    def slotNextPatient(self):
        if self.fl.next():
            self.__updatePatient()
        
    def slotPutOnConsole(self, text):
        self.tb_console.append(text) 

    def __updateComboSeries(self):
        """Update the series combobox when changing patient"""
        self.combo_series.clear()
        series = self.fl.curr_patient.getEntries()
        self.combo_series.addItems(series)
        # set defult image series
        if SERIES in series:
            self.combo_series.setCurrentText(SERIES)
        else:
            self.combo_series.setCurrentText(list(series)[0])

    def __updatePatient(self):
        """Update current showing patient, will be triggeted when changing patient"""
        self.slice_id = 0
        self.__updateComboSeries()
        self.__readSeries()
        self.__updateImg()

    def __updateImg(self):
        """update image showing on im_frame"""
        im = F.map_mat_255(self.imgs[self.slice_id])
        self.im_widget.readNpArray(im)

    def __readSeries(self):
        """update self.imgs and self.SOPInstanceUIDs by current chosen image series"""
        entry = str(self.combo_series.currentText())
        self.imgs, self.SOPInstanceUIDs = self.fl.curr_patient.getSeriesImg(entry)
    
    #==============Event Handler================
    def wheelEvent(self, event):
        if event.angleDelta().y() < 0:
            self.slotNextSlice()
        else: self.slotPrevSlice()

class EmittingStream(QObject):
    """Reference: https://stackoverflow.com/questions/8356336/how-to-capture-output-of-pythons-interpreter-and-show-in-a-text-widget"""
    textWritten = pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))
