from PyQt5.QtWidgets import QMainWindow, QWidget, QAction, QFileDialog
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
        self.__initMenu()
        if self.args.dev: self.__loadPatients()

    def __initMenu(self):
        menu_file = self.menu_bar.addMenu('File')
        act_imp = QAction("Import", self)
        act_imp.triggered.connect(self.__loadPatients)
        menu_file.addAction(act_imp)

    def __loadPatients(self):
        """Load patients folder and display in the mainwindow"""
        if self.args.dev: 
            fname = self.args.file
        else: fname = QFileDialog.getExistingDirectory(self, "Select Directory")
        if fname == "":
            return 1
        file_path = Path(fname)
        self.fl = FolderLoader(file_path)
        return 0

    def __initImageUI(self):
        """Put image on to main window"""
        pass

    def __askChooseSeries(self):
        """ Prompt user to choose a series to display
        Will be called each time change patient"""
        pass
