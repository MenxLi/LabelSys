#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#
# import{{{
from typing import List, Tuple
from numpy.lib.arraysetops import isin
import vtk
from vtk.util import vtkImageImportFromArray
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
#from vtk.qt.QVTKOpenGLWidget import QVTKOpenGLWidget
from PyQt5.QtWidgets import *
import numpy as np
import cv2 as cv
from .utils import utils_ as F
from .configLoader import *
import os, sys
# }}}

class VtkWidget(QVTKRenderWindowInteractor):# {{{
    if sys.platform == "win32":
        _TEMP_FOLDER_NAME = ".TempDir"
    else:
        _TEMP_FOLDER_NAME = ".TempDir"
    _PAR_PATH = os.path.abspath(os.path.join(__file__, os.pardir))
    TEMP_DIR = os.path.join(_PAR_PATH, _TEMP_FOLDER_NAME)       # temporary directory to save image
    def __init__(self, frame, parent):# {{{
        super().__init__(frame)

        # Create temporary directory for color image storage,
        # The color image will be stored in this directory then be read by VTK
        if not os.path.exists(self.TEMP_DIR):
            print("Temporary directory created: ", self.TEMP_DIR)
            os.mkdir(self.TEMP_DIR)

        self.master = frame
        self.parent = parent

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
# }}}
    def readNpArray(self, arr, txt = "", clear_canvas = True):# {{{
        """
        Read numpy array and display in the window
        - txt: text to be shown on the screen
        """
        if clear_canvas:
            self.__clearCanvas()

        self.im = arr
        if len(self.im.shape) == 3 and self.im.shape[2] == 3:# {{{
            # read from image
            #  im_path = os.path.join(self.TEMP_DIR, "im.jpg")
            im_path = os.path.join(self.TEMP_DIR, "im.png")
            cv.imwrite(im_path, cv.cvtColor(self.im, cv.COLOR_RGB2BGR))
            #  im_reader = vtk.vtkJPEGReader()
            im_reader = vtk.vtkPNGReader()
            im_reader.SetFileName(im_path)
            self.actor = vtk.vtkImageActor()
            self.actor.GetMapper().SetInputConnection(im_reader.GetOutputPort())
            # }}}
        elif len(self.im.shape) == 2:# {{{
            #===============Update Image======================
            # https://gitlab.kitware.com/vtk/vtk/blob/741fffbf6490c34228dfe437f330d854b2494adc/Wrapping/Python/vtkmodules/util/vtkImageImportFromArray.py
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
            # }}}
        # Add actor to renderer, reset camera and render
        self.ren.AddActor(self.actor)
        if not self.camera_set:
            # Just reset camera once for each patient
            self.ren.ResetCamera()
            self.camera_set = True

        #===============Update Text=======================
        if txt is None:
            # not render text
            self.ren_win.Render()
            return 0

        self.t_actor = vtk.vtkTextActor()
        self.t_actor.SetInput(txt)
        txtprop = self.t_actor.GetTextProperty()
        txtprop.SetFontFamilyToCourier()
        txtprop.SetFontSize(12)
        self.t_actor.SetDisplayPosition(5,5)
        self.ren.AddActor(self.t_actor)

        # show label
        self.t_actor_label = vtk.vtkTextActor()
        self.t_actor_label.SetInput(self.parent.curr_lbl)
        txtprop_label = self.t_actor_label.GetTextProperty()
        txtprop_label.SetFontFamilyToArial()
        txtprop_label.BoldOn()
        txtprop_label.SetColor(0,1,0)
        txtprop_label.SetFontSize(32)
        #  txtprop_label.ShadowOn()
        #  txtprop_label.SetShadowOffset(4, 4)
        self.t_actor_label.SetDisplayPosition(5,50)
        self.ren.AddActor(self.t_actor_label)

        self.ren_win.Render()
# }}}
    def resetCamera(self):# {{{
        self.ren.ResetCamera()
        self.ren_win.Render()
        # }}}
    def contourWidget(self, color=[1, 0, 0], contourWidgetEndInteraction=None):# {{{
        """Create a template widget for drawing contours"""
        contourRep = vtk.vtkOrientedGlyphContourRepresentation()
        contourRep.GetLinesProperty().SetColor(color)

        contour_widget = vtk.vtkContourWidget()
        contour_widget.SetInteractor(self.iren)
        contour_widget.SetRepresentation(contourRep)
        contour_widget.AddObserver('EndInteractionEvent', contourWidgetEndInteraction)
        contour_widget.AddObserver('WidgetValueChangedEvent', contourWidgetEndInteraction)

        return contour_widget
# }}}
    def constructContour(self, pts, open_curve = None, save = True):# {{{
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

        try:
            color = self.parent._getColor(self.parent.combo_label.currentText())
        except:
            # for compare_win
            color = self.parent._getColor(self.parent.parent.combo_label.currentText())

        contour_widget = self.contourWidget(color = color, contourWidgetEndInteraction = self.__endInteraction)
        contour_widget.On()
        contour_widget.Initialize(pd,1)
        contour_widget.Render()
        self.contours.append(contour_widget)
        if save:
            # save on drawing contour but not save when loading contour with
            # self.loadContour
            self.__endInteraction(None, None)
        return 0
# }}}
    def loadContour(self, pts, open_curve):# {{{
        self.constructContour(pts, open_curve, save = False)
        self.style._reinitState()
# }}}
    def drawLine(self, pt0, pt1, color = [0.5,1,1], lw = 4):# {{{
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
# }}}
    def reInitStyle(self):# {{{
        self.style._reinitState()
# }}}
    def setStyleSampleStep(self, step = 1):# {{{
        self.style._setSampleStep(step)
# }}}
    def __endInteraction(self, obj, event):# {{{
        data = []
        for contour in self.contours:
            rep = contour.GetContourRepresentation()
            #if rep.GetClosedLoop():
                #mask = self.__getMask(contour, self.im.shape, "Close").astype(np.bool)
            #else:
                #mask = self.__getMask(contour, self.im.shape, "Open").astype(np.bool)
            full_cnt = self.__getFullCnt(contour, self.im.shape)

            pts_cnt = []
            point = np.empty((3))
            for pt_id in range(rep.GetNumberOfNodes()):
                rep.GetNthNodeWorldPosition(pt_id, point)
                pts_cnt.append(tuple(point))
            contour_data = {
                    "Open": not rep.GetClosedLoop(),
                    "Points": pts_cnt[:],
                    #"Mask": mask.copy()
                    "Contour": full_cnt
                    }
            data.append(contour_data)
        self.parent.saveCurrentSlice(data)
        # Update image in case of preview on panel is enabled
        if not self.parent.check_preview.isChecked():
            im = F.map_mat_255(self.parent.imgs[self.parent.slice_id])
        else:
            im = self.parent._getMarkedImg(self.parent.slice_id)
            self.readNpArray(im, None, clear_canvas=False)
# }}}
    def __getFullCnt(self, contour_widget, img_shape):# {{{
        """
        Get all point position in the image
        return point in (col, row)
        -img_shape : (H, W)
        """
        if len(img_shape) == 3:
            img_shape = img_shape[:2]
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
        return all_pts.tolist()
# }}}
    def __getMask(self, contour_widget, img_shape, mode):# {{{
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
        all_pts = np.rint(np.array(all_pts))
        if mode == "Close":
            cv_cnt = np.array([[arr] for arr in F.removeDuplicate2d(all_pts)])
            cv.fillPoly(mask, pts = [cv_cnt], color = 1)
        elif mode == "Open":
            cv_cnt = np.array([arr for arr in F.removeDuplicate2d(all_pts)])
            cv.polylines(mask,[cv_cnt],False,1)
        return mask
# }}}
    # def __getBackNpCoord(self, x, y, img_shape):# {{{
        # """Get coordinate in (row, col)
        # - img_shape: (W, H)"""
        # return np.array([img_shape[1]-1-y, x])
# # }}}
    def __getBackCvCoord(self, x, y, img_shape):# {{{
        """Get coordinate in (col, row)
        - img_shape: (W, H)"""
        return np.array([x, img_shape[0]-1-y])
# }}}
    def __clearCanvas(self):# {{{
        self.contours = []
        self.ren.RemoveAllViewProps()
        self.contours = []
# }}}
    def __isOpen(self):# {{{
        return self.parent.check_crv.isChecked()
# }}}
# }}}

class MyInteractorStyle(vtk.vtkInteractorStyleImage):# {{{
    """Interactor style for vtk widget"""
    HEIGHT = 0 # Z/W position of the curve
    def __init__(self,widget):# {{{
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
# }}}
    def leftButtonPressEvent(self, obj, event):# {{{
        ctrl = self.widget.iren.GetControlKey()
        alt = self.widget.iren.GetAltKey()
        shift = self.widget.iren.GetShiftKey()

        if self.__mode == "Drawing":
            now_pt = self._getMousePos()
            self.pts_raw.append(now_pt)

            self.__prev_pt = now_pt
            self.__drawing = True
            return 0
# }}}
    def mouseMoveEvent(self, obj, event):# {{{
        if self.__mode == "Drawing" and self.__drawing:
            now_pt = self._getMousePos()
            if now_pt == (0.0, 0.0, 0):
                # the cursor move out of the image
                now_pt = self.__prev_pt
            self.pts_raw.append(now_pt)
            self.lines.append(self.widget.drawLine(self.__prev_pt, now_pt))
            self.__prev_pt = now_pt
            return 0
# }}}
    def leftButtonReleaseEvent(self, obj, event):# {{{
        if self.__mode == "Drawing":
            # Interpolate between raw points
            full_curve = [self.pts_raw[0]]
            for i in range(1, len(self.pts_raw)):
                interp_pts = self.__linearInterp(*[pos[:2] for pos in self.pts_raw[i-1:i+1]], mode = "")
                full_curve += [[pt[0], pt[1], MyInteractorStyle.HEIGHT] for pt in interp_pts[1:] ]
            # Sampling inside full_curve
            # self.pts = full_curve[::self.sample_step]
            self.pts = self._sampleCurve(full_curve, self.sample_step)
            if np.linalg.norm(np.array(self.pts[-1]) - np.array(full_curve[-1])) > self.sample_step * 0.4:
                # when last point is too far from initialization, add last point
                self.pts.append(full_curve[-1])

            if len(self.pts) < 2:
                # if the line is too short to construct 2 points for the
                # contour, then just abort this line and allow re-draw
                for actor in self.lines:
                    self.widget.ren.RemoveActor(actor)
                self.widget.ren_win.Render()
                self._reinitState()
                return

            # Construct contour
            self.widget.constructContour(self.pts)

            # Re initialize
            for actor in self.lines:
                self.widget.ren.RemoveActor(actor)
            self.widget.ren_win.Render()
            self._reinitState()
# }}}
    def keyPressEvent(self, obj, event):# {{{
        key = self.widget.iren.GetKeySym()
        if key == "v": # Zoom in
            self.OnMouseWheelForward()
        elif key == "c": # Zoom out
            self.OnMouseWheelBackward()
        elif key == "r": # Reset camera
            self.widget.resetCamera()
# }}}
    def forceDrawing(self):# {{{
        self.__mode = "Drawing"
# }}}

    def _sampleCurve(self, curve: List[Tuple[int, int]], sample_step: int) -> List[Tuple[int, int]]:
        """Sample a curve in equally distributed interval of intergral curvature

        Args:
            curve (List[Tuple[int, int]]): [description]
            sample_step (int): [description]

        Returns:
            List[Tuple[int, int]]: [description]
        """
        # Calculate curvature
        if not isinstance(curve, np.ndarray):
            curve = np.array(curve)
        x_t = np.gradient(curve[:, 0])
        y_t = np.gradient(curve[:, 1])
        xx_t = np.gradient(x_t)
        yy_t = np.gradient(y_t)
        curvature = np.abs(xx_t * y_t - x_t * yy_t) / (x_t * x_t + y_t * y_t)**1.5

        # Decided where to sample
        counter = 0
        idx = [0]
        for i in range(len(curvature)):
            counter += curvature[i]
            if counter >= sample_step:
                counter = 0
                idx.append(i)
        idx.append(len(curve)-1)
        return curve[idx]

    def _setSampleStep(self, step):# {{{
        self.sample_step = step
# }}}
    def _reinitState(self):# {{{
        """Should be called when going to different slice"""
        self.__prev_pt = None
        self.__drawing = False
        if self.widget.contours == []:
            self.__mode = "Drawing"
        else: self.__mode = "Revising"
        self.lines = []
        self.pts = []
        self.pts_raw = []
# }}}
    def _getMousePos(self):# {{{
        click_pos = self.GetInteractor().GetEventPosition()
        self.picker.Pick(*click_pos, 0, self.GetDefaultRenderer())
        pos = self.picker.GetPickPosition()
        #return pos
        return (pos[0], pos[1], MyInteractorStyle.HEIGHT)
# }}}
    def __linearInterp(self, pos1, pos2, mode = "Int"):# {{{
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
        return self.__removeDuplicate2d(interp_pos)# }}}
    def __removeDuplicate2d(self, duplicate):# {{{
        final_list = []
        flag = True
        for num in duplicate:
            for num0 in final_list:
                if num[0] == num0[0] and num[1] == num0[1]:
                    flag = False
            if flag: final_list.append(num)
            flag = True
        return final_list# }}}
# }}}
