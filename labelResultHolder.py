from base64ImageConverter import imgEncodeB64, imgDecodeB64
import os
import vtk
import cv2 as cv
import numpy as np
import json
import copy
from threading import Thread

class LabelHolder:
    """
    HOlding the label result
    """
    def __init__(self):
        self.data = None
        self.SAVED = True
    def initialize(self, entries, SOPInstanceUIDs):
        self.data = []
        self.SAVED = True
        for ids in SOPInstanceUIDs:
            self.data.append({})
            for entry in entries:
                self.data[-1][entry] = []
            self.data[-1]["SOPInstanceUID"] = ids

    def loadFile(self, path):
        pass

    def saveToFile(self, path, imgs = None):
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
        thread = Thread(target = self.__threadSaveToFile, args = (path, imgs,))
        thread.start()
        #thread.join()

    def __threadSaveToFile(self, path, imgs):
        for i in range(len(imgs)):
            print("Saving...{}/{}".format(i+1, len(imgs)))
            file_name = "Slice"+str(i)+".json"
            im_string = imgEncodeB64(imgs[i])
            js_data = {
                    "Data": self.data[i],
                    "Image": im_string
                    }
            with open(os.path.join(path, file_name), "w") as f:
                json.dump(js_data, f)
        print("Exporting finished!\n Destination: ", path)

    def __getBackNpCoord(self, x, y, img_shape):
        """Get coordinate in (row, col)
        - img_shape: (W, H)"""
        return img_shape[1]-1-y, x

    def __getBackCvCoord(self, x, y, img_shape):
        """Get coordinate in (col, row)
        - img_shape: (W, H)"""
        return x, img_shape[1]-1-y
