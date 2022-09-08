import numpy as np
import matplotlib.pyplot as plt
from labelSys.clib.pywrapper import Contour2Mask

contours0 = [(10, 90), (30, 20), (40, 70)]
contours1 = [(50, 10), (60, 40), (90, 50)]

contours = [[contours0], [contours1]]
dest_vals = [1, 2]

msk = Contour2Mask.contours2Mask(
    contours,
    dest_vals,
    150, 100
)

plt.imshow(msk)
plt.show()
