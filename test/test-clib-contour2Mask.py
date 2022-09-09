import numpy as np
import matplotlib.pyplot as plt
from labelSys.clib.wrapper import Contour2Mask

from monsoonToolBox.logtools import Timer
import cv2

contours0 = np.array([(50, 90), (40, 70), (10, 90), ]) * 3
contours1 = np.array([(50, 10), (60, 40), (85, 60), (85, 50)]) * 3
contours2 = np.array([(70, 120), (85, 80), (95, 95), (90, 100), (88, 90), (80, 110)]) *3

IM_W = 400
IM_H = 1000

theta = np.linspace(0, 2*np.pi, 15)
sin_theta = np.sin(theta)
cos_theta = np.cos(theta)

xs = sin_theta*200 + 201
ys = cos_theta*200 + 201

contours3 = np.stack((xs,ys), axis = 1).astype(int)

contours = [[contours0], [contours1], [contours2], [contours3]]
#  contours = contours + contours

dest_vals = [i for i in range(len(contours))]


def cvDrawContours(cnts, dest_vals, im_h, im_w):
    msk = np.zeros((im_h, im_w), dtype=np.uint8)

    for cnt, val in zip(cnts, dest_vals):
        cv2.drawContours(msk, cnt, -1, val, -1)

    return msk

#  contours, hierarchy = cv2.findContours(msk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

#  print(contours[0].shape)

def toCVContours(cnts):
    new_cnts = []
    for cnt in cnts:
        cnt = np.array(cnt, dtype = np.int32)
        new_cnts.append(cnt)
    return new_cnts

cnts = toCVContours(contours)

with Timer("CV"):
    msk0 = cvDrawContours(cnts, dest_vals, IM_H, IM_W)
with Timer("Self"):
    msk1 = Contour2Mask.contours2Mask(
        contours,
        dest_vals,
        IM_H, IM_W
    )

plt.subplot(121)
plt.imshow(msk0)
plt.subplot(122)
plt.imshow(msk1)
plt.show()
