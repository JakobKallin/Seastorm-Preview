@echo off
REM Change into the seattle_repy directory
FOR /F "tokens=*" %%A IN ('cd') DO SET OrigDir=%%A
SET TargetPath=%~f0
SET TargetDir=%TargetPath:start_seattle.bat=%
cd %TargetDir%

set seattle_config_file_found=not
FOR /F %%C IN ('findstr /M "seattle_installed: True" nodeman.cfg') DO SET seattle_config_file_found=%%C

IF "%seattle_config_file_found%"=="nodeman.cfg" goto START_SEATTLE_NOW
echo."Seattle has not yet been installed. Before seattle can be started, be sure to double click the install.bat file."
goto FINISH

:START_SEATTLE_NOW
start /min pythonw.exe nmmain.py
start /min pythonw.exe softwareupdater.py
goto FINISH

:FINISH
REM Go back up to the seattle directory.
cd ..
