import json

with open("conf.json", "r") as f:
    CONF = json.load(f)

# CNT_OPEN = CONF["Contour_mode"]["Open"]
# CNT_CLOSE = CONF["Contour_mode"]["Close"]

LOADING_MODE = CONF["Loading_mode"]
SERIES = CONF["Default_series"]

LABELS = []
LBL_COLORS = []
LBL_MODE = []
for _label in CONF["Labels"].keys():
    LABELS.append(_label)
    LBL_COLORS.append(CONF["Labels"][_label]["color"])
    LBL_MODE.append(CONF["Labels"][_label]["mode"])

# Magnification for preview
PREVIEW2D_MAG = CONF["2D_preview_mag"]

