import importlib
import os

import numpy as np
from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import find_packages, setup

from labelSys.version import __version__

# Do not install opencv if any of cv variation exists
# e.g. opencv-headless, opencv-contrib
install_requires = ["PyQt6", "PyQt6-sip", "numpy", "pydicom", "vtk", "scipy", "json5"]
cv_spec = importlib.util.find_spec("cv2")
if cv_spec is None:
    install_requires.append("opencv-python")

extra_compile_args = ["/O2"] if os.name == "nt" else ["-O3"]

ext_modules = [
    Pybind11Extension(
        "labelSys.clib._native",
        ["labelSys/clib/native.cpp"],
        include_dirs=[np.get_include()],
        cxx_std=17,
        extra_compile_args=extra_compile_args,
    )
]

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

    ext_modules = ext_modules,
    cmdclass = {"build_ext": build_ext},
    zip_safe = False,

    entry_points = {
        "console_scripts":[
            "labelSys=labelSys.exec:main",
            "labelSys_=labelSys.exec:main_",
        ]
    }
)
