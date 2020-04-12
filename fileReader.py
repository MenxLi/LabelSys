from glob import glob
import numpy as np
import pydicom
import os
import scipy.ndimage
from pathlib import Path
import cv2 as cv
import utils_ as F

# Pydicom reading reference: https://pydicom.github.io/pydicom/stable/tutorials/dataset_basics.html

class LoaderBase:
    """
    Base class for different file type readers
    Define APIs
    Methods should be overwritten in child classes
    """
    # default attribute if designated file type doesn't contain them
    SOPInstanceUID_base = "-"
    spacing_base = (1, 1, 1)
    entry_base = "Unknown_entry"
    def __init__(self, file_path):
        self.path = file_path
        self.series = dict()
    def getSeriesImg(self, entry = None, series = None):
        """
        - entry: image series name to load - str
        - series: dictionary to classify images based on entries - dict
        return data
        => data = { "Images": 2D_array, "SOPInstanceUIDs": list[str], "Spacing": (f,f,f) }
        """
        if series == None and self.series == dict():
            raise Exception("Series haven't been set")
    def getEntries(self):
        """
        Return all entries' name
        """
        return self.series.keys()

class DicomLoader(LoaderBase):
    """Read single patient DICOM file"""
    def __init__(self, path):
        """
        - path: folder contain multiple dicom files, each dicom contain 2D image
        """
        super().__init__(path)
        self.patient = None
        self.load()
    def loadScan(self, patient_path):
        """
        @ patient_path: Folder contains image for a single patient, The folder must contain only DICOM file
        return a list of pydicom.dataset.FileDataset instance
        """
        dicom_path = glob(patient_path + '/*')
        slices = []
        for path_ in dicom_path:
            if os.path.isfile(path_) and Path(path_).stem != "DIOOMDIR":
                try:
                    s = pydicom.read_file(path_)
                    slices.append(s)
                except: pass
        #slices = [pydicom.read_file(s, force=True) for s in dicom_path]
        slices.sort(key = lambda x: int(x.InstanceNumber))
        return slices
    def creatSeries(self, slices):
        """
        @ slices: a list of FileDataset
        Re-classify the data of a patient into \'SeriesDiscription\'
        Return a dictionary of classified FileDataset with SeriesDiscription being the entry
        """
        series = {}
        for slice in slices:
            seriesDescript = slice["SeriesDescription"].value
            try:
                series[seriesDescript].append(slice)
            except KeyError:
                series[seriesDescript] = [slice]
        return series
    def getEntries(self):
        """Return series entries"""
        return self.series.keys()
    def getSeriesImg(self, entry, series = None):
        """
        @ series: a dictionary of classified FileDataset
        @ entry: entry for the series
        """
        super().getSeriesImg(entry, series)
        if series == None and self.series != dict():
            series = self.series
        scan = series[entry]
        images = np.stack([s.pixel_array for s in scan])
        SOPInstanceUIDs = [s['SOPInstanceUID'].value for s in series[entry]]
        spacing = [scan[0].SliceThickness, *scan[0].PixelSpacing]
        spacing = [float(s) for s in spacing]
        data = {
                "Images": images,
                "SOPInstanceUIDs": SOPInstanceUIDs,
                "Spacing": spacing
                }
        return data
    def resampleSpacing(self, imgs, old_spacing, new_spacing = [1,1,1]):
        spacing = np.array(old_spacing)
        resize_factor = spacing / new_spacing

        new_real_shape = imgs.shape * resize_factor
        new_shape = np.round(new_real_shape)
        real_resize_factor = new_shape / imgs.shape
        new_spacing = spacing / real_resize_factor
        imgs = scipy.ndimage.interpolation.zoom(imgs, real_resize_factor)

        return imgs, new_spacing
    def load(self):
        self.patient = self.loadScan(self.path)
        self.series = self.creatSeries(self.patient)

class GeneralImageLoader(LoaderBase):
    """
    Read Jpeg, png, or other type of images
    refer to cv2.imread for supported type
    https://docs.opencv.org/4.2.0/d4/da8/group__imgcodecs.html
    """
    def __init__(self, path):
        """
        - path: directory that contain multiple images
        """
        super().__init__(path)
        self.__readImages()
        return
    def __readImages(self):
        arr = []
        p = sorted([path_ for path_ in os.listdir(self.path)])
        abs_paths = [ os.path.join(self.path, path_) for path_ in p]
        for path_ in  abs_paths:
            try:
                im = cv.imread(path_)
                if F.img_channel(im) != 1:
                    arr.append(im[:, :, 0])
                else: arr.append(im)
            except: pass
        if arr != []:
            self.series[self.entry_base] = arr
        return
    def getEntries(self):
        return super().getEntries()
    def getSeriesImg(self, entry = None, series = None):
        super().getSeriesImg(entry, series)
        if series == None and self.series != dict():
            series = self.series
        images = series[entry]
        data = {
            "Images": images,
            "SOPInstanceUIDs": [self.SOPInstanceUID_base]*len(images),
            "Spacing": self.spacing_base
        }
        return data

class GeneralVideoLoader(LoaderBase):
    pass

class FolderLoader:
    """
    Load data folder
    Data type has to be specified when loading
    Supported file types:
        DICOM
        Jpeg, png, tif, bmp, ...
        Mpeg4, ...
    """
    def __init__(self, parent_dir, mode = 0):
        """
        - parent_dir: directory to store data
        - mode:
            0 - DICOM (default)
            1 - Image
            2 - Video
        """
        self.paths = []
        self.parent_dir = parent_dir # folder that contains folders of dicom file
        self.curr_patient = None        # Loader class
        self.ptr = 0
        self.__mode = mode
        for i in os.listdir(parent_dir):
            curr_path = os.path.join(parent_dir, i)
            if mode == 0 or mode == 1:
                # DICOM or image files should be put in subfolders
                if os.path.isdir(curr_path):
                    self.paths.append(curr_path)
            elif mode == 2:
                # Video can be place as single file
                if os.path.isfile(curr_path):
                    self.paths.append(curr_path)
        self.loadData(self.ptr)
    def loadData(self, id):
        loaderCases = {
            0: DicomLoader,
            1: GeneralImageLoader
        }
        self.curr_patient = loaderCases[self.__mode](self.paths[id])

    def next(self):
        if self.ptr < len(self.paths)-1:
            self.ptr += 1
            self.loadData(self.ptr)
            return 1
        else: return 0
    def previous(self):
        if self.ptr > 0:
            self.ptr -= 1
            self.loadData(self.ptr)
            return 1
        else: return 0
    def getPath(self):
        return self.paths[self.ptr]
