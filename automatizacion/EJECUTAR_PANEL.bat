@echo off
rem Panel web de la automatizacion: http://127.0.0.1:8090 (usuario y clave: RUNNER_USER / RUNNER_PASSWORD de .env)
cd /d "%~dp0"
start "" http://127.0.0.1:8090
".venv\Scripts\python.exe" -m uvicorn runner_web.app:app --host 127.0.0.1 --port 8090
