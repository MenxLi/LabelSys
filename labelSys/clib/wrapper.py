
from typing import List, Tuple

import numpy as np

from . import _native

class Contour2Mask:
    """
    I found this method is slower than opencv in most situation
    except for small simple polygons 
    """
    @classmethod
    def contours2Mask(cls, contours: List[List[List[Tuple[int, int]]]], dest_vals: List[int], im_h: int, im_w: int):
        return _native.cnts2msk(contours, dest_vals, im_h, im_w)

        

class MergeMasks:
    @classmethod
    def mergeBool2Color2D(cls, masks: np.ndarray, colors: List[Tuple[int, int, int]]) -> np.ndarray:
        """
         - masks: bool (uint8) np.ndarray of dimension (n, H, W)
         return uint8 3 channel image (H, W, 3)
        """
        masks = np.ascontiguousarray(masks, dtype=np.uint8)
        return _native.mergeBool2Color2D(masks, colors)
