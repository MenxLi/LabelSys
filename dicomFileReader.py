from glob import glob
import numpy as np
import pydicom
import os

# Pydicom reading reference: https://pydicom.github.io/pydicom/stable/tutorials/dataset_basics.html

class DicomLoader:
    """Read single patient DICOM file"""
    def __init__(self, path):
        self.path = path
        self.patient = None
        self.series = None

        self.load()
    def loadScan(self, patient_path):
        """
        @ patient_path: Folder contains image for a single patient, The folder must contain only DICOM file
        return a list of pydicom.dataset.FileDataset instance
        """
        dicom_path = glob(patient_path + '/*')
        slices = [pydicom.read_file(s, force=True) for s in dicom_path]
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
        return images stack of a series of given entry
        """
        if series == None and self.series != None:
            series = self.series
        images = np.stack([s.pixel_array for s in series[entry]])
        SOPInstanceUIDs = [s['SOPInstanceUID'].value for s in series[entry]]
        return (images, SOPInstanceUIDs)

    def load(self):
        self.patient = self.loadScan(self.path)
        self.series = self.creatSeries(self.patient)

class FolderLoader:
    """load a folder of different patients' MRI images"""
    def __init__(self, parent_dir):
        self.paths = []
        self.parent_dir = parent_dir # folder that contains folders of dicom file
        self.curr_patient = None
        self.ptr = 0
        for i in os.listdir(parent_dir):
            curr_path = os.path.join(parent_dir, i)
            if os.path.isdir(curr_path):
                self.paths.append(curr_path)
        self.loadDicom(self.ptr)
    def loadDicom(self, id):
        self.curr_patient = DicomLoader(self.paths[id])
    def next(self):
        if self.ptr < len(self.paths)-1:
            self.ptr += 1
            self.loadDicom(self.ptr)
            return 1
        else: return 0
    def previous(self):
        if self.ptr > 0:
            self.ptr -= 1
            self.loadDicom(self.ptr)
            return 1
        else: return 0
    def get_path(self):
        return self.paths[self.ptr]



