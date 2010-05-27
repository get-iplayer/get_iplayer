;Product Info
Name "get_iplayer"
!define PRODUCT "get_iplayer"
!define VERSION "4.0" 

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
  FileWrite $pvr_file "cd $\"$INSTDIR$\"$\r$\n"
  FileWrite $pvr_file "get_iplayer.cmd --pvr$\r$\n"
  FileWrite $pvr_file "$\r$\n"
  FileClose "$pvr_file"

  ;download get_iplayer
  Delete $INSTDIR\get_iplayer.pl
  NSISdl::download http://www.infradead.org/get_iplayer/get_iplayer $INSTDIR\get_iplayer.pl

  ;download get_iplayer.cgi
  NSISdl::download http://www.infradead.org/get_iplayer/get_iplayer.cgi $INSTDIR\get_iplayer.cgi

  ;startmenu
  CreateDirectory "$SMPROGRAMS\get_iplayer"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Get_iPlayer.lnk" "$SYSDIR\cmd.exe" "/k get_iplayer.cmd --search dontshowanymatches && get_iplayer.cmd --help" "$INSTDIR\iplayer_logo.ico"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Update Get_iPlayer.lnk" "$SYSDIR\cmd.exe" "/k Update_get_iplayer.cmd" "$INSTDIR\iplayer_logo.ico"
  WriteIniStr "$INSTDIR\get_iplayer.url" "InternetShortcut" "URL" "http://wiki.github.com/jjl/get_iplayer/"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Show Home Page.lnk" "$INSTDIR\get_iplayer.url" "" "$SYSDIR\SHELL32.dll" 175
  WriteIniStr "$INSTDIR\command_examples.url" "InternetShortcut" "URL" "http://wiki.github.com/jjl/get_iplayer/"
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
  NSISdl::download "http://www8.mplayerhq.hu/MPlayer/releases/win32/MPlayer-mingw32-1.0rc2.zip" "$INSTDIR\mplayer.zip"
  ;NSISdl::download "http://www.infradead.org/cgi-bin/get_iplayer.cgi?mplayer" "$INSTDIR\mplayer.zip"
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of Mplayer failed: $R0, Mplayer install failed, Install it manually"
    Return
  CreateDirectory "$INSTDIR\mplayer"
  ZipDLL::extractall $INSTDIR\mplayer.zip $INSTDIR\mplayer <ALL>
  Delete $INSTDIR\mplayer.zip
SectionEnd
LangString DESC_Section2 ${LANG_ENGLISH} "Download and install Mplayer (~10MB)"

Section "Lame" section3
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ;download lame
  CreateDirectory "$INSTDIR\lame"
  SetOutPath "$INSTDIR\lame"
  NSISdl::download "http://lame.bakerweb.biz/lame-3.98.2.7z" "$INSTDIR\lame\lame.7z"
  ;NSISdl::download "http://www.infradead.org/cgi-bin/get_iplayer.cgi?lame" "$INSTDIR\lame\lame.7z"
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of Lame failed: $R0, Install it manually"
    Return
  CreateDirectory "$INSTDIR\lame"
  Nsis7z::ExtractWithDetails "$INSTDIR\lame\lame.7z" "Installing package %s..."
  Delete "$INSTDIR\lame\lame.7z"
  SetOutPath "$INSTDIR"
SectionEnd
LangString DESC_Section3 ${LANG_ENGLISH} "Download and install Lame (~1MB)"

Section "ffmpeg" section4
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ;download ffmpeg
  CreateDirectory "$INSTDIR\ffmpeg"
  SetOutPath "$INSTDIR\ffmpeg"
  ;NSISdl::download  "http://www.infradead.org/cgi-bin/get_iplayer.cgi?ffmpeg" $INSTDIR\ffmpeg\ffmpeg.7z
  NSISdl::download  "http://ffmpeg.arrozcru.org/autobuilds/ffmpeg-latest-mingw32-static.7z" "$INSTDIR\ffmpeg\ffmpeg.7z"
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of ffmpeg.7z failed: $R0, Install it manually"
    Return
    Nsis7z::ExtractWithDetails "$INSTDIR\ffmpeg\ffmpeg.7z" "Installing package %s..."
  Delete "$INSTDIR\ffmpeg\ffmpeg.7z"
  SetOutPath "$INSTDIR"
SectionEnd
LangString DESC_Section4 ${LANG_ENGLISH} "Download and install ffmpeg (~6MB)"

Section "VLC" section5
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ;download vlc
  SetOutPath "$INSTDIR\"
  NSISdl::download "http://www.grangefields.co.uk/mirrors/videolan/vlc/1.0.5/win32/vlc-1.0.5-win32.7z" "$INSTDIR\vlc.7z"
  ;NSISdl::download "http://www.infradead.org/cgi-bin/get_iplayer.cgi?vlc" "$INSTDIR\vlc.7z"
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of VLC failed: $R0, Install it manually"
    Return
  Nsis7z::ExtractWithDetails "$INSTDIR\vlc.7z"  "Installing package %s..."
  Delete $INSTDIR\vlc.7z
  SetOutPath "$INSTDIR"
  Rename "$INSTDIR\vlc-1.0.5" "$INSTDIR\vlc"
SectionEnd
LangString DESC_Section5 ${LANG_ENGLISH} "Download and install VLC (~15MB)"

Section "rtmpdump" section6
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ;download flvstreamer
  NSISdl::download http://www.infradead.org/cgi-bin/get_iplayer.cgi?rtmpdumpz "$INSTDIR\rtmpdump.zip"
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of rtmpdump failed: $R0, Install it manually"
    Return
  ZipDLL::extractall $INSTDIR\rtmpdump.zip $INSTDIR <ALL>
  Delete $INSTDIR\rtmpdump.zip
SectionEnd
LangString DESC_Section6 ${LANG_ENGLISH} "Download and install rtmpdump(win32) (~300k)"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${Section1} $(DESC_Section1)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section2} $(DESC_Section2)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section3} $(DESC_Section3)  
  !insertmacro MUI_DESCRIPTION_TEXT ${Section4} $(DESC_Section4)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section5} $(DESC_Section5)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section6} $(DESC_Section6)
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
  RMDir /r "$INSTDIR\secure"
  RMDir /r "$INSTDIR\mplayer"  
  RMDir /r "$INSTDIR\lame"
  RMDir /r "$INSTDIR\ffmpeg\Doc\ffpresets"
  RMDir /r "$INSTDIR\ffmpeg\Doc"  
  RMDir /r "$INSTDIR\ffmpeg"
  RMDir /r "$INSTDIR\vlc"
  RMDir /r "$INSTDIR\lib"
  RMDir /r "$INSTDIR\perl-license"
  RMDir /r "$INSTDIR\rtmpdump-2.2d"
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
