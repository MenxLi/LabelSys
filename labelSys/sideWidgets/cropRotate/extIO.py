import logging
from typing import Callable, Sequence, Union
import numpy as np
from immarker import Immarker
from immarker.core.io import ReaderRGBImage
from immarker.core.utils import isRGB
from immarker.extensions.extStyle import ExtStyle
from immarker.extensions import ExtensionAbstract, ExtensionRefs
from immarker.gui.tools import ToolItem, ToolBar

from .extCrop import ExtCrop

class ExportItem(ToolItem, ExtensionRefs):
    NAME = "export_tool"
    DESCRIPTION = "Export"
    def __init__(self):
        super().__init__("OK")
        self.initExtRefs()
    
    def onClick(self):
        if not "crop_coords" in self.app.data[self.idx]["meta"]:
            return super().onClick()
        img_now = self.app.data[self.idx]["image"].arr
        img_ori = self.app.data[self.idx]["meta"]["ori_arr"]
        crop_coords = self.app.data[self.idx]["meta"]["crop_coords"]
        self.GLOBAL_VAR.objs["save_callback"](img_now, img_ori, crop_coords)
        return super().onClick()

class RevertItem(ToolItem, ExtensionRefs):
    NAME = "revert_tool"
    DESCRIPTION = "Revert"
    def __init__(self):
        super().__init__("Revert")
        self.initExtRefs()
    
    def onClick(self):
        if not "crop_coords" in self.app.data[self.idx]["meta"]:
            return super().onClick()
        img_ori = self.app.data[self.idx]["meta"]["ori_arr"]
        self.app.data[self.idx]["image"].arr = img_ori
        self.app.render()
        self.app.resetCamera()
        return super().onClick()

class ExtExport(ExtensionAbstract, ExtensionRefs):
    NAME = "IO"
    DESCRIPTION = "Save result"
    def __init__(self, save_callback: Callable[[np.ndarray, np.ndarray, Sequence[np.ndarray]], None]):
        self.save_callback = save_callback
        self.initExtRefs()
        self.GLOBAL_VAR.objs["save_callback"] = save_callback
    
    def rc(self):
        self.im_win.addToolBar(ToolBar("button_tools"))
        self.im_win.toolbars["button_tools"].addItem(ExportItem())
        self.im_win.toolbars["button_tools"].addItem(RevertItem())

def startCropGUI(im: np.ndarray, save_callback: Callable[[np.ndarray, np.ndarray, Sequence[np.ndarray]], None]):
    assert isRGB(im), "im must be RGB"
    logging.basicConfig(level=logging.INFO)
    imm = Immarker()

    ext_style = ExtStyle()
    ext_crop = ExtCrop()
    ext_io = ExtExport(save_callback)

    imm.registerExtension(ext_style)
    imm.registerExtension(ext_crop)
    imm.registerExtension(ext_io)

    imm.loadArrays([im], ReaderRGBImage())
    imm.start()
