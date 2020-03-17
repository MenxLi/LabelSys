import webbrowser
from pathlib import Path
import os,sys
import copy

from version import __version__
from dicomFileReader import FolderLoader
from configLoader import *
import utils_ as F
from labelResultHolder import LabelHolder
from previewGUI import Preview3DWindow, Preview2DWindow
from settingsGUI import SettingsDialog

import numpy as np
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent
from PyQt5 import uic
from vtkClass import VtkWidget
import cv2 as cv

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))

class MainWindow(QMainWindow):
    def __init__(self,args):
        super().__init__()
        # load UI
        ui_path = os.path.join(LOCAL_DIR, "mainWindow.ui")
        uic.loadUi(ui_path, self)
        self.args = args
        sys.stdout = EmittingStream(textWritten = self.stdoutStream)

        # set style sheet
        self.tb_console.setStyleSheet("color: white; background-color:black;")

        # UI change
        self.showFullScreen(); self.__screen_mode = 2
        self.setWindowTitle("LabelSys "+__version__)
        self.setFocus()
        self.setFocusPolicy(Qt.StrongFocus)

        self.initMenu()

        # Attribute init
        self.output_path = Path(os.getcwd()).parent
        self.labeler_name = "Anonymous"
        self.lbl_holder = LabelHolder() 

        self.slice_id = 0

        # store some status indicator and temporary variables
        self.__cache = {
                "data_loaded":False, # Indicate whether there are date loaded in main window
                "prev_combo_series": None # used for decline combo series change with unsaved data
                }
        # data
        # self.imgs = None # current image series of a patient
        # self.SOPInstanceUIDs = None # SOPInstanceUIDs of self.imgs
        # self.slice_id = None  # current slice id
        # self.curr_lbl = None  # current label selected

        self.central_widget.setEnabled(False)

        self.initImageUI()
        self.initPanel()

        if self.args.dev: 
            print("Developing mode...")
            self.loadPatietns()
        else:
            print("Welcome to ")

    def initMenu(self):
        # File
        self.act_open.triggered.connect(self.loadPatietns)
        self.act_open.setShortcut("Ctrl+O")
        self.act_quit.triggered.connect(self.quitApp)
        self.act_quit.setShortcut("Ctrl+Q")
        self.act_load.triggered.connect(self.loadLabeledFile)
        self.act_load.setShortcut("Ctrl+L")

        # View
        self.act_fullscreen.triggered.connect(self.changeScreenMode)
        self.act_fullscreen.setShortcut("Ctrl+F")
        self.act_3D_preview.triggered.connect(self.previewLabels3D)

        # Operation
        self.act_op_next_slice.triggered.connect(self.nextSlice)
        self.act_op_next_slice.setShortcut("Up")
        self.act_op_prev_slice.triggered.connect(self.prevSlice)
        self.act_op_prev_slice.setShortcut("Down")
        self.act_op_next_patient.triggered.connect(self.nextPatient)
        self.act_op_next_patient.setShortcut("Right")
        self.act_op_prev_patient.triggered.connect(self.prevPatient)
        self.act_op_prev_patient.setShortcut("Left")
        self.act_op_change_lbl.triggered.connect(self.switchLabel)
        self.act_op_change_lbl.setShortcut("Tab")
        self.act_op_save.triggered.connect(self.saveCurrentPatient)
        self.act_op_save.setShortcut("Ctrl+S")
        self.act_op_clear.triggered.connect(self.clearCurrentSlice)
        self.act_op_clear.setShortcut("Esc")
        self.act_op_interp.triggered.connect(self.interpCurrentSlice)
        self.act_op_interp.setShortcut("Ctrl+I")
        self.act_op_add_cnt.triggered.connect(self.addContour)
        self.act_op_add_cnt.setShortcut("Ctrl+A")

        # Settings
        self.act_set_path.triggered.connect(self.setOutputPath)
        self.act_set_path.setShortcut("Ctrl+Alt+P")
        self.act_set_lbler.triggered.connect(self.setLabeler)
        self.act_set_lbler.setShortcut("Ctrl+Alt+L")
        self.act_set_settings.triggered.connect(self.setSettings)
        self.act_set_settings.setShortcut("Ctrl+Alt+S")

        # Help
        self.act_manual.triggered.connect(self.showHelpManual)

    def initPanel(self):
        """Init the whole panel, will be called on loading the patients""" 
        self.slider_im.setPageStep(1)
        self.combo_label.addItems(LABELS)
        self.curr_lbl = str(self.combo_label.currentText())
        self.__updateQLabelText()

        self.combo_series.currentTextChanged.connect(self.changeComboSeries)
        self.combo_label.currentTextChanged.connect(self.changeComboLabels)
        self.check_crv.stateChanged.connect(self.changeCheckCrv)
        self.btn_next_slice.clicked.connect(self.nextSlice)
        self.btn_prev_slice.clicked.connect(self.prevSlice)
        self.btn_next_patient.clicked.connect(self.nextPatient)
        self.btn_prev_patient.clicked.connect(self.prevPatient)
        self.btn_save.clicked.connect(self.saveCurrentPatient)
        self.btn_clear.clicked.connect(self.clearCurrentSlice)
        self.btn_interp.clicked.connect(self.interpCurrentSlice)
        self.btn_preview.clicked.connect(self.previewLabels2D)
        self.btn_add_cnt.clicked.connect(self.addContour)
        self.slider_im.valueChanged.connect(self.changeSliderValue)

    def initImageUI(self):
        """Put image on to main window, will be called on loading the patients"""
        self.im_widget = VtkWidget(self.im_frame, self.check_crv, self.saveCurrentSlice) 

    def loadPatietns(self):
        """Load patients folder, and call initPanelAct() to initialize the panel""" 
        self.central_widget.setEnabled(True)
        if self.args.dev: 
            fname = self.args.file
        else: 
            fname = QFileDialog.getExistingDirectory(self, "Select Directory")
        if fname == "":
            return 1
        file_path = Path(fname)
        self.fl = FolderLoader(file_path)

        self.__updatePatient()

        self.__cache["data_loaded"] = True
        return 0

    def loadLabeledFile(self):
        """Load a labeld file for one patient"""
        fname = QFileDialog.getExistingDirectory(self, "Select loading directory")
        if fname == "":
            return 1
        self.central_widget.setEnabled(True)
        self.__disableWidgets(
                self.btn_next_patient, 
                self.btn_prev_patient,
                self.combo_series
                )
        self.slice_id = 0
        header, self.imgs = self.lbl_holder.loadFile(Path(fname))
        self.output_path = Path(fname).parent
        self.SOPInstanceUIDs = [s["SOPInstanceUID"] for s in self.lbl_holder.data]
        self.labeler_name = header["Labeler"]
        self.spacing = header["Spacing"]

        self.combo_label.clear()
        self.combo_label.addItems(header["Labels"])
        self.curr_lbl = str(self.combo_label.currentText())

        self.combo_series.clear()
        self.combo_series.addItem(header["Series"])

        self.slider_im.setSliderPosition(self.slice_id)
        self.slider_im.setMaximum(len(self.imgs)-1)

        self.__cache["data_loaded"] = True
        #self.__updateImg()
        self.__updateQLabelText()

    def quitApp(self):
        if not self.lbl_holder.SAVED and not self.args.dev:
            if not self._alertMsg("Unsaved changes, quitting?"):
                return 1
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

    def setLabeler(self):
        """Set labeler name"""
        text, ok = QInputDialog.getText(self, "Set labeler", "Enter your name: ")
        if ok:
            self.labeler_name = str(text)
            self.__updateQLabelText()

    def setSettings(self):
        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.exec_()
        #self.settings_dialog.show()

    def changeComboSeries(self, entry):
        """Triggered when self.combo_series change the entry"""
        if self.__querySave() == 1:
            # decline action with unsaved changes
            self.combo_series.currentTextChanged.disconnect()
            self.combo_series.setCurrentText(self.__cache["prev_combo_series"])
            self.combo_series.currentTextChanged.connect(self.changeComboSeries)
            return
        self.slice_id = 0
        self.__cache["prev_combo_series"] = entry
        try: # prevent triggering when changing patient
            self.__readSeries()
            self.__updateImg()
        except: pass
        finally:
            self.slider_im.setSliderPosition(self.slice_id)
            self.slider_im.setMaximum(len(self.imgs)-1)
            self.im_widget.resetCamera()

    def changeComboLabels(self, entry):
        self.curr_lbl = entry
        try:    # prevent triggering when clear
            self.__updateImg()
        except: pass
        mode = LBL_MODE[LABELS.index(self.curr_lbl)]
        if mode == 1:
            self.check_crv.setChecked(True)
        elif mode == 0:
            self.check_crv.setChecked(False)

    def changeCheckCrv(self, i):
        if self.check_crv.isChecked():
            LBL_MODE[LABELS.index(self.curr_lbl)] = 1
        else:
            LBL_MODE[LABELS.index(self.curr_lbl)] = 0

    def changeSliderValue(self):
        """Triggered when slider_im changes value"""
        self.slice_id = self.slider_im.value()
        self.__updateImg()

    def switchLabel(self):
        """switch between labels, for shortcut use"""
        new_label_id = (LABELS.index(self.curr_lbl) + 1)%len(LABELS)
        self.combo_label.setCurrentText(LABELS[new_label_id]) # will trigger changeComboLabels()

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
        if self.__querySave() == 1:
            return
        if self.fl.next():
            self.__updatePatient()
            return 0
        
    def prevPatient(self):
        if self.__querySave() == 1:
            return
        if self.fl.previous():
            self.__updatePatient()
            return 0

    def stdoutStream(self, text):
        #self.tb_console.append(text) 
        self.tb_console.insertPlainText(text)
        self.tb_console.verticalScrollBar().setValue(self.tb_console.verticalScrollBar().maximum())

    def clearCurrentSlice(self):
        self.lbl_holder.data[self.slice_id][self.curr_lbl] = []
        self.__updateImg()

    def interpCurrentSlice(self):
        prev_mask = self.__getSingleMask(self.slice_id-1, self.combo_label.currentText())
        next_mask = self.__getSingleMask(self.slice_id+1, self.combo_label.currentText())
        if type(prev_mask) == type(None) and type(next_mask) == type(None):
            print("Nothing to interpolate")
            return
        elif type(prev_mask) == type(None):
            print("Copied from next slice")
            self.lbl_holder.data[self.slice_id] = copy.deepcopy(self.lbl_holder.data[self.slice_id+1])
            self.lbl_holder.SAVED = False
            self.__updateImg()
        elif type(next_mask) == type(None):
            print("Copied from previous slice")
            self.lbl_holder.data[self.slice_id] = copy.deepcopy(self.lbl_holder.data[self.slice_id-1])
            self.lbl_holder.SAVED = False
            self.__updateImg()
        else:
            """should be improved in the futute"""
            print("Copied from previous slice")
            self.lbl_holder.data[self.slice_id] = copy.deepcopy(self.lbl_holder.data[self.slice_id-1])
            self.lbl_holder.SAVED = False
            self.__updateImg()

    def previewLabels3D(self):
        if not self.__cache["data_loaded"]:
            pass
        self.preview_win_3d = Preview3DWindow(self.imgs, self.__getMasks(), spacing = self.spacing)
        self.preview_win_3d.show()

    def previewLabels2D(self):
        if not self.__cache["data_loaded"]:
            pass
        self.preview_win_2d = Preview2DWindow(self.imgs, self.__getMasks(), self.slice_id) 
        self.preview_win_2d.show()

    def addContour(self):
        self.im_widget.style.forceDrawing()

    def saveCurrentSlice(self, cnts_data):
        """
        Will be triggered automatically when modifying the contour, will be
        called by vtkClass
        """
        self.lbl_holder.data[self.slice_id][self.curr_lbl] = cnts_data
        self.lbl_holder.data[self.slice_id]["SOPInstanceUID"] = self.SOPInstanceUIDs[self.slice_id]
        self.lbl_holder.SAVED = False

    def saveCurrentPatient(self):
        folder_name = "Label-"+Path(self.fl.getPath()).stem + "-" + self.labeler_name.replace(" ", "_")
        file_path = os.path.join(self.output_path, folder_name)
        if os.path.exists(file_path):
            if not self._alertMsg("Data exists, overwrite?"):
                return 
        self.lbl_holder.saveToFile(
                path = file_path,
                imgs = self.imgs,
                labeler = self.labeler_name,
                spacing = self.spacing,
                series = str(self.combo_series.currentText())
                )
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

    def __getSingleMask(self, idx, label):
        """get mask for a single label in single image, used for interpolation"""
        if idx <0 or idx > len(self.imgs)-1:
            return None
        im_shape = self.imgs[idx].shape
        mask = np.zeros(im_shape[:2], np.uint8)
        cnts_data = self.lbl_holder.data[idx][label]
        if cnts_data == []:
            return None
        for cnt_data in cnts_data:
            all_pts = cnt_data["Contour"] # All the points position on the contour, in CV coordinate
            if cnt_data["Open"] == True:
                cv_cnt = np.array([arr for arr in F.removeDuplicate2d(all_pts)])
                cv.polylines(mask,[cv_cnt],False,1)
            else:
                cv_cnt = np.array([[arr] for arr in F.removeDuplicate2d(all_pts)])
                cv.fillPoly(mask, pts = [cv_cnt], color = 1)
        mask = mask.astype(np.bool)
        return mask

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
        self.lbl_wd.setText("Console -- LABELER: {} || OUTPUT_PATH: {}".\
                format(self.labeler_name, str(self.output_path)))

    def __readSeries(self):
        """update self.imgs and self.SOPInstanceUIDs by current chosen image series"""
        entry = str(self.combo_series.currentText())
        image_data = self.fl.curr_patient.getSeriesImg(entry)
        self.imgs = image_data["Images"]
        self.SOPInstanceUIDs = image_data["SOPInstanceUIDs"]
        self.spacing = image_data["Spacing"]
        self.lbl_holder.initialize(LABELS, self.SOPInstanceUIDs) 

    def __disableWidgets(self, *widgets):
        for w in widgets:
            w.setEnabled(False)
    
    def __querySave(self):
        """Check if there are unsaved changes"""
        if not self.lbl_holder.SAVED:
            if self._alertMsg("Unsaved changes, continue?"):
                self.lbl_holder.SAVED = True # prevent multiple calls
                return 0
            else:
                return 1
        else:
            return 0

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

    def showHelpManual(self):
        file_path = os.path.realpath("help.html")
        webbrowser.open("file://"+file_path)
    
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
            if not self.__cache["data_loaded"]:
                return False
            self.im_widget.style.mouseMoveEvent(None, None)
        return super().eventFilter(receiver, event)

    def wheelEvent(self, event):
        if not self.__cache["data_loaded"]:
            return 
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
