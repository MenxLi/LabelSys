import numpy as np
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
from labelResultHolder import LabelHolder
from config import *
from previewGUI import Preview3DWindow, Preview2DWindow
import cv2 as cv

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

        self.showFullScreen(); self.__screen_mode = 2
        self.setWindowTitle("LabelSys "+__VERSION__)
        self.setFocus()
        self.setFocusPolicy(Qt.StrongFocus)

        self.initMenu()
        self.output_path = os.getcwd()
        # set style sheet
        self.tb_console.setStyleSheet("color: white; background-color:black;")

        self.lbl_holder = LabelHolder() 
        # data
        # self.imgs = None # current image series of a patient
        # self.SOPInstanceUIDs = None # SOPInstanceUIDs of self.imgs
        # self.slice_id = None  # current slice id
        # self.curr_lbl = None  # current label selected

        if self.args.dev: 
            print("Developing mode...")
            self.loadPatietns()
        else:
            print("Normal mode")

    def initMenu(self):
        self.act_open.triggered.connect(self.loadPatietns)
        self.act_open.setShortcut("Ctrl+O")
        self.act_quit.triggered.connect(self.quitApp)
        self.act_quit.setShortcut("Ctrl+Q")
        self.act_fullscreen.triggered.connect(self.changeScreenMode)
        self.act_fullscreen.setShortcut("Ctrl+F")
        self.act_load.triggered.connect(self.loadLabeledFile)
        self.act_set_path.triggered.connect(self.setOutputPath)
        self.act_set_path.setShortcut("Ctrl+P")
        self.act_3D_preview.triggered.connect(self.previewLabels3D)

    def initPanel(self):
        """Init the whole panel, will be called on loading the patients""" 
        self.slider_im.setPageStep(1)        
        self.slider_im.setEnabled(True)
        self.combo_label.addItems(LABELS)
        self.curr_lbl = str(self.combo_label.currentText())
        self.__updateQLabelText()

        self.combo_series.currentTextChanged.connect(self.changeComboSeries)
        self.combo_label.currentTextChanged.connect(self.changComboLabels)
        self.btn_next_slice.clicked.connect(self.nextSlice)
        self.btn_prev_slice.clicked.connect(self.prevSlice)
        self.btn_next_patient.clicked.connect(self.nextPatient)
        self.btn_prev_patient.clicked.connect(self.prevPatient)
        self.btn_save.clicked.connect(self.saveCurrentPatient)
        self.btn_clear.clicked.connect(self.clearCurrentSlice)
        self.btn_preview.clicked.connect(self.previewLabels2D)
        self.btn_add_cnt.clicked.connect(self.addContour)
        self.slider_im.valueChanged.connect(self.changeSliderValue)

    def initImageUI(self):
        """Put image on to main window, will be called on loading the patients"""
        self.im_widget = VtkWidget(self.im_frame, self.check_crv, self.saveCurrentSlice) 

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

        self.initPanel()
        self.initImageUI()
        self.__updatePatient()

        self.DATALOADED = True
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

    def setOutputPath(self):
        fname = QFileDialog.getExistingDirectory(self, "Select output directory")
        if fname == "":
            return 1
        self.output_path = Path(fname)
        self.__updateQLabelText()
        return 0

    def loadLabeledFile(self):
        """Load a labeld file for one patient"""
        pass

    def changeComboSeries(self, entry):
        """Triggered when self.combo_series change the entry"""
        self.slice_id = 0
        try: # prevent triggering when changing patient
            if not self.lbl_holder.SAVED:
                if not self._alertMsg("Unsaved changes, continue?"):
                    return 1
            self.__readSeries()
            self.__updateImg()
        except: pass
        finally:
            self.slider_im.setSliderPosition(self.slice_id)
            self.im_widget.resetCamera()

    def changComboLabels(self, entry):
        self.curr_lbl = entry
        self.__updateImg()

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
        if not self.lbl_holder.SAVED:
            if not self._alertMsg("Unsaved changes, continue?"):
                return 1
        if self.fl.next():
            self.__updatePatient()
            return 0
        
    def prevPatient(self):
        if not self.lbl_holder.SAVED:
            if not self._alertMsg("Unsaved changes, continue?"):
                return 1
        if self.fl.previous():
            self.__updatePatient()
            return 0

    def putOnConsole(self, text):
        self.tb_console.append(text) 

    def clearCurrentSlice(self):
        self.lbl_holder.data[self.slice_id][self.curr_lbl] = []
        self.__updateImg()

    def previewLabels3D(self):
        if not self.DATALOADED:
            pass
        self.preview_win_3d = Preview3DWindow(self.imgs, self.__getMasks(), spacing = self.spacing)
        self.preview_win_3d.show()

    def previewLabels2D(self):
        if not self.DATALOADED:
            pass
        self.preview_win_2d = Preview2DWindow(self.imgs, self.__getMasks(), self.slice_id) 
        self.preview_win_2d.show()

    def addContour(self):
        self.im_widget.style.forceDrawing()

    def saveCurrentSlice(self, cnts_data):
        self.lbl_holder.data[self.slice_id][self.curr_lbl] = cnts_data
        self.lbl_holder.data[self.slice_id]["SOPInstanceUID"] = self.SOPInstanceUIDs[self.slice_id]
        self.lbl_holder.SAVED = False

    def saveCurrentPatient(self):
        folder_name = "Label-"+Path(self.fl.getPath()).stem
        file_path = os.path.join(self.output_path, folder_name)
        if os.path.exists(file_path):
            if not self._alertMsg("Data exists, overwrite?"):
                return 
        self.lbl_holder.saveToFile(file_path, self.imgs)
        self.lbl_holder.SAVED = True

    def __getMasks(self):
        im_shape = self.imgs[0].shape
        for im in self.imgs:
            if im.shape != im_shape:
               return None 
        masks = []
        for slice_idx in range(len(self.imgs)):
            mask_data = {}
            for label in LABELS:
                mask_data[label] = np.zeros(im_shape[:2], np.uint8)
                cnts_data = self.lbl_holder.data[slice_idx][label]
                if cnts_data == []:
                    continue
                for cnt_data in cnts_data:
                    all_pts = cnt_data["Contour"] # All the points position on the contour, in CV coordinate
                    if cnt_data["Open"] == True:
                        cv_cnt = np.array([arr for arr in F.removeDuplicate2d(all_pts)])
                        cv.polylines(mask_data[label],[cv_cnt],False,1)
                    else:
                        cv_cnt = np.array([[arr] for arr in F.removeDuplicate2d(all_pts)])
                        cv.fillPoly(mask_data[label], pts = [cv_cnt], color = 1)
                    mask_data[label] = mask_data[label].astype(np.bool)
            masks.append(mask_data) 
        return masks

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
        self.im_widget.reInitStyle()

        # load contour
        cnts_data = self.lbl_holder.data[self.slice_id][self.curr_lbl]
        if cnts_data != []:
            for cnt in cnts_data:
                self.im_widget.loadContour(cnt["Points"], cnt["Open"])

    def __updateQLabelText(self):
        self.lbl_wd.setText("Console -- Output path: {}".format(str(self.output_path)))

    def __readSeries(self):
        """update self.imgs and self.SOPInstanceUIDs by current chosen image series"""
        entry = str(self.combo_series.currentText())
        #self.imgs, self.SOPInstanceUIDs = self.fl.curr_patient.getSeriesImg(entry)
        image_data = self.fl.curr_patient.getSeriesImg(entry)
        self.imgs = image_data["Images"]
        self.SOPInstanceUIDs = image_data["SOPInstanceUIDs"]
        self.spacing = image_data["Spacing"]
        self.lbl_holder.initialize(LABELS, self.SOPInstanceUIDs) 
    
    def _alertMsg(self,msg, title = "Alert", func = lambda x : None):
        msg_box = QMessageBox()
        msg_box.setText(msg)
        msg_box.setWindowTitle(title)
        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg_box.buttonClicked.connect(func)
        return_value = msg_box.exec()
        if return_value == QMessageBox.Ok:
            return True
        else: return False
    
    #==============Event Handler================
    def eventFilter(self, receiver, event):
        """Globally defined event"""
        modifier = QtWidgets.QApplication.keyboardModifiers() 
        if(event.type() == QEvent.KeyPress):
            """KeyBoard shortcut"""
            key = event.key()
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

class EmittingStream(QObject):
    """Reference: https://stackoverflow.com/questions/8356336/how-to-capture-output-of-pythons-interpreter-and-show-in-a-text-widget"""
    textWritten = pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))
