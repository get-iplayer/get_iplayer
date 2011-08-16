@echo off
REM Utility script to download get_iplayer helper applications
setlocal EnableDelayedExpansion
REM show help if requested
echo.%1 | find "?" >NUL
if not ERRORLEVEL 1 goto usage
REM script location
set CMDDIR=%~dp0
set CMDNAME=%~n0
REM perform common init
call "%CMDDIR%\make-init"
if %ERRORLEVEL% neq 0 (
    call :log ERROR: %CMDDIR%\make-init failed
    goto die
)
call :log START %CMDNAME% %date% %time%
REM process command line
for %%A in (%*) do (
    set FLAG=%%A
    set FLAG=!FLAG:/D=!
    set FLAG=!FLAG:/=!
    set !FLAG!=/D!FLAG!
)
REM create clean temp dir
if exist "%TMPDIR%" (
    rd /q /s "%TMPDIR%" >> "%LOG%" 2>&1
)
md "%TMPDIR%"
call :log Temp directory: %TMPDIR%
REM rebuild if requested
if not "%REBUILD%"=="" goto rebuild
if not exist "%CD%\%CMDNAME%.exe" goto rebuild
goto exeskip
:rebuild
REM build in temp dir
call :log Building installer...
"%MAKENSIS%" /NOCD /DBUILDPATH="%TMPDIR%" "%GIPDIR%\windows\%CMDNAME%.nsi" >> "%LOG%" 2>&1
if %ERRORLEVEL% neq 0 (
    call :log ERROR: %MAKENSIS% failed
    goto die
)
call :log ...Finished
copy /y "%TMPDIR%\%CMDNAME%.exe" "%CD%" >> "%LOG%" 2>&1
call :log Created: %CD%\%CMDNAME%.exe
:exeskip
call :log Running installer...
call %CD%\%CMDNAME%.exe
call :log ...Finished
REM clean up
rd /q /s "%TMPDIR%" >> "%LOG%" 2>&1
call :log FINISH %CMDNAME% %date% %time%
:done
exit /b
:die
echo Exiting - see %LOG%
exit /b 1
:log
echo %*
echo %* >> "%LOG%"
goto :eof
:usage
echo.
echo Generate and run NSIS installer to download get_iplayer helper applications
echo.
echo Usage:
echo   %~n0 [/rebuild]
echo   %~n0 /? - this message
echo.
echo Parameters:
echo   /rebuild - force rebuild of installer
echo.
