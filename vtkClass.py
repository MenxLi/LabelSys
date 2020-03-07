import vtk
from vtk.util import vtkImageImportFromArray
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtWidgets import *

class VtkWidget(QWidget):
    def __init__(self, frame):
        super().__init__()
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

        # Attribute
        self.colors = vtk.vtkNamedColors()
        self.pts_raw = []
        self.pts = []
        self.lines = []
        self.contour = None


    def readNpArray(self, arr, txt = ""):
        """
        Read numpy array and display in the window
        - txt: text to be shown on the screen
        """
        # https://gitlab.kitware.com/vtk/vtk/blob/741fffbf6490c34228dfe437f330d854b2494adc/Wrapping/Python/vtkmodules/util/vtkImageImportFromArray.py

        self.im = arr

        self.__clearCanvas()
        # clear render
        #try:
            #self.ren.RemoveActor(self.actor)
            #self.ren.RemoveActor(self.t_actor)
        #except:
            #pass
        #===============Update Image======================
        # import from numpy array
        importer = vtkImageImportFromArray.vtkImageImportFromArray()
        importer.SetArray(arr) 
        importer.Update()

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

        #===============Update Text=======================
        self.t_actor = vtk.vtkTextActor()
        self.t_actor.SetInput(txt)
        txtprop = self.t_actor.GetTextProperty()
        txtprop.SetFontFamilyToCourier()
        txtprop.SetFontSize(12)
        self.t_actor.SetDisplayPosition(5,5)
        
        self.ren.AddActor(self.t_actor)

        self.ren_win.Render()

    def resetCamera(self):
        self.ren.ResetCamera()
        self.ren_win.Render()

    def contourWidget(self, color=[1, 0, 0], contourWidgetEndInteraction=None):
        """Create a template widget for drawing contours"""
        contourRep = vtk.vtkOrientedGlyphContourRepresentation()
        contourRep.GetLinesProperty().SetColor(color) 
               
        contour_widget = vtk.vtkContourWidget()
        contour_widget.SetInteractor(self.iren)
        contour_widget.SetRepresentation(contourRep)
        contour_widget.AddObserver('EndInteractionEvent', contour_widgetEndInteraction)
        contour_widget.AddObserver('WidgetValueChangedEvent', contour_widgetEndInteraction)
        
        return contour_widget

    def drawLine(pt0, pt1, color = [1,0,0], lw = 4):
        line_source = vtk.vtkLineSource()
        line_source.SetPoint1(p0)
        line_source.SetPoint2(p1)
        line_source.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(line_source.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetLineWidth(lw)
        self.ren.AddActor(actor)
        self.ren_win.Render()
        return actor

    def __clearCanvas(self):
        self.ren.RemoveAllViewProps()


class MyInteractorStyle(vtk.vtkInteractorStyleImage):
    def __init__(self,widget):
        self.widget = widget
        self.picker = vtk.vtkPropPicker()

        # Right button for move
        self.AddObserver("RightButtonPressEvent", lambda obj, event: self.OnMiddleButtonDown())
        self.AddObserver("RightButtonReleaseEvent", lambda obj, event: self.OnMiddleButtonUp())
        # Suspend wheel and implement in Qt framwork
        self.AddObserver("MouseWheelForwardEvent", lambda x, y : None)
        self.AddObserver("MouseWheelBackwardEvent", lambda x, y : None)
        # Middle button for Brightness change
        self.AddObserver("MiddleButtonPressEvent", lambda obj, event: self.OnLeftButtonDown())
        self.AddObserver("MiddleButtonReleaseEvent", lambda obj, event: self.OnLeftButtonUp())

        # Left button for label
        #self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)
        self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)
        #self.AddObserver(self.widget.vtk_widget.DragMoveEvent, self.mouseMoveEvent)
        self.AddObserver("LeftButtonReleaseEvent", self.leftButtonReleaseEvent)

        self.AddObserver("KeyPressEvent", self.keyPressEvent)

        # Attribute
        self.__drawing = False 
        self.__prev_pt = None

    def leftButtonPressEvent(self, obj, event):
        ctrl = self.widget.iren.GetControlKey()
        alt = self.widget.iren.GetAltKey()
        shift = self.widget.iren.GetShiftKey()

        click_pos = self.GetInteractor().GetEventPosition()
        #print("Click pos: ", click_pos)

        self.picker.Pick(*click_pos, 0, self.GetDefaultRenderer())
        pos = self.picker.GetPickPosition()
        print(pos)

        self.__prev_pt = pos
        self.__drawing = True
    
    def mouseMoveEvent(self, obj, event):
        self.OnRightButtonDown()

    def OnRightButtonDown(self):
        print("Hello")
    
    def OnMouseMove(self, obj, event):
        print("haha")

    def leftButtonReleaseEvent(self, obj, event):
        pass

    def keyPressEvent(self, obj, event):
        key = self.widget.iren.GetKeySym()
        if key == "v": # Zoom in
            self.OnMouseWheelForward()  
        elif key == "c": # Zoom out
            self.OnMouseWheelBackward()
        elif key == "r": # Reset camera
            self.widget.resetCamera()
