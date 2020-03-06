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
        self.camera_set = False
        self.ren_win.AddRenderer(self.ren)

        self.iren = self.ren_win.GetInteractor()  
        self.ren_win.Render()
        self.iren.Initialize()

        # change key binding
        self.style = MyInteractorStyle(widget = self)
        self.style.SetDefaultRenderer(self.ren)
        self.iren.SetInteractorStyle(self.style)

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
        if not self.camera_set:
            # Just reset camera once for each patient
            self.ren.ResetCamera()
            self.camera_set = True
        self.ren_win.Render()

    def resetCamera(self):
        self.ren.ResetCamera()
        self.ren_win.Render()

class MyInteractorStyle(vtk.vtkInteractorStyleImage):
    def __init__(self,widget):
        self.widget = widget
        self.AddObserver("RightButtonPressEvent", self.rightButtonPressEvent)
        self.AddObserver("RightButtonReleaseEvent", self.rightButtonReleaseEvent)
        self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)
        self.AddObserver("KeyPressEvent", self.keyPressEvent)
        self.AddObserver("MouseWheelForwardEvent", lambda x, y : None)
        self.AddObserver("MouseWheelBackwardEvent", lambda x, y : None)

    def rightButtonPressEvent(self, obj, event):
        self.OnMiddleButtonDown()

    def rightButtonReleaseEvent(self, obj, event):
        self.OnMiddleButtonUp()

    def leftButtonPressEvent(self, obj, event):
        click_pos = self.GetInteractor().GetEventPosition()
        print(click_pos)

        if self.widget.iren.GetControlKey():
            pass

    def keyPressEvent(self, obj, event):
        key = self.widget.iren.GetKeySym()
        if key == "v": # Zoom in
            self.OnMouseWheelForward()  
        elif key == "c": # Zoom out
            self.OnMouseWheelBackward()
        elif key == "r": # Reset camera
            self.widget.resetCamera()
