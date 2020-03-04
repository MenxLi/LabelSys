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

        # change key binding
        style = MyInteractorStyle()
        style.SetDefaultRenderer(self.ren)
        self.iren.SetInteractorStyle(style)

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

        # flip image along y axis
        flipY_filter = vtk.vtkImageFlip()
        flipY_filter.SetFilteredAxis(1)
        flipY_filter.SetInputConnection(importer.GetOutputPort())
        flipY_filter.Update()

        self.actor = vtk.vtkImageActor()
        self.actor.GetMapper().SetInputConnection(flipY_filter.GetOutputPort())
        
        # Add actor to renderer, reset camera and render
        self.ren.AddActor(self.actor)
        self.ren.ResetCamera()
        self.ren_win.Render()

class MyInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self,parent = None):
        #self.AddObserver("RightButtonPressEvent", self.rightButtonPressEvent)
        #self.AddObserver("RightButtonReleaseEvent", self.rightButtonReleaseEvent)
        self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)

    def rightButtonPressEvent(self, obj, event):
        self.OnMiddleButtonDown()

    def rightButtonReleaseEvent(self, obj, event):
        self.OnMiddleButtonUp()

    def leftButtonPressEvent(self, obj, event):
        click_pos = self.GetInteractor().GetEventPosition()
        print(click_pos)
