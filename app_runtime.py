"""
Flask uygulama modülünü çift yüklemeden çözümler.

``python app.py`` çalıştırıldığında dosya ``__main__`` olarak yüklenir.
Route modüllerinde ``from app import app`` kullanmak aynı dosyayı ikinci kez
``app`` adıyla yükler; IMS/IATF vb. rotalar kullanılmayan instance'a yazılır ve
404 üretir.

Bu yardımcı, mevcut (yarım yüklenmiş) ``app`` veya ``__main__`` modülünü
tercih eder; böylece tek Flask instance kullanılır.
"""

from __future__ import annotations

import sys


def host():
    """``app`` Flask nesnesini ve dekoratörleri taşıyan modülü döndürür."""
    mod = sys.modules.get("app")
    if mod is not None and getattr(mod, "app", None) is not None:
        return mod

    main = sys.modules.get("__main__")
    if main is not None and getattr(main, "app", None) is not None:
        main_file = (getattr(main, "__file__", "") or "").replace("\\", "/")
        if main_file.endswith("/app.py") or main_file.endswith("app.py"):
            return main

    # start_dys / pytest: henüz sys.modules'ta yoksa normal import
    import app as mod  # noqa: WPS433
    return mod
