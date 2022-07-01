import logging
from typing import Callable, Sequence, Union
import numpy as np
from immarker import Immarker
from immarker.core.io import ReaderRGBImage
from immarker.core.utils import isRGB
from immarker.extensions.extStyle import ExtStyle
from immarker.extensions.extStyleInfo import ExtStyleInfo
from immarker.extensions.extImWinInfoText import ExtImWinInfoText
from immarker.extensions import ExtensionAbstract, ExtensionRefs
from immarker.gui.tools import ToolItem, ToolBar
from immarker.gui.widgetCore import WidgetCore

from .extCrop import ExtCrop

class ExportItem(ToolItem, ExtensionRefs):
    NAME = "export_tool"
    DESCRIPTION = "Export"
    def __init__(self):
        super().__init__("OK")
        self.initExtRefs()
    
    def onClick(self):
        if "crop_marker" in self.GLOBAL_VAR.objs.keys():
            # Not confirmed yet
            if WidgetCore._queryDialog("Press <Enter> before apply cropping, apply and exit?",
                                       "Not yet confirmed"):
                self.im_win.toolbars["InteractionStyleTools"]["crop_tool"].click()
                self.app.im_wid.istyle.applyChanges()
            else:
                return super().onClick()
        if not "crop_coords" in self.app.data[self.idx]["meta"]:
            # Haven't cropped yet
            return super().onClick()
        img_now = self.app.data[self.idx]["image"].arr
        img_ori = self.app.data[self.idx]["meta"]["ori_arr"]
        crop_coords = self.app.data[self.idx]["meta"]["crop_coords"]
        self.GLOBAL_VAR.objs["save_callback"](img_now, img_ori, crop_coords)
        self.im_win.close()
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
        super().__init__()
        self.save_callback = save_callback
        self.initExtRefs()
        self.GLOBAL_VAR.objs["save_callback"] = save_callback
    
    def rc(self):
        self.im_win.addToolBar(ToolBar("ButtonTools"))
        self.im_win.toolbars["ButtonTools"].addItem(ExportItem())
        self.im_win.toolbars["ButtonTools"].addItem(RevertItem())

class ExtClickCropBtn(ExtensionAbstract, ExtensionRefs):
    NAME = "ClickCropBtn"
    DESCRIPTION = "Automatically click crop button"
    DEPENDENCE_EXTS = ["CropButton"]

    def rc(self):
        self.im_win.toolbars["InteractionStyleTools"]["crop_tool"].click()

def startCropGUI(im: np.ndarray, save_callback: Callable[[np.ndarray, np.ndarray, Sequence[np.ndarray]], None]):
    assert isRGB(im), "im must be RGB"
    imm = Immarker()
    imm.im_win.setMinimumWidth(800)

    ext_style_info = ExtStyleInfo()
    ext_style = ExtStyle()
    ext_im_info = ExtImWinInfoText()
    ext_crop = ExtCrop()
    ext_io = ExtExport(save_callback)
    ext_click_crop_btn = ExtClickCropBtn()

    imm.registerExtension(ext_style_info)
    imm.registerExtension(ext_style)
    imm.registerExtension(ext_im_info)
    imm.registerExtension(ext_crop)
    imm.registerExtension(ext_io)
    imm.registerExtension(ext_click_crop_btn)

    imm.loadArrays([im], ReaderRGBImage())
    imm.start()
