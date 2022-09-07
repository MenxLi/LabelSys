from typing import Callable, Union, List
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QMainWindow, QPushButton, QLabel, QTextEdit, QVBoxLayout, QWidget, QRadioButton

from .coreWidgets import WidgetCore

class ClassLine(QWidget, WidgetCore):
    def __init__(self, parent, name: str, classes: List[str], help: str, full_name = None) -> None:
        super().__init__()
        self.setToolTip(help)
        self.name = name
        self.classes = classes
        self.full_name = full_name
        self.initUI()
    
    def initUI(self):
        h_layout = QHBoxLayout()
        v_layout = QVBoxLayout()

        v_layout.addWidget(QLabel(f"{self.name} ({self.full_name})"))
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
    def __init__(self, parent:QMainWindow, save_callback: Callable, 
        classes: dict = {},
        current_classes_str: Union[str, None] = None,
        current_comment: Union[str, None] = None,
        ) -> None:
        super().__init__(parent=parent, )
        self.classes = classes
        self.prev_class_str = current_classes_str
        self.prev_comment = current_comment
        self.save_callback = save_callback
        self.classification_lines = []
        self.classification_lines: List[ClassLine]
        self.initUI()
        if not current_classes_str is None:
            self.setClassificationFromStr(current_classes_str)

    def initUI(self):
        self.setWindowTitle("Comment")
        v_layout = QVBoxLayout()
        h_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Cancel")
        self.txt_edit = QTextEdit()
        h_layout.addWidget(self.btn_ok)
        h_layout.addWidget(self.btn_cancel)
        for k in self.classes.keys():
            if "short_title" in self.classes[k]:
                # old version compatablility
                full_name_key = "short_title"
            else:
                full_name_key = "full_name"
            class_line = ClassLine(self, k,
                self.classes[k]["class"],
                self.classes[k]["description"],
                self.classes[k][full_name_key],
                )
            self.classification_lines.append(class_line)
            v_layout.addWidget(class_line)
        v_layout.addWidget(QLabel("Comments:"))
        v_layout.addWidget(self.txt_edit)
        v_layout.addLayout(h_layout)
        self.setLayout(v_layout)
        if not self.prev_comment is None:
            self.txt_edit.setText(self.prev_comment)
        
        self.btn_ok.clicked.connect(self.ok)
        self.btn_cancel.clicked.connect(self.cancel)
    
    def getClassficationStr(self):
        comments = []
        comments: List[str]
        for cl in self.classification_lines:
            name = cl.name
            idx = cl.getClassIdx()
            if idx >= 1:
                c_text = cl.classes[idx-1]
                comments.append(f"{name}:{c_text}")
        if len(comments)>0:
            return "&".join(comments)
        else:
            return None
    
    def setClassificationFromStr(self, txt: str):
        splits = txt.split("&")
        splits_ = [s.split(":") for s in splits]
        for cl in self.classification_lines:
            for s in splits_:
                if s[0] == cl.name:
                    cl.setClass(s[1])
    
    def ok(self):
        class_txt = self.getClassficationStr()
        comment_txt = self.txt_edit.toPlainText()
        self.save_callback(class_txt, comment_txt)
        self.close()
    
    def cancel(self):
        self.close()
