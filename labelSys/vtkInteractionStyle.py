# import vtk
import numpy as np
from typing import List, Tuple, Union
import time
from vtkmodules.vtkRenderingCore import vtkPropPicker
from vtkmodules.vtkInteractionWidgets import vtkContourWidget
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleImage


class InteractionStyleBase(vtkInteractorStyleImage):
    HEIGHT = 0 # Z/W position of the curve
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.picker = vtkPropPicker()

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

    def _getMousePos(self) -> Tuple[float, float, float]:
        click_pos = self.GetInteractor().GetEventPosition()
        self.picker.Pick(*click_pos, 0, self.GetDefaultRenderer())
        pos = self.picker.GetPickPosition()
        #return pos
        return (pos[0], pos[1], self.HEIGHT)

    def _reinitState(self):
        """Should be called when going to different slice"""
        raise NotImplementedError

    def forceDrawing(self):
        """Should be called when add another contour/bbox"""
        raise NotImplementedError
    
    def mouseMoveEvent(self, obj, event):
        pass

    def leftButtonPressEvent(self, obj, event):
        pass

    def leftButtonReleaseEvent(self, obj, event):
        pass

    def doubleClickEvent(self, *args, **kwargs):
        # Will be called by Qt
        pass

    def keyPressEvent(self, obj, event):
        key = self.widget.iren.GetKeySym()
        if key == "v": # Zoom in
            self.OnMouseWheelForward()
        elif key == "c": # Zoom out
            self.OnMouseWheelBackward()
        elif key == "r": # Reset camera
            self.widget.resetCamera()

class PtContourInteractorStyle(InteractionStyleBase):
    def __init__(self, widget):
        super().__init__(widget)
        self.pts: List[Tuple[float, float, float]] = []
        self.tmp_cnt: Union[None, vtkContourWidget] = None
        self._reinitState()
    
    def leftButtonPressEvent(self, obj, event):
        if self.__mode == "Drawing":
            if self.tmp_cnt:
                cnt_pts = self.__getPtsInCnt(self.tmp_cnt)
                if cnt_pts[0] == cnt_pts[1]:
                    cnt_pts.pop(0)
                self.pts = cnt_pts
            self.pts.append(self._getMousePos())
            self.__removeTmpCnt()
            if len(self.pts) == 1:
                self.tmp_cnt = self.widget.constructContour(self.pts*2, open_curve = True, tmp_contour = True)
            else:
                self.tmp_cnt = self.widget.constructContour(self.pts, open_curve = True, tmp_contour = True)
            # self.tmp_cnt.SetFollowCursor(True)
            # self.tmp_cnt.Render()

    def doubleClickEvent(self, *args, **kwargs):
        self.__removeTmpCnt()
        if len(self.pts) > 1:
            self.widget.constructContour(self.pts)
            self._reinitState()
        
    def forceDrawing(self):
        self.__mode = "Drawing"

    def _reinitState(self):
        if self.widget.contours == []:
            self.__mode = "Drawing"
        else: self.__mode = "Revising"
        self.pts = []
        self.__removeTmpCnt()
    
    def __removeTmpCnt(self):
        if self.tmp_cnt:
            del self.tmp_cnt
            # self.widget.ren.RemoveActor(self.tmp_cnt)
            self.tmp_cnt = None
    
    def __getPtsInCnt(self, cnt: vtkContourWidget) -> List[Tuple[float, float, float]]:
        rep = cnt.GetContourRepresentation()
        cnt_pts = []
        point = np.empty(3)
        for pt_id in range(rep.GetNumberOfNodes()):
            rep.GetNthNodeWorldPosition(pt_id, point)
            cnt_pts.append(tuple(point))
        return cnt_pts

class DrawContourInteractorStyle(InteractionStyleBase):
    """Interactor style for vtk widget"""
    def __init__(self,widget):
        super().__init__(widget=widget)
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
            if now_pt == (0.0, 0.0, 0):
                # the cursor move out of the image
                now_pt = self.__prev_pt
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
                full_curve += [[pt[0], pt[1], self.HEIGHT] for pt in interp_pts[1:] ]
            full_curve = self.__removeDuplicate2d(full_curve)
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

    def forceDrawing(self):
        self.__mode = "Drawing"

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
        epsilon = 1e-6
        x_t = np.gradient(curve[:, 0])
        y_t = np.gradient(curve[:, 1])
        xx_t = np.gradient(x_t)
        yy_t = np.gradient(y_t)
        curvature = np.abs(xx_t * y_t - x_t * yy_t) / (x_t * x_t + y_t * y_t + epsilon)**2.5
        kernel = np.array([0.1, 0.15, 0.5, 0.15, 0.1])

        curvature = np.convolve(curvature, kernel, mode = "same")
        curvature = np.abs(curvature)

        # None maximum compression
        window_width = 5
        for i in range(0, len(curvature), window_width):
            clip = curvature[i:i+window_width]
            max_idx = np.argmax(clip)
            clip *= np.eye(len(clip))[max_idx]
            curvature[i:i+window_width] = clip

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

    def _setSampleStep(self, step):
        self.sample_step = step

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

