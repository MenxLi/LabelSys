#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#
import json5 as json
import os, shutil
from typing import TypedDict, Dict, List
from .argParse import args

class _ConfLabelType(TypedDict):
    color: List[float]
    mode: int
    draw: int
    label_step: float

_ConfClassificationType = TypedDict(
    "_ConfClassificationType",
    {
        "full_name": str,
        "class": List[str],
        "description": str
    }
)

ConfType = TypedDict(
    "ConfType",
    {
        "Labels": Dict[str, _ConfLabelType],
        "Classifications": Dict[str, _ConfClassificationType],
        "Loading_mode": int,
        "2D_preview_mag": int,
        "Default_series": str,
        "Default_label": str,
        "Max_im_height": int
    }
)


_CURR_DIR = os.path.dirname(__file__)
if args.config_file:
    # provided by argParse
    CONF_PATH = args.config_file
else:
    CONF_PATH = os.path.join(_CURR_DIR, "conf.json")

with open(CONF_PATH, "r", encoding="utf-8") as f:
    CONF: ConfType = json.load(f)
_HOME_DIR = os.path.expanduser("~")
_UI_DIR = os.path.join(_CURR_DIR, "ui")
_DOC_DIR = os.path.join(_CURR_DIR, "docs")
_ICON_DIR = os.path.join(_CURR_DIR, "icons")
_TMP_DIR = os.path.join(_CURR_DIR, ".TempDir")
_BIN_DIR = os.path.join(_CURR_DIR, "bin")
if not os.path.exists(_BIN_DIR):
    os.mkdir(_BIN_DIR)

LOG_FILE = os.path.join(_HOME_DIR, ".labelSys.log")

if args.gen_conf:
    dst =  "./{}.json".format("conf_labelsysDefault")
    shutil.copyfile(CONF_PATH,dst)
    print("Generated configuration file at: ", os.path.abspath(dst))
    exit()

if args.show_log:
    from .utils.utils_ import openFile
    openFile(LOG_FILE)
    exit()

LOADING_MODE = CONF["Loading_mode"]
SERIES = CONF["Default_series"]
DEFAULT_LABEL = CONF["Default_label"]
MAX_IM_HEIGHT = CONF["Max_im_height"]   # Maximum image height, when image is bigger than this value it will be resize to this height
# DRAW_CONTOUR = CONF["Draw_contour"]

LABELS = []
LBL_COLORS = []
LBL_MODE = []
LBL_DRAW = []
LBL_STEP = []
for _label in CONF["Labels"].keys():
    LABELS.append(_label)
    if "color" in CONF["Labels"][_label]:
        # Label color
        LBL_COLORS.append(CONF["Labels"][_label]["color"])
    else:
        LBL_COLORS.append([1.0, 0.0, 0.0])

    if "mode" in CONF["Labels"][_label]:
        # Open or close contour
        LBL_MODE.append(CONF["Labels"][_label]["mode"])
    else:
        LBL_MODE.append(0)

    if "draw" in CONF["Labels"][_label]:
        # Draw the contour or click to add points
        LBL_DRAW.append(CONF["Labels"][_label]["draw"])
    else:
        LBL_DRAW.append(1)

    if "label_step" in CONF["Labels"][_label]:
        # Drawing resample step
        LBL_STEP.append(CONF["Labels"][_label]["label_step"])
    else:
        LBL_STEP.append(1)

# Magnification for preview
PREVIEW2D_MAG = CONF["2D_preview_mag"]

CLASSIFICATIONS = CONF["Classifications"]

