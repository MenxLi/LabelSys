# Data/Library Files necessary for pyinstaller to build excutable

[Pyinstaller-Spec](http://pyinstaller.readthedocs.io/en/stable/spec-files.html#adding-data-files)

```Python
data_path = [
( "labelSys/ui/*", "./labelSys/ui" ),
( "labelSys/utils/*.dll", "./labelSys/utils" ),
( "labelSys/utils/*.so", "./labelSys/utils" ),
( "labelSys/docs", "./labelSys/docs" ),
( "labelSys/conf.json", "./labelSys" )
]
```
