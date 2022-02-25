#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#
# import{{{
from typing import List, Union
from .utils.base64ImageConverter import imgEncodeB64, imgDecodeB64
from .configLoader import *
import os
import vtk
import cv2 as cv
import numpy as np
import json
import copy
from threading import Thread
import datetime
import re
# }}}

class LabelHolder:
    """
    HOlding the label result
    """
    def __init__(self):# {{{
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
        self.data: List[dict] = None
        self.SAVED: bool = True
        self.uids: List[str]
        self.comments: List[Union[None, str]]
        self.class_comments: List[Union[None, str]]
# }}}
    def initialize(self, entries, SOPInstanceUIDs):# {{{
        self.data = []
        self.uids = []      # For future version
        self.SAVED = True
        for ids in SOPInstanceUIDs:
            self.data.append({})
            for entry in entries:
                self.data[-1][entry] = []
            # self.data[-1]["SOPInstanceUID"] = ids
            self.uids.append(ids)
        self.comments = [None]*len(self.data)
        self.class_comments = [None]*len(self.data)
# }}}
    def loadFile(self, path):# {{{
        imgs = []
        data = []
        uids = []
        comments = []
        class_comments = []
        file_list = [x for x in os.listdir(path) if x.endswith('.json')]
        for file_name in sorted(file_list, key = lambda x : int(re.findall('\d+|$', x)[0])):
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
                else:                           # Older version compatablility (<1.6.7)
                    uid = slice_data["Data"]["SOPInstanceUID"]      
                uids.append(uid)
        self.data = data
        self.uids = uids
        self.comments = comments
        self.class_comments = class_comments
        self.SAVED = True
        return  header_data, imgs
# }}}
    def saveToFile(self, path, imgs, head_info):# {{{
        """
        - path: directory to store all the data for current patient
        Note: the x,y coordinate is in vtk coordinate
        """
        if os.path.exists(path):
            print("Overwriting...", path)
            for file in os.listdir(path):
                os.remove(os.path.join(path, file))
        else:
            print("Saving to file ", path)
            os.mkdir(path)

        print("Saving header file...")
        with open(os.path.join(path, "HEAD_0.json"), "w") as hf:
            json.dump(head_info, hf, indent=1)

        thread = Thread(target = self.__threadSaveToFile, args = (path, imgs.copy(),))
        thread.start()
# }}}
    def __threadSaveToFile(self, path, imgs):# {{{
        for i in range(len(imgs)):
            print("Saving...{}/{}".format(i+1, len(imgs)))
            file_name = "Slice_"+str(i+1)+".json"
            img_name = "Slice_"+str(i+1)+".npz"
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
# }}}
    def __getBackNpCoord(self, x, y, img_shape):# {{{
        """Get coordinate in (row, col)
        - img_shape: (W, H)"""
        return img_shape[1]-1-y, x
# }}}
    def __getBackCvCoord(self, x, y, img_shape):# {{{
        """Get coordinate in (col, row)
        - img_shape: (W, H)"""
        return x, img_shape[1]-1-y
# }}}
    def __creatThreadFunction(self, func, *args, start = False, deamon = False):# {{{
        thread = Thread(target = func, args = args)
        if start:
            thread.start()
        return thread
# }}}
