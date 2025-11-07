@echo off
REM === Create DurangDBack folder structure ===

mkdir DurangDBack
cd DurangDBack

echo Creating subfolders...
mkdir core
mkdir assets
mkdir notes
mkdir backup

echo.> main.py
echo.> README.md
echo.> core\__init__.py
echo.> core\note_manager.py
echo.> core\ui_manager.py

echo.
echo ✅ DurangDBack structure created successfully!
pause