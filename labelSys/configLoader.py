#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#
import json
import os

_CURR_DIR = os.path.dirname(__file__)
with open(os.path.join(_CURR_DIR, "conf.json"), "r") as f:
    CONF = json.load(f)
_UI_DIR = os.path.join(_CURR_DIR, "ui")
_DOC_DIR = os.path.join(_CURR_DIR, "docs")

# CNT_OPEN = CONF["Contour_mode"]["Open"]
# CNT_CLOSE = CONF["Contour_mode"]["Close"]

LOADING_MODE = CONF["Loading_mode"]
SERIES = CONF["Default_series"]
DEFAULT_LABEL = CONF["Default_label"]
MAX_IM_HEIGHT = CONF["Max_im_height"]   # Maximum image height, when image is bigger than this value it will be resize to this height

LABELS = []
LBL_COLORS = []
LBL_MODE = []
LBL_STEP = []
for _label in CONF["Labels"].keys():
    LABELS.append(_label)
    LBL_COLORS.append(CONF["Labels"][_label]["color"])
    LBL_MODE.append(CONF["Labels"][_label]["mode"])
    LBL_STEP.append(CONF["Labels"][_label]["label_step"])

# Magnification for preview
PREVIEW2D_MAG = CONF["2D_preview_mag"]

# For TMJ-Ped
CLASSES = CONF["Classifications"]
