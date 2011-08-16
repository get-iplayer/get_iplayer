@echo off
REM Build script for get_iplayer installer
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
    if exist "%%A" (
        set PERLARC=%%A
    ) else (
        set FLAG=%%A
        set FLAG=!FLAG:/D=!
        set FLAG=!FLAG:/=!
        set !FLAG!=/D!FLAG!
    )
)
REM create clean temp dir
if exist "%TMPDIR%" (
    rd /q /s "%TMPDIR%" >> "%LOG%" 2>&1
)
md "%TMPDIR%"
call :log Temp directory: %TMPDIR%
REM helper app archives folder in current dir
set HELPERS=%CD%\helpers
REM skip perl if requested
if not "%WITHOUTPERL%"=="" (
    call :log Skipping perl support
    goto perldone
)
REM force makeperl if specified
if not "%MAKEPERL%"=="" (
    set PERLARC=%CD%\%GIPZIP%
    goto makeperl
)
REM skip makeperl if perl archive specified
if not "%PERLARC%"=="" (
    call :log Using specified Perl archive: %PERLARC%
    call :log Skipping makeperl...
    goto perlskip
)
REM skip makeperl if expanded archive found in current dir
if exist "%CD%\%GIPPFX%" (
    call :log Using expanded Perl support archive: %CD%\%GIPPFX%
    set PERLFILES=%CD%\%GIPPFX%
    goto perldone
)
REM default perl support archive in current dir
set PERLARC=%CD%\%GIPZIP%
if exist "%PERLARC%" (
    call :log Using default Perl support archive: %PERLARC%
    goto perlskip
)
:makeperl
set PERLARC=%CD%\%GIPZIP%
REM rebuild perl support archive in current dir
call :log Calling %CMDDIR%\make-perlfiles /makepar %KEEPTMP%
call "%CMDDIR%\make-perlfiles" /makepar %KEEPTMP%
if %ERRORLEVEL% neq 0 (
    call :log ERROR: %CMDDIR%\make-perlfiles failed
    goto die
)
REM make sure that archive is available
if not exist "%PERLARC%" (
    call :log ERROR: Cannot find %PERLARC%
    goto die
)
:perlskip
REM perl support as expanded archive
call :log Extracting Perl support files...
set PERLFILES=%TMPDIR%\%GIPPFX%
"%P7ZIP%" x "%PERLARC%" -o"%PERLFILES%" >> "%LOG%" 2>&1
call :log ...Finished
:perldone
REM build in temp dir
call :log Building installer...
"%MAKENSIS%" /NOCD %WITHOUTPERL% %WITHSCRIPTS% %WITHHELPERS% %STANDALONE% %NOCONFIG% %NOCHECK% %PRERELEASE% ^
    /DBUILDPATH="%TMPDIR%" /DSOURCEPATH="%GIPDIR%" /DPERLFILES="%PERLFILES%" /DHELPERS="%HELPERS%" ^
    "%NSIDIR%\%NSIFILE%" >> "%LOG%" 2>&1
if %ERRORLEVEL% neq 0 (
    call :log ERROR: %MAKENSIS% failed
    goto die
)
call :log ...Finished
REM copy output to current dir
for %%A in ("%TMPDIR%\%NSIPFX%*.exe") do (
    copy /y "%%A" "%CD%" >> "%LOG%" 2>&1
    call :log Created: %CD%\%%~nxA
)
REM clean up
if "%KEEPTMP%"=="" (
    rd /q /s "%TMPDIR%" >> "%LOG%" 2>&1
) else (
    call :log /keeptmp specified - files available in %TMPDIR%
)
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
echo Generate NSIS installer for get_iplayer
echo.
echo Usage:
echo   %~n0 [/keeptmp] [/makeperl] [/withoutperl]
echo     [/withscripts] [/withhelpers] [/standalone]
echo     [/offline] [/prelease] [\path\to\perlfiles.zip]
echo   %~n0 /? - this message
echo.
echo Parameters:
echo   /keeptmp     - retain contents of temp directory
echo   /makeperl    - force rebuild of Perl support archive
echo   /withoutperl - omit Perl support from build
echo   /withscripts - embed get_iplayer Perl scripts in build
echo   /withhelpers - embed get_iplayer helper apps in build
echo   /standalone  - /withscripts + /withhelpers
echo   /noconfig    - use CGI script for download URLs instead of config file
echo   /nocheck     - no installer update check (testing only)
echo   /prerelease  - prerelease build with warning dialog at launch
echo.
echo Input (in current directory):
echo   perlfiles     - expanded Perl support archive
echo   OR (if expanded archive not found):
echo   perlfiles.zip - Perl support archive file [output from make-perlfiles]
echo     (override by specifying Perl archive file on command line)
echo   helpers       - folder with helper app archives (/withhelpers only)
echo.
echo Output (in current directory):
echo   get_iplayer_setup_N.N.exe - installer EXE
echo     (N.N = installer version)
echo.
