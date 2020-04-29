#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#

__author__ = "Mengxun Li"
__copyright__ = "Copyright 2020"
__credits__ = ["Kumaradevan Punithakumar, Abhilash Hareendranathan"]
__license__ = "2-Clause BSD"
__maintainer__ = "Mengxun Li"
__email__ = "mengxunli@whu.edu.cn | mengxun1@ualberta.ca"

__VERSIONS__ =[ \
        ["0.X", "Implemented with Tkinter"],
        ["1.0-alpha", "Re-write the whole program using PyQt5 and vtk, under develpment"],
        ["1.0.0", "For MRI labeling - disc, condyle and eminence"],
        ["1.0.1", "Fix curve initialization crash bug; Add individual curve initialization step; Add image/video loading support"],
        ["1.1.0", "Speed up loading and exporting process; Change data storing header file rule to include configration; Add compare widget; Add labeling panel preview; Change version naming rule"]
        ]
__version__, __description__ = __VERSIONS__[-1]
