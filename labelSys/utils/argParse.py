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
from ..version import __version__, __description__

parser = argparse.ArgumentParser(description = "LabeySys v{}, \n{}".format(__version__, __description__))
parser.add_argument("-d", "--dev", action = "store_true", default = False)
parser.add_argument("-l", "--load", action = "store_true", default = False)
parser.add_argument("-f", "--file", type = str, default = "")
parser.add_argument("-m", "--loading_mode", type = int)


args = parser.parse_args()

