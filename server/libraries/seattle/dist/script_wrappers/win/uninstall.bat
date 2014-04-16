@echo off
REM Change into the seattle_repy directory.
FOR /F "tokens=*" %%A IN ('cd') DO SET OrigDir=%%A
SET TargetPath=%~f0
SET seattle_repyDir=%TargetPath:uninstall.bat=seattle_repy%
cd %seattle_repyDir%

uninstall.bat %*

cd %OrigDir%