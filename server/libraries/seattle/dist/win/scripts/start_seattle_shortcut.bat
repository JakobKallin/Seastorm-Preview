@echo off
FOR /F "tokens=*" %%A IN ('cd') DO SET OrigDir=%%A
if not exist "%PROG_PATH%" goto REMOVAL
cd "%PROG_PATH%"
start_seattle.bat
goto END
:REMOVAL
del "%STARTER_FILE%"
got END
:END
cd %OrigDir%