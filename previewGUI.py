#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#
import vtk# {{{
from vtk.util import vtkImageImportFromArray
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QImage, QPixmap
import numpy as np
from configLoader import *
import utils.utils_ as F
import cv2 as cv
# }}}

class PreviewWindow(QWidget):# {{{
    def __init__(self, parent, imgs, masks, spacing = [1,1,1]):# {{{
        super().__init__(None, QtCore.Qt.WindowStaysOnTopHint)
        self.parent = parent
        if masks== None:
            self.close()
        self.imgs = imgs
        self.masks_raw = masks
        self.spacing = spacing
        self.masks = self.generateMasks(self.masks_raw)
        #self._center()

        self.initUI()
# }}}
    def initUI(self):# {{{
        pass
# }}}
    def _center(self):# {{{
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
# }}}
    def generateMasks(self, masks_raw):# {{{
        masks = []
        for mask_ in masks_raw:
            color = 1
            # mask = np.ma.zeros(self.imgs[0].shape[:2], np.uint8)
            mask = np.ma.zeros(list(mask_.values())[0].shape[:2], np.uint8)
            for label in mask_.keys():
                mask.mask = ~mask_[label]
                mask += np.array(color).astype(np.uint8)
                color += 1
            masks.append(mask.data)
        try:
            return np.array(masks)
        except ValueError:
            # incompatible shape among images
            # 3D preview will be unavaliable
            return masks
# }}}
# }}}

class Preview3DWindow(PreviewWindow):# {{{
    def __init__(self, parent, imgs, masks, spacing = [1,1,1]):# {{{
        super().__init__(parent, imgs, masks, spacing)
        self.show3D()
# }}}
    def initUI(self):# {{{
        self.vtk_widget = QVTKRenderWindowInteractor()
        self.ren_win = self.vtk_widget.GetRenderWindow()
        self.ren = vtk.vtkRenderer()
        self.ren_win.AddRenderer(self.ren)
        self.iren = self.ren_win.GetInteractor()
        self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

        self.setWindowTitle("Preview-3D")
        layout = QGridLayout()
        layout.addWidget(self.vtk_widget, 0, 1)
        self.setLayout(layout)

        self.ren_win.Render()
        self.iren.Initialize()
        self.iren.Start()
# }}}
    def show3D(self, smoothing = False):# {{{
        """
        https://github.com/lorensen/VTKExamples/blob/master/src/Python/Utilities/VTKWithNumpy.py
        https://lorensen.github.io/VTKExamples/site/Python/Medical/MedicalDemo1/
        https://lorensen.github.io/VTKExamples/site/Python/Visualization/ViewFrog/
        """
        self.r_masks = F.resampleSpacing(self.masks, self.spacing, [0.5,0.5,0.5])[0].astype(np.uint8)*2
        colors = vtk.vtkNamedColors()
        colors.SetColor("BkgColor", [51, 77, 102, 255])

        data_importer = vtk.vtkImageImport()
        data_string = self.r_masks.tostring()
        data_importer.CopyImportVoidPointer(data_string, len(data_string))
        data_importer.SetDataScalarTypeToUnsignedChar()
        data_importer.SetNumberOfScalarComponents(1)
        data_importer.SetDataExtent(0, self.r_masks.shape[1]-1, 0, self.r_masks.shape[2]-1, 0, self.r_masks.shape[0]-1)
        data_importer.SetWholeExtent(0, self.r_masks.shape[1]-1, 0, self.r_masks.shape[2]-1, 0, self.r_masks.shape[0]-1)

        surface_extractor = vtk.vtkMarchingCubes()
        surface_extractor.SetInputConnection(data_importer.GetOutputPort())
        surface_extractor.SetValue(0, 1)

        if smoothing:
            smoothingIterations = 5
            passBand = 0.001
            featureAngle = 60.0
            smoother = vtk.vtkWindowedSincPolyDataFilter()
            smoother.SetInputConnection(surface_extractor.GetOutputPort())
            smoother.SetNumberOfIterations(smoothingIterations)
            smoother.BoundarySmoothingOff()
            smoother.FeatureEdgeSmoothingOff()
            smoother.SetFeatureAngle(featureAngle)
            smoother.SetPassBand(passBand)
            smoother.NonManifoldSmoothingOn()
            smoother.NormalizeCoordinatesOn()
            smoother.Update()

            normals = vtk.vtkPolyDataNormals()
            normals.SetInputConnection(smoother.GetOutputPort())
            normals.SetFeatureAngle(featureAngle)

            stripper = vtk.vtkStripper()
            stripper.SetInputConnection(normals.GetOutputPort())
        else:
            stripper = vtk.vtkStripper()
            stripper.SetInputConnection(surface_extractor.GetOutputPort())

        surface_mapper = vtk.vtkPolyDataMapper()
        surface_mapper.SetInputConnection(stripper.GetOutputPort())
        surface_mapper.ScalarVisibilityOff()

        colors.SetColor("SurfaceColor", [255, 125, 64, 255])
        surface = vtk.vtkActor()
        surface.SetMapper(surface_mapper)
        surface.GetProperty().SetDiffuseColor(colors.GetColor3d("SurfaceColor"))

        # An outline provides context around the data.
        ouline_data = vtk.vtkOutlineFilter()
        ouline_data.SetInputConnection(data_importer.GetOutputPort())

        map_outline = vtk.vtkPolyDataMapper()
        map_outline.SetInputConnection(ouline_data.GetOutputPort())

        outline = vtk.vtkActor()
        outline.SetMapper(map_outline)
        outline.GetProperty().SetColor(colors.GetColor3d("Black"))

        self.ren.AddActor(outline)
        self.ren.AddActor(surface)
        self.ren.ResetCamera()
        self.ren.SetBackground(colors.GetColor3d("BkgColor"))
# }}}
    def __show3D_(self):# {{{
        self.r_masks = F.resampleSpacing(self.masks, self.spacing)[0].astype(np.uint8)

        colors = vtk.vtkNamedColors()
        data_importer = vtk.vtkImageImport()
        data_string = self.r_masks.tostring()
        data_importer.CopyImportVoidPointer(data_string, len(data_string))
        data_importer.SetDataScalarTypeToUnsignedChar()
        data_importer.SetNumberOfScalarComponents(1)
        data_importer.SetDataExtent(0, self.r_masks.shape[1]-1, 0, self.r_masks.shape[2]-1, 0, self.r_masks.shape[0]-1)
        data_importer.SetWholeExtent(0, self.r_masks.shape[1]-1, 0, self.r_masks.shape[2]-1, 0, self.r_masks.shape[0]-1)

        alphaChannelFunc = vtk.vtkPiecewiseFunction()
        alphaChannelFunc.AddPoint(0, 0.0)
        for i in range(len(LABELS)):
            value = (i+1)*1
            alphaChannelFunc.AddPoint(value, 1.0)

        gradientFunc = vtk.vtkPiecewiseFunction()
        gradientFunc.AddPoint(0, 0.0)
        gradientFunc.AddPoint(1, 1.0)
        gradientFunc.AddPoint(5, 1.0)

        colorFunc = vtk.vtkColorTransferFunction()
        for i in range(len(LABELS)):
            value = (i+1)*1
            colorFunc.AddRGBPoint(value, *LBL_COLORS[i])
            #colorFunc.AddRGBPoint(value, 1.0, 0.0, 0.0)

        volume_property = vtk.vtkVolumeProperty()
        volume_property.SetColor(colorFunc)
        volume_property.SetScalarOpacity(alphaChannelFunc)
        volume_property.SetGradientOpacity(gradientFunc)
        volume_property.SetInterpolationTypeToLinear()
        volume_property.ShadeOn()
        volume_property.SetAmbient(0.4)
        volume_property.SetDiffuse(0.6)
        volume_property.SetSpecular(0.2)


        volume_mapper = vtk.vtkFixedPointVolumeRayCastMapper()
        volume_mapper.SetInputConnection(data_importer.GetOutputPort())

        volume = vtk.vtkVolume()
        volume.SetMapper(volume_mapper)
        volume.SetProperty(volume_property)

        self.ren.SetBackground(colors.GetColor3d("MistyRose"))
        self.ren.AddVolume(volume)

        self.ren.ResetCamera()
        self.ren_win.Render()
# }}}
# }}}

class Preview2DWindow(PreviewWindow):# {{{
    def __init__(self, parent, imgs, masks, curr_slice_id = 0, spacing = [1,1,1], magnification = 1):# {{{
        """
        - parent: mainwindow object
        """
        super().__init__(parent, imgs, masks, spacing)

        self.slice_id = curr_slice_id
        self.mag = magnification
        self.lbl_color = dict()
        for lbl_id_ in range(len(LABELS)):
            self.lbl_color[lbl_id_+1] = [int(i*255) for i in LBL_COLORS[lbl_id_]]

        self._updatePanel()
# }}}
    def initUI(self):# {{{
        self.setWindowTitle("Preview-2D")
        self.lbl_im = QLabel(self)
        self.lbl_txt = QLabel()

        layout = QVBoxLayout()
        layout.addWidget(self.lbl_txt)
        layout.addWidget(self.lbl_im)
        self.setLayout(layout)
# }}}
    def nextSlice(self):# {{{
        self.slice_id = min(self.slice_id +1, len(self.imgs)-1)
        self._updatePanel()
# }}}
    def prevSlice(self):# {{{
        self.slice_id = max(self.slice_id -1, 0)
        self._updatePanel()
# }}}
    def updateInfo(self, masks, curr_slice_id):# {{{
        self.slice_id = curr_slice_id
        self.masks = self.generateMasks(masks)
        self._updatePanel()
# }}}
    def _updatePanel(self):# {{{
        self.__updateImg()
        self.__updateText()
# }}}
    def __updateText(self):# {{{
        self.lbl_txt.setText("Slice: {}/{}".format(self.slice_id+1, len(self.imgs)))
# }}}
    def __updateImg(self):# {{{
        im = self.__generateImg()
        height, width, channel = im.shape
        byte_per_line = 3*width
        qimg = QImage(im.data, width, height, byte_per_line, QImage.Format_RGB888)
        self.lbl_im.setPixmap(QPixmap(qimg))
# }}}
    def __generateImg(self):# {{{
        mask = self.masks[self.slice_id]
        im = self.imgs[self.slice_id].copy()
        im = F.map_mat_255(im)
        for key, color in self.lbl_color.items():
            mask_ = mask == key
            im = F.overlap_mask(im, mask_, color, alpha = 0.4)
        return cv.resize(im, None, fx = self.mag, fy = self.mag, interpolation = cv.INTER_NEAREST)
# }}}
    #==============Event Handler================
    def wheelEvent(self, event):# {{{
        modifier = QtWidgets.QApplication.keyboardModifiers()
        if event.angleDelta().y() < 0:
            if modifier == QtCore.Qt.ControlModifier:
                pass
            else:
                self.prevSlice()
        else:
            if modifier == QtCore.Qt.ControlModifier:
                pass
            else:
                self.nextSlice()
# }}}
# }}}
