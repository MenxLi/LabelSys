import myFuncs as F
import vtk
from vtk.util import vtkImageImportFromArray
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtWidgets import *
import numpy as np
from config import *

import cv2 as cv
#
#https://stackoverflow.com/questions/31516748/render-segmentation-stored-in-a-numpy-array-with-vtk
# https://lorensen.github.io/VTKExamples/site/Python/Medical/MedicalDemo1/

# https://github.com/lorensen/VTKExamples/blob/master/src/Python/Utilities/VTKWithNumpy.py

class PreviewWindow(QWidget):
    def __init__(self, imgs, masks, spacing = [1,1,1]):
        super().__init__()
        if masks== None:
            self.close()
        self.imgs = imgs
        self.masks_raw = masks
        self.spacing = spacing
        self.masks = self.generateMasks()

        self.vtk_widget = QVTKRenderWindowInteractor()
        layout = QGridLayout()
        layout.addWidget(self.vtk_widget, 0, 0)
        self.setLayout(layout)

        self.ren_win = self.vtk_widget.GetRenderWindow()
        self.ren = vtk.vtkRenderer()
        self.ren_win.AddRenderer(self.ren)
        self.iren = self.ren_win.GetInteractor()  
        self.ren_win.Render()
        self.iren.Initialize()
        self.iren.Start()

        self.show3D()

    def generateMasks(self):
        masks = []
        for mask_ in self.masks_raw: 
            color = 1
            mask = np.ma.zeros(self.imgs[0].shape[:2], np.uint8)
            for label in mask_.keys():
                mask.mask = ~mask_[label]
                mask += np.array(color).astype(np.uint8)
                color += 1
            masks.append(mask.data)
        return np.array(masks)
    
    def show3D(self):
        self.r_masks = F.resampleSpacing(self.masks, self.spacing)[0].astype(np.uint8)*10

        colors = vtk.vtkNamedColors()
        data_importer = vtk.vtkImageImport()
        data_string = self.r_masks.tostring()
        data_importer.CopyImportVoidPointer(data_string, len(data_string))
        data_importer.SetDataScalarTypeToUnsignedChar()
        data_importer.SetNumberOfScalarComponents(1)
        data_importer.SetDataExtent(0, self.r_masks.shape[2]-1, 0, self.r_masks.shape[1]-1, 0, self.r_masks.shape[0]-1)
        data_importer.SetWholeExtent(0, self.r_masks.shape[2]-1, 0, self.r_masks.shape[1]-1, 0, self.r_masks.shape[0]-1)

        alphaChannelFunc = vtk.vtkPiecewiseFunction()
        alphaChannelFunc.AddPoint(0, 0.0)
        for i in range(len(LABELS)):
            value = (i+1)*10
            alphaChannelFunc.AddPoint(value, 0.8)
        colorFunc = vtk.vtkColorTransferFunction()
        for i in range(len(LABELS)):
            value = (i+1)*10
            #colorFunc.AddRGBPoint(value, *LBL_COLORS[i])
            colorFunc.AddRGBPoint(value, 1.0, 0.0, 0.0)

        volume_property = vtk.vtkVolumeProperty()
        volume_property.SetColor(colorFunc)
        volume_property.SetScalarOpacity(alphaChannelFunc)

        volume_mapper = vtk.vtkFixedPointVolumeRayCastMapper()
        volume_mapper.SetInputConnection(data_importer.GetOutputPort())

        volume = vtk.vtkVolume()
        volume.SetMapper(volume_mapper)
        volume.SetProperty(volume_property)

        self.ren.SetBackground(colors.GetColor3d("MistyRose"))
        self.ren.AddVolume(volume)

        self.ren.ResetCamera()
        self.ren_win.Render()

