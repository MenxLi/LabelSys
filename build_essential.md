# Data/Library Files necessary for pyinstaller to build excutable

[Pyinstaller-Spec](http://pyinstaller.readthedocs.io/en/stable/spec-files.html#adding-data-files)

```Python
data_path = [
( "ui/*.ui", "./ui" ),
( "ui/QTDark.stylesheet", "./ui" ),
( "utils/*.dll", "./utils" ),
( "utils/*.so", "./utils" ),
( "help.html", "./" ),
( "Pics", "./Pics" ), 
( "conf.json", "./" )
]
```
