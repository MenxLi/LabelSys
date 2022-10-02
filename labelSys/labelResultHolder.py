
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#
from typing import List, Union, Optional, TypedDict, Any, Dict, Tuple

from immarker.core.globalVar import logging
from .utils.base64ImageConverter import imgEncodeB64, imgDecodeB64
from .utils.labelReaderV2 import checkFolderEligibility
from .utils import utils_ as F
from .configLoader import *
import os
import cv2 as cv
import numpy as np
import json
from threading import Thread
import re

from .clib.wrapper import MergeMasks

class HeaderData(TypedDict):
    Labeler: str
    Time: str
    Spacing: List[float]
    Series: str
    Version: str
    Config: Dict[str, Any]

class SliceLabelDataTypeSingle(TypedDict):
    # This represents a contour
    Open: bool
    Points: List[Tuple[float, float, float]]    # VTK nodes
    Contour: List[Tuple[int, int]]              # Full contour in VTK coordinate

SliceLabelDataType = List[SliceLabelDataTypeSingle]

# Contour data type in holder.data
ContourDataT = List[Dict[str, SliceLabelDataType]]

class LabelHolder:
    """
    HOlding the label result
    """
    logger = logging.getLogger("labelSys")
    def __init__(self):
        """
        self.data: List[dict]:
            main data, list of dictionary:
            {
                "<Label1>": {
                    "Open":: bool,                                  # indicate whether it is open contour
                    "Points":: List[Tuple[float, float, float]],    # vtk nodes
                    "Contour":: List[Tuple[int, int]]               # full contour (int) in vtk coordinate
                },
                "<Label2>": {...},
                ...
                "SOPInstanceUID": str                               # Will remove in the future Only appear on version < 1.6.7
            }
        """
        self.data: Optional[ContourDataT] = None
        self.SAVED: bool = True
        self.uids: List[str]
        self.comments: List[Union[None, str]]
        self.class_comments: List[Union[None, str]]
        self.drawer = LabelDrawer(self)

    def initialize(self, entries, SOPInstanceUIDs):
        self.data = []
        self.uids = []          # For future version
        self.SAVED = True
        for ids in SOPInstanceUIDs:
            self.data.append({})
            for entry in entries:
                self.data[-1][entry] = []
            # self.data[-1]["SOPInstanceUID"] = ids
            self.uids.append(ids)
        self.comments = [None]*len(self.data)
        self.class_comments = [None]*len(self.data)
        self.drawer.init()

    def loadFile(self, path):
        imgs = []
        data = []
        uids = []
        comments = []
        class_comments = []
        # A default header data, in case of HEAD_0.json not found
        header_data: HeaderData = {
            "Labeler": "Unknown",
            "Time": "Unknown",
            "Spacing": [1,1,1],
            "Series": "Unknown",
            "Config": {"Unknown": None},
            "Version": "0.0.0"
        }
        file_list = [x for x in os.listdir(path) if x.endswith('.json')]
        for file_name in sorted(file_list, key = lambda x : int(re.findall(r'\d+|$', x)[0])):
            # Sort according to slice number "SliceXXX.json"
            file_path = os.path.join(path, file_name)
            if file_name == "HEAD_0.json":
                with open(file_path, "r") as f_:
                    header_data = json.load(f_)
            else:
                with open(file_path, "r") as f_:
                    slice_data = json.load(f_)
                data_ = slice_data["Data"]
                data.append(data_)
                if "Image" in slice_data:               
                    img = imgDecodeB64(slice_data["Image"], accelerate=True)
                else:                           # Older version compatbility (<1.5.4)
                    img = np.load(file_path[:-4] + "npz")["img"]
                imgs.append(img)
                if "Comment" in slice_data:
                    comments_ = slice_data["Comment"]  
                else:                           # Older version compatablility (<1.5.1)
                    comments_ = None
                comments.append(comments_)
                if "Classification" in slice_data:
                    c_comments_ = slice_data["Classification"]  
                else:                           # Older version compatablility (<1.5.3)
                    c_comments_ = None
                class_comments.append(c_comments_)
                if "Uid" in slice_data:
                    uid = slice_data["Uid"]  
                else:                           # Older version compatablility (<1.7.0)
                    uid = slice_data["Data"]["SOPInstanceUID"]      
                uids.append(uid)
        self.data = data
        self.uids = uids
        self.comments = comments
        self.class_comments = class_comments
        self.SAVED = True
        self.drawer.init()
        return  header_data, imgs


    def saveToFile(self, path, imgs, head_info):
        """
        - path: directory to store all the data for current patient
        Note: the x,y coordinate is in vtk coordinate
        """
        if os.path.exists(path):
            # prevent accidentally deleting wrong folder...
            assert checkFolderEligibility(path), f"Not an eligiable labeled folder: {path}"

            print("Overwriting...", path)
            self.logger.debug("Cleaning directory: {}".format(path))
            for file in os.listdir(path):
                self.logger.debug("Deleting file... {}".format(file))
                os.remove(os.path.join(path, file))
        else:
            print("Saving to file ", path)
            os.mkdir(path)

        print("Saving header file...")
        with open(os.path.join(path, "HEAD_0.json"), "w") as hf:
            json.dump(head_info, hf, indent=1)

        thread = Thread(target = self.__threadSaveToFile, args = (path, imgs.copy(),))
        thread.start()

    def clearContourData(self, idx: int, lbl: str):
        if self.data:
            self.data[idx][lbl] = []
            self.drawer.onModifyContour(idx, lbl)

    def __threadSaveToFile(self, path, imgs):
        for i in range(len(imgs)):
            print("Saving...{}/{}".format(i+1, len(imgs)))
            file_name = "Slice_"+str(i+1)+".json"
            img_name = "Slice_"+str(i+1)+".npz"
            assert self.data    # type checking
            js_data = {
                    "Data": self.data[i],
                    "Comment": self.comments[i],
                    "Classification": self.class_comments[i],
                    "Uid": self.uids[i]
                    }
            with open(os.path.join(path, file_name), "w") as f:
                json.dump(js_data, f)
            np.savez_compressed(os.path.join(path, img_name), img = imgs[i])
        print("Exporting finished!\nDestination: ", path)

    def __getBackNpCoord(self, x, y, img_shape):
        """Get coordinate in (row, col)
        - img_shape: (W, H)"""
        return img_shape[1]-1-y, x

    def __getBackCvCoord(self, x, y, img_shape):
        """Get coordinate in (col, row)
        - img_shape: (W, H)"""
        return x, img_shape[1]-1-y

    def __creatThreadFunction(self, func, *args, start = False, deamon = False):
        thread = Thread(target = func, args = args)
        if start:
            thread.start()
        return thread

class LabelDrawer:
    CECHE_MASK = True
    def __init__(self, holder: LabelHolder) -> None:
        self._holder = holder

    def init(self):
        # To cache mask
        self.__binary_masks: List[Dict[str, Optional[np.ndarray]]] = []
        if not self.data:
            return

        for d in self.data:
            mask_dict = dict()
            for lbl in d.keys():
                mask_dict[lbl] = None
            self.__binary_masks.append(mask_dict)

    @property
    def data(self) -> Optional[ContourDataT]:
        return self._holder.data

    @property
    def lbl_keys(self) -> List[str]:
        if self.data:
            return list(self.data[0].keys())
        else:
            return []

    @property
    def binary_masks(self):
        return self.__binary_masks

    def onModifyContour(self, idx: int, lbl: Optional[str] = None):
        """
        Delete cached contour masks
        """
        if lbl:
            self.__binary_masks[idx][lbl] = None
        else:
            mask_dict = dict()
            for k in self.lbl_keys:
                mask_dict[k] = None
            self.binary_masks[idx] = mask_dict

    def getSingleMask(self, idx: int, label: str, im_hw: Tuple[int, int]) -> np.ndarray:
        assert self.data
        if self.CECHE_MASK:
            # Check if there are cached mask
            cached_mask = self.binary_masks[idx][label]
            if isinstance(cached_mask, np.ndarray) and cached_mask.shape[0] == im_hw[0] and cached_mask.shape[1] == im_hw[1]:
                return cached_mask

        mask = np.zeros(im_hw, np.uint8)
        cnts_data = self.data[idx][label]
        if cnts_data == []:
            return mask
        for cnt_data in cnts_data:
            all_pts = cnt_data["Contour"] # All the points position on the contour, in CV coordinate
            if cnt_data["Open"] == True:
                cv_cnt = np.array([arr for arr in F.removeDuplicate2d(all_pts)])
                cv.polylines(mask,[cv_cnt],False,1)
            else:
                cv_cnt = np.array([[arr] for arr in F.removeDuplicate2d(all_pts)])
                cv.fillPoly(mask, pts = [cv_cnt], color = 1)
        mask = mask.astype(np.uint8)

        if self.CECHE_MASK:
            self.__binary_masks[idx][label] = mask
        return mask

    def getColorMask(self, idx: int, im_hw: Tuple[int, int], label_colors: Dict[str, Tuple[int, int, int]]) -> np.ndarray:

        #  masks = np.array((len(label_colors), im_hw[0], im_hw[1]), np.uint8)
        masks = list()
        color_list = []
        for i, k in enumerate(label_colors.keys()):
            color_list.append(label_colors[k])
            #  masks[i, ...] = self.getSingleMask(idx, k, im_hw)
            masks.append(self.getSingleMask(idx, k, im_hw))
        return MergeMasks.mergeBool2Color2D(np.array(masks, np.uint8), colors = color_list)

    def getColorMarkdImg(self, img: np.ndarray, idx: int, label_colors: Dict[str, Tuple[int, int, int]], alpha = 0.5):
        assert len(img.shape) == 3 and img.shape[2] == 3
        color_mask = self.getColorMask(idx, img.shape[:2], label_colors)

        msk = color_mask == np.array([0, 0, 0], dtype = np.uint8)
        msk = 1 - msk.all(axis = -1)
        msk = F.gray2rgb_(msk)

        img = img.astype(float)
        msk = msk.astype(float)
        
        color_mask = color_mask.astype(float)
        im = img*(1-msk) + img*(1-alpha)*msk + color_mask*alpha*msk
        return im.astype(np.uint8)


