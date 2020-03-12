from base64ImageConverter import imgEncodeB64, imgDecodeB64
import os
import vtk
import cv2 as cv
import numpy as np

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
        pass

    def __getBackNpCoord(self, x, y, img_shape):
        """Get coordinate in (row, col)
        - img_shape: (W, H)"""
        return img_shape[1]-1-y, x

    def __getBackCvCoord(self, x, y, img_shape):
        """Get coordinate in (col, row)
        - img_shape: (W, H)"""
        return x, img_shape[1]-1-y
