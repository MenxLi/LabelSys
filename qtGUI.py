# from PyQt5.QtWidgets import QMainWindow, QWidget, QAction, QFileDialog, QComboBox, QFrame, Qsplitter, QVBoxLayout
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5 import uic
from version import __VERSION__, __DESCRIPTION__
from dicomFileReader import FolderLoader
from pathlib import Path
import os,sys

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))

class MainWindow(QMainWindow):
    def __init__(self,args):
        super().__init__()
        # load UI
        ui_path = os.path.join(LOCAL_DIR, "mainWindow.ui")
        uic.loadUi(ui_path, self)
        self.args = args
        # if dev mode, read from cmd
        if self.args.dev: self._loadPatients()

        self.showMaximized()
        self.setWindowTitle("LabelSys "+__VERSION__)

        sys.stdout = EmittingStream(textWritten = self.slotPutOnConsole)

    def _initMenuAct(self):
        self.act_imp.triggered.connect(self._loadPatients)

    def _loadPatients(self):
        """Load patients folder, and call _initPanelAct() to initialize the panel""" 
        if self.args.dev: 
            fname = self.args.file
        else: fname = QFileDialog.getExistingDirectory(self, "Select Directory")
        if fname == "":
            return 1
        file_path = Path(fname)
        self.fl = FolderLoader(file_path)
        self._initPanelAct()
        return 0

    def _initPanelAct(self):
        """Init the whole panel, will be called on loading the patients""" 
        self._updateComboSeries()
        self.combo_series.currentTextChanged.connect(self.slotChangeComboSeries)

    def _initImageUI(self):
        """Put image on to main window"""
        pass

    def slotChangeComboSeries(self, entry):
        """Triggered when self.combo_series change the entry, will change the
        image showing"""
        print(entry)
        
    def slotPutOnConsole(self, text):
       self.tb_console.append(text) 

    def _updateComboSeries(self):
        """Update the series combobox with image series get from self.fl.curr_patient"""
        self.combo_series.clear()
        series = self.fl.curr_patient.getEntries()
        self.combo_series.addItems(series)

class EmittingStream(QObject):
    """Reference: https://stackoverflow.com/questions/8356336/how-to-capture-output-of-pythons-interpreter-and-show-in-a-text-widget"""
    textWritten = pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))
