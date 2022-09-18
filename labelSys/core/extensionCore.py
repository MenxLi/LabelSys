from . import globalVar as G
import markdown
from functools import wraps
from typing import Literal, Callable, List, TypeVar, Union

CallVar = TypeVar("CallVar", bound=Callable)

class HookCallbackHolder():
    def __init__(self,
                 before: List[Callable],
                 after: List[Callable]
                 ):
        self.before = before
        self.after = after
    def __str__(self) -> str:
        return f" - Before: {self.before}\n - After: {self.after}\n"

    def call(self, mode: Literal["before", "after"], *args, **kwargs):
        funcs = getattr(self, mode)
        for func in funcs:
            if func.__code__.co_argcount == 0:
                func()
            else:
                func(*args, **kwargs)

    __repr__ = __str__

class HookEventRecord:
    """
    To record functions that extended with additional callbacks
    """
    def __init__(self, tag: str, func: Callable):
        self.tag = tag
        self.name = func.__name__
        self.classname = "_"
        self.module = func.__module__
        self.doc = func.__doc__
        self.code = func.__code__

    @staticmethod
    def _multilineMark(txt: Union[str, None], pre_mark: str, default_str = "") -> str:
        if not txt:
            txt = default_str
        txt_split = txt.split("\n")
        txt_split = [pre_mark + line for line in txt_split ]
        return "\n".join(txt_split)

    @property
    def md_doc(self) -> str:
        doclines = [
            f"## {self.tag}",
            "",
            f"**=>** {'.'.join([self.module, self.classname, self.name])}",
            "{}".format(self._multilineMark(self.doc, "> ", default_str="No doc")),
            "",
            f"**arguments**: {self.code.co_varnames}"
        ]
        return "\n".join(doclines)

    @property
    def html_doc(self) -> str:
        return markdown.markdown(self.md_doc)

    def __str__(self) -> str:
        return self.md_doc
    __repr__ = __str__

def hookEvent(flag: str, class_name: str = "_UnknownClass_"):
    """Should be used as a decorator, in conjugation with hookCallback
    Mark a function as need to be extend with additional callbacks
    Flag is set to trace this function

    Args:
        flag (str): Flag of the function
        class_name (str, optional): The class name of the function, if is a method of a class \
            this argument is set manually as the class name can't be inferred automatically in class body.\ 
            Defaults to "_UnknownClass_".
    """
    def wapper(method: CallVar) -> CallVar:
        record = HookEventRecord(flag, method)
        record.classname = class_name
        G.hook_records.append(record)
        @wraps(method)
        def _func(*args, **kwargs):
            callback_holder = G.hook_callbacks.setdefault(flag, HookCallbackHolder([], []))
            callback_holder.call("before", *args, **kwargs)
            out = method(*args, **kwargs)
            callback_holder.call("after", *args, **kwargs)
            return out
        return _func
    return wapper

def hookCallback(flag: str, mode: Literal["before", "after"] = "after"):
    """ Should be used as a decorator, in cojugation with hookEvent
    Register a callback function to given flag,
    The callback function to register should take no arguments \
        or take arguments the same as the function associated with the flag

    Args:
        flag (str): Flag of the function to register.
        mode (Literal[&quot;before&quot;, &quot;after&quot;], optional): the timing of function execution. \
            Defaults to "after".
    """
    def wrapper(func: CallVar) -> CallVar:
        callback_holder = G.hook_callbacks.setdefault(flag, HookCallbackHolder([], []))
        getattr(callback_holder, mode).append(func)
        @wraps(func)
        def _func(*args, **kwargs):
            out = func(*args, **kwargs)
            return out
        return _func
    return wrapper

def generateWrapperDoc(dst: str, *records: HookEventRecord):
    with open(dst, "w", encoding="utf-8") as fp:
        for rec in records:
            fp.write(rec.html_doc)
            fp.write("\n\n")
