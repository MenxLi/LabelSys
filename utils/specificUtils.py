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
