;Product Info
Name "get_iplayer" ;Define your own software name here
!define PRODUCT "get_iplayer" ;Define your own software name here
!define VERSION "2.54+" ;Define your own software version here

; Script create for version 2.0rc1/final (from 12.jan.04) with GUI NSIS (c) by Dirk Paehl. Thank you for use my program

 !include "MUI.nsh"
 !include "Sections.nsh"


SetCompressor /SOLID lzma
;--------------------------------
;Configuration
 
  OutFile "get_iplayer_setup_${VERSION}.exe"

  ;Folder selection page
  InstallDir "$PROGRAMFILES\${PRODUCT}\"
   
  ;DEFINE THE SETUP exe LOGO
  !define MUI_ICON "installer_files\iplayer_logo.ico"

  ;get all user profile path
  Var TempGlobalProfile
  Var TempUserProfile
  Var pvr_file
  Var opt_file
  Var DataDir
  Var InstallDir

  ;Remember install folder
  InstallDirRegKey HKCU "Software\${PRODUCT}" ""


;--------------------------------
;Pages

  !insertmacro MUI_PAGE_WELCOME
  !insertmacro MUI_PAGE_LICENSE "installer_files\LICENSE.txt"
  !insertmacro MUI_PAGE_COMPONENTS

  !define MUI_PAGE_CUSTOMFUNCTION_SHOW DirectoryShow
  !define MUI_PAGE_CUSTOMFUNCTION_LEAVE DirectoryLeave
  !insertmacro MUI_PAGE_DIRECTORY

  !define MUI_PAGE_CUSTOMFUNCTION_SHOW RecordingsDirectoryShow
  !define MUI_PAGE_CUSTOMFUNCTION_LEAVE RecordingsDirectoryLeave
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
  ReadEnvStr $TempUserProfile "USERPROFILE"
  SetOutPath "$InstallDir"
  FILE /r "get_iplayer\*.*"
  
  ;clear the global files
  Delete $TempGlobalProfile\get_iplayer\*
  
  ;move the options file to the global position
  CreateDirectory $TempGlobalProfile\get_iplayer
  
  ;create user download folder
  ;;CreateDirectory "$TempUserProfile\Desktop\iPlayer Recordings\"
  CreateDirectory $DataDir

  ;create options file
  FileOpen $opt_file "$TempGlobalProfile\get_iplayer\options" "w"
  FileWrite $opt_file "lame .\lame\lame.exe$\r$\n"
  FileWrite $opt_file "mplayer .\mplayer\MPlayer-1.0rc2\mplayer.exe$\r$\n"
  ;;FileWrite $opt_file "output $TempUserProfile\Desktop\iPlayer Recordings\$\r$\n"
  FileWrite $opt_file "output $DataDir$\r$\n"
  FileWrite $opt_file "flvstreamer .\flvstreamer.exe$\r$\n"
  FileWrite $opt_file "ffmpeg .\ffmpeg\bin\ffmpeg.exe$\r$\n"
  FileWrite $opt_file "vlc .\vlc\vlc.exe$\r$\n"
  FileWrite $opt_file "mmsnothread 1$\r$\n"
  FileWrite $opt_file "nopurge 1$\r$\n"
  FileClose "$opt_file"

  FileOpen $pvr_file "$InstallDir\run_pvr.bat" "w"
  FileWrite $pvr_file "cd $InstallDir$\r$\n"
  FileWrite $pvr_file "get_iplayer.cmd --pvrschedule 14400$\r$\n"
  FileWrite $pvr_file "$\r$\n"
  FileClose "$pvr_file"

  ;download get_iplayer
  Delete $InstallDir\get_iplayer.pl
  NSISdl::download http://linuxcentre.net/get_iplayer/get_iplayer $InstallDir\get_iplayer.pl

  ;download get_iplayer.cgi
  NSISdl::download http://linuxcentre.net/winredirect/get_iplayer.cgi $InstallDir\get_iplayer.cgi

  ;startmenu
  CreateDirectory "$SMPROGRAMS\get_iplayer"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Get_iPlayer.lnk" "$SYSDIR\cmd.exe" "/k get_iplayer.cmd --search dontshowanymatches && get_iplayer.cmd --help" "$InstallDir\iplayer_logo.ico"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Update Get_iPlayer.lnk" "$SYSDIR\cmd.exe" "/k Update_get_iplayer.cmd" "$InstallDir\iplayer_logo.ico"
  WriteIniStr "$InstallDir\get_iplayer.url" "InternetShortcut" "URL" "http://linuxcentre.net/getiplayer/"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Show Home Page.lnk" "$InstallDir\get_iplayer.url" "" "$SYSDIR\SHELL32.dll" 175
  WriteIniStr "$InstallDir\command_examples.url" "InternetShortcut" "URL" "http://linuxcentre.net/getiplayer/documentation/"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Show Example Commands.lnk" "$InstallDir\command_examples.url" "" "$SYSDIR\SHELL32.dll" 175
  CreateShortCut "$SMPROGRAMS\get_iplayer\Recordings Folder.lnk" "$DataDir"
  WriteIniStr "$InstallDir\pvr_manager.url" "InternetShortcut" "URL" "http://127.0.0.1:1935"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Web PVR Manager.lnk" "$SYSDIR\cmd.exe" "/c pvr_manager.cmd" "$InstallDir\iplayer_logo.ico"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Run PVR Scheduler Now.lnk" "$SYSDIR\cmd.exe" "/k run_pvr.bat" "$InstallDir\iplayer_logo.ico"

  ;uninstall info
  CreateShortCut "$SMPROGRAMS\get_iplayer\Uninstall.lnk" "$InstallDir\uninst.exe" "" "$InstallDir\uninst.exe" 0
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "DisplayName" "${PRODUCT} ${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "URLInfoAbout" "http://linuxcentre.net/getiplayer"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "Publisher" "Phil Lewis"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "UninstallString" "$InstallDir\Uninst.exe"
  WriteRegStr HKCU "Software\${PRODUCT}" "" $InstallDir
  WriteUninstaller "$InstallDir\Uninst.exe"
SectionEnd
LangString DESC_Section1 ${LANG_ENGLISH} "Install get_iplayer."
   
Section "Mplayer" section2
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ;download mplayer
  NSISdl::download http://linuxcentre.net/winredirect/mplayer $InstallDir\mplayer.zip
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of Mplayer failed: $R0, Install it manually"
    Return
  CreateDirectory "$InstallDir\mplayer"
  ZipDLL::extractall $InstallDir\mplayer.zip $InstallDir\mplayer <ALL>
  Delete $InstallDir\mplayer.zip
SectionEnd
LangString DESC_Section2 ${LANG_ENGLISH} "Download and install Mplayer from http://linuxcentre.net/winredirect/mplayer (10.3MB)"

Section "Lame" section3
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ;download lame
  NSISdl::download http://linuxcentre.net/winredirect/lame $InstallDir\lame.zip
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of Lame failed: $R0, Install it manually"
    Return
  CreateDirectory "$InstallDir\lame"
  ZipDLL::extractall $InstallDir\lame.zip $InstallDir\lame <ALL>
  Delete $InstallDir\lame.zip
SectionEnd
LangString DESC_Section3 ${LANG_ENGLISH} "Download and install Lame from http://linuxcentre.net/winredirect/lame (535k)"

Section "ffmpeg" section4
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ;download ffmpeg
  CreateDirectory "$InstallDir\ffmpeg"
  NSISdl::download http://linuxcentre.net/winredirect/ffmpeg "$InstallDir\ffmpeg.tbz"
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of ffmpeg.tar.bz2 failed: $R0, Install it manually"
    Return
  untgz::extract  -zbz2  -d "$InstallDir\ffmpeg" "$InstallDir\ffmpeg.tbz" 
  DetailPrint "untgz returned ($R0)"
  Delete "$InstallDir\ffmpeg.tbz"
SectionEnd
LangString DESC_Section4 ${LANG_ENGLISH} "Download and install ffmpeg from http://linuxcentre.net/winredirect/ffmpeg (6.3MB)"

Section "VLC" section5
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ;download vlc
  NSISdl::download http://linuxcentre.net/winredirect/vlc $InstallDir\vlc.7z
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of VLC failed: $R0, Install it manually"
    Return
  Nsis7z::Extract "$InstallDir\vlc.7z"
  Delete $InstallDir\vlc.7z
  Rename "$InstallDir\vlc-1.0.1" "$InstallDir\vlc"
SectionEnd
LangString DESC_Section5 ${LANG_ENGLISH} "Download and install VLC from http://linuxcentre.net/winredirect/vlc (15.0MB)"

Section "flvstreamer (non-cygwin)" section6
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ;download flvstreamer
  NSISdl::download http://linuxcentre.net/winredirect/flvstreamer "$InstallDir\flvstreamer.exe"
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of flvstreamer failed: $R0, Install it manually"
    Return
SectionEnd
LangString DESC_Section6 ${LANG_ENGLISH} "Download and install flvstreamer(win32) from http://linuxcentre.net/winredirect/flvstreamer (~300k)"

Section /o "flvstreamer (using cygwin library)" section7
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ;download flvstreamer-cygwin
  NSISdl::download http://linuxcentre.net/winredirect/flvstreamer-cygwin "$InstallDir\flvstreamer.exe"
  Pop $R0 ;Get the return value
  StrCmp $R0 "success" +3
    MessageBox MB_OK "Download of flvstreamer(cygwin) failed: $R0, Install it manually"
    Return
  NSISdl::download http://linuxcentre.net/winredirect/cygwindll "$InstallDir\cygwin1.dll"
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


Function DirectoryShow
  ReadEnvStr $TempUserProfile "USERPROFILE"
  !insertmacro MUI_HEADER_TEXT "Choose Install Destination" "Choose the folder in which ${PRODUCT} will be installed."
  !insertmacro MUI_INNERDIALOG_TEXT 1041 "Destination Folder"
  !insertmacro MUI_INNERDIALOG_TEXT 1019 "$PROGRAMFILES\${PRODUCT}\"
  !insertmacro MUI_INNERDIALOG_TEXT 1006 "${PRODUCT} will be installed into the following folder.$\r$\n$\r$\nTo use a different folder, click Browse and select another folder. Click Next to continue."
FunctionEnd

Function DirectoryLeave
  StrCpy $InstallDir $INSTDIR
FunctionEnd

               
Function RecordingsDirectoryShow
  ReadEnvStr $TempUserProfile "USERPROFILE"
  !insertmacro MUI_HEADER_TEXT "Choose Recordings Location" "Choose the folder in which ${PRODUCT} will save all the recordings."
  !insertmacro MUI_INNERDIALOG_TEXT 1041 "Recordings Folder"
  !insertmacro MUI_INNERDIALOG_TEXT 1019 "$TempUserProfile\Desktop\iPlayer Recordings\"
  !insertmacro MUI_INNERDIALOG_TEXT 1006 "${PRODUCT} will record all programmes into the following folder.$\r$\n$\r$\nTo use a different folder, click Browse and select another folder. Click Next to continue."
FunctionEnd


Function RecordingsDirectoryLeave
  StrCpy $DataDir $INSTDIR
FunctionEnd

Function .onInit
  ; Must set $INSTDIR here to avoid adding ${PRODUCT} to the end of the
  ; path when user selects a new directory using the 'Browse' button.
  StrCpy $INSTDIR "$PROGRAMFILES\${PRODUCT}"
 
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
  ; Read install dir from registry
  ReadRegStr $InstallDir HKCU "Software\${PRODUCT}" ""
  StrCpy $INSTDIR $InstallDir
  ; set the installer path from this
  SetOutPath "$INSTDIR"
  ExecWait '$R0 _?=$INSTDIR' ;Do not copy the uninstaller to a temp file
  ; cleanly remove uninstaller
  SetOutPath "$INSTDIR\..\"
  Delete "$R0"
  RMDir "$INSTDIR"
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
