
import random
from typing import Tuple, List
import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt
from labelSys.clib.wrapper import MergeMasks
from labelSys.utils.utils_ import gray2rgb_
from monsoonToolBox.logtools import Timer
import numba


def getCircleMsk(im_w, im_h, center: Tuple[int, int], radius: float, val: int):
    msk = np.zeros((im_h, im_w), np.uint8)
    cv.circle(msk, center, radius, val, -1)
    return msk

cs = []
colors = []

for i in range(5):
    for j in range(5):
        cs.append((i*200 + 100, j*100 + 50))
        
        color = [random.randint(50, 220) for _ in range(3) ]
        colors.append(color)

H = 1000//2
W = 2000//2

msks = []
for c in cs:
    msks.append(getCircleMsk(W, H, c, 50, 1))

def simpleOverlapNP(msks, colors):
    msk_new = np.zeros((H, W, 3), np.uint8)
    for msk,color in zip(msks, colors):
        msk_3c = gray2rgb_(msk)
        msk_new = (1-msk_3c)*msk_new + msk_3c * np.array(color)
    return msk_new

def overlapPyLoop(msks: List[np.ndarray], colors: List[Tuple[int, int, int]]): 
    msks_np = np.array(msks, np.uint8)
    colors_np = np.array(colors, np.uint8)

    assert len(msks_np.shape) == 3

    N, H, W = msks_np.shape
    dst = np.zeros((H, W, 3), np.uint8)

    for row in range(H):
        for col in range(W):

            for m in range(N):
                if msks_np[m][row][col] == 1:
                    dst[row][col] = colors_np[m]
                    break
    return dst

def overlapPyLoopJIT(msks: List[np.ndarray], colors: List[Tuple[int, int, int]]): 
    msks_np = np.array(msks, np.uint8)
    colors_np = np.array(colors, np.uint8)

    assert len(msks_np.shape) == 3

    N, H, W = msks_np.shape
    dst = np.zeros((H, W, 3), np.uint8)

    @numba.jit(nopython=True)
    def loopMsk(msks_np, colors_np, dst, N, H, W):
        for row in range(H):
            for col in range(W):

                for m in range(N):
                    if msks_np[m][row][col] == 1:
                        dst[row][col] = colors_np[m]
                        break
    loopMsk(msks_np, colors_np, dst, N, H, W)
    return dst



with Timer("Python-loop"):
    out0 = overlapPyLoop(msks, colors)

with Timer("Numpy"):
    out1 = simpleOverlapNP(msks, colors)

with Timer("JIT"):
    out2 = overlapPyLoopJIT(msks, colors)

with Timer("C-loop"):
    msks = np.array(msks)
    out3 = MergeMasks.mergeBool2Color2D(msks, colors)

plt.subplot(141)
plt.imshow(out0)
plt.subplot(142)
plt.imshow(out1)
plt.subplot(143)
plt.imshow(out2)
plt.subplot(144)
plt.imshow(out3)
plt.show()
