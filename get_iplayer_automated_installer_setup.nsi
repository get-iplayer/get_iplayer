;Product Info
Name "get_iplayer" ;Define your own software name here
!define PRODUCT "get_iplayer" ;Define your own software name here
!define VERSION "1.5+" ;Define your own software version here

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
  FileWrite $pvr_file "cd $\"C:\Program Files\get_iplayer$\"$\r$\n"
  FileWrite $pvr_file "get_iplayer.cmd --pvr$\r$\n"
  FileWrite $pvr_file "$\r$\n"
  FileClose "$pvr_file"

  ;download get_iplayer
  Delete $INSTDIR\get_iplayer.pl
  NSISdl::download http://linuxcentre.net/get_iplayer/get_iplayer $INSTDIR\get_iplayer.pl

  ;startmenu
  CreateDirectory "$SMPROGRAMS\get_iplayer"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Get Iplayer.lnk" "$SYSDIR\cmd.exe" "/k get_iplayer.cmd" "$INSTDIR\iplayer_logo.ico"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Update Get Iplayer.lnk" "$SYSDIR\cmd.exe" "/k Update_get_iplayer.cmd" "$INSTDIR\iplayer_logo.ico"
  WriteIniStr "$INSTDIR\get_iplayer.url" "InternetShortcut" "URL" "http://linuxcentre.net/getiplayer/"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Help.lnk" "$INSTDIR\get_iplayer.url" "" "$SYSDIR\SHELL32.dll" 175
  WriteIniStr "$INSTDIR\command_examples.url" "InternetShortcut" "URL" "http://linuxcentre.net/getiplayer/documentation/"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Example Commands.lnk" "$INSTDIR\command_examples.url" "" "$SYSDIR\SHELL32.dll" 175
  CreateShortCut "$SMPROGRAMS\get_iplayer\Download Directory.lnk" "$INSTDIR\Downloads\"
  
  ;uninstall info
  CreateShortCut "$SMPROGRAMS\get_iplayer\Uninstall.lnk" "$INSTDIR\uninst.exe" "" "$INSTDIR\uninst.exe" 0
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "DisplayName" "${PRODUCT} ${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "URLInfoAbout" "http://linuxcentre.net/?page_id=6"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "Publisher" "Phill Lewis"
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

Section "rtmpdump" section5
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ;download rtmpdump
  NSISdl::download http://linuxcentre.net/get_iplayer/contrib/rtmpdump-WIN32-latest.exe "$INSTDIR\rtmpdump.exe"
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of rtmp failed: $R0, Install it manually"
    Return
    
SectionEnd
LangString DESC_Section5 ${LANG_ENGLISH} "Download and install rtmpdump(win32) from http://linuxcentre.net/get_iplayer/contrib/rtmpdump-WIN32-latest.exe (~650k)"


!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${Section1} $(DESC_Section1)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section2} $(DESC_Section2)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section3} $(DESC_Section3)  
  !insertmacro MUI_DESCRIPTION_TEXT ${Section4} $(DESC_Section4)  
  !insertmacro MUI_DESCRIPTION_TEXT ${Section5} $(DESC_Section5)   
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
  MessageBox MB_YESNO "Remove Downloaded Files?" IDYES true IDNO false
  true:
    Delete  "$INSTDIR\Downloads\*.*" 
    RMDir "$INSTDIR\Downloads"
    Goto next
  false:
    ;do nothing
  next:
  
  ReadEnvStr $TempGlobalProfile "ALLUSERSPROFILE"
  RMDir /r "$INSTDIR\mplayer"  
  RMDir /r "$INSTDIR\lame"
  RMDir /r "$INSTDIR\ffmpeg\Doc\ffpresets"
  RMDir /r "$INSTDIR\ffmpeg\Doc"  
  RMDir /r "$INSTDIR\ffmpeg"
  RMDir /r "$INSTDIR\lib"
  RMDir /r "$INSTDIR\perl-license"
  Delete  "$INSTDIR\*.*" 
  Delete "$SMPROGRAMS\get_iplayer\*.*"
  RmDir "$SMPROGRAMS\get_iplayer"
  
  ;remove the global options file 
  Delete $TempGlobalProfile\get_iplayer\options
  RmDir $TempGlobalProfile\get_iplayer
  
  ;delete the local user data
  Delete $PROFILE\.get_iplayer\*
  RmDir $PROFILE\.get_iplayer
 
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
