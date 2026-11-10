@echo off
cd /d "%~dp0"
echo Building PDFReader...
python -m PyInstaller --noconsole --onefile --clean --name "PDFReader" --icon "app.ico" --add-data "app.ico;." --add-data "app.png;." reader.py
echo Done!
pause
