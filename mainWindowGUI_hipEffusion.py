from mainWindowGUI import *

class MainWindow_HE(MainWindow):
    def __init__(self, args):
        super().__init__(args)

        self.act_op_otsu.triggered.connect(self.otsuContour)
        self.act_op_otsu.setShortcut("Ctrl+T")

    def loadPatients(self):
        super().loadPatients()
        self.ori_imgs = copy.deepcopy(self.imgs)

    def loadLabeledFile(self):
        super().loadLabeledFile()
        self.ori_imgs = copy.deepcopy(self.imgs)

    def clearCurrentSlice(self):
        self.imgs[self.slice_id] = self.ori_imgs[self.slice_id][:]
        super().clearCurrentSlice()

    def otsuContour(self):
        mask = super()._getSingleMask(self.slice_id, self.curr_lbl)
        if mask == None:
            return 1
        im = self.imgs[self.slice_id]
        pixels = np.ma.masked_array(im, 1-mask).compressed() # labeled pixels
        t = F.otsuThresh(pixels)
        _ , thresh = cv.threshold(im, t, im.max(), cv.THRESH_BINARY)
        self.imgs[self.slice_id] = thresh*mask + self.imgs[self.slice_id]*(1-mask)
        super()._updateImg()
        return 0
