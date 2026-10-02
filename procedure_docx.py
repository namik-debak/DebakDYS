"""Load compiled module from __pycache__ or sibling .pyc (source restored separately if present)."""
import importlib.util
import os
import sys

_name = "procedure_docx"
_dir = os.path.dirname(os.path.abspath(__file__))
_tag = f"cpython-{sys.version_info.major}{sys.version_info.minor}"
# Önce kök dizindeki .pyc: __pycache__ içindeki dosya, bu yükleyici derlendiğinde Python tarafından
# üzerine yazılabilir (yükleyicinin kendisine dönüşür). Kök .pyc'ye Python dokunmaz.
_candidates = [
    os.path.join(_dir, f"{_name}.pyc"),
    os.path.join(_dir, "__pycache__", f"{_name}.{_tag}.pyc"),
    os.path.join(_dir, "__pycache__", f"{_name}.cpython-310.pyc"),
]
_pyc = next((p for p in _candidates if os.path.isfile(p)), None)
if not _pyc:
    raise ImportError(
        f"{_name}: kaynak veya derlenmiş modül yok. "
        f"Sunucuda Python 3.10 önerilir; __pycache__/{_name}.cpython-310.pyc gerekli."
    )
_spec = importlib.util.spec_from_file_location(_name, _pyc)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
for _attr in dir(_mod):
    if not _attr.startswith("_"):
        globals()[_attr] = getattr(_mod, _attr)
