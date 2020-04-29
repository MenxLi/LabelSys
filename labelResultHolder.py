#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#
# import{{{
from utils.base64ImageConverter import imgEncodeB64, imgDecodeB64
from configLoader import *
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
        self.data = None
        self.SAVED = True
# }}}
    def initialize(self, entries, SOPInstanceUIDs):# {{{
        self.data = []
        self.SAVED = True
        for ids in SOPInstanceUIDs:
            self.data.append({})
            for entry in entries:
                self.data[-1][entry] = []
            self.data[-1]["SOPInstanceUID"] = ids
# }}}
    def loadFile(self, path):# {{{
        imgs = []
        data = []
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
                img = imgDecodeB64(slice_data["Image"], accelerate=True)
                imgs.append(img)
                data_ = slice_data["Data"]
                data.append(data_)
        self.data = data
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

        #  head_info = {
        #          "Labeler":labeler,
        #          "Time":str(datetime.datetime.now()),
        #          "Spacing":spacing,
        #          #"Labels": labels,
        #          "Series": series,
        #          "Config": config
        #          }

        print("Saving header file...")
        with open(os.path.join(path, "HEAD_0.json"), "w") as hf:
            json.dump(head_info, hf)

        thread = Thread(target = self.__threadSaveToFile, args = (path, imgs.copy(),))
        thread.start()
# }}}
    def __threadSaveToFile(self, path, imgs):# {{{
        for i in range(len(imgs)):
            print("Saving...{}/{}".format(i+1, len(imgs)))
            file_name = "Slice_"+str(i+1)+".json"
            im_string = imgEncodeB64(imgs[i], accelerate= True)
            js_data = {
                    "Data": self.data[i],
                    "Image": im_string
                    }
            with open(os.path.join(path, file_name), "w") as f:
                json.dump(js_data, f)
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
