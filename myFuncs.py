"""
Useful functions
"""

import numpy as np

def gray2rgb_(img):
    new_img = np.concatenate((img[:,:,np.newaxis], img[:,:,np.newaxis], img[:,:,np.newaxis]), axis=2)
    return new_img
def removeDuplicate2d(duplicate):
    final_list = []
    for num in duplicate:
        for num0 in final_list:
            if num[0] == num0[0] and num[1] == num0[1]:
                continue
            final_list.append(num)
            #print("Appended: ", num)
            #print("final_list", final_list)
    return final_list

def plot_imgs(imgs, n_col = 3, gray = False, titles = None):
    """Take a list of images and plot them in grids"""
    if titles ==None:
        print_title = False
    else: print_title = True
    if len(imgs)//n_col == len(imgs)/n_col:
        n_row = len(imgs)//n_col
    else:
        n_row = len(imgs)//n_col + 1
    _, axs = plt.subplots(n_row, n_col)
    axs = axs.flatten()
    count = 0
    for img, ax in zip(imgs, axs):
        if print_title:
            ax.set_title(titles[count])
            count +=1
        if gray:
            ax.imshow(img, cmap = 'gray')
        else: ax.imshow(img)
    plt.show()

def img_hist(img):
    plt.hist(equ.ravel(), bins=256, range=(0, 256), fc='k', ec='k')
    plt.show()

def normalize_mat(mat, minimum = "mean"):
    if minimum == "zero":
        return (mat - mat.min())/(mat.max() - mat.min())
    if minimum == "mean":
        return (mat - mat.mean())/(mat.max() - mat.min())

def map_mat_255(img):
    img = img.astype(np.float)
    if (img == 0).all():
        return img.astype(np.uint8)
    result = normalize_mat(img, minimum = "zero")*255
    return result.astype(np.uint8)

def img_channel(img):
    if len(img.shape)==3:
        return img.shape[2]
    if len(img.shape)==2:
        return 1

def equal_multiChannel(mat, template):
    """
    To find template in a mat
    tamplate must be 1D and len(template) == mat.shape[-1]
    mat is a 2D image with multiple channels
    """
    template = np.array(template)
    if not (len(template.shape) == 1 and len(template) == mat.shape[-1]):
        raise Exception("illegal parameter, see --help")
    x = mat==template
    bools = [x[:,:,i] for i in range(len(template))]
    result = np.ones(mat.shape[:2], np.bool)
    for bl in bools:
        result = np.logical_and(result, bl)
    return result




def overlap_(fg_img, bg_img, mask):
    """
    按蒙版重叠图像fg_img和bg_img，fg_img在蒙版的白色区bg_img在黑色区
    @fg_img: 前景图，三通道
    @bg_img: 背景图，三通道
    @mask: 蒙版，最大值为1, 三通道
    三图要有相同大小
    """
    #mask = gray2rgb(mask)

    new_img = fg_img * mask + bg_img * (1 - mask)
    return new_img

def returned_img(patch, img, pos):
    """
    return an image patch into the original image
    pos: upper left corner (row, col)
    """
    if img_channel(img) == 1:
        img = gray2rgb_(img)
    if img_channel(patch) == 1:
        patch = gray2rgb_(patch)
    patch_h = patch.shape[0]
    patch_w = patch.shape[1]
    img[pos[0]:pos[0]+patch_h, pos[1]:pos[1]+patch_w] = patch
    return img

def get_region(img, h_range, w_range):
    """
    fetch a image patch without worrying about get out of the image dimension
    """
    return [[max(0, h_range[0]), min(h_range[1], img.shape[0])], [max(0, w_range[0]), min(w_range[1], img.shape[1])]]

def find_region(mask, value = 1):
    """Find the row & col image region that the mask == value"""
    coord = np.where(mask==value)
    row_start = coord[0].min()
    row_end = coord[0].max()
    col_start = coord[1].min()
    col_end = coord[1].max()
    return((row_start, row_end), (col_start, col_end))


