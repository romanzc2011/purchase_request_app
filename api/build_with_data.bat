@echo on
echo Building PRAS API executable...

REM Build the executable
..\pras_venv\Scripts\pyinstaller.exe .\pras_api.spec --clean

REM Copy required data files
echo Copying data files...
if not exist "dist\db" mkdir "dist\db"
copy "db\*" "dist\db\"
copy "..\.env" "dist\.env"
if not exist "dist\img_assets" mkdir "dist\img_assets"
copy "img_assets\*" "dist\img_assets\"
if not exist "dist\src\assets\fonts" mkdir "dist\src\assets\fonts"
copy "..\src\assets\fonts\*" "dist\src\assets\fonts\"
if not exist "dist\services\smtp_service\templates" mkdir "dist\services\smtp_service\templates"
copy "services\smtp_service\templates\*" "dist\services\smtp_service\templates\"

echo Build complete with data files!
pause
