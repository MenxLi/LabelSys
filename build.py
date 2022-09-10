
"""
Compile binary with pyinstaller
"""

import subprocess, platform, os

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
( "labelSys/conf.json", "./labelSys" ),

( "../immarker/immarker/icons/*", "./immarker/icons" ),
( "../immarker/immarker/docs/*", "./immarker/docs" ),
]

cmd = ["pyinstaller", "--noconfirm", "--collect-submodules=pydicom", "-i", "./labelSys/icons/main.ico", "./run.py"]

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
