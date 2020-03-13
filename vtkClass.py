import vtk
from vtk.util import vtkImageImportFromArray
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
#from vtk.qt.QVTKOpenGLWidget import QVTKOpenGLWidget
from PyQt5.QtWidgets import *
import numpy as np
import cv2 as cv
import myFuncs as F

class VtkWidget(QVTKRenderWindowInteractor):
    def __init__(self, frame, checkbox, main_UI):
        """
        - save_func: functions to be triggered when modify the contour
        """
        super().__init__(frame)
        self.master = frame
        self.checkbox = checkbox
        self.main_UI = main_UI

        layout = QGridLayout()
        layout.addWidget(self, 0, 0)
        self.master.setLayout(layout)

        self.ren_win = self.GetRenderWindow()
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
        self.contours = []

    def readNpArray(self, arr, txt = ""):
        """
        Read numpy array and display in the window
        - txt: text to be shown on the screen
        """
        # https://gitlab.kitware.com/vtk/vtk/blob/741fffbf6490c34228dfe437f330d854b2494adc/Wrapping/Python/vtkmodules/util/vtkImageImportFromArray.py

        self.im = arr

        self.__clearCanvas()
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
        contour_widget.AddObserver('EndInteractionEvent', contourWidgetEndInteraction)
        contour_widget.AddObserver('WidgetValueChangedEvent', contourWidgetEndInteraction)
        
        return contour_widget

    def constructContour(self, pts, open_curve = None):
        """
        Default behaviour:
        - LeftButtonPressEvent - triggers a Select event
        - MouseMoveEvent - triggers a Move event
        - LeftButtonReleaseEvent - triggers an EndSelect event
        - Delete key event - triggers a Delete event
        """
        if pts ==[]:
            return 1
        pd = vtk.vtkPolyData()
        points = vtk.vtkPoints()
        lines = vtk.vtkCellArray()
        for i in range(len(pts)):
            points.InsertPoint(i, pts[i])

        if open_curve == None:
            open_curve = self.__isOpen()

        if not open_curve:
            vertex_ids = list(range(len(pts))) + [0]
            lines.InsertNextCell(len(pts)+1, vertex_ids)
        else:
            vertex_ids = list(range(len(pts))) 
            lines.InsertNextCell(len(pts), vertex_ids)

        pd.SetPoints(points)
        pd.SetLines(lines)

        contour_widget = self.contourWidget(contourWidgetEndInteraction = self.__saveContour)
        contour_widget.On()
        contour_widget.Initialize(pd,1)
        contour_widget.Render()
        self.contours.append(contour_widget)
        self.__saveContour(None, None)
        return 0

    def loadContour(self, pts, open_curve):
        self.constructContour(pts, open_curve)
        self.style._reinitState()

    def drawLine(self, pt0, pt1, color = [0.5,1,1], lw = 4):
        line_source = vtk.vtkLineSource()
        line_source.SetPoint1(pt0)
        line_source.SetPoint2(pt1)
        line_source.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(line_source.GetOutputPort())
        actor = vtk.vtkActor()
        actor.GetProperty().SetColor(*color)
        actor.SetMapper(mapper)
        actor.GetProperty().SetLineWidth(lw)
        self.ren.AddActor(actor)
        self.ren_win.Render()
        return actor

    def reInitStyle(self):
        self.style._reinitState()

    def __saveContour(self, obj, event):
        data = []
        for contour in self.contours:
            rep = contour.GetContourRepresentation()
            if rep.GetClosedLoop():
                mask = self.__getMask(contour, self.im.shape, "Close").astype(np.bool)
            else: 
                mask = self.__getMask(contour, self.im.shape, "Open").astype(np.bool)

            pts_cnt = []
            point = np.empty((3))
            for pt_id in range(rep.GetNumberOfNodes()):
                rep.GetNthNodeWorldPosition(pt_id, point)
                pts_cnt.append(tuple(point))
            contour_data = {
                    "Open": not rep.GetClosedLoop(),
                    "Points": pts_cnt[:],
                    "Mask": mask.copy()
                    }
            data.append(contour_data)
        self.main_UI.saveCurrentSlice(data)

    def __getMask(self, contour_widget, img_shape, mode):
        """
        -img_shape : (H, W)
        """
        mask = np.zeros(img_shape, np.uint8)
        cnt = contour_widget
        rep = cnt.GetContourRepresentation()
        all_pts = []
        point = np.empty((3))
        for pt_id in range(rep.GetNumberOfNodes()):
            rep.GetNthNodeWorldPosition(pt_id, point)
            all_pts.append(self.__getBackCvCoord(*point[:2], img_shape))
            for ipt_id in range(rep.GetNumberOfIntermediatePoints(pt_id)):
                rep.GetIntermediatePointWorldPosition(pt_id, ipt_id, point)
                all_pts.append(self.__getBackCvCoord(*point[:2], img_shape))
        all_pts = np.array(all_pts).astype(np.int)
        if mode == "Close":
            cv_cnt = np.array([[arr] for arr in F.removeDuplicate2d(all_pts)])
            cv.fillPoly(mask, pts = [cv_cnt], color = 1)
        elif mode == "Open":
            cv_cnt = np.array([arr for arr in F.removeDuplicate2d(all_pts)])
            cv.polylines(mask,[cv_cnt],False,255)
        #cv.imshow("Test",mask)
        #cv.waitKey(0)
        return mask

    def __getBackNpCoord(self, x, y, img_shape):
        """Get coordinate in (row, col)
        - img_shape: (W, H)"""
        return np.array([img_shape[1]-1-y, x])

    def __getBackCvCoord(self, x, y, img_shape):
        """Get coordinate in (col, row)
        - img_shape: (W, H)"""
        return np.array([x, img_shape[1]-1-y])

    def __clearCanvas(self):
        self.contours = []
        self.ren.RemoveAllViewProps()
        self.contours = []
    
    def __isOpen(self):
        return self.checkbox.isChecked()


class MyInteractorStyle(vtk.vtkInteractorStyleImage):
    """Interactor style for vtk widget"""
    HEIGHT = 0 # Z/W position of the curve 
    SAMPLE_STEP = 10
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

        # Left button for label, move event is implemented in Qt
        self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)
        self.AddObserver("LeftButtonReleaseEvent", self.leftButtonReleaseEvent)

        self.AddObserver("KeyPressEvent", self.keyPressEvent)

        # Attribute
        self.pts_raw = []
        self.pts = []
        self.lines = []
        self.__mode = "Drawing"
        self.__drawing = False 
        self.__prev_pt = None

    def leftButtonPressEvent(self, obj, event):
        ctrl = self.widget.iren.GetControlKey()
        alt = self.widget.iren.GetAltKey()
        shift = self.widget.iren.GetShiftKey()

        if self.__mode == "Drawing":
            now_pt = self._getMousePos()
            self.pts_raw.append(now_pt)

            self.__prev_pt = now_pt
            self.__drawing = True
            return 0
    
    def mouseMoveEvent(self, obj, event):
        if self.__mode == "Drawing" and self.__drawing:
            now_pt = self._getMousePos()
            self.pts_raw.append(now_pt)

            self.lines.append(self.widget.drawLine(self.__prev_pt, now_pt))
            self.__prev_pt = now_pt
            return 0

    def leftButtonReleaseEvent(self, obj, event):
        if self.__mode == "Drawing":
            # Interpolate between raw points
            full_curve = [self.pts_raw[0]]
            for i in range(1, len(self.pts_raw)):
                interp_pts = self.__linearInterp(*[pos[:2] for pos in self.pts_raw[i-1:i+1]], mode = "")
                full_curve += [[pt[0], pt[1], MyInteractorStyle.HEIGHT] for pt in interp_pts[1:] ]
            # Sampling inside full_curve
            self.pts = full_curve[::MyInteractorStyle.SAMPLE_STEP*2]
            # Construct contour
            self.widget.constructContour(self.pts)

            # Re initialize
            for actor in self.lines:
                self.widget.ren.RemoveActor(actor)
            self.widget.ren_win.Render()
            self._reinitState()

    def keyPressEvent(self, obj, event):
        key = self.widget.iren.GetKeySym()
        if key == "v": # Zoom in
            self.OnMouseWheelForward()  
        elif key == "c": # Zoom out
            self.OnMouseWheelBackward()
        elif key == "r": # Reset camera
            self.widget.resetCamera()

    def forceDrawing(self):
        self.__mode = "Drawing"

    def _reinitState(self):
        """Should be called when going to different slice"""
        self.__prev_pt = None
        self.__drawing = False
        if self.widget.contours == []:
            self.__mode = "Drawing"
        else: self.__mode = "Revising"
        self.lines = []
        self.pts = []
        self.pts_raw = []
    
    def _getMousePos(self):
        click_pos = self.GetInteractor().GetEventPosition()
        self.picker.Pick(*click_pos, 0, self.GetDefaultRenderer())
        pos = self.picker.GetPickPosition()
        #return pos
        return (pos[0], pos[1], MyInteractorStyle.HEIGHT)

    def __linearInterp(self, pos1, pos2, mode = "Int"):
        """Linear interpolation between two 2D points"""
        pos1 = np.array(pos1)
        pos2 = np.array(pos2)
        L = np.linalg.norm(pos1-pos2)
        if L < 1/2 :
            return [pos1]
        step = 1/(2*L)
        interp_pos = [pos1]
        for t in np.arange(0,1,step):
            if mode == "Int":
                interp_pos.append((pos2*t+pos1*(1-t)).astype(int))
            else:
                interp_pos.append(pos2*t+pos1*(1-t))
        interp_pos.append(pos2)
        #print(interp_pos)
        t
        return self.__removeDuplicate2d(interp_pos)
    def __removeDuplicate2d(self, duplicate):
        final_list = []
        flag = True
        for num in duplicate:
            for num0 in final_list:
                if num[0] == num0[0] and num[1] == num0[1]:
                    flag = False
            if flag: final_list.append(num)
            flag = True
        return final_list

