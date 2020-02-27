from PyQt5.QtWidgets import QMainWindow, QWidget
from version import __VERSION__, __DESCRIPTION__

class MainWindow(QMainWindow):
    def __init__(self,args):
        super().__init__()
        self.args = args
        self.initUI()

    def initUI(self):
        self.showMaximized()
        self.setWindowTitle("LabelSys "+__VERSION__)
