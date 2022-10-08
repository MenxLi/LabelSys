#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#

from .labelReaderV2 import LabelSysReader, recursivelyFindLabelDir
from typing import Any
import numpy as np


def vtk2CvCoord(x_vtk, y_vtk, img_shape):
    """
    Get coordinate in (col, row)
    - img_shape: (H, W, ...)
    """
    return np.array([x_vtk+1, img_shape[0]-2-y_vtk])
