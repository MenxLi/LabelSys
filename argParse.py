"""
Parse argument from command line
should be imported at the start of main file
"""
import argparse
from version import __VERSION__, __DESCRIPTION__

parser = argparse.ArgumentParser(description = "MRILabeySys v{}, \n{}".format(__VERSION__, __DESCRIPTION__))
parser.add_argument("-d", "--dev", action = "store_true", default = False)
parser.add_argument("-f", "--file", type = str, default = "")


args = parser.parse_args()

