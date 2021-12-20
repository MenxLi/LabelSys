from typing import Callable, List, Union
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QMainWindow, QPushButton, QLabel, QCheckBox, QRadioButton, QVBoxLayout, QWidget
import numpy as np

from .coreWidgets import WidgetCore

class CommentLine(QWidget, WidgetCore):
    def __init__(self, parent, name: str, classes: List[str], help: str, short_name = None) -> None:
        super().__init__()
        self.setToolTip(help)
        self.name = name
        self.classes = classes
        self.short_name = short_name
        self.initUI()
    
    def initUI(self):
        h_layout = QHBoxLayout()
        v_layout = QVBoxLayout()

        v_layout.addWidget(QLabel(self.name))
        self.rbs = [QRadioButton("<none>")]
        self.rbs += [QRadioButton(c) for c in self.classes]
        self.rbs[0].setChecked(True)
        for rb in self.rbs:
            h_layout.addWidget(rb)
        v_layout.addLayout(h_layout)
        self.setLayout(v_layout)
    
    def getClassIdx(self):
        for i in range(len(self.rbs)):
            if self.rbs[i].isChecked():
                return i
        return -1
    
    def setClass(self, txt):
        for i in range(len(self.rbs)):
            if self.rbs[i].text() == txt:
                self.rbs[i].setChecked(True)
                return True
        return False


class CommentGUI(QDialog, WidgetCore):
    def __init__(self, parent:QMainWindow, classes: dict, save_func: Callable, comments:Union[None, str] = None) -> None:
        super().__init__(parent=parent)
        self.parent = parent
        self.classes = classes
        self.comment_lines = []
        self.comment_lines: List[CommentLine]
        self.save_func = save_func
        self.setWindowTitle("Add Classification")
        self.initUI()
        if not comments is None:
            self.setClassesFromStr(comments)
    
    def initUI(self):
        v_layout = QVBoxLayout()
        h_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self.ok)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.cancel)
        h_layout.addWidget(self.btn_ok)
        h_layout.addWidget(self.btn_cancel)
        for k in self.classes.keys():
            comment_line = CommentLine(self, k, 
                self.classes[k]["class"], 
                self.classes[k]["description"], 
                self.classes[k]["short_title"])
            self.comment_lines.append(comment_line)
            v_layout.addWidget(comment_line)
        v_layout.addLayout(h_layout)
        self.setLayout(v_layout)
    
    def getComments(self):
        comments = []
        comments: List[str]
        for cl in self.comment_lines:
            name = cl.name
            idx = cl.getClassIdx()
            if idx >= 1:
                c_text = cl.classes[idx-1]
                comments.append(f"{name}:{c_text}")
        if len(comments)>0:
            return "&".join(comments)
        else:
            return None

    def setClassesFromStr(self, txt: str):
        splits = txt.split("&")
        splits_ = [s.split(":") for s in splits]
        for cl in self.comment_lines:
            for s in splits_:
                if s[0] == cl.name:
                    cl.setClass(s[1])
    
    def ok(self):
        comments = self.getComments()
        self.save_func(comments)
        self.close()

    def cancel(self):
        self.close()