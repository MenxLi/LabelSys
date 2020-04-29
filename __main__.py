#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#
import sys, os
from PyQt5.QtWidgets import QApplication
from mainWindowGUI import MainWindow
from utils.argParse import parser, args


class Application(QApplication):
    def __init__(self, *args):
        super().__init__(*args)
    def notify(self, receiver, e):
        try:
            return QApplication.notify(self, receiver, e)
        except Exception as exp:
            print("An exception occured: ", exp)
            return 1
if __name__ == "__main__":
    app = Application([parser.prog])
    # set stylesheet
    #import qdarkstyle
    #app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    with open(os.path.join("ui", "QTDark.stylesheet")) as f:
        app.setStyleSheet(f.read())
    w = MainWindow(args)
    app.installEventFilter(w)
    sys.exit(app.exec_())
