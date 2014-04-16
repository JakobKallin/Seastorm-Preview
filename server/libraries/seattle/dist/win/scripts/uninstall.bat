@echo off
REM Change into the seattle_repy directory.
FOR /F "tokens=*" %%A IN ('cd') DO SET OrigDir=%%A
SET TargetPath=%~f0
SET TargetDir=%TargetPath:uninstall.bat=%
cd %TargetDir%

python seattleuninstaller.py %*

REM Go back up to the seattle directory.
cd ..