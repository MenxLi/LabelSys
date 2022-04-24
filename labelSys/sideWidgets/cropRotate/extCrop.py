from typing import Literal, Tuple, Union
import numpy as np

from immarker.core.utils import degreeVec2, cropByBox
from immarker.extensions import ExtensionAbstract, ExtensionRefs
from immarker.gui.tools import ToolItemCheckable
from immarker.markers.rectangle import MarkerRectangle
from immarker.interactionStyles.styleBoxReshape import StyleBoxReshape
from immarker.core import globalVar as G

Number = Union[int, float]
Coord = Tuple[Number, Number]


class MarkerCrop(MarkerRectangle, ExtensionRefs):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initExtRefs()

    def crop(self, img: np.ndarray) -> np.ndarray:
        im_crop = cropByBox(img, self.pts)
        self.GLOBAL_VAR.logger.debug(f"Crop points: {self.pts}")
        if im_crop is None:
            self.app.popupMsg("Crop range out of the image.", flag = "warning")
            return img
        return im_crop

class StyleCrop(StyleBoxReshape):
    DESCRIPTION = "Crop the showing image"
    def __init__(self):
        super().__init__()
        self.watch(self.GLOBAL_VAR.objs["crop_marker"])

    def applyChanges(self):
        super().applyChanges()
        coords = self.rect_marker.pts
        im = self.rect_marker.crop(self.app.data[self.idx]["image"].arr)

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
            self.app.setInteractionStyle(StyleCrop(), G.app.im_wid)
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
    NAME = "CropButton"
    DEPENDENCE_EXTS = ["InteractionStylePanelItems"]
    def rc(self):
        crop_item = CropItem()
        self.im_win.toolbars["InteractionStyleTools"].addItem(crop_item)
