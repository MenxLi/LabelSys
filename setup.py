from setuptools import setup, find_packages
from labelSys.version import __version__

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

    install_requires = ["PyQt5", "numpy", "opencv-python", "pydicom", "vtk"],

    entry_points = {
        "console_scripts":[
            "labelSys=labelSys.exec:main",
            "labelSys_=labelSys.exec:main_",
        ]
    }
)