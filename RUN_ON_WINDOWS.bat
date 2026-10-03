@echo off
setlocal
cd /d "%~dp0"

echo ==========================================================
echo    RETENTIONINTEL: EMPLOYEE ATTRITION INTELLIGENCE SUITE
echo ==========================================================
echo.

if not exist ".venv\Scripts\python.exe" (
  echo Creating Python virtual environment in .venv...
  py -3 -m venv .venv
  if errorlevel 1 goto :error
)

set "PY=.venv\Scripts\python.exe"

echo [1/4] Verifying dependencies...
%PY% -m pip install -r requirements.txt --quiet
if errorlevel 1 goto :error

echo [2/4] Executing multi-model benchmark and training...
%PY% -m src.train
if errorlevel 1 goto :error

echo [3/4] Updating workforce analytics summaries and charts...
%PY% -m src.analyze
if errorlevel 1 goto :error

echo [4/4] Launching RetentionIntel Executive Dashboard...
echo.
echo ==========================================================
echo  DASHBOARD ONLINE AT: http://127.0.0.1:5000
echo  Press Ctrl+C in this console window to terminate server.
echo ==========================================================
echo.
start http://127.0.0.1:5000
%PY% -m src.app
goto :end

:error
echo.
echo [ERROR] Setup or execution failed. Check Python 3 installation.
pause

:end
