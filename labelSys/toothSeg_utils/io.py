import pickle, os, copy
from typing import TypedDict, List, Tuple, Union
import numpy as np

Number = Union[int, float]
PT = Tuple[Number, Number]
#  PT4 = Tuple[PT, PT, PT, PT]
PT4 = np.ndarray
PT4_OPT = Union[PT4, None]

class ResizeData(TypedDict):
    ori_imgs: List[np.ndarray]
    crop_coords: List[PT4_OPT]

class ResizeImageRecord:
    def __init__(self):
        self._data: ResizeData

    def init(self, ori_imgs: List[np.ndarray]):
        num = len(ori_imgs)
        self._data = {
            "ori_imgs": copy.deepcopy(ori_imgs),
            "crop_coords": [None for _ in range(num)]
        }

    def flush(self):
        del self._data

    @property
    def data(self):
        return self._data

    def setOriIm(self, idx: int, img: np.ndarray):
        self._data["ori_imgs"][idx] = img

    def setCoords(self, idx:int, coords: PT4_OPT):
        self._data["crop_coords"][idx] = coords

    def export(self, pth: str):
        assert pth.endswith(".pkl"), "Path should endswith pkl"
        with open(pth, "wb") as fp:
            pickle.dump(self.data, fp)

    def loadFromFile(self, pth: str):
        assert pth.endswith(".pkl"), "Path should endswith pkl"
        with open(pth, "rb") as fp:
            self._data = pickle.load(fp)
