REM Common startup code for make-perlfiles and make-installer
if not "%MAKEINIT%"=="" goto done
set MAKEINIT=MAKEINIT
REM init logfile
set LOG=%CD%\%CMDNAME%.log
echo Logging to file: %LOG%
REM get base dir - assumes script in %BASEDIR%\get_iplayer\windows
for %%D in (%CMDDIR%..\..) do (
    set BASEDIR=%%~fD
)
REM location of get_iplayer source
set GIPDIR=%BASEDIR%\get_iplayer
REM perl support naming
set PAREXE=perlpar.exe
set GIPPFX=perlfiles
set GIPEXE=%GIPPFX%.exe
set GIPZIP=%GIPPFX%.zip
REM location of installer script
set NSIDIR=%GIPDIR%\windows
set NSIPFX=get_iplayer_setup
set NSIFILE=%NSIPFX%.nsi
REM temp dir
REM set TMPDIR=%TEMP%\%CMDNAME%%RANDOM%
set TMPDIR=%CD%\%CMDNAME%.tmp
REM location of NSIS installation
set NSISDIR=C:\Program Files\NSIS
set MAKENSIS=%NSISDIR%\makensis.exe
REM location of 7-Zip utility
set P7ZIP=C:\Program Files\7-Zip\7z.exe
REM location of Strawberry Perl
set PERLDIST=C:\strawberry
REM get version numbers as sanity check
set BADVER=0
REM determine perl version
set PERLVER=0.0.0
for /f "usebackq tokens=1-3 delims=v." %%A in (`perl -e "print $^V;"`) do (
    set PERLVER=%%A.%%B.%%C
)
if "%PERLVER%"=="0.0.0" (
    call :log Could not determine Perl version
    set BADVER=1
)
call :log Perl version: %PERLVER%
REM extract get_iplayer version
set GIPVER=0.00
for /f "usebackq tokens=1" %%V in (`perl -nle "print $1 if /^\s*my\s+\$version\W+(\d+\.\d+)/; exit if $1;" "%GIPDIR%\get_iplayer"`) do (
    set GIPVER=%%V
)
if "%GIPVER%"=="0.00" (
    call :log Could not determine get_iplayer version
    set BADVER=1
)
call :log get_iplayer version: %GIPVER%
REM extract installer version
set INSTVER=0.0
for /f "usebackq tokens=1" %%V in (`perl -nle "print $1 if /^\s*\Wdefine\s+VERSION\W+(\d+\.\d+)/; exit if $1;" "%NSIDIR%\%NSIFILE%"`) do (
    set INSTVER=%%V
)
if "%INSTVER%"=="0.0" (
    call :log Could not determine installer version
    set BADVER=1
)
call :log Installer version: %INSTVER%
if %BADVER% equ 1 goto die
:done
exit /b
:die
exit /b 1
:log
echo %*
echo %* >> "%LOG%"
goto :eof
