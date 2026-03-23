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

### install with pip
```bash
python -m pip install .
```

<!-- ### build native extension in place
```bash
python setup.py build_ext --inplace
```

### Binary distribution
```bash
python build.py
``` -->

## Usage
```bash
labelSys [config_file_path]
```

For CLI arguments see: `labelSys -h`

<!-- ## Known issues:

* Saving while another saving thread is running will raise a permission error. -->

## Reading labeled data using API
```python
from labelSys.utils.labelReaderV2 import LabelSysReader

label_directories: list[str]
reader = LabelSysReader(label_directories)

# get the first data
i = 0

data_i = reader[i]
print(f"Total Data count: {len(reader)}")
print(f"Number of images for this data: {len(data_i)}")
print(f"Avaliable labels: \n\t{data_i.avalLabels()}")

for (image, mask_dict, cls_dict) in zip(data_i.images, data_i.masks, data_i.classifications):
    ...
```