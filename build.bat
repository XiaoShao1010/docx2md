@echo off
echo ========================================
echo   DOCX2MD — Build Windows Executable
echo ========================================
echo.

echo [1/2] Installing dependencies...
pip install -r requirements.txt pyinstaller -q

echo [2/2] Building exe with PyInstaller...
pyinstaller docx2md.spec --clean

if exist "dist\docx2md.exe" (
    echo.
    echo ========================================
    echo   Build complete: dist\docx2md.exe
    echo ========================================
) else (
    echo.
    echo ERROR: Build failed — dist\docx2md.exe not found.
)
pause
