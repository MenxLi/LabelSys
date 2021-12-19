#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#
# {{{
from PyQt5 import uic
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent
from .labelResultHolder import LabelHolder
from .vtkClass import VtkWidget
from .utils import utils_ as F
from .configLoader import _UI_DIR

import os, sys
from pathlib import Path
# }}}

class CompareWidget(QWidget):
    def __init__(self, parent):# {{{
        super().__init__()
        self.parent = parent    # mainWindow
        self.initUI()
# }}}
    def initUI(self):# {{{
        ui_path = os.path.join(_UI_DIR, "compareWidget.ui")
        uic.loadUi(ui_path, self)
        self.setWindowTitle("Compare Widget")
        self.L_part = CompareWidgetVisualPart(self.frame_L, self)
        self.R_part = CompareWidgetVisualPart(self.frame_R, self)

        self.btn_next_slice.clicked.connect(self.nextSlice)
        self.btn_prev_slice.clicked.connect(self.prevSlice)
        self.combo_label.currentTextChanged.connect(self.changeComboLabels)
        self.btn_save.clicked.connect(self.save)
        self.btn_reset_camera.clicked.connect(self.resetCamera)
# }}}
    def nextSlice(self):# {{{
        self.L_part.nextSlice()
        self.R_part.nextSlice()
# }}}
    def prevSlice(self):# {{{
        self.L_part.prevSlice()
        self.R_part.prevSlice()
# }}}
    def changeComboLabels(self, entry):# {{{
        self.R_part.curr_lbl = entry
        self.L_part.curr_lbl = entry
        if self.R_part._cache["data_loaded"]:
            try:    # prevent triggering with blank entry
                self.R_part._updateImg()
            except: pass
        if self.L_part._cache["data_loaded"]:
            try:    # prevent triggering with blank entry
                self.L_part._updateImg()
            except: pass
# }}}
    def save(self):# {{{
        if self.R_part.file_path == self.L_part.file_path:
            if not self._alertMsg("The two images have the same output path and are labeled by same labeler. Output files will overwrite each other to corrupt the result. Continue?"):
                return
        if self.R_part._cache["data_loaded"]:
            self.R_part.saveCurrentPatient()
        if self.L_part._cache["data_loaded"]:
            self.L_part.saveCurrentPatient()
# }}}
    def rebaseSliceId(self):# {{{
        """Will be called by CompareWidgetVisualPart to sync slice idx"""
        self.R_part.slice_id = 0
        self.R_part._updateImg()
        self.L_part.slice_id = 0
        self.L_part._updateImg()
# }}}
    def resetCamera(self):#{{{
        self.R_part.resetCamera()
        self.L_part.resetCamera()
#}}}
    def wheelEvent(self, event):# {{{
        modifier = QtWidgets.QApplication.keyboardModifiers()
        if event.angleDelta().y() < 0:
            if modifier != Qt.ControlModifier:
                self.prevSlice()
            else:
                if self.R_part._cache["data_loaded"]: self.R_part.im_widget.style.OnMouseWheelForward()
                if self.L_part._cache["data_loaded"]: self.L_part.im_widget.style.OnMouseWheelForward()
        else:
            if modifier != Qt.ControlModifier:
                self.nextSlice()
            else:
                if self.R_part._cache["data_loaded"]: self.R_part.im_widget.style.OnMouseWheelBackward()
                if self.L_part._cache["data_loaded"]: self.L_part.im_widget.style.OnMouseWheelBackward()
#}}}
    def _alertMsg(self,msg, title = "Alert", func = lambda x : None):# {{{
        msg_box = QMessageBox()
        msg_box.setText(msg)
        msg_box.setWindowTitle(title)
        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg_box.buttonClicked.connect(func)
        return_value = msg_box.exec()
        if return_value == QMessageBox.Ok:
            return True
        else: return False
# }}}

class CompareWidgetVisualPart(QWidget):
    INIT_STEP = 15
    COLOR = (1,0,0)
    def __init__(self, frame, parent):# {{{
        super().__init__(frame)
        self.parent = parent    # compareWidget
        self.master = frame
        self.initUI()

        # Should be the same format as mainWindow
        # Will be finished in the future, now using class static variables instead
        self.config = {
            "labels":[],
            "label_colors":[],
            "label_steps":[]
        }
        self._cache = {
            "data_loaded": False
        }

        # arributes
        self.header = {}    # header in the saved file
        self.slice_id = 0
        self.curr_lbl = ""
        self.imgs = []
        self.SOPInstanceUIDs = []
        self.spacing = (1,1,1)
        self.labeler_name = "Anonymous"
        self.lbl_holder = LabelHolder()
        self.file_path = ""
# }}}
    def initUI(self):# {{{
        ui_path = os.path.join(_UI_DIR, "compareVisualWidget.ui")
        uic.loadUi(ui_path, self)
        layout = QGridLayout()
        layout.addWidget(self, 0,0)
        self.master.setLayout(layout)
        self.check_crv = QCheckBox()        # decoy checkbox to record curve type used by VtkWidget
        self.check_crv.setVisible(False)
        self.im_widget = VtkWidget(self.im_frame, self)
        self.btn_load.clicked.connect(self.loadFile)
# }}}
    def initConfig(self, header):# {{{
        """
        This method is a placeholder method for now, will be deprecated in the future
        """
        self.config["labels"] = header["Labels"]
        for i in self.config["labels"]:
            self.config["label_colors"].append(self.COLOR)
            self.config["label_steps"].append(self.INIT_STEP)
# }}}
    def loadFile(self):# {{{
        """Load a labeld file for one patient"""
        fname = QFileDialog.getExistingDirectory(self, "Select loading directory")
        if fname == "":
            return 1
        header, imgs = self.lbl_holder.loadFile(Path(fname))
        self.loadData(header, self.lbl_holder.data, imgs, fname)
# }}}
    def loadData(self, header, data, imgs, file_path):# {{{
        """
        load directly from data directly (from mainWindow) instead of loading from file
        - header: Label result header file
        - data: LabelHolder.data
        - imgs
        - file_path: path to save the result
        """
        if self.lbl_holder.data == None or self.lbl_holder.data == []:
            # Loaded from file
            self.lbl_holder.data = data
            self.lbl_holder.SAVED = True
        self.imgs = imgs
        self.SOPInstanceUIDs = [s["SOPInstanceUID"] for s in self.lbl_holder.data]
        self.labeler_name = header["Labeler"]
        self.spacing = header["Spacing"]
        #  self.series = header["Series"]
        self.file_path = file_path

        try:
            self.config = header["Config"]
        except KeyError:
            # in the older version of this tool header don't contain "config" attribute, Labels
            # attribute was used instead
            print("Warning: The header file does not contain config attribute, maybe this data was labeled with older version of the tool. \n You can ignore this warning if no error occurs, please save this file in the mainWindow to overwrite previous one to add config attribute.")
            self.config = self.parent.parent.config     # load mainWindow configration file
            #  self.config["labels"] = header["Labels"]
            #  for i in self.config["labels"]:
            #      self.config["label_colors"].append(self.COLOR)
            #      self.config["label_steps"].append(self.INIT_STEP)

        self.parent.combo_label.clear()
        self.parent.combo_label.addItems(self.config["labels"])
        self.curr_lbl = str(self.parent.combo_label.currentText())

        self._cache["data_loaded"] = True

        self.lbl_output_path.setText("OUTPUT_PATH: "+ os.path.dirname(str(self.file_path)))
        self.lbl_info.setText(header["Labeler"]+" - "+header["Time"][:19])

        self.header = header

        self.parent.rebaseSliceId()     # Sync silce by forcing slice id to 0
        self._updateImg()
# }}}
    def nextSlice(self):# {{{
        if not self._cache["data_loaded"]:
            return
        if self.slice_id >= len(self.imgs)-1:
            return 1
        self.slice_id += 1
        self._updateImg()
# }}}
    def prevSlice(self):# {{{
        if not self._cache["data_loaded"]:
            return
        if self.slice_id < 1:
            return 1
        self.slice_id -= 1
        self._updateImg()
        return 0
# }}}
    def _updateImg(self):# {{{
        if not self._cache["data_loaded"]:
            return
        im = F.map_mat_255(self.imgs[self.slice_id])
        slice_info = "Slice: "+ str(self.slice_id+1)+"/"+str(len(self.imgs))
        img_info = "Image size: {} x {}".format(*im.shape)
        txt = slice_info + "\n" + img_info

        self.im_widget.readNpArray(im, txt)
        self.im_widget.reInitStyle()
        idx = self.config["labels"].index(self.curr_lbl)
        self.im_widget.setStyleSampleStep(self.config["label_steps"][idx])

        # load contour
        cnts_data = self.lbl_holder.data[self.slice_id][self.curr_lbl]
        if cnts_data != []:
            for cnt in cnts_data:
                self.im_widget.loadContour(cnt["Points"], cnt["Open"])
# }}}
    def resetCamera(self):#{{{
        if self._cache["data_loaded"]:
            self.im_widget.resetCamera()
#}}}
    def saveCurrentSlice(self, cnts_data):# {{{
        # will be called by vtkClass
        self.lbl_holder.data[self.slice_id][self.curr_lbl] = cnts_data
        self.lbl_holder.data[self.slice_id]["SOPInstanceUID"] = self.SOPInstanceUIDs[self.slice_id]
        self.lbl_holder.SAVED = False
# }}}
    def saveCurrentPatient(self):# {{{
        self.lbl_holder.saveToFile(self.file_path, self.imgs, self.header)
        self.lbl_holder.SAVED = True
# }}}
    def _getColor(self, label):# {{{
        # will be called by vtkClass
        try:
            idx = self.config["labels"].index(label)
        except:
            return (1,0,0)
        return self.config["label_colors"][idx]
# }}}
    def wheelEvent_deprecated(self, event):# {{{
        if self._cache["data_loaded"] == False:
            return
        modifier = QtWidgets.QApplication.keyboardModifiers()
        if event.angleDelta().y() < 0:
            if modifier == Qt.ControlModifier:
                self.im_widget.style.OnMouseWheelForward()
        else:
            if modifier == Qt.ControlModifier:
                self.im_widget.style.OnMouseWheelBackward()
# }}}
