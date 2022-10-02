# README

To use label reading API:
```python
import typing
from labelSys.utils import LabelSysReader

label_dirs: typing.List[str]    # Result folders (list of folder paths) to inspect
i: int                          # Data index

reader = LabelSysReader(label_dirs)
data_i = reader[i]
```

## Installation

```bash
make
pip install .
```

## Usage
```bash
labelSys [config_file_path]
```

For CLI arguments see: `labelSys -h`
