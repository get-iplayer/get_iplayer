@echo off
setlocal

set PERLEXE=%~dp0perl.exe

:: if local perl.exe doesn't exist assume it can be found on PATH
if not exist "%PERLEXE%" set PERLEXE=perl.exe

"%PERLEXE%" "%~dp0get_iplayer.pl" %*
