
"""
Compile binary with pyinstaller
"""

import subprocess, platform, os, argparse, tempfile, shutil

parser = argparse.ArgumentParser(description="Build labelSys binary")
parser.add_argument("-c", "--config", default="")
args = parser.parse_args()

# specifiying configuration file
if args.config:
    _conf_src = "confs" + os.sep + "conf_" + args.config + ".json"
    _tmp_dir = tempfile.mkdtemp()
    conf_src = os.path.join(_tmp_dir, "conf.json")
    shutil.copy2(_conf_src, conf_src)
    print("Created temporary configuration file: ", conf_src)
else:
    conf_src = "labelSys/conf.json"
if not os.path.exists(conf_src):
    print("Configuration file not exists: ", conf_src)
    exit()

__this_dir = os.path.abspath(os.path.dirname(__file__))
C_LIB_PTH = os.path.join(__this_dir, "labelSys", "clib")

print("Compile binaries...")
os.chdir(C_LIB_PTH)
subprocess.check_call(["make"])
os.chdir(__this_dir)

hiddenimports=[
    'vtkmodules','vtkmodules.all',
    'vtkmodules.qt.QVTKRenderWindowInteractor',
    'vtkmodules.util','vtkmodules.util.vtkImageImportFromArray',
    'vtkmodules.util.numpy_support','vtkmodules.numpy_interface', 
    'vtkmodules.numpy_interface.dataset_adapter']

data_path = [
( "labelSys/ui/*", "./labelSys/ui" ),

# Binaries
( "labelSys/utils/*.dll", "./labelSys/utils" ),
( "labelSys/utils/*.so", "./labelSys/utils" ),
( "labelSys/utils/*.dylib", "./labelSys/utils" ),

( "labelSys/bin/*", "./labelSys/bin" ),

( "labelSys/docs", "./labelSys/docs" ),
# ( "labelSys/conf.json", "./labelSys" ),
( conf_src, "./labelSys" ),

( "../immarker/immarker/icons/*", "./immarker/icons" ),
( "../immarker/immarker/docs/*", "./immarker/docs" ),
]

cmd = ["pyinstaller", "-w", "--noconfirm", "--collect-submodules=pydicom", "-i", "./labelSys/icons/main.ico", "./run.py"]

for himp in hiddenimports:
    cmd += ["--hidden-import", himp]

if platform.system() == "Windows":
    sep = ";"
else: 
    sep = ":"
for data in data_path:
    cmd += ["--add-data", '{src}{sep}{dst}'\
            .format(src = data[0], sep=sep, dst = data[1])]

print(" ".join(cmd))
subprocess.check_call(cmd)
