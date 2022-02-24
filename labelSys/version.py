#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#

__author__ = "Mengxun Li"
__copyright__ = "Copyright 2020-2021"
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
        ["1.3.4", "Change interpolation method to equally-spaced points on curvature integral."],
        ["1.3.5", "Liscense change; Add load file selection to console args; Default label can be set to \"\" to prevent label change while changing slices; Not raise error when select incorrect loading directory."],
        ["1.4.0", "Using setup.py for distribution"],
        ["1.4.1", "Bug fix - relative path"],
        ["1.5.0", "UI updates, add comment functionality"],
        ["1.5.1", "Performance optimization with better color image loading."],
        ["1.5.2", "Resample stratagy update"],
        ["1.5.3", "Add classification functionality"],
        ["1.5.4", "Saving format change, now using .npz for image saving; Add dtype to on-panel img info"],
        ["1.5.5", "Add -c to argparse"],
        ["1.6.0", "Add new click interaction style, new labelReader API, more entry on config file"],
        ["1.6.1", "Set configure file as optional positional argument"],
        ["1.6.2", "Able to generate default conf; double the default label step;"],
        ["1.6.3", "Add to another contour in 'operation', old label loading compatability"],
        ]
__version__, __description__ = __VERSIONS__[-1]
