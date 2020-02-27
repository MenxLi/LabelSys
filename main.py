import sys
from PyQt5.QtWidgets import QApplication
from qtGUI import MainWindow
from argParse import parser, args

if __name__ == "__main__":
    app = QApplication([parser.prog])
    w = MainWindow(args)
    sys.exit(app.exec_())
