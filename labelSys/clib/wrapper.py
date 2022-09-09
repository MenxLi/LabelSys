
from typing import List, Tuple
import numpy as np
import ctypes
from sys import platform
import os

root_path = os.path.dirname(os.path.abspath(__file__))

if platform == "linux" or platform == "linux2":
    # linux
    dll_ext = ".so"
elif platform == "darwin":
    # OS X
    dll_ext = ".dylib"
elif platform == "win32":
    # Windows...
    dll_ext = ".dll"

def loadLibrary(lib_name: str):
    return ctypes.cdll.LoadLibrary(os.path.join(root_path, lib_name + dll_ext))

class Contour2Mask:
    """
    I found this method is slower than opencv in most situation
    except for small simple polygons 
    """
    clib = loadLibrary("contour2Mask")

    arr_t = ctypes.c_uint8
    coord_t = ctypes.c_int32
    len_t = ctypes.c_uint32

    arr_ptr = ctypes.POINTER(arr_t)
    coord_ptr = ctypes.POINTER(coord_t)
    len_ptr = ctypes.POINTER(len_t)

    @classmethod
    def contours2Mask(cls, contours: List[List[List[Tuple[int, int]]]], dest_vals: List[int], im_h: int, im_w: int):
        assert len(contours) == len(dest_vals)

        # Flatten contour
        _contours: List[List[Tuple[int, int]]] = []
        _contour_lens: List[int] = []
        _vals = []

        for contour, dest_val in zip(contours, dest_vals):
            for cnt in contour:
                _contours.append(cnt)
                _contour_lens.append(len(cnt)*2)
                _vals.append(dest_val)
        
        #  contours_np = np.array(_contours, dtype=np.uint32)
        contours_np = np.array([], dtype=np.int32)
        for c in _contours:
            contours_np = np.concatenate([contours_np, np.array(c, dtype=np.int32).ravel()])


        contour_lens_np = np.array(_contour_lens, dtype=np.uint32)
        dest_vals_np = np.array(_vals, dtype=np.uint8)


        msk = np.zeros((im_h, im_w), dtype = np.uint8)

        cls.clib.cnts2msk(
            msk.ctypes.data_as(cls.arr_ptr), cls.coord_t(im_h), cls.coord_t(im_w),
            contours_np.ravel().ctypes.data_as(cls.coord_ptr),
            cls.len_t(len(_contours)), contour_lens_np.ctypes.data_as(cls.len_ptr),
            dest_vals_np.ctypes.data_as(cls.arr_ptr)
        )

        return msk

        

class MergeMasks:
    clib = loadLibrary("mergeMasks")
    int_t = ctypes.c_int32
    arr_t = ctypes.c_uint8
    msk_t = ctypes.c_uint8

    @classmethod
    def mergeBool2Color2D(cls, masks: np.ndarray, colors: List[Tuple[int, int, int]]) -> np.ndarray:
        """
         - masks: bool (uint8) np.ndarray of dimension (n, H, W)
         return uint8 3 channel image (H, W, 3)
        """

        n_msks = masks.shape[0]
        H = masks.shape[1]
        W = masks.shape[2]

        dest = np.zeros([H, W, 3], np.uint8)
        if masks.dtype != np.uint8:
            masks = masks.astype(np.uint8)
        colors_np = np.array(colors, np.uint8)

        cls.clib.mergeBool2Color2D(
            dest.ravel().ctypes.data_as(ctypes.POINTER(cls.arr_t)),
            masks.ravel().ctypes.data_as(ctypes.POINTER(cls.msk_t)),
            colors_np.ravel().ctypes.data_as(ctypes.POINTER(cls.arr_t)),
            cls.int_t(H),
            cls.int_t(W),
            cls.int_t(n_msks)
        )

        return dest
