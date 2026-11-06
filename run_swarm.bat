@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Запуск комнаты наблюдения. Остановка: Ctrl+C.
:loop
python swarm_lab.py
echo Скрипт завершился. Перезапуск через 60 секунд...
timeout /t 60 /nobreak >nul
goto loop
