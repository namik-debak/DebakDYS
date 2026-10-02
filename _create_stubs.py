"""Pyc loader stub'lari olusturur."""
import os

LOADER_TEMPLATE = '''"""Auto-loader: pycache'den .pyc modulu yukler."""
import importlib.util, os as _os

_name = "{name}"
_pyc = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "__pycache__", _name + ".cpython-310.pyc")
if _os.path.exists(_pyc):
    _spec = importlib.util.spec_from_file_location(_name, _pyc, submodule_search_locations=[])
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    for _attr in dir(_mod):
        if not _attr.startswith("__"):
            globals()[_attr] = getattr(_mod, _attr)
'''

# ims_routes zaten guncellendi, digerleri:
remaining = [
    'iatf_routes', 'env_routes', 'ohs_routes',
    'isms_routes', 'competency_routes',
    'audit_routes', 'audit_checklist_routes',
]

for m in remaining:
    out = m + ".py"
    with open(out, "w", encoding="utf-8") as f:
        f.write(LOADER_TEMPLATE.format(name=m))
    print(f"{m}.py: OVERWRITTEN with loader")

print("Done!")
