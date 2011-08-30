@echo off
REM Build script for get_iplayer Perl support files
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
        set GIPPAR=%%A
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
md "%TMPDIR%" >> "%LOG%"
call :log Temp directory: %TMPDIR%
REM skip pp if PAR file specified
if not "%GIPPAR%"=="" (
    call :log Using specified PAR file: %GIPPAR%
    call :log Skipping pp...
    goto parskip
)
REM PAR file in current dir
set GIPPAR=%CD%\%PAREXE%
REM make PAR file if required/necessary
if not "%MAKEPAR%"=="" goto makepar
if not exist "%GIPPAR%" goto makepar
REM use default PAR file
if exist "%GIPPAR%" (
    call :log Using default PAR file: %GIPPAR%
    goto parskip
)
:makepar
REM location of pp
set PP=%PERLDIST%\perl\site\bin\pp
REM include modules from CPAN - pp will check if present
set PPMODS=-M MP3::Tag -M MP3::Info
REM force XML parsers into PAR
set PPMODS=%PPMODS% -M XML::LibXML::SAX -M XML::LibXML::SAX::Parser -M XML::SAX::PurePerl -M XML::Parser
call :log Running pp...
REM run pp
call perl "%PP%" %PPMODS% -o "%TMPDIR%\%PAREXE%" "%GIPDIR%\get_iplayer" "%GIPDIR%\get_iplayer.cgi" >> "%LOG%" 2>&1
REM check result
if %ERRORLEVEL% neq 0 (
    call :log ERROR: %PP% failed
    goto die
)
call :log ...Finished
REM copy output to current dir
copy /y "%TMPDIR%\%PAREXE%" "%GIPPAR%" >> "%LOG%" 2>&1
call :log Created: %GIPPAR%
REM make sure that PAR file is available
if not exist "%GIPPAR%" (
    call :log ERROR: Cannot find %GIPPAR%
    goto die
)
:parskip
REM unpack lib dir from PAR
call :log Unpacking Perl library...
REM filter out get_iplayer scripts and some unicore files
"%P7ZIP%" x "%GIPPAR%" -o"%TMPDIR%" -aoa -xr^^!get_iplayer* -xr^^!lib\unicore\*.txt ^
    -x^^!lib\unicore\mktables* -x^^!lib\unicore\TestProp.pl lib >> "%LOG%" 2>&1
call :log ...Finished
REM copy additional files from Strawberry Perl
call :log Copying Perl support files...
xcopy "%PERLDIST%\licenses\perl\*.*" "%TMPDIR%\perl-license" /e /i /r /y >> "%LOG%" 2>&1
copy /y "%PERLDIST%\perl\bin\*.dll" "%TMPDIR%" >> "%LOG%" 2>&1
copy /y "%PERLDIST%\perl\bin\perl.exe" "%TMPDIR%" >> "%LOG%" 2>&1
REM XML parser support
copy /y "%PERLDIST%\c\bin\libexpat*.dll" "%TMPDIR%" >> "%LOG%" 2>&1
copy /y "%PERLDIST%\c\bin\libiconv*.dll" "%TMPDIR%" >> "%LOG%" 2>&1
copy /y "%PERLDIST%\c\bin\libxml2*.dll" "%TMPDIR%" >> "%LOG%" 2>&1
copy /y "%PERLDIST%\c\bin\libz*.dll" "%TMPDIR%" >> "%LOG%" 2>&1
call :log ...Finished
REM create archive in temp dir
call :log Archiving Perl support files...
pushd "%TMPDIR%"
"%P7ZIP%" a "%TMPDIR%\%GIPZIP%" lib perl-license *.dll perl.exe >> "%LOG%" 2>&1
popd
call :log ...Finished
REM copy output to current dir
copy /y "%TMPDIR%\%GIPZIP%" "%CD%" >> "%LOG%" 2>&1
call :log Created: %CD%\%GIPZIP%
REM remove old expanded archive unconditionally
call :log Deleting old expanded Perl support archive...
rd /q /s "%CD%\%GIPPFX%" >> "%LOG%" 2>&1
call :log ...Finished
REM perl support as expanded archive
if not "%EXPAND%"=="" (
    call :log Extracting Perl support files...
    "%P7ZIP%" x "%CD%\%GIPZIP%" -o"%CD%\%GIPPFX%" >> "%LOG%" 2>&1
    call :log ...Finished
    call :log Created: %CD%\%GIPPFX%
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
echo Generate archive of Perl support files for get_iplayer
echo.
echo Usage:
echo   %~n0 [/keeptmp] [/makepar] [/expand] [\path\to\perlpar.exe]
echo   %~n0 /? - this message
echo.
echo Parameters:
echo   /keeptmp - retain contents of temp directory upon completion
echo   /makepar - force rebuild of PAR file (re-run pp)
echo   /expand  - expand Perl support archive in current directory
echo.
echo Input/Output (in current directory):
echo   perlpar.exe - PAR file [output from pp]
echo     (override by specifying PAR file on command line)
echo.
echo Output (in current directory):
echo   perlfiles.zip - Perl support archive
echo.
echo Required Perl modules (install from CPAN):
echo   MP3::Info   - localfiles plugin
echo   MP3::Tag    - MP3 tagging
echo   PAR::Packer - archive creation
echo.
