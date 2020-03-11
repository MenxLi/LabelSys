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

    def getMasks(self, label, img_shape):
        """
        get binary masks of a single label from data,
        - img_shape: (H, W)
        """
        mask = np.zeros(img_shape, np.uint8)
        data_contours = self.data[0][label]
        for data in data_contours:
            pts = data["Points"]
            open_curve = data["Open"]
            cnt = self.__contourWidget(pts, open_curve)
            rep = cnt.GetContourRepresentation()
            pts_cnt = []    # Every point in the contour in (col, row)
            point = np.empty((3))
            for pt_id in range(rep.GetNumberOfNodes()):
                rep.GetNthNodeWorldPosition(pt_id, point)
                pts_cnt.append(self.__getBackCvCoord(*point[:2], img_shape))

    def __contourWidget(self, pts, open_curve):
        """
        Plain contour widget without render window and interactor
        """
        contourRep = vtk.vtkOrientedGlyphContourRepresentation()
        contour_widget = vtk.vtkContourWidget()
        contour_widget.SetRepresentation(contourRep)

        if pts ==[]:
            return 1
        pd = vtk.vtkPolyData()
        points = vtk.vtkPoints()
        lines = vtk.vtkCellArray()
        for i in range(len(pts)):
            points.InsertPoint(i, pts[i])

        if not open_curve:
            vertex_ids = list(range(len(pts))) + [0]
            lines.InsertNextCell(len(pts)+1, vertex_ids)
        else:
            vertex_ids = list(range(len(pts))) 
            lines.InsertNextCell(len(pts), vertex_ids)

        pd.SetPoints(points)
        pd.SetLines(lines)

        return contour_widget

    def __getBackNpCoord(self, x, y, img_shape):
        """Get coordinate in (row, col)
        - img_shape: (W, H)"""
        return img_shape[1]-1-y, x

    def __getBackCvCoord(self, x, y, img_shape):
        """Get coordinate in (col, row)
        - img_shape: (W, H)"""
        return x, img_shape[1]-1-y
