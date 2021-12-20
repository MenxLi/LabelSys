from PyQt5.QtWidgets import QMainWindow, QPushButton, QLabel, QCheckBox, QWidget
import numpy as np

from .coreWidgets import WidgetCore

class ClassificationGUI(WidgetCore):
    def __init__(self, parent:QMainWindow, img: np.ndarray) -> None:
        super().__init__(parent=parent, )