# README #

Module requirement are in ***requirements.txt***

To use API:
```python
import typing
from labelSys.utils import LabelSysReader

label_dirs: typing.List[str]    # Result folders (list of folder paths) to inspect
i: int                          # Data index

reader = LabelSysReader(label_dirs)
data_i = reader[i]
```

