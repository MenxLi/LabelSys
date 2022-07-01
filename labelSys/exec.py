#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#

import sys, os, logging
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
from .configLoader import _UI_DIR, LOG_FILE
from .argParse import parser, args
from logging.handlers import RotatingFileHandler

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
    logger = logging.getLogger("labelSys")
    logger.setLevel(logging.DEBUG)

    # FileHandler show DEBUG log level
    f_handler = RotatingFileHandler(LOG_FILE, "a", maxBytes=5*1024*1024, backupCount=1, encoding="utf-8")
    f_handler.setLevel(logging.DEBUG)
    fomatter = logging.Formatter('%(asctime)s (%(levelname)s) - %(message)s')
    f_handler.setFormatter(fomatter)
    logger.addHandler(f_handler)

    # re-direct unhandled exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
        else:
            logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        logger.info("Exit.")
        sys.exit()
    sys.excepthook = handle_exception

    codec = QTextCodec.codecForName("UTF-8")
    QTextCodec.setCodecForLocale(codec)
    app = Application([parser.prog])
    font = QFont("Verdana", 9)
    app.setFont(font)
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
