from __future__ import annotations
from typing import Callable, Dict, Literal, NewType, Tuple, List, TypedDict, TYPE_CHECKING
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QObject, QEvent
from PyQt6.QtGui import QCursor, QPixmap
from . import utils
import numpy as np
import logging

if TYPE_CHECKING:
    from .mainWindowGUI import MainWindow
    from .labelResultHolder import LabelHolder
    from .vtkClass import VtkWidget
    from .vtkInteractionStyle import InteractionStyleBase as vtkInteractionStyle

qlogger = logging.getLogger("qlogger")
labelsys_logger = logging.getLogger("labelSys")

class KeyRecord(TypedDict):
    callback: Callable[[], None]
    auto_repeat: bool

class StyleInfo(TypedDict):
    description: str
    key_function: dict[str, str]

class Cursor():
    def __init__(self, wid: QWidget):
        self.wid = wid
        self._cursor = QCursor()

    def setShapeArrow(self):
        self._cursor.setShape(Qt.CursorShape.ArrowCursor)
        self.wid.setCursor(self._cursor)

    def setShapeOpenHand(self):
        self._cursor.setShape(Qt.CursorShape.OpenHandCursor)
        self.wid.setCursor(self._cursor)

    def setShapeClosedHand(self):
        self._cursor.setShape(Qt.CursorShape.ClosedHandCursor)
        self.wid.setCursor(self._cursor)

    def setShapeCross(self):
        self._cursor.setShape(Qt.CursorShape.CrossCursor)
        self.wid.setCursor(self._cursor)

    def setShapeFromFile(self, f: str):
        self._cursor = QCursor(QPixmap(f))
        self.wid.setCursor(self._cursor)


class StyleBase(QObject):
    DESCRIPTION = "A interaction style"
    def __init__(self):
        super().__init__()
        self.info: StyleInfo = {
            "description": self.DESCRIPTION,
            "key_function": dict()
        }
        self._keypress_events: Dict[Qt.Key, KeyRecord] = {}
        self._keyrelease_events: Dict[Qt.Key, KeyRecord] = {}
        self._watching_keys: Dict[Qt.Key, bool] = {}

    @property
    def info_string(self):
        shown = []
        shown.append(self.info["description"])
        shown.append("--------Usage-------")
        for k, v in self.info["key_function"].items():
            shown.append(f"{k}: {v}")
        return "\n".join(shown)

    def apply(self, wid: QWidget) -> None:
        """Apply based interaction styles to a QtWidget

        Args:
            wid (QWidget): the widget to which to apply styles
        """
        self._applyEventFilter(wid)
        wid.closeEvent = lambda a0: self.closeEvent()

    def _applyEventFilter(self, wid: QWidget):
        # Remove old event fileter
        if hasattr(wid, "istyle"):
            wid.removeEventFilter(wid.istyle)
        # Install new event fileter
        wid.setMouseTracking(True)
        setattr(wid, "istyle", self)
        wid.installEventFilter(self)

    def watchKeyStatus(self, k: str):
        try:
            key = getattr(Qt.Key, "Key_{}".format(k))
            self._watching_keys[key] = False
        except AttributeError:
            labelsys_logger.error("Can't find key {} to watch on {}".format(k, self.__class__))

    def queryKeyStatus(self, k: str) -> bool:
        try:
            key = getattr(Qt.Key, "Key_{}".format(k))
            return self._watching_keys[key]
        except AttributeError:
            labelsys_logger.error("Can't find key {} to query on {}".format(k, self.__class__))
            return False

    @staticmethod
    def keyModifiers(*args: Literal["Control", "Shift", "Alt"]) -> bool:
        """Check if key modifiers has been pressed

        Args:
            *args (Literal[&quot;Control&quot;, &quot;Shift&quot;, &quot;Alt&quot;]): Modifiers to be checked

        Returns:
            bool: True if all modifiers are pressed
        """
        modifiers = []
        for k in args:
            try:
                attr = getattr(Qt.KeyboardModifier, k + "Modifier")
                modifiers.append(attr)
            except AttributeError:
                labelsys_logger.error("Unable to get modifier from QtCore.Qt: {}".format(k))
                return False
        m_total = modifiers[0]
        for m in modifiers[1:]:
            m_total = m|m_total
        return QApplication.keyboardModifiers() == m_total

    def registerKey(self, k: str, callback: Callable[[], None], 
                    mode: Literal["press", "release"] = "press",
                    auto_repeat: bool = False, auto_doc: bool = True):
        """Register a key to a callback, should be called before self.apply(...)

        Args:
            k (str): Keybord key, should be able to be found with Qt.Key_{k}
            callback (Callable[[], None]): callback function
            auto_repeat (bool): allow for continues trigger
            auto_doc (bool): automatically add an entry in self.info["key_function"]
        """
        try:
            key = getattr(Qt.Key, "Key_{}".format(k))
            event_record = getattr(self, "_key{}_events".format(mode))
            event_record[key] = {
                "callback": callback,
                "auto_repeat": auto_repeat
            }
            if k not in self.info["key_function"] and auto_doc:
                self.info["key_function"][k] = callback.__name__
        except AttributeError:
            labelsys_logger.error("Can't register key {} on {}".format(k, self.__class__))

    def mouseMoveEvent(self):
        pass

    def leftButtonPressEvent(self):
        pass

    def leftButtonReleaseEvent(self):
        pass

    def rightButtonPressEvent(self):
        pass

    def rightButtonReleaseEvent(self):
        pass

    def doubleClickEvent(self):
        pass

    def wheelForwardEvent(self):
        pass

    def wheelBackwardEvent(self):
        pass

    def closeEvent(self):
        pass

    def eventFilter(self, receiver, event: QEvent):
        if event.type() == QEvent.Type.MouseMove:
            self.mouseMoveEvent()

        if event.type() == QEvent.Type.MouseButtonPress:
            qlogger.debug(event)
            if event.button() == Qt.MouseButton.LeftButton:
                self.leftButtonPressEvent()
            if event.button() == Qt.MouseButton.RightButton:
                self.rightButtonPressEvent()

        if event.type() == QEvent.Type.MouseButtonRelease:
            qlogger.debug(event)
            if event.button() == Qt.MouseButton.LeftButton:
                self.leftButtonReleaseEvent()
            if event.button() == Qt.MouseButton.RightButton:
                self.rightButtonReleaseEvent()

        if event.type() == QEvent.Type.KeyPress:
            if not event.isAutoRepeat():
                qlogger.debug("{} : key - {}".format(event, event.key()))
            for k in self._watching_keys.keys():
                if event.key() == k and not event.isAutoRepeat():
                    self._watching_keys[k] = True
            for k in self._keypress_events.keys():
                if event.key() == k and not \
                (event.isAutoRepeat() and not self._keypress_events[k]["auto_repeat"]):
                    self._keypress_events[k]["callback"]()

        if event.type() == QEvent.Type.KeyRelease:
            if not event.isAutoRepeat():
                qlogger.debug("{} : key - {}".format(event, event.key()))
            for k in self._watching_keys.keys():
                if event.key() == k and not event.isAutoRepeat():
                    self._watching_keys[k] = False
            for k in self._keyrelease_events.keys():
                if event.key() == k and not \
                (event.isAutoRepeat() and not self._keypress_events[k]["auto_repeat"]):
                    self._keyrelease_events[k]["callback"]()

        if event.type() == QEvent.Type.Wheel:
            qlogger.debug("{} : delta - {}".format(event, event.angleDelta()))
            y = event.angleDelta().y()
            if y>0:
                self.wheelForwardEvent()
            if y<0:
                self.wheelBackwardEvent()
        return super().eventFilter(receiver, event)

StyleType = NewType("StyleType", StyleBase)

class StyleImWidgetBase(StyleBase):
    def __init__(self, main_win: MainWindow):
        super().__init__()
        self.main_win = main_win
        self.cursor = Cursor(main_win.im_widget)

        self.registerKey("Space", mode = "press", \
                         callback = self.startImMov)
        self.registerKey("Space", mode = "release", \
                         callback = self.endImMov)

        # Press alt key to select label on image by mouse click
        self.registerKey("Alt", mode = "press", \
                         callback = self.startSelectLabelStatus)
        self.registerKey("Alt", mode = "release", \
                         callback = self.endSelectLabelStatus)

        self.watchKeyStatus("Space")

    @property
    def lbl_holder(self) -> LabelHolder:
        return self.main_win.lbl_holder

    @property
    def imgs(self) -> List[np.ndarray]:
        return self.main_win.imgs

    @property
    def slice_id(self) -> int:
        return self.main_win.slice_id

    @property
    def mouse_im_pos(self) -> Tuple[float, float]:
        """
        Get mouse position on the image
        return position in opencv coordinate
        """
        vtk_widget:VtkWidget = self.main_win.im_widget
        vtk_pos = vtk_widget.style._getMousePos()
        return tuple(utils.vtk2CvCoord(vtk_pos[0], vtk_pos[1], vtk_widget.im.shape))

    @property
    def vtk_style(self):
        vtk_widget:VtkWidget = self.main_win.im_widget
        return vtk_widget.style

    def leftButtonPressEvent(self):
        """
        Click to select the label
        """
        if self.keyModifiers("Alt"):
            if self.vtk_style.is_drawing:
                print("Can't select item now")
                return

            im_hw = tuple(self.imgs[self.slice_id].shape[:2])
            lbl = self.lbl_holder.getLabelNameByPosition(self.slice_id, self.mouse_im_pos, im_hw)
            if lbl:
                self.main_win.combo_label.setCurrentText(lbl)

    def startSelectLabelStatus(self):
        self.cursor.setShapeCross()
        if self.vtk_style.is_drawable:
            # Prevent vtk_style drawing events
            # maybe unnecessary?
            self.vtk_style.disableDrawing()

    def endSelectLabelStatus(self):
        self.cursor.setShapeArrow()

    def startImMov(self):
        vtk_widget:VtkWidget = self.main_win.im_widget
        vtk_widget.style.dragImgStart()
        self.cursor.setShapeOpenHand()

    def endImMov(self):
        vtk_widget:VtkWidget = self.main_win.im_widget
        vtk_widget.style.dragImgEnd()
        self.cursor.setShapeArrow()

    def mouseMoveEvent(self):
        if self.queryKeyStatus("Space"):
            self.cursor.setShapeClosedHand()
        return super().mouseMoveEvent()

    def wheelForwardEvent(self):
        if self.keyModifiers("Control"):
            vtk_widget:VtkWidget = self.main_win.im_widget
            vtk_widget.style.OnMouseWheelForward()
        else:
            self.main_win.prevSlice()
        return super().wheelForwardEvent()

    def wheelBackwardEvent(self):
        if self.keyModifiers("Control"):
            vtk_widget:VtkWidget = self.main_win.im_widget
            vtk_widget.style.OnMouseWheelBackward()
        else:
            self.main_win.nextSlice()
        return super().wheelBackwardEvent()
