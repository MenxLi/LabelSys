# Data/Library Files necessary for pyinstaller to build excutable

[Pyinstaller-Spec](http://pyinstaller.readthedocs.io/en/stable/spec-files.html#adding-data-files)

`pyi-makespec -F --collect-submodules=pydicom -i ./labelSys/icons/main.ico ./run.py`
```Python
data_path = [
( "labelSys/ui/*", "./labelSys/ui" ),

# Binaries
( "labelSys/utils/*.dll", "./labelSys/utils" ),
( "labelSys/utils/*.so", "./labelSys/utils" ),
( "labelSys/utils/*.dylib", "./labelSys/utils" ),
( "labelSys/clib/*.so", "./labelSys/clib" ),
( "labelSys/clib/*.dll", "./labelSys/clib" ),
( "labelSys/clib/*.so", "./labelSys/clib" ),

( "labelSys/docs", "./labelSys/docs" ),
( "labelSys/conf.json", "./labelSys" ),

( "../immarker/immarker/icons/*", "./immarker/icons" ),
( "../immarker/immarker/docs/*", "./immarker/docs" ),
]
```
```
hiddenimports=['vtkmodules','vtkmodules.all','vtkmodules.qt.QVTKRenderWindowInteractor','vtkmodules.util','vtkmodules.util.vtkImageImportFromArray','vtkmodules.util.numpy_support','vtkmodules.numpy_interface', 'vtkmodules.numpy_interface.dataset_adapter']
```
