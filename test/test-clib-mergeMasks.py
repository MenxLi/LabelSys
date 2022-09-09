
import random
from typing import Tuple
import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt
from labelSys.clib.wrapper import MergeMasks
from labelSys.utils.utils_ import gray2rgb_
from monsoonToolBox.logtools import Timer


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

H = 1000
W = 2000

msks = []
for c in cs:
    msks.append(getCircleMsk(W, H, c, 50, 1))

def simpleOverlapNP(msks, colors):
    msk_new = np.zeros((H, W, 3), np.uint8)
    for msk,color in zip(msks, colors):
        msk_3c = gray2rgb_(msk)
        msk_new = (1-msk_3c)*msk_new + msk_3c * np.array(color)
    return msk_new

with Timer("Numpy"):
    out0 = simpleOverlapNP(msks, colors)

with Timer("Self"):
    msks = np.array(msks)
    out1 = MergeMasks.mergeBool2Color2D(msks, colors)

plt.subplot(121)
plt.imshow(out0)
plt.subplot(122)
plt.imshow(out1)
plt.show()
