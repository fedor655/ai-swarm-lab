# -*- coding: utf-8 -*-
"""
build_exe.py — собирает SwarmLab.exe одним файлом.

Читает .env (ключ, адрес API, модель) и зашивает их в exe через
сгенерированный embedded_config.py — отдельный .env рядом с exe не нужен.
Результат: dist\\SwarmLab.exe, копия кладётся рядом со скриптом.
"""

import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ENV_FILE = BASE / ".env"
EMBEDDED = BASE / "embedded_config.py"

def read_env():
    vals = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip()
    return vals

def write_embedded(vals):
    keys = ["OPENAI_API_KEY", "OPENAI_BASE_URL", "MODEL",
            "AGENT_COUNT", "SWARM_SECRET_SALT", "SWARM_SECRET_HASH"]
    lines = [
        "# -*- coding: utf-8 -*-",
        '"""Автогенерация build_exe.py: настройки, зашитые в exe. Не коммитить!"""',
        "import os",
        "",
    ]
    for k in keys:
        if k in vals:
            lines.append(f'os.environ.setdefault("{k}", {vals[k]!r})')
    lines.append("")
    EMBEDDED.write_text("\n".join(lines), encoding="utf-8")
    print(f"embedded_config.py: зашиты ключи {', '.join(k for k in keys if k in vals)}")

def main():
    vals = read_env()
    if not vals.get("OPENAI_API_KEY"):
        sys.exit("В .env нет OPENAI_API_KEY — exe без ключа собирать бессмысленно.")
    write_embedded(vals)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",
        "--uac-admin",
        "--clean",
        "--name", "SwarmLab",
        "swarm_lab.py",
    ]
    print("Сборка:", " ".join(cmd))
    subprocess.run(cmd, cwd=BASE, check=True)

    src = BASE / "dist" / "SwarmLab.exe"
    dst = BASE / "SwarmLab.exe"
    dst.write_bytes(src.read_bytes())
    print(f"\nГотово: {dst}")
    print(f"Размер: {dst.stat().st_size / 1024 / 1024:.1f} МБ")

if __name__ == "__main__":
    main()
