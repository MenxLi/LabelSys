from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent
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
        sys.stdout = EmittingStream(textWritten = self.putOnConsole)

        self.DATALOADED = False # Indicate whether there are date loaded in current window
        if self.args.dev: 
            print("Developing mode...")
            self.loadPatietns()
        else:
            print("Normal mode")

        self.showFullScreen(); self.__screen_mode = 2
        self.setWindowTitle("LabelSys "+__VERSION__)
        self.setFocus()
        self.setFocusPolicy(Qt.StrongFocus)

        self.initMenu()
        # set style sheet
        self.tb_console.setStyleSheet("color: white; background-color:black;")


        # data
        # self.imgs = None # current image series of a patient
        # self.SOPInstanceUIDs = None # SOPInstanceUIDs of self.imgs
        # self.slice_id = None  # current slice id

    def initMenu(self):
        self.act_open.triggered.connect(self.loadPatietns)
        self.act_quit.triggered.connect(self.quitApp)
        self.act_fullscreen.triggered.connect(self.changeScreenMode)

    def loadPatietns(self):
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

        self.DATALOADED = True
        self.initPanel()
        return 0

    def quitApp(self):
        self.close()
        return 0

    def changeScreenMode(self):
        """Change screen mode between Normal Maximized and full screen"""
        self.__screen_mode = (self.__screen_mode+1)%3
        if self.__screen_mode == 0:
            self.showNormal()
        elif self.__screen_mode == 1: 
            self.showMaximized()
        elif self.__screen_mode == 2:
            self.showFullScreen()

    def initPanel(self):
        """Init the whole panel, will be called on loading the patients""" 
        self.slider_im.setPageStep(1)        
        self.slider_im.setEnabled(True)
        self.combo_label.addItems(LABELS)

        self.combo_series.currentTextChanged.connect(self.changeComboSeries)
        self.combo_label.currentTextChanged.connect(self.changComboLabels)
        self.btn_next_slice.clicked.connect(self.nextSlice)
        self.btn_prev_slice.clicked.connect(self.prevSlice)
        self.btn_next_patient.clicked.connect(self.nextPatient)
        self.btn_prev_patient.clicked.connect(self.prevPatient)
        self.slider_im.valueChanged.connect(self.changeSliderValue)

    def initImageUI(self):
        """Put image on to main window, will be called on loading the patients"""
        self.im_widget = VtkWidget(self.im_frame) 

    def changeComboSeries(self, entry):
        """Triggered when self.combo_series change the entry"""
        self.slice_id = 0
        try:
            # prevent triggering when changing patient
            self.__readSeries()
            self.__updateImg()
        except: pass
        finally:
            self.slider_im.setSliderPosition(self.slice_id)
            self.im_widget.resetCamera()

    def changComboLabels(self, entry):
        pass

    def changeSliderValue(self):
        """Triggered when slider_im changes value"""
        self.slice_id = self.slider_im.value()
        self.__updateImg()

    def nextSlice(self):
        if self.slice_id >= len(self.imgs)-1:
            return 1
        self.slice_id += 1
        self.slider_im.setSliderPosition(self.slice_id)
        #self.__updateImg()
        return 0

    def prevSlice(self):
        if self.slice_id < 1:
            return 1
        self.slice_id -= 1
        self.slider_im.setSliderPosition(self.slice_id)
        #self.__updateImg()
        return 0

    def nextPatient(self):
        if self.fl.next():
            self.__updatePatient()
        
    def prevPatient(self):
        if self.fl.previous():
            self.__updatePatient()

    def putOnConsole(self, text):
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
        self.slider_im.setSliderPosition(self.slice_id)
        self.slider_im.setMaximum(len(self.imgs)-1)

    def __updateImg(self):
        """update image showing on im_frame"""
        im = F.map_mat_255(self.imgs[self.slice_id])

        slice_info = "Slice: "+ str(self.slice_id+1)+"/"+str(len(self.imgs))
        img_info = "Image size: {} x {}".format(*im.shape)
        txt = slice_info + "\n" + img_info

        self.im_widget.readNpArray(im, txt)

    def __readSeries(self):
        """update self.imgs and self.SOPInstanceUIDs by current chosen image series"""
        entry = str(self.combo_series.currentText())
        self.imgs, self.SOPInstanceUIDs = self.fl.curr_patient.getSeriesImg(entry)
    
    #==============Event Handler================
    def eventFilter(self, receiver, event):
        """Globally defined event"""
        modifier = QtWidgets.QApplication.keyboardModifiers() 
        if(event.type() == QEvent.KeyPress):
            """KeyBoard shortcut"""
            key = event.key()
            if key == Qt.Key_F and modifier == Qt.ControlModifier:
                # Ctrl-F : change screen mode
                self.changeScreenMode()
            if key == Qt.Key_Q and modifier == Qt.ControlModifier:
                # Ctrl-Q : quit Program
                self.quitApp()
            if key == Qt.Key_O and modifier == Qt.ControlModifier:
                # Ctrl-O : open file
                self.loadPatietns()
            if key == Qt.Key_Up:
                # Up : next slice
                self.nextSlice()
            if key == Qt.Key_Down:
                # Down : previous slice
                self.prevSlice()
        if(event.type() == QEvent.MouseMove):
            """vtk seems difficult in recognizing mouse dragging, so 
            implimented With Qt"""
            if not self.DATALOADED:
                return False
            self.im_widget.style.mouseMoveEvent(None, None)
        return super().eventFilter(receiver, event)

    def wheelEvent(self, event):
        modifier = QtWidgets.QApplication.keyboardModifiers() 
        if event.angleDelta().y() < 0:
            if modifier == Qt.ControlModifier:
                self.im_widget.style.OnMouseWheelForward()
            else:
                self.prevSlice()
        else: 
            if modifier == Qt.ControlModifier:
                self.im_widget.style.OnMouseWheelBackward()
            else:
                self.nextSlice()
    
    #def keyPressEvent(self, event):
        #key = event.key()
        #modifier = QtWidgets.QApplication.keyboardModifiers() 
        #if key == Qt.Key_F and modifier == Qt.ControlModifier:
            #print("Change screen mode")
            #self.changeScreenMode()
        #if key == Qt.Key_Q and modifier == Qt.ControlModifier:
            #self.quitApp()
        #if key == Qt.Key_O and modifier == Qt.ControlModifier:
            #self.loadPatietns()
        #if key == Qt.Key_Up:
            #self.nextSlice()
        #if key == Qt.Key_Down:
            #self.prevSlice()

    def mouseMoveEvent(self, event):
        print(event.localPos())

class EmittingStream(QObject):
    """Reference: https://stackoverflow.com/questions/8356336/how-to-capture-output-of-pythons-interpreter-and-show-in-a-text-widget"""
    textWritten = pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))
