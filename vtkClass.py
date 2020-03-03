import vtk
from vtk.util import vtkImageImportFromArray
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtWidgets import *

class VtkWidget:
    def __init__(self, frame):
        self.frame = frame
        self.layout = QGridLayout()
        self.vtk_widget = QVTKRenderWindowInteractor(self.frame) 
        self.layout.addWidget(self.vtk_widget, 0, 0)
        self.frame.setLayout(self.layout)

        self.ren_win = self.vtk_widget.GetRenderWindow()

        self.ren = vtk.vtkRenderer()
        self.ren_win.AddRenderer(self.ren)

        self.iren = self.ren_win.GetInteractor()  
        self.ren_win.Render()
        self.iren.Initialize()

        self.colors = vtk.vtkNamedColors()

    def readNpArray(self, arr):
        """Read numpy array and display in the window"""
        # https://gitlab.kitware.com/vtk/vtk/blob/741fffbf6490c34228dfe437f330d854b2494adc/Wrapping/Python/vtkmodules/util/vtkImageImportFromArray.py

        # clear render
        try:
            self.ren.RemoveActor(self.actor)
        except:
            pass
        # import from numpy array
        importer = vtkImageImportFromArray.vtkImageImportFromArray()
        importer.SetArray(arr) 
        importer.Update()
        self.im = importer.GetOutput()

        self.actor = vtk.vtkImageActor()
        self.actor.GetMapper().SetInputConnection(importer.GetOutputPort())
        
        # Add actor to renderer, reset camera and render
        self.ren.AddActor(self.actor)
        self.ren.ResetCamera()
        self.ren_win.Render()

