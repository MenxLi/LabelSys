
from __future__ import annotations
from typing import TypedDict, Union, Dict, Any, List, Tuple

_Number = Union[int, float]

LabelHeaderT = TypedDict('LabelHeaderT', {
    "Labeler": str,
    "Time": str,
    "Spacing": tuple[_Number, _Number, _Number] | list[_Number],
    "Series": str,
    "Config": Dict[str, Any],
    "Version": str
})

class SliceLabelDataTypeSingle(TypedDict):
    # This represents a contour
    Open: bool
    Points: List[Tuple[float, float, float]]    # VTK nodes
    Contour: List[Tuple[int, int]]              # Full contour in VTK coordinate

SliceLabelDataType = List[SliceLabelDataTypeSingle]

# Contour data type in holder.data
ContourDataT = List[Dict[str, SliceLabelDataType]]
