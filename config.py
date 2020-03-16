import json

with open("conf.json", "r") as f:
    CONF = json.load(f)

CNT_OPEN = 1
CNT_CLOSE = 0

SERIES = 'SAG PD'

LABELS = []
LBL_COLORS = []
LBL_MODE = []
for _label in CONF["Labels"].keys():
    LABELS.append(_label)
    LBL_COLORS.append(CONF["Labels"][_label]["color"])
    LBL_MODE.append(CONF["Labels"][_label]["mode"])

# Magnification for preview
PREVIEW2D_MAG = 2

