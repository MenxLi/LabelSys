#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#
from typing import List, Optional, Sequence
import webbrowser
from pathlib import Path
import os,sys, platform
import copy

from .version import __version__, __license__, __license_full__
from .fileReader import FolderLoader
from .utils.labelReader import checkFolderEligibility
from .configLoader import *
from .utils import utils_ as F
from .utils import specificUtils as SU
from .labelResultHolder import LabelHolder
from .previewGUI import Preview3DWindow, Preview2DWindow
from .settingsGUI import SettingsDialog
from .compareWidget import CompareWidget
from .vtkClass import VtkWidget
from .coreWidgets import WidgetCore, EmittingStream, loggedFunction
from .configLoader import _ICON_DIR, _DOC_DIR, _UI_DIR, LOG_FILE
from .commentGUI import CommentGUI
from .interactionStyle import StyleImWidgetBase

from .ui._mainWindowGUI import MainWindowGUI

import numpy as np
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QIcon
from PyQt6 import uic
import cv2 as cv

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))
from .toothSeg_utils.io import ResizeImageRecord

class MainWindow(MainWindowGUI, WidgetCore):
    resized = QtCore.pyqtSignal()
    # Init{{{
    def __init__(self,args):
        super().__init__()
        self.setWindowIcon(QIcon(os.path.join(_ICON_DIR, "main.ico")))
        if not args.dev:
            sys.stdout = EmittingStream(textWritten = self.stdoutStream)
            sys.stderr = EmittingStream(textWritten = self.stdoutStream)
        # load UI
        ui_path = os.path.join(_UI_DIR,  "mainWindow.ui")
        uic.load_ui.loadUi(ui_path, self)
        self.args = args

        # set style sheet
        self.tb_console.setStyleSheet("color: white; background-color:black;")

        # UI change
        self.showFullScreen(); self.__screen_mode = 2
        self.setWindowTitle("LabelSys "+__version__)
        self.setFocus()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.initMenu()

        # Attribute init
        self.output_path = Path(os.getcwd()).parent
        self.labeler_name = platform.node()
        self.lbl_holder = LabelHolder()
        self.resize_record = ResizeImageRecord()

        self.slice_id = 0

        # Widget to disable when load
        self.loading_disable_list = (
                self.btn_next_patient,
                self.btn_prev_patient,
                self.combo_series
                )

        self.__configSetup()

        # store some status indicator and temporary variables
        self.__cache = {
                "data_loaded":False, # Indicate whether there are date loaded in main window
                "prev_combo_series": None, # used for decline combo series change with unsaved data
                "output_set": False, # Indecate wether user have set the output path
                "load_path": None # save the path of loaded labeled data
                }
        # data
        self.imgs: List[np.ndarray]     # current image series of a patient
        self.uids: List[str]            # UIDs of self.imgs
        self.slice_id: int              # current slice id
        self.curr_lbl: str              # current label selected

        self.central_widget.setEnabled(False)

        self.initImageUI()
        self.initPanel()

        im_wid_style_base = StyleImWidgetBase(self)
        im_wid_style_base.apply(self.im_widget)

        if args.file:
            if args.load:
                self.loadLabeledFile(args.file)
            else:
                self.loadPatients(args.file)

        welcome_msg = "\
---------------------------------------------\n\
Welcome to LabelSys v{version},\n\
 - Using Configuration file at: \n\
    {conf_path},\n\
 - Log file: \n\
    {log_file_path},\n\
 - For help see: Help -> manual\n\
---------------------------------------------\n\
".format(version = __version__,conf_path = CONF_PATH, log_file_path = LOG_FILE)

        if self.args.dev:
            print("Developing mode...")
        print(welcome_msg)

    def __configSetup(self):
        """Unfinished function, will move all CONF attributes into self.config in the future"""
        self.config = {
            "labels": LABELS,
            "label_modes": LBL_MODE,
            "label_colors": LBL_COLORS,
            "label_steps": LBL_STEP,
            "loading_mode": None,
            "default_series": SERIES,
            "default_label":DEFAULT_LABEL,
            "2D_magnification":PREVIEW2D_MAG,
            "max_im_height":MAX_IM_HEIGHT,
            "classifications": CLASSIFICATIONS,
            "label_draw": LBL_DRAW,
        }
        if self.args.loading_mode != None:
            # if not loading mode in the command line
            self.config["loading_mode"] = self.args.loading_mode
        else: self.config["loading_mode"] = CONF["Loading_mode"]

    def initMenu(self):
        # File
        self.act_open.triggered.connect(lambda: self.loadPatients())
        self.act_open.setShortcut("Ctrl+O")
        self.act_quit.triggered.connect(lambda: self.quitApp())
        self.act_quit.setShortcut("Ctrl+Q")
        self.act_load.triggered.connect(lambda: self.loadLabeledFile())
        self.act_load.setShortcut("Ctrl+L")

        # View
        self.act_fullscreen.triggered.connect(lambda: self.changeScreenMode())
        self.act_fullscreen.setShortcut("Ctrl+F")
        self.act_2D_preview.triggered.connect(lambda: self.previewLabels2D())
        self.act_2D_preview.setShortcut("Ctrl+P")
        self.act_3D_preview.triggered.connect(lambda: self.previewLabels3D())
        self.act_check_preview.triggered.connect(lambda : self.check_preview.setChecked(not self.check_preview.isChecked()))
        self.act_check_preview.setShortcut("Ctrl+Space")

        # Operation
        self.act_op_next_slice.triggered.connect(lambda: self.nextSlice())
        self.act_op_next_slice.setShortcut("Up")
        self.act_op_prev_slice.triggered.connect(lambda: self.prevSlice())
        self.act_op_prev_slice.setShortcut("Down")
        self.act_op_next_patient.triggered.connect(lambda: self.nextPatient())
        self.act_op_next_patient.setShortcut("Right")
        self.act_op_prev_patient.triggered.connect(lambda: self.prevPatient())
        self.act_op_prev_patient.setShortcut("Left")
        self.act_op_change_lbl.triggered.connect(lambda: self.switchLabel())
        self.act_op_change_lbl.setShortcut("Tab")
        self.act_op_change_lbl_reverse.triggered.connect(lambda: self.switchLabelReverse())
        self.act_op_change_lbl_reverse.setShortcut("Shift+Tab")
        self.act_op_toAnotherLbl.triggered.connect(lambda: self.queryToAnotherLabel())
        self.act_op_change_lbl_reverse.setShortcut("Shift+Tab")
        self.act_op_save.triggered.connect(lambda: self.saveCurrentPatient())
        self.act_op_save.setShortcut("Ctrl+S")
        self.act_op_clear.triggered.connect(lambda: self.clearCurrentSlice())
        self.act_op_clear.setShortcut("Esc")
        self.act_op_interp.triggered.connect(self.interpCurrentSlice)
        self.act_op_interp.setShortcut("Ctrl+I")
        self.act_op_add_cnt.triggered.connect(lambda: self.addContour())
        self.act_op_add_cnt.setShortcut("Ctrl+A")
        self.act_op_rotate.triggered.connect(self.rotateImage)
        self.act_op_rotate.setShortcut("Ctrl+R")
        self.act_op_add_bbox.triggered.connect(self.addBBox)
        self.act_op_add_bbox.setShortcut("Ctrl+B")
        self.act_op_edit_comment.triggered.connect(lambda: self.editComment())
        self.act_op_edit_comment.setShortcut("Ctrl+C")

        # Tools
        self.act_tool_compare.triggered.connect(self.openCompareWindow)
        self.act_tool_compare.setShortcut("Ctrl+Shift+Alt+C")
        self.act_tool_crop.triggered.connect(self.openCropAndRotateWindow)
        self.act_tool_crop.setShortcut("Shift+C")

        # Settings
        self.act_set_path.triggered.connect(lambda: self.setOutputPath())
        self.act_set_path.setShortcut("Ctrl+Alt+P")
        self.act_set_lbler.triggered.connect(lambda: self.setLabeler())
        self.act_set_lbler.setShortcut("Ctrl+Alt+L")
        self.act_set_settings.triggered.connect(lambda: self.setSettings())
        self.act_set_settings.setShortcut("Ctrl+Alt+S")

        # Help
        self.act_help_manual.triggered.connect(self.showHelpManual_en)
        self.act_help_manual_zh.triggered.connect(self.showHelpManual_zh)
        self.act_help_info.triggered.connect(lambda: self._msgDialog(
            title="Info",
            message="\n".join([
                "LabelSys (Version: {})".format(__version__),
                "Author: Li, Mengxun (mengxunli@whu.edu.cn)",
                "License: {}".format(__license__)
            ]),
            info_msg=__license_full__
        ))

    def initPanel(self):
        """Init the whole panel, will be called on loading the patients"""
        self.slider_im.setPageStep(1)
        self.combo_label.addItems(self.config["labels"])
        self.curr_lbl = str(self.combo_label.currentText())
        self.__updateQLabelText()

        self.resized.connect(self.__updateVTKText)
        self.combo_series.currentTextChanged.connect(self.changeComboSeries)
        self.combo_label.currentTextChanged.connect(self.changeComboLabels)
        self.check_crv.stateChanged.connect(self.changeCheckCrv)
        self.check_draw.stateChanged.connect(self.changeCheckDraw)
        self.check_preview.stateChanged.connect(lambda: self.changeCheckPreview())
        self.btn_next_slice.clicked.connect(lambda: self.nextSlice())
        self.btn_prev_slice.clicked.connect(lambda: self.prevSlice())
        self.btn_next_patient.clicked.connect(lambda: self.nextPatient())
        self.btn_prev_patient.clicked.connect(lambda: self.prevPatient())
        self.btn_save.clicked.connect(lambda: self.saveCurrentPatient())
        self.btn_clear.clicked.connect(lambda: self.clearCurrentSlice())
        self.btn_interp.clicked.connect(self.interpCurrentSlice)
        # self.btn_preview.clicked.connect(self.previewLabels2D)
        self.btn_add_cnt.clicked.connect(self.addContour)
        self.btn_add_bbox.clicked.connect(self.addBBox)
        self.btn_comment.clicked.connect(lambda: self.editComment())
        self.slider_im.valueChanged.connect(self.changeSliderValue)

    def initImageUI(self):
        """Put image on to main window, will be called on loading the patients"""
        self.im_widget = VtkWidget(self.im_frame, self)

    # Load images{{{
    @loggedFunction
    def loadPatients(self, fname: Optional[str] = None):
        """Load patients folder, and call initPanelAct() to initialize the panel"""
        if fname is None:
            fname = QFileDialog.getExistingDirectory(self, "Select data directory to open")
        if fname == "":
            return 1
        file_path = Path(fname)

        if not self.args.dev:
            # Do not quit when error occur while opening files
            try:
                self.fl = FolderLoader(file_path, mode = self.config["loading_mode"])
                self.__updatePatient()
            except Exception as excp:
                print("An error happend when opening files: ", excp)
                return 1
        else:
            self.fl = FolderLoader(file_path, mode = self.config["loading_mode"])
            self.__updatePatient()


        self.central_widget.setEnabled(True)
        self.setWidgetsEnabled(True, *self.loading_disable_list)

        self.__cache["data_loaded"] = True
        return 0

    @loggedFunction
    def loadLabeledFile(self, fname: Optional[str] = None):
        """Load a labeld file for one patient"""
        if fname is None:
            fname = QFileDialog.getExistingDirectory(self, "Select labeled directory to load")
        if fname == "":
            return 1
        if not checkFolderEligibility(fname):
            print("The selected folder is not eligiable: ", fname)
            return 1
        self.central_widget.setEnabled(True)
        self.setWidgetsEnabled(False, *self.loading_disable_list)
        self.fl = None  # prevent lbl_holder initialize when changing series and alter saving behaviour
        self.slice_id = 0
        header, self.imgs = self.lbl_holder.loadFile(Path(fname))
        try:
            self.config = header["Config"]
            # To compat oler version (<1.6.0)
            if "classifications" not in self.config.keys():
                self.config["classifications"] = [None]*len(self.imgs)
            if "label_draw" not in self.config.keys():
                self.config["label_draw"] = [1]*len(self.imgs)
        except KeyError:
            # In the older version of this tool header don't contain "config" attribute, Labels
            # attribute was used instead
            self.config["labels"] = header["Labels"]
            print("Warning: The header file does not contain config attribute, maybe this data was labeled with older version of the tool. \n You can ignore this warning if no error occurs, please save this file to overwrite previous one to add config attribute.")

        # self.uids = [s["SOPInstanceUID"] for s in self.lbl_holder.data]
        self.uids = self.lbl_holder.uids
        self.labeler_name = header["Labeler"]
        self.spacing = header["Spacing"]

        self.combo_label.clear()
        # self.combo_label.addItems(header["Labels"])
        self.combo_label.addItems(self.config["labels"])
        self.curr_lbl = str(self.combo_label.currentText())

        self.combo_series.clear()
        self.combo_series.addItem(header["Series"])

        self.slider_im.setSliderPosition(self.slice_id)
        self.slider_im.setMaximum(len(self.imgs)-1)

        self.__cache["data_loaded"] = True

        self.output_path = Path(fname).parent
        self.__cache["load_path"] = fname
        self.__updateQLabelText()
        self.resize_record.loadFromFile(os.path.join(fname, "resize_data.pkl"))
        print("Data loaded")

    def quitApp(self):
        if not self.lbl_holder.SAVED and not self.args.dev:
            if not self._alertMsg("Unsaved changes, quitting?"):
                return 1
        # Erase some log if it's too long
        #  MAX_LOG_LINES = 1000
        #  with open(LOG_FILE, "r", encoding="utf-8") as fp:
        #      lines = fp.readlines()
        #  if len(lines) > MAX_LOG_LINES:
        #      with open(LOG_FILE, "w", encoding="utf-8") as fp:
        #          fp.write("".join(lines[-MAX_LOG_LINES//2:]))
        self.close()
        return 0

    @loggedFunction
    def changeScreenMode(self):
        """Change screen mode between Normal Maximized and full screen"""
        self.__screen_mode = (self.__screen_mode+1)%3
        if self.__screen_mode == 0:
            self.showNormal()
        elif self.__screen_mode == 1:
            self.showMaximized()
        elif self.__screen_mode == 2:
            self.showFullScreen()

    @loggedFunction
    def setOutputPath(self):
        fname = QFileDialog.getExistingDirectory(self, "Select output directory")
        if fname == "":
            return 1
        self.output_path = Path(fname)
        self.__cache["output_set"] = True
        self.__updateQLabelText()
        return 0

    @loggedFunction
    def setLabeler(self):
        """Set labeler name"""
        text, ok = QInputDialog.getText(self, "Set labeler", "Enter your name: ")
        if ok:
            self.labeler_name = str(text)
            self.__updateQLabelText()

    @loggedFunction
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
        """
        Change label, be linked to self.combo_label.currentTextChange;
        should not be called directly if aiming at change combo text,
        self.combo_label.setCurrentText(...) should be used instead.
        """
        self.curr_lbl = entry
        try:    # prevent triggering when clear
            self.__updateImg()
            mode = self.config["label_modes"][self.config["labels"].index(self.curr_lbl)]
            if mode == 1:
                self.check_crv.setChecked(True)
            elif mode == 0:
                self.check_crv.setChecked(False)
            draw_mode = self.config["label_draw"][self.config["labels"].index(self.curr_lbl)]
            if draw_mode == 1:
                self.check_draw.setChecked(True)
            elif draw_mode == 0:
                self.check_draw.setChecked(False)
            self.im_widget.setStyleAuto()      # May change label drawing mode
        except: pass

    @loggedFunction
    def queryToAnotherLabel(self):
        """Change current label selection while retain the contours,
        would be useful if someone did some labeling already,
        and found they are working in a wrong label.
        """
        aval_labels:List[str] = self.config["labels"]
        item, ok = QInputDialog.getItem(self, "Select label name.", "Avaliable labels", \
            aval_labels, aval_labels.index(self.curr_lbl), False)
        if ok and item!=self.curr_lbl:
            assert self.lbl_holder.data is not None     # Type checking
            data = self.lbl_holder.data[self.slice_id]
            data[item] += data[self.curr_lbl]
            data[self.curr_lbl] = []
            self.combo_label.setCurrentText(item)
        else:
            self._warnDialog("Failed.")

    @loggedFunction
    def changeCheckCrv(self, i):
        if self.check_crv.isChecked():
            self.config["label_modes"][self.config["labels"].index(self.curr_lbl)] = 1
        else:
            self.config["label_modes"][self.config["labels"].index(self.curr_lbl)] = 0

    @loggedFunction
    def changeCheckDraw(self, i):
        if self.check_draw.isChecked():
            self.config["label_draw"][self.config["labels"].index(self.curr_lbl)] = 1
        else:
            self.config["label_draw"][self.config["labels"].index(self.curr_lbl)] = 0
        self.im_widget.setStyleAuto()          # May change label drawing mode

    @loggedFunction
    def changeCheckPreview(self):
        self.__updateImg()

    def changeSliderValue(self):
        """Triggered when slider_im changes value"""
        self.slice_id = self.slider_im.value()
        # self.__updateImg()
        self.changeComboLabels(self.combo_label.currentText())  # A hack to update checkboxes and image

    def switchLabel(self):
        """switch between labels, for shortcut use"""
        new_label_id = (self.config["labels"].index(self.curr_lbl) + 1)%len(self.config["labels"])
        self.combo_label.setCurrentText(self.config["labels"][new_label_id]) # will trigger changeComboLabels()

    def switchLabelReverse(self):
        """switch between labels, for shortcut use"""
        new_label_id = (self.config["labels"].index(self.curr_lbl) - 1)%len(self.config["labels"])
        self.combo_label.setCurrentText(self.config["labels"][new_label_id]) # will trigger changeComboLabels()

    @loggedFunction
    def nextSlice(self):
        if self.slice_id >= len(self.imgs)-1:
            return 1
        self.slice_id += 1
        self.slider_im.setSliderPosition(self.slice_id)
        try:
            # to be compatible with older version (1.2.2 and below)
            if self.config["default_label"] != "":
                self.combo_label.setCurrentText(self.config["default_label"])
        except KeyError:pass
        try:
            # update 2D preview window
            if self.preview_win_2d.isVisible():
                #  self.preview_win_2d.nextSlice()
                self.preview_win_2d.slice_id = self.slice_id
                self.preview_win_2d._updatePanel()
        except: pass
        return 0

    @loggedFunction
    def prevSlice(self):
        if self.slice_id < 1:
            return 1
        self.slice_id -= 1
        self.slider_im.setSliderPosition(self.slice_id)
        try:
            # to be compatible with older version (1.2.2 and below)
            self.combo_label.setCurrentText(self.config["default_label"])
        except KeyError:pass
        try:
            # update 2D preview window
            if self.preview_win_2d.isVisible():
                self.preview_win_2d.prevSlice()
        except: pass
        return 0

    @loggedFunction
    def nextPatient(self):
        if self.__querySave() == 1:
            return
        if self.fl.next():
            self.__updatePatient()
            return 0

    @loggedFunction
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
        self.preview_win_3d = Preview3DWindow(self, self.imgs, self.__getMasks(), spacing = self.spacing)
        self.preview_win_3d.show()

    def previewLabels2D(self):
        if not self.__cache["data_loaded"]:
            pass
        self.preview_win_2d = Preview2DWindow(self, self.imgs, self.__getMasks(), self.slice_id,\
                                              self.spacing, magnification = self.config["2D_magnification"])
        self.preview_win_2d.show()

    def openCompareWindow(self):
        self.compare_win = CompareWidget(self)
        self.compare_win.show()

        try:
            # When there is file loaded in main window. Get output file path
            try:
                # Opening dicom file
                folder_name = "Label-"+Path(self.fl.getPath()).stem + "-" + self.labeler_name.replace(" ", "_")
            except:
                # Loading labeled data
                folder_name = Path(self.__cache["load_path"]).stem
            file_path = os.path.join(self.output_path, folder_name)

            # open up compare window with left side loading current images
            header = SU.createHeader(labeler = self.labeler_name,
                                 spacing = self.spacing,
                                 series = str(self.combo_series.currentText()),
                                 config = self.config)

            self.compare_win.L_part.loadData(header, \
            self.lbl_holder.data, self.imgs, file_path)
        except:pass     # When no file is loaded

    def openCropAndRotateWindow(self):
        try:
            from .sideWidgets.cropRotate.extIO import startCropGUI
            from immarker.extensions import registerCallback
        except ModuleNotFoundError:
            self._warnDialog("Immarker module is needed.")
            return 
        #  import logging
        #  logging.basicConfig(level = logging.DEBUG)
        img = self.imgs[self.slice_id]
        curr_slice_id = self.slice_id
        def callback_save(crop_im: np.ndarray, ori_im: np.ndarray, crop_coords: Sequence[np.ndarray]):
            """
            - crop_im: cropped image
            - ori_im: original image
            - crop_coords: 4 crop box vertices points' coordinate, in (x, y) - opencv coordinate
            """
            slice_uid = self.lbl_holder.uids[self.slice_id]
            self.resize_record.setCoords(self.slice_id, crop_coords)
            if self.imgs[curr_slice_id].shape != ori_im.shape:
                if not self._queryDialog("Original crop will lost, continue?"):
                    return
                self.resize_record.setOriIm(self.slice_id, ori_im)

            self.imgs[curr_slice_id] = crop_im
            self.__updateImg()
            if curr_slice_id != self.slice_id:
                self._warnDialog("You are at wrong slice. The correct slice has been changed.")
                return
            self.im_widget.resetCamera()

        @registerCallback("onPopupMsg")
        def on_popupMsg(app, msg: str, flag: str ):
            if flag == "warning":
                self._warnDialog(msg)
        startCropGUI(img.copy(), callback_save)

    def addContour(self):
        self.im_widget.style.forceDrawing()

    def addBBox(self):
        self._warnDialog("This function has not been implemented yet")

    @loggedFunction
    def editComment(self):
        def saveComments(classification_txt: str, comment_txt: str):
            if comment_txt == "":
                comment_txt = None
            self.lbl_holder.comments[self.slice_id] = comment_txt
            if classification_txt == "":
                classification_txt = None
            self.lbl_holder.class_comments[self.slice_id] = classification_txt
            self.__updateVTKText()

        self.comment_gui = CommentGUI(self, saveComments,
            classes= self.config["classifications"],
            current_classes_str=self.lbl_holder.class_comments[self.slice_id],
            current_comment=self.lbl_holder.comments[self.slice_id])
        self.comment_gui.show()

    @loggedFunction
    def saveCurrentSlice(self, cnts_data: List[dict]):
        """
        Will be triggered automatically when modifying the contour, will be
        called by vtkClass
        """
        self.lbl_holder.data[self.slice_id][self.curr_lbl] = cnts_data
        # self.lbl_holder.data[self.slice_id]["SOPInstanceUID"] = self.uids[self.slice_id]
        self.lbl_holder.uids[self.slice_id] = self.uids[self.slice_id]
        self.lbl_holder.SAVED = False

        # goes into segmentaion fault
        #  if self.check_preview.isChecked():
        #      self.__updateImg()

        try:
            # update 2D preview window
            if self.preview_win_2d.isVisible():
                self.preview_win_2d.updateInfo(self.__getMasks(), self.slice_id)
        except: pass

    @loggedFunction
    def saveCurrentPatient(self):
        file_path = self._getOutputPath()
        if os.path.exists(file_path):
            if not self._alertMsg("Data exists, overwrite?"):
                return
        header = SU.createHeader(labeler = self.labeler_name,
                                 spacing = self.spacing,
                                 series = str(self.combo_series.currentText()),
                                 config = self.config)
        #  self.lbl_holder.saveToFile( path = file_path,
        #          imgs = self.imgs,
        #          #labels = self.config["labels"],
        #          labeler = self.labeler_name,
        #          spacing = self.spacing,
        #          series = str(self.combo_series.currentText()),
        #          config = self.config
        #          )
        self.lbl_holder.saveToFile(file_path, self.imgs, header)
        self.__updateQLabelText()           # To get labeled marker
        self.lbl_holder.SAVED = True

        print("Exporting resize data.")
        self.resize_record.export(os.path.join(file_path, "resize_data.pkl"))
        print("done.")

    @loggedFunction
    def rotateImage(self):
        _has_label = False
        for entry in self.config["labels"]:
            if self.lbl_holder.data[self.slice_id][entry] != []:
                _has_label = True
                break
        if _has_label:
            if self._alertMsg("Rotate image will clear all labels for current image, continue?"):
                self.clearCurrentSlice()
                for lbl in self.config["labels"]:
                    self.lbl_holder.data[self.slice_id][lbl] = []
                self.clearCurrentSlice()
            else:
                return False
        self.imgs[self.slice_id] = self.imgs[self.slice_id][::-1]
        if F.img_channel(self.imgs[self.slice_id]) == 3:
            self.imgs[self.slice_id] = self.imgs[self.slice_id].transpose(1,0,2)
        elif F.img_channel(self.imgs[self.slice_id]) == 1:
            self.imgs[self.slice_id] = self.imgs[self.slice_id].transpose()
        self.__updateImg()
        return True
    
    def _getOutputPath(self) -> str:
        if not self.__cache["data_loaded"]:
            return ""
        try:
            # Opening dicom file
            folder_name = "Label-"+Path(self.fl.getPath()).stem + "-" + self.labeler_name.replace(" ", "_")
        except:
            # Loading labeled data
            folder_name = Path(self.__cache["load_path"]).stem
        file_path = os.path.join(self.output_path, folder_name)
        return file_path

    def _getColor(self, label):
        try:
            idx = self.config["labels"].index(label)
        except:
            return (1,0,0)
        return self.config["label_colors"][idx]

    def __getMasks(self):
        masks = []
        for slice_idx in range(len(self.imgs)):
            mask_data = {}
            for label in self.config["labels"]:
                mask_data[label] = np.zeros(self.imgs[slice_idx].shape[:2], np.uint8)
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

    def _getMarkedImg(self, idx):
        im = F.map_mat_255(self.imgs[idx])
        if F.img_channel(im) == 1:
            im = F.gray2rgb_(F.map_mat_255(im))
        for label, color in zip(self.config["labels"], self.config["label_colors"]):
            mask = self.__getSingleMask(idx, label)
            if mask is None:
                continue
            im = F.overlap_mask(im, mask, np.array(color)*255, alpha = 0.3)
        return im.copy()

    def __updateComboSeries(self):
        """Update the series combobox when changing patient"""
        self.combo_series.clear()
        series = self.fl.curr_patient.getEntries()
        self.combo_series.addItems(series)
        # set defult image series
        if self.config["default_series"] in series:
            self.combo_series.setCurrentText(self.config["default_series"])
        else:
            self.combo_series.setCurrentText(list(series)[0])

    def __updatePatient(self):
        """Update current showing patient, will be triggeted when changing patient"""
        self.slice_id = 0
        self.__updateComboSeries()
        self.__readSeries()
        # self.__updateImg()
        self.changeComboLabels(self.combo_label.currentText())  # A hack to update checkboxes and update image
        self.slider_im.setSliderPosition(self.slice_id)
        self.slider_im.setMaximum(len(self.imgs)-1)
        try:
            # to be compatible with older version (1.2.2 and below)
            self.combo_label.setCurrentText(self.config["default_label"])
        except KeyError:pass
        if not self.__cache["output_set"]:
            self.output_path = os.path.abspath( self.fl.getPath() )
            self.__updateQLabelText()
        self.CheckShapeCompatibility()

    def __updateImg(self):
        """update image showing on im_frame"""
        if not self.check_preview.isChecked():
            im = F.map_mat_255(self.imgs[self.slice_id])
        else:
            im = self._getMarkedImg(self.slice_id)

        self.im_widget.readNpArray(im)
        self.__updateVTKText()
        self.im_widget.reInitStyle()
        idx = self.config["labels"].index(self.curr_lbl)
        self.im_widget.setStyleSampleStep(self.config["label_steps"][idx])

        # load contour
        cnts_data = self.lbl_holder.data[self.slice_id][self.curr_lbl]
        if cnts_data != []:
            for cnt in cnts_data:
                self.im_widget.loadContour(cnt["Points"], cnt["Open"])

    def __updateVTKText(self):
        if not hasattr(self, "imgs") or self.imgs is None:
            return
        slice_info = "Slice: "+ str(self.slice_id+1)+"/"+str(len(self.imgs))
        img_info = "Image size: {} x {} ({dtype})".format(*self.imgs[self.slice_id].shape,
            dtype = self.imgs[self.slice_id].dtype)
        thickness_info = "Thickness: {}".format(self.spacing)
        comment = self.lbl_holder.comments[self.slice_id]
        class_comment = self.lbl_holder.class_comments[self.slice_id]
        if comment is None:
            comment_info = "Comment: <none>"
        else:
            comment_info = f"Comment: {comment}"
        if class_comment is None:
            class_comment_info = "Classification: <none>"
        else:
            class_comment_info = f"Classification: {class_comment}"
        show_txt = [slice_info, img_info, thickness_info, class_comment_info, comment_info]
        txt = "\n".join(show_txt)
        self.im_widget.updateText(txt)

    def __updateQLabelText(self):
        qlabel_txt = "Console -- LABELER: {} || OUTPUT_PATH: {}"
        if os.path.exists(self._getOutputPath()):
            qlabel_txt += " [LABELED]"
        self.lbl_wd.setText(qlabel_txt.\
                format(self.labeler_name, str(self.output_path)))

    def __readSeries(self):
        """update self.imgs and self.uids by current chosen image series"""
        entry = str(self.combo_series.currentText())
        image_data = self.fl.curr_patient.getSeriesImg(entry)
        self.imgs = image_data["Images"]
        self.uids = image_data["UIDs"]
        self.spacing = image_data["Spacing"]
        self.lbl_holder.initialize(self.config["labels"], self.uids)
        
        # for tooth segment project
        self.resize_record.init(self.imgs)

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

    def showHelpManual_en(self):
        file_path = os.path.join(_DOC_DIR, "help.html")
        file_path = os.path.realpath(file_path)
        webbrowser.open("file://"+file_path)

    def showHelpManual_zh(self):
        file_path = os.path.join(_DOC_DIR, "help-zh.html")
        file_path = os.path.realpath(file_path)
        webbrowser.open("file://"+file_path)

    def CheckShapeCompatibility(self):
        im_shape0 = self.imgs[0].shape
        for im in self.imgs:
            if im.shape != im_shape0:
                print("Incompatible shape among images, 3D preview will be unavaliable.")
                return False
        return True

    #==============Event Handler================
    def eventFilter(self, receiver, event):
        """Globally defined event"""
        modifier = QtWidgets.QApplication.keyboardModifiers()
        if(event.type() == QEvent.Type.KeyPress):
            """KeyBoard shortcut"""
            key = event.key()
            if key == Qt.Key.Key_Up:
                # Up : next slice
                self.nextSlice()
            if key == Qt.Key.Key_Down:
                # Down : previous slice
                self.prevSlice()
        if(event.type() == QEvent.Type.MouseMove):
            """vtk seems difficult in recognizing mouse dragging, so
            implimented With Qt"""
            if not self.__cache["data_loaded"]:
                return False
            self.im_widget.style.mouseMoveEvent(None, None)
        return super().eventFilter(receiver, event)

    def _wheelEvent_(self, event):
        # ** DEPRECATED **
        # The wheel event somehow can't be recognized (With PyQt6?)
        # re-implemented in interactionStyle.py using eventFilter
        if not self.__cache["data_loaded"]:
            return
        modifier = QtWidgets.QApplication.keyboardModifiers()
        if event.angleDelta().y() < 0:
            if modifier == Qt.KeyboardModifier.ControlModifier:
                self.im_widget.style.OnMouseWheelForward()
            else:
                self.prevSlice()
        else:
            if modifier == Qt.KeyboardModifier.ControlModifier:
                self.im_widget.style.OnMouseWheelBackward()
            else:
                self.nextSlice()

    def resizeEvent(self, a0) -> None:
        self.resized.emit()
        return super().resizeEvent(a0)

    def closeEvent(self, a0) -> None:
        self.im_widget.close()
        del self.im_widget
        return super().closeEvent(a0)
