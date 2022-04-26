import cv2 as cv
import numpy as np

def calcAffineMatrix(ori_coords, new_coords):
    ori_coords = np.array(ori_coords[:3], np.float32)
    new_coords = np.array(new_coords[:3], np.float32)
    matrix = cv.getAffineTransform(ori_coords, new_coords)
    matrix = np.concatenate((matrix, [[0, 0, 1]]), axis = 0)
    return matrix

def applyTransform(coord, T):
    FLAT = False; HOMOGENOUS = True;
    DIM = len(T) - 1
    
    coord = np.array(coord)
    if len(coord.shape) == 1:
        FLAT = True
        coord = coord[:, np.newaxis]
    if len(coord) == DIM:
        HOMOGENOUS = False
        coord = np.concatenate((coord, [[1]]), axis = 0)
        
    coord = np.dot(T, coord)
    
    if not HOMOGENOUS:
        coord = coord[:DIM]
    if FLAT:
        coord = coord.ravel()
    return coord
