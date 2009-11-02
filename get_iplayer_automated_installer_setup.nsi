;Product Info
Name "get_iplayer" ;Define your own software name here
!define PRODUCT "get_iplayer" ;Define your own software name here
!define VERSION "2.44+" ;Define your own software version here

; Script create for version 2.0rc1/final (from 12.jan.04) with GUI NSIS (c) by Dirk Paehl. Thank you for use my program

 !include "MUI.nsh"
 !include "Sections.nsh"


SetCompressor /SOLID lzma
;--------------------------------
;Configuration
 
   OutFile "get_iplayer_setup_${VERSION}.exe"

  ;Folder selection page
   InstallDir "$PROGRAMFILES\${PRODUCT}"
   
  ;DEFINE THE SETUP exe LOGO
  !define MUI_ICON "installer_files\iplayer_logo.ico"

  ;get all user profile path
  Var TempGlobalProfile
  Var pvr_file

;Remember install folder
InstallDirRegKey HKCU "Software\${PRODUCT}" ""

;--------------------------------
;Pages

  !insertmacro MUI_PAGE_WELCOME
  !insertmacro MUI_PAGE_LICENSE "installer_files\LICENSE.txt"
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  !insertmacro MUI_PAGE_FINISH
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES

 !define MUI_ABORTWARNING

 
;--------------------------------
 ;Language
 
  !insertmacro MUI_LANGUAGE "English"
;--------------------------------

     
Section "get_iplayer" section1
  ReadEnvStr $TempGlobalProfile "ALLUSERSPROFILE"
  SetOutPath "$INSTDIR"
  FILE /r "get_iplayer\*.*"
  
  ;clear the global files
  Delete $TempGlobalProfile\get_iplayer\*
  
  ;move the options file to the global position
  CreateDirectory $TempGlobalProfile\get_iplayer
  Rename "$INSTDIR\options" "$TempGlobalProfile\get_iplayer\options"

  FileOpen $pvr_file "$INSTDIR\run_pvr.bat" "w"
  FileWrite $pvr_file "cd $INSTDIR$\r$\n"
  FileWrite $pvr_file "get_iplayer.cmd --pvr$\r$\n"
  FileWrite $pvr_file "$\r$\n"
  FileClose "$pvr_file"

  ;download get_iplayer
  Delete $INSTDIR\get_iplayer.pl
  NSISdl::download http://linuxcentre.net/get_iplayer/get_iplayer $INSTDIR\get_iplayer.pl

  ;download get_iplayer.cgi
  NSISdl::download http://linuxcentre.net/winredirect/get_iplayer.cgi $INSTDIR\get_iplayer.cgi

  ;startmenu
  CreateDirectory "$SMPROGRAMS\get_iplayer"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Get_iPlayer.lnk" "$SYSDIR\cmd.exe" "/k get_iplayer.cmd --search dontshowanymatches && get_iplayer.cmd --help" "$INSTDIR\iplayer_logo.ico"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Update Get_iPlayer.lnk" "$SYSDIR\cmd.exe" "/k Update_get_iplayer.cmd" "$INSTDIR\iplayer_logo.ico"
  WriteIniStr "$INSTDIR\get_iplayer.url" "InternetShortcut" "URL" "http://linuxcentre.net/getiplayer/"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Show Home Page.lnk" "$INSTDIR\get_iplayer.url" "" "$SYSDIR\SHELL32.dll" 175
  WriteIniStr "$INSTDIR\command_examples.url" "InternetShortcut" "URL" "http://linuxcentre.net/getiplayer/documentation/"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Show Example Commands.lnk" "$INSTDIR\command_examples.url" "" "$SYSDIR\SHELL32.dll" 175
  CreateShortCut "$SMPROGRAMS\get_iplayer\Downloads Folder.lnk" "$INSTDIR\Downloads\"
  WriteIniStr "$INSTDIR\pvr_manager.url" "InternetShortcut" "URL" "http://127.0.0.1:1935"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Web PVR Manager.lnk" "$SYSDIR\cmd.exe" "/c pvr_manager.cmd" "$INSTDIR\iplayer_logo.ico"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Run PVR Now.lnk" "$SYSDIR\cmd.exe" "/k run_pvr.bat" "$INSTDIR\iplayer_logo.ico"

  ;uninstall info
  CreateShortCut "$SMPROGRAMS\get_iplayer\Uninstall.lnk" "$INSTDIR\uninst.exe" "" "$INSTDIR\uninst.exe" 0
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "DisplayName" "${PRODUCT} ${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "URLInfoAbout" "http://linuxcentre.net/getiplayer"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "Publisher" "Phil Lewis"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "UninstallString" "$INSTDIR\Uninst.exe"
  WriteRegStr HKCU "Software\${PRODUCT}" "" $INSTDIR
  WriteUninstaller "$INSTDIR\Uninst.exe"
SectionEnd
LangString DESC_Section1 ${LANG_ENGLISH} "Install get_iplayer."
   
Section "Mplayer" section2
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ;download mplayer
  NSISdl::download http://linuxcentre.net/winredirect/mplayer $INSTDIR\mplayer.zip
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of Mplayer failed: $R0, Install it manually"
    Return
  CreateDirectory "$INSTDIR\mplayer"
  ZipDLL::extractall $INSTDIR\mplayer.zip $INSTDIR\mplayer <ALL>
  Delete $INSTDIR\mplayer.zip
SectionEnd
LangString DESC_Section2 ${LANG_ENGLISH} "Download and install Mplayer from http://linuxcentre.net/winredirect/mplayer (10.3MB)"

Section "Lame" section3
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ;download lame
  NSISdl::download http://linuxcentre.net/winredirect/lame $INSTDIR\lame.zip
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of Lame failed: $R0, Install it manually"
    Return
  CreateDirectory "$INSTDIR\lame"
  ZipDLL::extractall $INSTDIR\lame.zip $INSTDIR\lame <ALL>
  Delete $INSTDIR\lame.zip
SectionEnd
LangString DESC_Section3 ${LANG_ENGLISH} "Download and install Lame from http://linuxcentre.net/winredirect/lame (535k)"

Section "ffmpeg" section4
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ;download ffmpeg
  CreateDirectory "$INSTDIR\ffmpeg"
  NSISdl::download http://linuxcentre.net/winredirect/ffmpeg "$INSTDIR\ffmpeg.tbz"
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of ffmpeg.tar.bz2 failed: $R0, Install it manually"
    Return
  untgz::extract  -zbz2  -d "$INSTDIR\ffmpeg" "$INSTDIR\ffmpeg.tbz" 
  DetailPrint "untgz returned ($R0)"
  Delete "$INSTDIR\ffmpeg.tbz"
SectionEnd
LangString DESC_Section4 ${LANG_ENGLISH} "Download and install ffmpeg from http://linuxcentre.net/winredirect/ffmpeg (6.3MB)"

Section "VLC" section5
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ;download vlc
  NSISdl::download http://linuxcentre.net/winredirect/vlc $INSTDIR\vlc.7z
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of VLC failed: $R0, Install it manually"
    Return
  Nsis7z::Extract "$INSTDIR\vlc.7z"
  Delete $INSTDIR\vlc.7z
  Rename "$INSTDIR\vlc-1.0.1" "$INSTDIR\vlc"
SectionEnd
LangString DESC_Section5 ${LANG_ENGLISH} "Download and install VLC from http://linuxcentre.net/winredirect/vlc (15.0MB)"

Section /o "flvstreamer (non-cygwin)" section6
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ;download flvstreamer
  NSISdl::download http://linuxcentre.net/winredirect/flvstreamer "$INSTDIR\flvstreamer.exe"
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of flvstreamer failed: $R0, Install it manually"
    Return
SectionEnd
LangString DESC_Section6 ${LANG_ENGLISH} "Download and install flvstreamer(win32) from http://linuxcentre.net/winredirect/flvstreamer (~300k)"

Section "flvstreamer (using cygwin library)" section7
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ;download flvstreamer-cygwin
  NSISdl::download http://linuxcentre.net/winredirect/flvstreamer-cygwin "$INSTDIR\flvstreamer.exe"
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of flvstreamer(cygwin) failed: $R0, Install it manually"
    Return
  NSISdl::download http://linuxcentre.net/winredirect/cygwindll "$INSTDIR\cygwin1.dll"
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of cygwin library failed: $R0, Install it manually"
    Return
SectionEnd
LangString DESC_Section7 ${LANG_ENGLISH} "Download and install flvstreamer(win32/cygwin) from http://linuxcentre.net/winredirect/flvstreamer-cygwin (~2500k)"


!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${Section1} $(DESC_Section1)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section2} $(DESC_Section2)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section3} $(DESC_Section3)  
  !insertmacro MUI_DESCRIPTION_TEXT ${Section4} $(DESC_Section4)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section5} $(DESC_Section5)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section6} $(DESC_Section6)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section7} $(DESC_Section7)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

 
Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer.."
FunctionEnd
  
Function un.onInit 
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to completely remove $(^Name) and all of its components?" IDYES +2
  Abort
FunctionEnd
 
Section "Uninstall" 
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Remove Downloaded Files?" IDYES true1 IDNO false1
  true1:
    Delete  "$INSTDIR\Downloads\*.*" 
    RMDir "$INSTDIR\Downloads"
    Goto next1
  false1:
    ;do nothing
  next1:
  
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Remove User Preferences, PVR Searches, Presets and Recording History?" IDYES true2 IDNO false2
  true2:
    ;delete the local user data
    Delete $PROFILE\.get_iplayer\*
    RmDir $PROFILE\.get_iplayer
    Goto next2
  false2:
    ;do nothing
  next2:

  ReadEnvStr $TempGlobalProfile "ALLUSERSPROFILE"
  RMDir /r "$INSTDIR\mplayer"  
  RMDir /r "$INSTDIR\lame"
  RMDir /r "$INSTDIR\ffmpeg\Doc\ffpresets"
  RMDir /r "$INSTDIR\ffmpeg\Doc"  
  RMDir /r "$INSTDIR\ffmpeg"
  RMDir /r "$INSTDIR\vlc"
  RMDir /r "$INSTDIR\lib"
  RMDir /r "$INSTDIR\perl-license"
  Delete  "$INSTDIR\*.*" 
  Delete "$SMPROGRAMS\get_iplayer\*.*"
  RmDir "$SMPROGRAMS\get_iplayer"
  
  ;remove the global options file 
  Delete $TempGlobalProfile\get_iplayer\options
  RmDir $TempGlobalProfile\get_iplayer
   
  DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\get_iplayer"
  DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer"
  RMDir "$INSTDIR"
             
SectionEnd
               


Function .onInit
 
  ReadRegStr $R0 HKLM \
  "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}" \
  "UninstallString"
  StrCmp $R0 "" done
 
  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
  "${PRODUCT} is already installed. $\n$\nClick `OK` to remove the \
  previous version or `Cancel` to continue this upgrade without uninstalling (not recomended for pre 1.4)." \
  IDOK uninst
  Return
 
;Run the uninstaller
uninst:
  ClearErrors
  ExecWait '$R0 _?=$INSTDIR' ;Do not copy the uninstaller to a temp file
  
done:
 
FunctionEnd


Function ConnectInternet

  Push $R0
    
    ClearErrors
    Dialer::AttemptConnect
    IfErrors noie3
    
    Pop $R0
    StrCmp $R0 "online" connected
      MessageBox MB_OK|MB_ICONSTOP "Cannot connect to the internet."
      Quit
    
    noie3:
  
    ; IE3 not installed
    MessageBox MB_OK|MB_ICONINFORMATION "Please connect to the internet now."
    
    connected:
  
  Pop $R0
  
FunctionEnd
   
;eof
