
import vtk
from vtk.util import vtkImageImportFromArray
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtWidgets import *
import numpy as np

# https://lorensen.github.io/VTKExamples/site/Python/Medical/MedicalDemo1/

class PreviewWindow(QWidget):
    def __init__(self, imgs, lbl_holder):
        super().__init__()
        self.imgs = imgs
        self.lbl_holder = lbl_holder
        self.im_shape = imgs[0].shape
        for im in imgs:
            if im.shape != self.im_shape:
                print("Warning! image shape unmatch")


        self.vtk_widget = QVTKRenderWindowInteractor()
        layout = QGridLayout()
        layout.addWidget(self.vtk_widget, 0, 0)
        self.setLayout(layout)

        self.ren_win = self.vtk_widget.GetRenderWindow()
        self.ren = vtk.vtkRenderer()
        self.camera_set = False
        self.ren_win.AddRenderer(self.ren)
        self.iren = self.ren_win.GetInteractor()  
        self.ren_win.Render()
        self.iren.Initialize()

    def test(self):
        self.lbl_holder.getMasks("Condyle", self.im_shape)
