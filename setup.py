import os
from setuptools import setup, find_packages
import importlib
from labelSys.version import __version__

# Do not install opencv if any of cv variation exists
# e.g. opencv-headless, opencv-contrib
install_requires = ["PyQt6", "PyQt6-sip", "numpy", "pydicom", "vtk", "scipy", "json5"]
cv_spec = importlib.util.find_spec("cv2")
if cv_spec is None:
    install_requires.append("opencv-python")

# Compile binaries
__this_dir = os.path.abspath(os.path.dirname(__file__))
C_LIB_PTH = os.path.join(__this_dir, "labelSys", "clib")
BIN_PTH = os.path.join(__this_dir, "labelSys", "bin")
if not os.path.exists(BIN_PTH):
    os.mkdir(BIN_PTH)
print("Compile binaries...")
os.chdir(C_LIB_PTH)
os.system("make")
os.chdir(__this_dir)

setup(
    name="LabelSys",
    version=__version__,
    author="Mengxun Li",
    author_email="mengxunli@whu.edu.cn",
    description="A segmentation labeling software",

    # 项目主页
    url="https://github.com/MenxLi/LabelSys", 

    packages=find_packages(),

    classifiers = [
        #   Development Status
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 4",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent"
    ],
    python_requires=">=3.5",

    include_package_data = True,

    install_requires = install_requires,

    entry_points = {
        "console_scripts":[
            "labelSys=labelSys.exec:main",
            "labelSys_=labelSys.exec:main_",
        ]
    }
)
