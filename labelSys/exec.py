#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#

import sys, os
# Import MainWindow will somehow change this enviroment variable to improprate path
# Export it manually before starting the program will not work as it will change after import
# So, save it here for later useage
try:
    QT_QPA_PLATFORM_PLUGIN_PATH = os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"]
except KeyError:
    # if not export enviroment variable before the program start
    QT_QPA_PLATFORM_PLUGIN_PATH = None
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTextCodec
from .mainWindowGUI import MainWindow
from .configLoader import _UI_DIR
from .argParse import parser, args

if not QT_QPA_PLATFORM_PLUGIN_PATH is None:
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QT_QPA_PLATFORM_PLUGIN_PATH

class Application(QApplication):
    def __init__(self, *args):
        super().__init__(*args)
    def notify(self, receiver, e):
        try:
            return QApplication.notify(self, receiver, e)
        except Exception as exp:
            print("An exception occured: ", exp)
            return 1
def main():
    codec = QTextCodec.codecForName("UTF-8")
    QTextCodec.setCodecForLocale(codec)
    app = Application([parser.prog])
    font = QFont("Verdana", 9)
    app.setFont(font)
    # set stylesheet
    #import qdarkstyle
    #app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    CURR_DIR = os.path.dirname(__file__)
    with open(os.path.join(_UI_DIR, "QTDark.stylesheet")) as f:
        app.setStyleSheet(f.read())
    w = MainWindow(args)
    app.installEventFilter(w)
    sys.exit(app.exec_())

def main_():
    """
    For linux, if following error occurred:
    "This application failed to start because no Qt platform plugin could be initialized."
    call this function to start the program
    """
    _QT_QPA_PLATFORM_PLUGIN_PATH="/home/monsoon/Documents/Code/.venv/mainEnv/lib/python3.8/site-packages/cv2/qt/plugins/platforms"
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = _QT_QPA_PLATFORM_PLUGIN_PATH
    main()

if __name__ == "__main__":
    main()