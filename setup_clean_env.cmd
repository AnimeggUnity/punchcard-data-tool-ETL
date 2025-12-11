@echo off
chcp 65001 >nul
echo ==========================================
echo Create clean virtual environment for packaging
echo ==========================================

REM Delete old virtual environment if exists
if exist "venv_clean" (
    echo Removing old virtual environment...
    rmdir /s /q venv_clean
)

REM Create new virtual environment
echo Creating new virtual environment...
python -m venv venv_clean

REM Activate virtual environment
echo Activating virtual environment...
call venv_clean\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install required packages
echo Installing required packages...
pip install -r requirements.txt

REM Display installed packages
echo ==========================================
echo Installed packages list:
pip list

echo ==========================================
echo Virtual environment setup completed!
echo To activate the environment manually, run:
echo call venv_clean\Scripts\activate.bat
echo ==========================================
pause