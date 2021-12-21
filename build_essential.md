# Data/Library Files necessary for pyinstaller to build excutable

[Pyinstaller-Spec](http://pyinstaller.readthedocs.io/en/stable/spec-files.html#adding-data-files)

`pyi-makespec -F --collect-submodules=pydicom`
```Python
data_path = [
( "labelSys/ui/*", "./labelSys/ui" ),
( "labelSys/utils/*.dll", "./labelSys/utils" ),
( "labelSys/utils/*.so", "./labelSys/utils" ),
( "labelSys/docs", "./labelSys/docs" ),
( "labelSys/conf.json", "./labelSys" )
]
```
```
hiddenimports=['vtkmodules','vtkmodules.all','vtkmodules.qt.QVTKRenderWindowInteractor','vtkmodules.util','vtkmodules.util.vtkImageImportFromArray','vtkmodules.util.numpy_support','vtkmodules.numpy_interface', 'vtkmodules.numpy_interface.dataset_adapter']
```
