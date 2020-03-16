from PyQt5.QtWidgets import *


class SettingsDialog(QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)

        btns = QDialogButtonBox.Apply | QDialogButtonBox.Cancel
        self.button_box = QDialogButtonBox(btns)
        self.button_box.clicked.connect(self.__handleButtonClick)

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(GeneralTab(self), "General")

        self.layout = QVBoxLayout() 
        self.layout.addWidget(self.tab_widget)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)

        self.setWindowTitle("Settings")

    def quitWindow(self):
        self.close()

    def applyChanges(self):
        print("This part isn't finished")
        self.close()

    def __handleButtonClick(self, button):
        sb = self.button_box.standardButton(button)
        if sb == QDialogButtonBox.Apply:
            self.applyChanges()
        elif sb == QDialogButtonBox.Cancel:
            self.quitWindow()


class SettingsTab(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)

    def applyTabChanges(self):
        pass


class GeneralTab(SettingsTab):
    def __init__(self, parent = None):
        super().__init__(parent)

