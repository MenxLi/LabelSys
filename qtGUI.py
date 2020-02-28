# from PyQt5.QtWidgets import QMainWindow, QWidget, QAction, QFileDialog, QComboBox, QFrame, Qsplitter, QVBoxLayout
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from version import __VERSION__, __DESCRIPTION__
from dicomFileReader import FolderLoader
from pathlib import Path

class MainWindow(QMainWindow):
    def __init__(self,args):
        super().__init__()
        self.args = args
        self.initUI()

    def initUI(self):
        self.showMaximized()
        self.setWindowTitle("LabelSys "+__VERSION__)
        self.menu_bar = self.menuBar()
        self._initMenu()
        self.frame = QWidget(self)
        self.setCentralWidget(self.frame)
        if self.args.dev: self._loadPatients()

    def _initMenu(self):
        menu_file = self.menu_bar.addMenu('File')
        act_imp = QAction("Import", self)
        act_imp.triggered.connect(self._loadPatients)
        menu_file.addAction(act_imp)

    def _loadPatients(self):
        """Load patients folder, and call _initPanel() to initialize main panel""" 
        if self.args.dev: 
            fname = self.args.file
        else: fname = QFileDialog.getExistingDirectory(self, "Select Directory")
        if fname == "":
            return 1
        file_path = Path(fname)
        self.fl = FolderLoader(file_path)
        self._initPanel()
        return 0

    def _initPanel(self):
        """Init the whole panel, will be called on loading the patients""" 
        grid = QGridLayout()
        self.frame.setLayout(grid)
        grid.setSpacing(10)

        self.combo_series = QComboBox(self)
        self.__updateComboSeries()
        self.combo_series.currentTextChanged.connect(self.slotChangeComboSeries)

        grid.addWidget(self.combo_series, 0,0)

    def _initImageUI(self):
        """Put image on to main window"""
        pass

    def slotChangeComboSeries(self, entry):
        """Triggered when self.combo_series change the entry, will change the
        image showing"""
        print(entry)
        

    def __updateComboSeries(self):
        """Update the series combobox with image series get from self.fl.curr_patient"""
        self.combo_series.clear()
        series = self.fl.curr_patient.getEntries()
        self.combo_series.addItems(series)

