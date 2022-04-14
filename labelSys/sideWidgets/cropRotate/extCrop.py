from typing import Literal, Tuple, Union
import os
import cv2 as cv
import numpy as np

import scipy.ndimage as ndimage

from immarker.core.utils import rotateVec2, degreeVec2, cropByBox
from immarker.extensions import ExtensionAbstract, ExtensionRefs
from immarker.core.imLayer import ImLayer
from immarker.gui.tools import ToolItemCheckable
from immarker.markers.polygon import MarkerPolygon
from immarker.markers.rectangle import MarkerRectangle
from immarker.interactionStyles import StyleBase
from immarker.core import globalVar as G

Number = Union[int, float]
Coord = Tuple[Number, Number]

DLL_PATH = os.path.join(os.path.dirname(__file__), "solveP2.o")

class MarkerRectangleHPT(MarkerRectangle):
    def __init__(self, head_pt, diag_pt, theta):
        super().__init__(head_pt, diag_pt, theta)
        self.config["head_pt_color"] = [255, 255, 0]

    def toNewVisualLayer(self, size_hw: Tuple[int, int]) -> ImLayer:
        base_layer = super().toNewVisualLayer(size_hw)
        head_pt = np.rint(self.head_pt).astype(int)
        cv.circle(base_layer.arr, head_pt, self.config["pt_radius"], self.config["head_pt_color"], thickness = -1)
        return base_layer

class MarkerCrop(MarkerRectangleHPT):
    def crop(self, img: np.ndarray) -> np.ndarray:
        im_crop = cropByBox(img, self.pts)
        return im_crop

class StyleCrop(StyleBase, ExtensionRefs):
    def __init__(self):
        super().__init__()
        self.initExtRefs()
        self.__style_status: Literal["none", "scale", "rotate", "grab", "extrude"] = "none"
        self.__start_pos: Union[None, Tuple[Number, Number]]
        self.__cache = dict()
        self.crop_marker: MarkerCrop
        self.crop_marker = self.GLOBAL_VAR.objs["crop_marker"]
        self.registerKey("R", self.setBoxRotate)
        self.registerKey("S", self.setBoxScale)
        self.registerKey("G", self.setBoxGrab)
        self.registerKey("E", self.setBoxExtrude)
        self.registerKey("Return", self.applyChanges)

    def leftButtonPressEvent(self):
        self.setBoxDefault()
        self.__start_pos = None
        return super().leftButtonPressEvent()

    def mouseMoveEvent(self):
        if self.__style_status == "none":
            return
        start_v = self._fromBoxCenter(self.__start_pos)
        now_v = self._fromBoxCenter(self._mousePos())
        if self.__style_status == "scale":
            fac = np.linalg.norm(now_v)/np.linalg.norm(start_v)
            # Scale
            new_head_pt = self.__cache["start_mk_center_pt"] + fac*(self.__cache["start_mk_head_pt"] - self.__cache["start_mk_center_pt"])
            new_diag_pt = self.__cache["start_mk_center_pt"] + fac*(self.__cache["start_mk_diag_pt"] - self.__cache["start_mk_center_pt"])
            self.crop_marker.head_pt = new_head_pt
            self.crop_marker.diag_pt = new_diag_pt

        if self.__style_status == "rotate":
            degree = degreeVec2(start_v, now_v)
            head_vec = self.__cache["start_mk_head_pt"] - self.__cache["start_mk_center_pt"]
            head_vec_new = rotateVec2(head_vec, degree)
            new_diag_pt = self.__cache["start_mk_center_pt"] - head_vec_new
            new_head_pt = self.__cache["start_mk_center_pt"] + head_vec_new
            self.crop_marker.head_pt = new_head_pt
            self.crop_marker.diag_pt = new_diag_pt

        if self.__style_status == "grab":
            move_v = now_v - start_v
            new_head_pt = self.__cache["start_mk_head_pt"] + move_v
            new_diag_pt = self.__cache["start_mk_diag_pt"] + move_v
            self.crop_marker.head_pt = new_head_pt
            self.crop_marker.diag_pt = new_diag_pt

        if self.__style_status == "extrude":
            move_v = now_v - start_v
            start_center = self.__cache["start_mk_center_pt"]
            start_angle = self.__cache["start_mk_angle"]
            start_p1, start_p2, start_p3, start_p4 = self.__cache["start_mk_pts"]
            start_v1 = start_p1 - start_center
            start_v2 = start_p2 - start_center

            new_v1 = start_v1 + move_v
            #  new_v2 = start_v2 + rotateVec2(move_v, start_angle*2)
            #  new_v2 = start_v2 + rotateVec2(move_v, self.crop_marker.angle*2)
            move_angle_v1 = degreeVec2(move_v, np.array([0, 1]))
            half_angle = move_angle_v1 - self.crop_marker.angle
            new_v2 = start_v2 + rotateVec2(move_v, half_angle*2)

            new_p1 = start_center + new_v1
            new_p3 = start_center - new_v1
            new_theta = -degreeVec2(-new_v1, new_v2)

            self.crop_marker.head_pt = new_p1
            self.crop_marker.diag_pt = new_p3
            self.crop_marker.theta = new_theta

        self.app.render()
        return super().mouseMoveEvent()

    def setBoxScale(self):
        self.GLOBAL_VAR.logger.debug("setBoxScale")
        self.__start_pos = self._mousePos()
        self.__style_status = "scale"
        self.__cache = {
            "start_mk_center_pt": self.crop_marker.center_pt,
            "start_mk_head_pt": self.crop_marker.head_pt,
            "start_mk_diag_pt": self.crop_marker.diag_pt,
        }

    def setBoxRotate(self):
        self.__start_pos = self._mousePos()
        self.__style_status = "rotate"
        self.__cache = {
            "start_mk_center_pt": self.crop_marker.center_pt,
            "start_mk_head_pt": self.crop_marker.head_pt,
            "start_mk_diag_pt": self.crop_marker.diag_pt,
        }

    def setBoxGrab(self):
        self.__start_pos = self._mousePos()
        self.__style_status = "grab"
        self.__cache = {
            "start_mk_head_pt": self.crop_marker.head_pt,
            "start_mk_diag_pt": self.crop_marker.diag_pt,
        }

    def setBoxExtrude(self):
        self.__start_pos = self._mousePos()
        self.__style_status = "extrude"
        self.__cache = {
            "start_mk_theta": self.crop_marker.theta,
            "start_mk_pts": self.crop_marker.pts,
            "start_mk_angle": self.crop_marker.angle,
            "start_mk_center_pt": self.crop_marker.center_pt
        }
    
    def setBoxDefault(self):
        self.__style_status = "none"
        self.__start_pos = None

    def applyChanges(self):
        self.setBoxDefault()
        self.__cache = dict()
        coords = self.crop_marker.pts
        im = self.crop_marker.crop(self.app.data[self.idx]["image"].arr)

        # Keep a backup of original image and crop coordinate
        self.app.data[self.idx]["meta"]["ori_arr"] = self.app.data[self.idx]["image"].arr.copy()
        self.app.data[self.idx]["meta"]["crop_coords"] = coords
        # update image
        self.app.data[self.idx]["image"].arr = im
        self.app.data[self.idx]["markers"].markers = []
        self.app.render()
        self.app.resetCamera()
        try:
            del self.GLOBAL_VAR.objs["crop_marker"]
        except KeyError: pass
        self.im_win.toolbars["InteractionStyleTools"]["view_tool"].click()

    def _mousePos(self):
        return self.im_wid.mousePosImg

    def _fromBoxCenter(self, pos):
        if not isinstance(pos, np.ndarray):
            pos = np.array(pos)
        crop_center = self.crop_marker.center_pt
        return pos - crop_center

class CropItem(ToolItemCheckable, ExtensionRefs):
    NAME = "crop_tool"
    DESCRIPTION = "To crop and rotate image"
    SHORT_CUT = "Ctrl+C"
    def __init__(self):
        super().__init__("Crop")
        self.initExtRefs()

    def onClick(self):
        super().onClick()
        if "crop_marker" in self.GLOBAL_VAR.objs:
            self.GLOBAL_VAR.logger.info("Already in cropping")
            return
        curr_img_np = self.app.data[self.idx]["image"].arr
        im_size = curr_img_np.shape
        im_size_xy = np.array((im_size[:2][::-1]), float)
        _im_size_xy = np.array((im_size_xy[0], -im_size_xy[1]), float)
        theta = -degreeVec2(im_size_xy, _im_size_xy)
        mk = MarkerCrop((0, 0), im_size_xy, theta)
        mk.setConfig(line_thickness = 5)
        mk.setConfig(pt_radius = 10)
        self.app.data[self.idx]["markers"].append(mk)
        self.app.render()
        self.GLOBAL_VAR.objs["crop_marker"] = mk

        self.app.setInteractionStyle(StyleCrop(), G.app.im_wid)
        def on_close():
            self.GLOBAL_VAR.logger.info("Close crop window.")
            try:
                del self.GLOBAL_VAR.objs["crop_marker"]
            except KeyError: pass
        self.im_win.closeEvent = lambda a0: on_close()

class ExtCrop(ExtensionAbstract):
    NAME = "EXT_CROP"
    def rc(self):
        crop_item = CropItem()
        self.im_win.toolbars["InteractionStyleTools"].addItem(crop_item)
