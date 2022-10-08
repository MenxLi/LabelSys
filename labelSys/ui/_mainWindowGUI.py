

from PyQt6.QtWidgets import QApplication, QCheckBox, QComboBox, QFrame, QLabel, QPushButton, QSlider, QTextEdit, QWidget, QMainWindow
from PyQt6.QtGui import QAction

class MainWindowGUI(QMainWindow):

    central_widget: QWidget
    
    im_frame: QFrame

    tb_console: QTextEdit

    lbl_wd: QLabel

    btn_next_patient: QPushButton
    btn_prev_patient: QPushButton
    btn_next_slice: QPushButton
    btn_prev_slice: QPushButton
    btn_save: QPushButton
    btn_clear: QPushButton
    btn_interp: QPushButton
    btn_add_cnt: QPushButton
    btn_add_bbox: QPushButton
    btn_comment: QPushButton

    check_preview: QCheckBox
    check_crv: QCheckBox
    check_draw: QCheckBox

    combo_series: QComboBox
    combo_label: QComboBox

    slider_im: QSlider

    act_open: QAction
    act_quit: QAction
    act_load: QAction
    act_fullscreen: QAction
    act_2D_preview: QAction
    act_3D_preview: QAction
    act_check_preview: QAction

    act_op_next_slice: QAction
    act_op_prev_slice: QAction
    act_op_next_patient: QAction
    act_op_prev_patient: QAction
    act_op_change_lbl: QAction
    act_op_change_lbl_reverse: QAction
    act_op_toAnotherLbl: QAction
    act_op_switchToAnotherLbl: QAction
    act_op_save: QAction
    act_op_clear: QAction
    act_op_interp: QAction
    act_op_add_cnt: QAction
    act_op_rotate: QAction
    act_op_add_bbox: QAction
    act_op_edit_comment: QAction

    act_tool_compare: QAction
    act_tool_crop: QAction

    act_set_path: QAction
    act_set_lbler: QAction
    act_set_settings: QAction

    act_help_manual: QAction
    act_help_manual_zh: QAction
    act_help_info: QAction

