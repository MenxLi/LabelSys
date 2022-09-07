#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#
from PyQt6.QtWidgets import \
    (QRadioButton, QButtonGroup, QLabel, QWidget, QDialog, QFormLayout, QVBoxLayout, QHBoxLayout, \
     QGridLayout, QPushButton, QTabWidget, QDialogButtonBox, QLineEdit)
from PyQt6.QtGui import QIntValidator
import copy


class SettingsDialog(QDialog):
    def __init__(self, mainw):
        """- mainw: mainwindow object"""
        super().__init__(mainw)
        self.mainw = mainw
        self.config = copy.deepcopy(mainw.config)

        btns = QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel
        self.button_box = QDialogButtonBox(btns)
        self.button_box.clicked.connect(self.__handleButtonClick)

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(GeneralTab(self), "General")
        self.tab_widget.addTab(LabelTab(self), "Labels")

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tab_widget)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)

        self.setWindowTitle("Settings")

    def quitWindow(self):
        print("Change declined")
        self.close()

    def applyChanges(self):
        self.mainw.config = self.config
        print("Change applied")
        #  print("This part isn't finished")
        self.close()

    def __handleButtonClick(self, button):
        sb = self.button_box.standardButton(button)
        if sb == QDialogButtonBox.StandardButton.Apply:
            self.applyChanges()
        elif sb == QDialogButtonBox.StandardButton.Cancel:
            self.quitWindow()


class SettingsTab(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def applyTabChanges(self):
        pass


class GeneralTab(SettingsTab):
    def __init__(self, parent):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.loading_mode_settings = SetLoadingMode(self, self.parent.config)
        layout.addWidget(self.loading_mode_settings)
        self.preview_settings = Set2DMagification(self, self.parent.config)
        layout.addWidget(self.preview_settings)
        self.setLayout(layout)


class LabelTab(SettingsTab):
    def __init__(self, parent):
        super().__init__(parent)


class SetLoadingMode(QWidget):
    loading_mode_names = ["Dicom", "Image", "Video"]
    loading_modes = [0,1,2]
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config    # Shallow copy
        self.default_value = config["loading_mode"]
        self.initUI()

    def initUI(self):
        grid = QGridLayout()
        self.setLayout(grid)
        self.loading_mode_group = QButtonGroup(self)

        self.rb_group = QButtonGroup()
        grid.addWidget(QLabel(text = "Loading mode: "), 0, 0)
        for i in range(len(self.loading_modes)):
            r = QRadioButton(self.loading_mode_names[i])
            r.idx = self.loading_modes[i]
            r.toggled.connect(self.onClicked)
            self.rb_group.addButton(r, i)
            if r.idx == self.default_value:
                r.setChecked(True)
            self.loading_mode_group.addButton(r)
            grid.addWidget(r, 0, i+1)

    def onClicked(self):
        radioBtn: QRadioButton = self.sender()
        if radioBtn.isChecked():
            value = radioBtn.idx
            self.config["loading_mode"] = value


class Set2DMagification(QWidget):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.default_value = config["2D_magnification"]
        self.initUI()

    def initUI(self):
        layout = QFormLayout()
        e = QLineEdit()
        e.setValidator(QIntValidator(1, 10))
        e.setText(str(self.default_value))
        e.textChanged.connect(self.tChanged)
        #  e.editingFinished.connect(self.tEditFinish)
        #  e.setAlignment()

        layout.addRow("2D preview magnification: ", e)
        self.setLayout(layout)

    def tChanged(self, text):
        try:
            self.config["2D_magnification"] = int(text)
        except:
            pass

    def tEditFinish(self):
        pass



