#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#
# import{{{
from typing import List, Tuple
from vtkmodules.vtkCommonCore import \
    VTK_INT, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_INT, VTK_UNSIGNED_SHORT, \
    VTK_UNSIGNED_LONG, VTK_CHAR, VTK_SHORT, VTK_FLOAT, VTK_DOUBLE, VTK_UNSIGNED_LONG_LONG, VTK_LONG_LONG, \
    VTK_SIZEOF_LONG, VTK_LONG
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkRenderingCore import vtkRenderer, vtkImageActor, vtkTextActor, vtkActor, vtkPolyDataMapper
from vtkmodules.vtkCommonDataModel import vtkPolyData, vtkCellArray, vtkImageData
from vtkmodules.vtkInteractionWidgets import vtkContourWidget, vtkOrientedGlyphContourRepresentation
from vtkmodules.vtkFiltersSources import vtkLineSource
from vtkmodules.util import numpy_support
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtWidgets import *
import numpy as np
import cv2 as cv
from .utils import utils_ as F
from .configLoader import *
import os, sys
from .vtkInteractionStyle import InteractionStyleBase, PtContourInteractorStyle, DrawContourInteractorStyle
from .coreWidgets import WidgetCore


class VtkWidget(QVTKRenderWindowInteractor, WidgetCore):
    if sys.platform == "win32":
        _TEMP_FOLDER_NAME = ".TempDir"
    else:
        _TEMP_FOLDER_NAME = ".TempDir"
    _PAR_PATH = os.path.abspath(os.path.join(__file__, os.pardir))
    TEMP_DIR = os.path.join(_PAR_PATH, _TEMP_FOLDER_NAME)       # temporary directory to save image
    def __init__(self, frame, parent):
        super().__init__(frame)

        # Create temporary directory for color image storage,
        # The color image will be stored in this directory then be read by VTK
        # if not os.path.exists(self.TEMP_DIR):
            # print("Temporary directory created: ", self.TEMP_DIR)
            # os.mkdir(self.TEMP_DIR)

        self.master = frame
        self.parent = parent
        self.setMainWindow(parent)

        layout = QGridLayout()
        layout.addWidget(self, 0, 0)
        self.master.setLayout(layout)

        self.ren_win = self.GetRenderWindow()
        self.ren = vtkRenderer()
        self.camera_set = False
        self.ren_win.AddRenderer(self.ren)
        self.iren = self.ren_win.GetInteractor()
        self.ren_win.Render()
        self.iren.Initialize()

        # Attribute
        self.colors = vtkNamedColors()
        self.contours = []

        self.setStyleAuto()
        self.style: InteractionStyleBase
    
    def setStyleAuto(self):
        is_draw = self.__isDraw()
        # change key binding
        if is_draw:
            self.setStyle(DrawContourInteractorStyle)
        else:
            self.setStyle(PtContourInteractorStyle)
        self.reInitStyle()

        # If using DrawContourInteractorStyle
        if hasattr(self.getMainWindow(), "curr_lbl"):
            if self.getMainWindow().curr_lbl in self.getMainWindow().config["labels"]:
                lbl_idx = self.getMainWindow().config["labels"].index(self.getMainWindow().curr_lbl)
                self.setStyleSampleStep(self.getMainWindow().config["label_steps"][lbl_idx])
    
    def setStyle(self, style_: InteractionStyleBase):
        if hasattr(self, "style"):
            try:
                del self.style
            except AttributeError: pass
        self.style = style_(widget = self)
        self.style.SetDefaultRenderer(self.ren)
        self.iren.SetInteractorStyle(self.style)

    
    def readNpArray(self, arr, txt = "", clear_canvas = True):
        """
        Read numpy array and display in the window
        - txt: text to be shown on the screen
        """
        if clear_canvas:
            self.__clearCanvas()

        self.im = arr
        # if len(self.im.shape) == 3 and self.im.shape[2] == 3:
            # # read from image
            # #  im_path = os.path.join(self.TEMP_DIR, "im.jpg")
            # im_path = os.path.join(self.TEMP_DIR, "im.png")
            # cv.imwrite(im_path, cv.cvtColor(self.im, cv.COLOR_RGB2BGR))
            # #  im_reader = vtk.vtkJPEGReader()
            # im_reader = vtk.vtkPNGReader()
            # im_reader.SetFileName(im_path)
            # self.actor = vtk.vtkImageActor()
            # self.actor.GetMapper().SetInputConnection(im_reader.GetOutputPort())
            # 
        # elif len(self.im.shape) == 2:
            #===============Update Image======================
            # # https://gitlab.kitware.com/vtk/vtk/blob/741fffbf6490c34228dfe437f330d854b2494adc/Wrapping/Python/vtkmodules/util/vtkImageImportFromArray.py
            # # import from numpy array
            # importer = vtkImageImportFromArray()
            # importer.SetArray(arr)
            # importer.Update()

            # # flip image along y axis
            # flipY_filter = vtk.vtkImageFlip()
            # flipY_filter.SetFilteredAxis(1)
            # flipY_filter.SetInputConnection(importer.GetOutputPort())
            # flipY_filter.Update()

            # self.actor = vtk.vtkImageActor()
            # self.actor.GetMapper().SetInputConnection(flipY_filter.GetOutputPort())
        img_vtk = numpyArrayAsVtkImageData(self.im)
        self.actor = vtkImageActor()
        self.actor.GetMapper().SetInputData(img_vtk)
            
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
        self.updateText(txt)

    def updateText(self, txt: str):
        if txt is None:
            return
        try:
            self.ren.RemoveActor(self.t_actor)
            self.ren.RemoveActor(self.t_actor_label)
        except: pass
        self.t_actor = vtkTextActor()
        self.t_actor.SetInput(txt)
        txtprop = self.t_actor.GetTextProperty()
        txtprop.SetFontFamilyToCourier()
        txtprop.SetFontSize(12)
        self.t_actor.SetDisplayPosition(5,5)
        self.ren.AddActor(self.t_actor)

        # show label
        self.t_actor_label = vtkTextActor()
        self.t_actor_label.SetInput(self.parent.curr_lbl)
        txtprop_label = self.t_actor_label.GetTextProperty()
        txtprop_label.SetFontFamilyToArial()
        txtprop_label.BoldOn()
        txtprop_label.SetColor(0,1,0)
        txtprop_label.SetFontSize(32)
        #  txtprop_label.ShadowOn()
        #  txtprop_label.SetShadowOffset(4, 4)
        win_size = self.ren_win.GetSize()
        # self.t_actor_label.SetDisplayPosition(5,70)
        self.t_actor_label.SetDisplayPosition(5,win_size[1]-40)
        self.ren.AddActor(self.t_actor_label)

        self.ren_win.Render()

    def resetCamera(self):
        self.ren.ResetCamera()
        self.ren_win.Render()
        
    def contourWidget(self, color=[1, 0, 0], contourWidgetEndInteraction=None):
        """Create a template widget for drawing contours"""
        contourRep = vtkOrientedGlyphContourRepresentation()
        contourRep.GetLinesProperty().SetColor(color)

        contour_widget = vtkContourWidget()
        contour_widget.SetInteractor(self.iren)
        contour_widget.SetRepresentation(contourRep)
        contour_widget.AddObserver('EndInteractionEvent', contourWidgetEndInteraction)
        contour_widget.AddObserver('WidgetValueChangedEvent', contourWidgetEndInteraction)

        return contour_widget

    def constructContour(self, pts, open_curve = None, save = True, tmp_contour = False):
        """
        Default behaviour:
        - LeftButtonPressEvent - triggers a Select event
        - MouseMoveEvent - triggers a Move event
        - LeftButtonReleaseEvent - triggers an EndSelect event
        - Delete key event - triggers a Delete event
        """
        if pts ==[]:
            return 1
        pd = vtkPolyData()
        points = vtkPoints()
        lines = vtkCellArray()
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
        if tmp_contour:
            return contour_widget
        self.contours.append(contour_widget)
        if save:
            # save on drawing contour but not save when loading contour with
            # self.loadContour
            self.__endInteraction(None, None)
        return contour_widget

    def loadContour(self, pts, open_curve):
        self.constructContour(pts, open_curve, save = False)
        self.style._reinitState()

    def drawLine(self, pt0, pt1, color = [0.5,1,1], lw = 4):
        line_source = vtkLineSource()
        line_source.SetPoint1(pt0)
        line_source.SetPoint2(pt1)
        line_source.Update()
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(line_source.GetOutputPort())
        actor = vtkActor()
        actor.GetProperty().SetColor(*color)
        actor.SetMapper(mapper)
        actor.GetProperty().SetLineWidth(lw)
        self.ren.AddActor(actor)
        self.ren_win.Render()
        return actor

    def reInitStyle(self):
        self.style._reinitState()

    def setStyleSampleStep(self, step = 1):
        if isinstance(self.style, DrawContourInteractorStyle):
            STEP_SHAPE_MODIFIER = 128
            step *= self.im.shape[0]/STEP_SHAPE_MODIFIER
            self.style._setSampleStep(step)

    def __endInteraction(self, obj, event):
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

    def __getFullCnt(self, contour_widget, img_shape):
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
        all_pts = np.rint(np.array(all_pts))
        if mode == "Close":
            cv_cnt = np.array([[arr] for arr in F.removeDuplicate2d(all_pts)])
            cv.fillPoly(mask, pts = [cv_cnt], color = 1)
        elif mode == "Open":
            cv_cnt = np.array([arr for arr in F.removeDuplicate2d(all_pts)])
            cv.polylines(mask,[cv_cnt],False,1)
        return mask

    # def __getBackNpCoord(self, x, y, img_shape):
        # """Get coordinate in (row, col)
        # - img_shape: (W, H)"""
        # return np.array([img_shape[1]-1-y, x])
# 
    def __getBackCvCoord(self, x, y, img_shape):
        """Get coordinate in (col, row)
        - img_shape: (W, H)"""
        return np.array([x, img_shape[0]-1-y])

    def __clearCanvas(self):
        self.contours = []
        self.ren.RemoveAllViewProps()
        self.contours = []

    def __isOpen(self):
        return self.parent.check_crv.isChecked()

    def __isDraw(self):
        return self.parent.check_draw.isChecked()
    
    def mouseDoubleClickEvent(self, *args):
        self.style.doubleClickEvent(*args)



def numpyArrayAsVtkImageData(source_numpy_array):
    """
    :param source_numpy_array: source array with 2-3 dimensions. If used, the third dimension represents the channel count.
    Note: Channels are flipped, i.e. source is assumed to be BGR instead of RGB (which works if you're using cv2.imread function to read three-channel images)
    Note: Assumes array value at [0,0] represents the upper-left pixel.
    :type source_numpy_array: np.ndarray
    :return: vtk-compatible image, if conversion is successful. Raises exception otherwise
    :rtype vtk.vtkImageData
    """
    # https://stackoverflow.com/questions/45395269/numpy-uint8-t-arrays-to-vtkimagedata

    if len(source_numpy_array.shape) > 2:
        channel_count = source_numpy_array.shape[2]
    else:
        channel_count = 1

    output_vtk_image = vtkImageData()
    output_vtk_image.SetDimensions(source_numpy_array.shape[1], source_numpy_array.shape[0], channel_count)

    vtk_type_by_numpy_type = {
        np.uint8: VTK_UNSIGNED_CHAR,
        np.uint16: VTK_UNSIGNED_SHORT,
        np.uint32: VTK_UNSIGNED_INT,
        np.uint64: VTK_UNSIGNED_LONG if VTK_SIZEOF_LONG == 64 else VTK_UNSIGNED_LONG_LONG,
        np.int8: VTK_CHAR,
        np.int16: VTK_SHORT,
        np.int32: VTK_INT,
        np.int64: VTK_LONG if VTK_SIZEOF_LONG == 64 else VTK_LONG_LONG,
        np.float32: VTK_FLOAT,
        np.float64: VTK_DOUBLE
    }
    vtk_datatype = vtk_type_by_numpy_type[source_numpy_array.dtype.type]

    source_numpy_array = np.flipud(source_numpy_array)

    # Note: don't flip (take out next two lines) if input is RGB.
    # Likewise, BGRA->RGBA would require a different reordering here.
    # if channel_count > 1:
        # source_numpy_array = np.flip(source_numpy_array, 2)

    depth_array = numpy_support.numpy_to_vtk(source_numpy_array.ravel(), deep=True, array_type = vtk_datatype)
    depth_array.SetNumberOfComponents(channel_count)
    output_vtk_image.SetSpacing([1, 1, 1])
    output_vtk_image.SetOrigin([-1, -1, -1])
    output_vtk_image.GetPointData().SetScalars(depth_array)

    output_vtk_image.Modified()
    return output_vtk_image