from typing import List
import vtk
import sys

def _findModule(module_name: str):
    m = getattr(vtk, module_name)
    return m.__module__

def findModules(module_list: List[str]):
    modules = dict()
    for mod in module_list:
        module_path = _findModule(mod)
        modules.setdefault(module_path, []).append(mod)
    return modules

if __name__ == "__main__":
    module_names = sys.argv[1:]
    mods = findModules(module_names)
    for module_path, _modules in mods.items():
        print("from {} import {}".format(module_path, ", ".join(set(_modules))))
