#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#

__author__ = "Mengxun Li"
__copyright__ = "Copyright 2020"
__credits__ = ["Kumaradevan Punithakumar"]
__license__ = "All right reserved"
__maintainer__ = "Mengxun Li"
__email__ = "mengxunli@whu.edu.cn | mengxun1@ualberta.ca"

__VERSIONS__ =[ \
        ["0.X", "Implemented with Tkinter"],
        ["1.0-alpha", "Re-write the whole program using PyQt5 and vtk, under develpment"],
        ["1.0.0", "For MRI labeling - disc, condyle and eminence"],
        ["1.0.1", "Fix curve initialization crash bug; Add individual curve initialization step; Add image/video loading support"],
        ["1.1.0", "Speed up loading and exporting process; Change data storing header file rule to include configration; Add compare widget; Add labeling panel preview; Change version naming rule"],
        ["1.2.0", "Support Color image reading, license change"],
        ["1.2.1", "Bug fix - label interpretation error when dealing with non-square image"],
        ["1.2.2", "Now support color panel preview, cursor can move out of the image when labeling; Add max_im_height to config file"],
        ["1.3.0", "Add rotation function oin operation, support default label, support reverse switch label"],
        ["1.3.1", "Add on-panel label"],
        ["1.3.2", "Bug fix: rotate will not clear all labels"],
        ["1.3.3", "Add known issue into source code, add preview on panel shortcut and manual button, preview on panel will update on contour end interaction"],
        ["1.3.4", "Change interpolation method"]
        ]
__version__, __description__ = __VERSIONS__[-1]
