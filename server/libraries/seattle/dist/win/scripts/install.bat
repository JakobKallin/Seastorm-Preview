@echo off
REM change into the seattle_repy directory
FOR /F "tokens=*" %%A IN ('cd') DO SET OrigDir=%%A
SET TargetPath=%~f0
SET TargetDir=%TargetPath:install.bat=%
cd %TargetDir%

python seattleinstaller.py %*

REM Go back up the to seattle directory.
cd ..