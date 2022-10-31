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

class CMDArgT(argparse.Namespace):
    config_file: str
    dev: bool
    load: bool
    file: str
    loading_mode: int
    gen_conf: bool
    show_log: bool
    freeze_config: bool
    no_crop: bool

description = "\
    LabelSys v{version}: \n\
    LabelSys is a labeling software developed by Li, Mengxun (mengxunli@whu.edu.cn)\
    ".format(version = __version__)

parser = argparse.ArgumentParser(description = description)
parser.add_argument("config_file", nargs="?", type = str, default = "", \
    help = "Configuration file path")
parser.add_argument("-d", "--dev", action = "store_true", default = False, \
    help = "Development mode, in dev mode std streams and loggings will be shown on the terminal. "
                    "Otherwise, they will be stored in the log file.")
parser.add_argument("-l", "--load", action = "store_true", default = False, \
    help = "Loading mode, should be used in conjugation with -f, i.e.: -lf <labeled file path>")
parser.add_argument("-f", "--file", type = str, nargs="*", \
    help = "File path to open for labeling (use -f) or load labeled path (use -lf option)")
parser.add_argument("-m", "--loading_mode", type = int, \
    help = "(**Deprecated**) Set the loading mode, please use configuration file instead")
parser.add_argument("--gen_conf", action = "store_true", default = False, \
    help = "Generate a configuration file at current working directory, then exit")
parser.add_argument("--show_log", action = "store_true", default = False, \
    help = "Show log, then exit")
parser.add_argument("--freeze_config", action = "store_true", default = False, \
    help = "Set this flag and the application will not use labeled file configuration "
    "when loading labeled files")
parser.add_argument("--no_crop", action = "store_true", default=False, \
    help = "Set this flag and the application will not save nor read crop data")

args: CMDArgT = parser.parse_args(namespace = CMDArgT)


# Default options for this project
args.freeze_config = True
args.no_crop = True
