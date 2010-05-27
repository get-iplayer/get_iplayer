@echo off
start "PVR Manager Service" /min /b cmd /k .\get_iplayer.cgi.cmd
ping 127.0.0.1 -n 5 -w 1000 > NUL
.\pvr_manager.url
