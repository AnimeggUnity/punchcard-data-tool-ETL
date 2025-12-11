@echo off
chcp 65001 >nul
echo ==========================================
echo Punch Helper ETL - Clean Environment Build (最終版)
echo ==========================================

if not exist "venv_clean" (
    echo.
    echo ERROR: 找不到 venv_clean 資料夾！
    echo 請先執行 setup_clean_env.cmd 建立乾淨環境
    echo.
    pause
    exit /b 1
)

set VENV_PYTHON=%CD%\venv_clean\Scripts\python.exe
set VENV_PYINSTALLER=%CD%\venv_clean\Scripts\pyinstaller.exe

echo 使用乾淨環境 Python: %VENV_PYTHON%
echo.

%VENV_PYTHON% -c "from gui.main_window import run_app; print('匯入測試成功')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: 在乾淨環境中無法匯入程式！
    pause
    exit /b 1
)

if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
for %%f in (*.spec) do del /q "%%f" 2>nul

echo.
echo 正在偵測 UPX...
set UPX_ARGS=
where upx >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [UPX] 找到 upx，啟用壓縮
    set UPX_ARGS=--upx-dir . --upx-exclude python311.dll --upx-exclude python312.dll
) else if exist "%~dp0upx.exe" (
    echo [UPX] 在腳本目錄找到 upx.exe，啟用壓縮
    set UPX_ARGS=--upx-dir "%~dp0" --upx-exclude python311.dll --upx-exclude python312.dll
) else (
    echo [UPX] 未找到 upx，跳過壓縮
)

echo.
echo 開始打包（最精簡 + config.py 完全外部）...
echo.

%VENV_PYINSTALLER% ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --name="PunchHelper" ^
    --add-data "templates;templates" ^
    --hidden-import pydantic ^
    --hidden-import pydantic_core ^
    --hidden-import FreeSimpleGUI ^
    --hidden-import openpyxl ^
    --collect-all pydantic ^
    --exclude-module config ^
    --exclude-module config.py ^
    --exclude-module pydantic.json_schema ^
    --exclude-module pydantic.annotated ^
    --exclude-module pydantic.dataclasses ^
    --exclude-module pydantic.functional_validators ^
    --exclude-module pydantic.tools ^
    --exclude-module pydantic.deprecated ^
    --exclude-module pydantic.alias_generators ^
    --exclude-module pydantic_extra_types ^
    --exclude-module pydantic._migration ^
    --exclude-module pydantic._rich_repr ^
    --exclude-module matplotlib ^
    --exclude-module cryptography ^
    --exclude-module pytest ^
    --exclude-module IPython ^
    --exclude-module notebook ^
    %UPX_ARGS% ^
    main.py

if exist "dist\PunchHelper\PunchHelper.exe" (
    echo.
    echo ==========================================
    echo 打包成功！
    echo ==========================================
    echo.

    REM 複製 config.py 和 README.md 到打包資料夾
    echo 複製必要檔案到打包資料夾...
    if exist "config.py" (
        copy /Y "config.py" "dist\PunchHelper\" >nul
        echo [OK] config.py 已複製
    ) else (
        echo [WARNING] 找不到 config.py
    )

    if exist "README.md" (
        copy /Y "README.md" "dist\PunchHelper\" >nul
        echo [OK] README.md 已複製
    ) else (
        echo [WARNING] 找不到 README.md
    )

    echo.
    dir "dist\PunchHelper\PunchHelper.exe"
    echo.
    if defined UPX_ARGS (echo 預估大小: 28~38 MB) else (echo 預估大小: 45~55 MB)
    echo.
    echo ==========================================
    echo 部署方式:
    echo 1. 複製整個 dist\PunchHelper 資料夾
    echo 2. 執行 PunchHelper.exe
    echo ==========================================
) else (
    echo.
    echo 打包失敗! 請查看上方錯誤訊息
)

pause