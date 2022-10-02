from PyQt6.QtWidgets import QWidget, QMessageBox
from .configLoader import LOG_FILE
from .version import __version__
from PyQt6.QtCore import pyqtSignal, QObject
import datetime, logging
from typing import Callable, TypeVar
from functools import wraps

CallVar = TypeVar("CallVar", bound = Callable)

def loggedFunction(func: CallVar) -> CallVar:
    logger = logging.getLogger("labelSys")
    @wraps(func)
    def func_(*args, **kwargs):
        logger.debug(f" [{func.__name__}] ")
        return func(*args, **kwargs)
    return func_

class WidgetCore():

    logger = logging.getLogger("labelSys")
    def setMainWindow(self, main_win):
        self.__main_win = main_win

    def getMainWindow(self):
        return self.__main_win

    def setWidgetsEnabled(self, status: bool, *widgets):
        for w in widgets:
            w.setEnabled(status)

    def _msgDialog(self, title, message, info_msg = ""):
        msg_box = QMessageBox()
        msg_box.setText(message)
        msg_box.setWindowTitle(title)
        msg_box.setInformativeText(info_msg)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        return msg_box.exec()

    def _warnDialog(self, message, info_msg = ""):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(message)
        msg_box.setInformativeText(info_msg)
        msg_box.setWindowTitle("Warning")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        return msg_box.exec()

    def _warnDialogCritical(self, message, info_msg = "Please restart the program"):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setText(message)
        msg_box.setInformativeText(info_msg)
        msg_box.setWindowTitle("Critical warning")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        return msg_box.exec()

    def _queryDialog(self, msg, title = "Query", func = lambda x: None):
        msg_box = QMessageBox()
        msg_box.setText(msg)
        msg_box.setWindowTitle(title)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        msg_box.buttonClicked.connect(func)
        return_value = msg_box.exec()
        if return_value == QMessageBox.StandardButton.Ok:
            return True
        else: return False

    def _alertMsg(self,msg, title = "Alert", func = lambda x : None):
        msg_box = QMessageBox()
        msg_box.setText(msg)
        msg_box.setWindowTitle(title)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        msg_box.buttonClicked.connect(func)
        return_value = msg_box.exec()
        if return_value == QMessageBox.StandardButton.Ok:
            return True
        else: return False

    def _center(self):
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


class EmittingStream(QObject):
    """Reference: https://stackoverflow.com/questions/8356336/how-to-capture-output-of-pythons-interpreter-and-show-in-a-text-widget"""
    textWritten = pyqtSignal(str)
    logger = logging.getLogger("labelSys")

    def write(self, text):
        self.textWritten.emit(str(text))
        self.logText(text)

    @classmethod
    def logText(cls, text: str):
        log_txt = EmittingStream.setHeader(text)
        if log_txt:
            #  with open(LOG_FILE, "a", encoding="utf-8") as fp:
            #      fp.write(log_txt)
            cls.logger.info(text)

    @staticmethod
    def setHeader(text: str):
        time = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        header = "v{version}-{time}: ".format(
            version = __version__, time = time
        )
        if text.replace(" ", "") == "" or text.replace(" ", "") == "\n":
            return None
        if text[-1] != "\n":
            text += "\n"
        if text[0] != "\n":
            text = "\n" + text
        return header + text
