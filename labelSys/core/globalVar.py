from __future__ import annotations
import logging, sys
from typing import List, TYPE_CHECKING, Union
if TYPE_CHECKING:
    from .extensionCore import HookCallbackHolder, HookEventRecord
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QCoreApplication

#  global int_uid
#  global logger
#  global extened_methods
#  global extened_keys

__initialized: bool
logger: logging.Logger
_qapp: Union[QApplication, QCoreApplication]

hook_records: List[HookEventRecord]
hook_callbacks: dict[str, HookCallbackHolder]

def init():
    global logger
    global hook_records
    global hook_callbacks
    global __initialized
    thismodule = sys.modules[__name__]
    if hasattr(thismodule, "__initialized") and __initialized:
        return
    __initialized = True
    logger = logging.getLogger("labelSys")

    hook_callbacks = {}
    hook_records = []


def getQApp(args: List) -> Union[QApplication, QCoreApplication]:
    from PyQt6.QtWidgets import QApplication
    global _qapp
    thismodule = sys.modules[__name__]
    if not hasattr(thismodule, "_qapp"):
        app = QApplication.instance()
        if app is None:
            app = QApplication(args)
        _qapp = app
    return _qapp

