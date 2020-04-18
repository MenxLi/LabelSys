import sys
from PyQt5.QtWidgets import QApplication
#  from mainWindowGUI import MainWindow
from mainWindowGUI_hipEffusion import MainWindow_HE
from argParse import parser, args


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
    with open("QTDark.stylesheet") as f:
        app.setStyleSheet(f.read())
    w = MainWindow_HE(args)
    app.installEventFilter(w)
    sys.exit(app.exec_())
