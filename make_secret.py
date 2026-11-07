# -*- coding: utf-8 -*-
"""make_secret.py — создаёт секретный код на хосте и соль+хеш для exe.

Код хранится ТОЛЬКО на хосте (Desktop\\secret_code.txt). В exe зашиваются
только соль и SHA-256 хеш — из них код не восстановить.

Использование:
  python make_secret.py                # взять код из Desktop\\secret_code.txt или сгенерировать
  python make_secret.py МОЙ_КОД        # задать код явно
"""
import hashlib
import os
import secrets
import sys
from pathlib import Path

def get_windows_desktop():
    try:
        import ctypes
        from ctypes import wintypes
        class GUID(ctypes.Structure):
            _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD),
                        ("Data3", wintypes.WORD), ("Data4", ctypes.c_ubyte * 8)]
        folder_id = GUID(
            0xB4BFCC3A, 0xDB2C, 0x424C,
            (ctypes.c_ubyte * 8)(0xB0, 0x29, 0x7F, 0xE9, 0x9A, 0x87, 0xC6, 0x41),
        )
        ptr = ctypes.c_wchar_p()
        hr = ctypes.windll.shell32.SHGetKnownFolderPath(
            ctypes.byref(folder_id), 0, None, ctypes.byref(ptr))
        if hr == 0 and ptr.value:
            value = Path(ptr.value)
            ctypes.windll.ole32.CoTaskMemFree(ptr)
            if value.exists():
                return value
    except Exception:
        pass
    home = Path.home()
    candidates = (
        Path(os.environ.get("OneDrive", "")) / "Рабочий стол",
        Path(os.environ.get("OneDrive", "")) / "Desktop",
        home / "OneDrive" / "Рабочий стол",
        home / "OneDrive" / "Desktop",
        home / "Рабочий стол",
        home / "Desktop",
    )
    return next((p for p in candidates if str(p) and p.exists()), home / "Desktop")

HOST_FILE = get_windows_desktop() / "secret_code.txt"
ENV_FILE = Path(__file__).resolve().parent / ".env"

def main():
    code = sys.argv[1] if len(sys.argv) > 1 else None
    if not code and HOST_FILE.exists():
        code = HOST_FILE.read_text(encoding="utf-8", errors="replace").strip()
        if code.startswith("секретный код роя:"):
            code = code.split(":", 1)[1].strip()
    if not code:
        code = secrets.token_urlsafe(24)
    HOST_FILE.write_text(f"секретный код роя: {code}\n", encoding="utf-8")
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + ":" + code).encode("utf-8")).hexdigest()
    lines = []
    if ENV_FILE.exists():
        lines = [l for l in ENV_FILE.read_text(encoding="utf-8").splitlines()
                 if not l.startswith("SWARM_SECRET_")]
    lines += [f"SWARM_SECRET_SALT={salt}", f"SWARM_SECRET_HASH={h}"]
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"код сохранён на хосте: {HOST_FILE}")
    print("соль и хеш записаны в .env — в exe попадёт только хеш, не код")

if __name__ == "__main__":
    main()
