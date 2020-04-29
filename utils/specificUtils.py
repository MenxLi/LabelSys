#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#
"""
Specific utilities for this project
"""

import datetime

def createHeader(labeler, series, config,  time = str(datetime.datetime.now()), spacing = (1,1,1)):
    head_info = {
            "Labeler":labeler,
            "Time":time,
            "Spacing":spacing,
            "Series": series,
            "Config": config
    }
    return head_info
