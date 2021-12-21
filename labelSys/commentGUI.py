from typing import Callable, Union
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QMainWindow, QPushButton, QLabel, QCheckBox, QTextEdit, QVBoxLayout, QWidget
import numpy as np

from .coreWidgets import WidgetCore

class CommentGUI(QDialog, WidgetCore):
    def __init__(self, parent:QMainWindow, save_callback: Callable, current_comment: Union[str, None] = None) -> None:
        super().__init__(parent=parent, )
        self.prev_comment = current_comment
        self.save_callback = save_callback
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Comment")
        v_layout = QVBoxLayout()
        h_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Cancel")
        self.txt_edit = QTextEdit()
        h_layout.addWidget(self.btn_ok)
        h_layout.addWidget(self.btn_cancel)
        v_layout.addWidget(self.txt_edit)
        v_layout.addLayout(h_layout)
        self.setLayout(v_layout)
        if not self.prev_comment is None:
            self.txt_edit.setText(self.prev_comment)
        
        self.btn_ok.clicked.connect(self.ok)
        self.btn_cancel.clicked.connect(self.cancel)
    
    def ok(self):
        txt = self.txt_edit.toPlainText()
        self.save_callback(txt)
        self.close()
    
    def cancel(self):
        self.close()