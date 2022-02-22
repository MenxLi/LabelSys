#
# Copyright (c) 2020 Mengxun Li.
#
# This file is part of LabelSys
# (see https://bitbucket.org/Mons00n/mrilabelsys/).
#
"""
Parse argument from command line
should be imported at the start of main file
"""
import argparse
from .version import __version__, __description__

description = "\
    LabelSys v{version}: \n\
    LabelSys is a labeling software developed by Li, Mengxun (mengxunli@whu.edu.cn)\
    ".format(version = __version__)

parser = argparse.ArgumentParser(description = description)
parser.add_argument("-d", "--dev", action = "store_true", default = False)
parser.add_argument("-l", "--load", action = "store_true", default = False)
parser.add_argument("-f", "--file", type = str, default = "")
parser.add_argument("-c", "--config_file", type = str, default = "")
parser.add_argument("-m", "--loading_mode", type = int)

args = parser.parse_args()