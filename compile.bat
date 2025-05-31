@echo off

:: Проверка наличия Nuitka в системе
python -m nuitka --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Nuitka is not installed in the system.
    echo Install Nuitka using: pip install nuitka
    pause
    exit /b 1
)

:: Проверка существования .env.local
if not exist ".env.local" (
    echo The .env.local file was not found!
    pause
    exit /b 1
)

:: Поиск значения DEBUG в .env.local
set DEBUG_VALUE=
for /f "usebackq tokens=1,2 delims==" %%i in (".env.local") do (
    if "%%i"=="DEBUG" set DEBUG_VALUE=%%j
)

:: Установка флага консоли в зависимости от DEBUG
set CONSOLE_FLAG=
if "%DEBUG_VALUE%"=="True" (
    echo [DEBUG] Debugging mode: The console will be TURNED ON
) else (
    set CONSOLE_FLAG=--windows-disable-console
    echo [PROD] Non-DEBUG mode: the console will be DISABLED
)

echo Compilation of the application using Nuitka...
python -m nuitka --standalone --onefile --enable-plugin=pyqt5 --msvc=latest --include-data-dir=images=images --output-dir=dist_win --windows-icon-from-ico=icon.ico --include-data-file=.env.local=.env.local --output-file=SkyWings %CONSOLE_FLAG% main.py

if %ERRORLEVEL% equ 0 (
    echo The compilation has been completed successfully!
) else (
    echo Error during compilation!
)

pause