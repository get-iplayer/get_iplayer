;#######################################
;# Product Info
;#######################################

  Name "get_iplayer"

  !define PRODUCT "get_iplayer"
  !define VERSION "2.68"
  !define USERAGENT "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.2) Gecko/20100115 Firefox/3.6"
  !include "MUI.nsh"
  !include "Sections.nsh"

  SetCompressor /SOLID lzma



;#######################################
;# Configuration
;#######################################
 
  OutFile "get_iplayer_setup_${VERSION}.exe"

  ;Folder selection page
  InstallDir "$PROGRAMFILES\${PRODUCT}\"
   
  ;DEFINE THE SETUP exe LOGO
  !define MUI_ICON "get_iplayer\iplayer_logo.ico"

  ;get all user profile path
  Var TempGlobalProfile
  Var TempUserProfile
  Var fh
  Var DataDir
  Var InstallDir
  Var TestOrig
  Var Test

  ;Remember install folder
  InstallDirRegKey HKCU "Software\${PRODUCT}" ""



;#######################################
;# Pages
;#######################################

  !insertmacro MUI_PAGE_WELCOME

  !define MUI_PAGE_CUSTOMFUNCTION_PRE LicensePre
  !insertmacro MUI_PAGE_LICENSE "get_iplayer\LICENSE.txt"

  !define MUI_PAGE_CUSTOMFUNCTION_SHOW ComponentsShow
  !insertmacro MUI_PAGE_COMPONENTS

  !define MUI_PAGE_CUSTOMFUNCTION_PRE DirectoryPre
  !define MUI_PAGE_CUSTOMFUNCTION_SHOW DirectoryShow
  !define MUI_PAGE_CUSTOMFUNCTION_LEAVE DirectoryLeave
  !insertmacro MUI_PAGE_DIRECTORY

  !define MUI_PAGE_CUSTOMFUNCTION_PRE RecordingsDirectoryPre
  !define MUI_PAGE_CUSTOMFUNCTION_SHOW RecordingsDirectoryShow
  !define MUI_PAGE_CUSTOMFUNCTION_LEAVE RecordingsDirectoryLeave
  !insertmacro MUI_PAGE_DIRECTORY

  !insertmacro MUI_PAGE_INSTFILES
  !insertmacro MUI_PAGE_FINISH


  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_COMPONENTS
  !insertmacro MUI_UNPAGE_INSTFILES

  !define MUI_ABORTWARNING



;#######################################
;# Language
;#######################################
 
  !insertmacro MUI_LANGUAGE "English"



;#######################################
;# Sections
;#######################################     

Section "get_iplayer" section1
  ; Add 500k more than the installer files (i.e. perl)
  AddSize 500
  ReadEnvStr $TempGlobalProfile "ALLUSERSPROFILE"
  ReadEnvStr $TempUserProfile "USERPROFILE"
  ;SetOutPath "$InstallDir"
  Call SetInstallDir
  ; pre-clear
  RMDir /r "$InstallDir\lib"
  RMDir /r "$InstallDir\perl-license"
  Delete "$InstallDir\perl*.dll"
  Delete "$InstallDir\LICENSE.txt"
  Delete "$InstallDir\perl.exe"
  Delete "$InstallDir\run_pvr_scheduler.bat" 
  Delete "$InstallDir\get_iplayer--pvr.bat" 
  Delete "$InstallDir\get_iplayer.cmd"
  Delete "$InstallDir\get_iplayer.cgi"
  Delete "$InstallDir\get_iplayer.pl"
  Delete "$InstallDir\get_iplayer.cgi.cmd"
  Delete "$InstallDir\pvr_manager.cmd"
  Delete "$InstallDir\iplayer_logo.ico"
  Delete "$InstallDir\get_iplayer_setup.nsi"
  Delete "$InstallDir\get_iplayer-ver.txt"

  ; now rename ANY existing VirtualStore folder for Win7 / Vista
  ; IfFileExists "$TempUserProfile\AppData\Local\VirtualStore\Program Files\get_iplayer\" 0 novirtclean
    RMDir /r "$TempUserProfile\AppData\Local\VirtualStore\Program Files\get_iplayer\lib"
    RMDir /r "$TempUserProfile\AppData\Local\VirtualStore\Program Files\get_iplayer\perl-license"
    Delete "$TempUserProfile\AppData\Local\VirtualStore\Program Files\get_iplayer\perl*.dll"
    Delete "$TempUserProfile\AppData\Local\VirtualStore\Program Files\get_iplayer\LICENSE.txt"
    Delete "$TempUserProfile\AppData\Local\VirtualStore\Program Files\get_iplayer\perl.exe"
    Delete "$TempUserProfile\AppData\Local\VirtualStore\Program Files\get_iplayer\run_pvr_scheduler.bat" 
    Delete "$TempUserProfile\AppData\Local\VirtualStore\Program Files\get_iplayer\get_iplayer--pvr.bat" 
    Delete "$TempUserProfile\AppData\Local\VirtualStore\Program Files\get_iplayer\get_iplayer.cmd"
    Delete "$TempUserProfile\AppData\Local\VirtualStore\Program Files\get_iplayer\get_iplayer.cgi"
    Delete "$TempUserProfile\AppData\Local\VirtualStore\Program Files\get_iplayer\get_iplayer.pl"
    Delete "$TempUserProfile\AppData\Local\VirtualStore\Program Files\get_iplayer\get_iplayer.cgi.cmd"
    Delete "$TempUserProfile\AppData\Local\VirtualStore\Program Files\get_iplayer\pvr_manager.cmd"
    Delete "$TempUserProfile\AppData\Local\VirtualStore\Program Files\get_iplayer\iplayer_logo.ico"
    Delete "$TempUserProfile\AppData\Local\VirtualStore\Program Files\get_iplayer\get_iplayer_setup.nsi"
    Delete "$TempUserProfile\AppData\Local\VirtualStore\Program Files\get_iplayer\get_iplayer-ver.txt"
  ; novirtclean:

  ; Copy files into place
  FILE /r "get_iplayer\*.*"
  
  ;clear the global files
  Delete $TempGlobalProfile\get_iplayer\*
  
  ;move the options file to the global position
  CreateDirectory $TempGlobalProfile\get_iplayer
  
  ;create user download folder
  CreateDirectory $DataDir

  ;create options file
  FileOpen $fh "$TempGlobalProfile\get_iplayer\options" "w"
  FileWrite $fh "lame .\lame\lame.exe$\r$\n"
  FileWrite $fh "mplayer .\mplayer\MPlayer-1.0rc2\mplayer.exe$\r$\n"
  FileWrite $fh "atomicparsley .\atomicparsley\atomicparsley.exe$\r$\n"
  FileWrite $fh "output $DataDir$\r$\n"
  FileWrite $fh "flvstreamer .\flvstreamer.exe$\r$\n"
  FileWrite $fh "ffmpeg .\ffmpeg\bin\ffmpeg.exe$\r$\n"
  FileWrite $fh "vlc .\vlc\vlc.exe$\r$\n"
  FileWrite $fh "mmsnothread 1$\r$\n"
  FileWrite $fh "nopurge 1$\r$\n"
  ; prevents initial plugin downloads...
  ;FileWrite $fh "packagemanager Windows Installer$\r$\n"
  FileClose "$fh"

  ; Create run_pvr_scheduler batch file
  FileOpen $fh "$InstallDir\run_pvr_scheduler.bat" "w"
  FileWrite $fh "cd $InstallDir$\r$\n"
  FileWrite $fh "perl.exe get_iplayer.pl --pvrschedule 14400$\r$\n"
  FileWrite $fh "$\r$\n"
  FileClose "$fh"

  ; Create Windows scheduler batch file
  FileOpen $fh "$InstallDir\get_iplayer--pvr.bat" "w"
  FileWrite $fh "cd $InstallDir$\r$\n"
  FileWrite $fh "perl.exe get_iplayer.pl --pvr$\r$\n"
  FileWrite $fh "$\r$\n"
  FileClose "$fh"

  ;download get_iplayer
  Delete $InstallDir\get_iplayer.pl
  download1:
  inetc::get /USERAGENT "${USERAGENT}" "http://linuxcentre.net/get_iplayer/get_iplayer" "$InstallDir\get_iplayer.pl" /END
  Pop $R0 ;Get the return value
  StrCmp $R0 "OK" install1
     MessageBox MB_YESNO|MB_ICONQUESTION "Download of get_iplayer failed: $R0, Do you wish to try again?" IDYES download1
     Return
  install1:

  ; Update the plugins (with installer privs)
  SetOutPath "$InstallDir"
  ExecWait '"perl.exe" get_iplayer.pl --plugins-update'

  ; Get the current ver into this ver file
  inetc::get /USERAGENT "get_iplayer windows installer v${VERSION}" /SILENT "http://linuxcentre.net/get_iplayer/VERSION-get_iplayer" "$InstallDir\get_iplayer-ver.txt" /END
  Pop $R0 ;Get the return value

  ;download get_iplayer.cgi
  Delete $InstallDir\get_iplayer.cgi
  download2:
  inetc::get /USERAGENT "${USERAGENT}" "http://linuxcentre.net/winredirect/get_iplayer.cgi" "$InstallDir\get_iplayer.cgi" /END
  Pop $R0 ;Get the return value
  StrCmp $R0 "OK" install2
     MessageBox MB_YESNO|MB_ICONQUESTION "Download of get_iplayer Web PVR Manager failed: $R0, Do you wish to try again?" IDYES download2
     Return
  install2:

  ; URLs
  WriteIniStr "$InstallDir\command_examples.url" "InternetShortcut" "URL" "http://linuxcentre.net/getiplayer/documentation/"
  WriteIniStr "$InstallDir\faq.url" "InternetShortcut" "URL" "http://linuxcentre.net/getiplayer/documentation/"
  WriteIniStr "$InstallDir\pvr_manager.url" "InternetShortcut" "URL" "http://127.0.0.1:1935"
  WriteIniStr "$InstallDir\strawberry_docs.url" "InternetShortcut" "URL" "http://strawberryperl.com/"
  ; root startmenu items
  CreateShortCut "$SMPROGRAMS\get_iplayer\Get_iPlayer.lnk" "$SYSDIR\cmd.exe" "/k get_iplayer.cmd --search dontshowanymatches && get_iplayer.cmd --help" "$InstallDir\iplayer_logo.ico"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Recordings Folder.lnk" "$DataDir"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Web PVR Manager.lnk" "$SYSDIR\cmd.exe" "/c pvr_manager.cmd" "$InstallDir\iplayer_logo.ico"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Run PVR Scheduler Now.lnk" "$SYSDIR\cmd.exe" "/k run_pvr_scheduler.bat" "$InstallDir\iplayer_logo.ico"
  ; Help startmenu items
  CreateShortCut "$SMPROGRAMS\get_iplayer\Help\get_iplayer Example Commands.lnk" "$InstallDir\command_examples.url" "" "$SYSDIR\SHELL32.dll" 175
  CreateShortCut "$SMPROGRAMS\get_iplayer\Help\get_iplayer FAQ.lnk" "$InstallDir\faq.url" "" "$SYSDIR\SHELL32.dll" 175
  CreateShortCut "$SMPROGRAMS\get_iplayer\Help\Strawberry Perl Home.lnk" "$InstallDir\strawberry_docs.url" "" "$SYSDIR\SHELL32.dll" 175
  ; Update startmenu items
SectionEnd

Section "un.get_iplayer" un.section1
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Remove User Preferences, PVR Searches, Presets and Recording History?" IDYES true2 IDNO false2
  true2:
    ;delete the local user data
    Delete $PROFILE\.get_iplayer\*
    RmDir $PROFILE\.get_iplayer
  false2:
  RMDir /r "$INSTDIR\lib"
  RMDir /r "$INSTDIR\perl-license"
  Delete "$INSTDIR\perl*.dll"
  Delete "$INSTDIR\LICENSE.txt"
  Delete "$INSTDIR\perl.exe"
  Delete "$INSTDIR\run_pvr_scheduler.bat" 
  Delete "$INSTDIR\get_iplayer--pvr.bat" 
  Delete "$INSTDIR\get_iplayer.cmd"
  Delete "$INSTDIR\get_iplayer.cgi.cmd"
  Delete "$INSTDIR\get_iplayer.pl"
  Delete "$INSTDIR\get_iplayer.cgi"
  Delete "$INSTDIR\pvr_manager.cmd"
  Delete "$INSTDIR\iplayer_logo.ico"
  Delete "$INSTDIR\get_iplayer_setup.nsi"
  Delete "$INSTDIR\get_iplayer-ver.txt"
  ; URLs and start menu
  Delete "$INSTDIR\command_examples.url"
  Delete "$INSTDIR\faq.url"
  Delete "$INSTDIR\pvr_manager.url"
  Delete "$INSTDIR\strawberry_docs.url"
  Delete "$SMPROGRAMS\get_iplayer\Get_iPlayer.lnk"
  Delete "$SMPROGRAMS\get_iplayer\Recordings Folder.lnk"
  Delete "$SMPROGRAMS\get_iplayer\Web PVR Manager.lnk"
  Delete "$SMPROGRAMS\get_iplayer\Run PVR Scheduler Now.lnk"
  Delete "$SMPROGRAMS\get_iplayer\Help\get_iplayer Example Commands.lnk"
  Delete "$SMPROGRAMS\get_iplayer\Help\get_iplayer FAQ.lnk"
  Delete "$SMPROGRAMS\get_iplayer\Help\Strawberry Perl Home.lnk"
  ; remove the global options file 
  ReadEnvStr $TempGlobalProfile "ALLUSERSPROFILE"
  Delete $TempGlobalProfile\get_iplayer\options
  RmDir $TempGlobalProfile\get_iplayer
SectionEnd

LangString DESC_Section1 ${LANG_ENGLISH} "Install get_iplayer and required Strawberry Perl - Required for all recordings. Also bundled with Web PVR Manager (~6.5MB)"
   


Section "Mplayer" section2
  AddSize 10500
  Call SetInstallDir
  Call ConnectInternet ;Make an internet connection (if no connection available)
  download:
  inetc::get /USERAGENT "${USERAGENT}" "http://linuxcentre.net/winredirect/mplayer" "$InstallDir\mplayer.zip" /END
  Pop $R0 ;Get the return value
  StrCmp $R0 "OK" install
     MessageBox MB_YESNO|MB_ICONQUESTION "Download of Mplayer failed: $R0, Do you wish to try again?" IDYES download
     Return
  install:
  ; pre-clear
  RMDir /r "$InstallDir\mplayer"  
  CreateDirectory "$InstallDir\mplayer"
  ZipDLL::extractall $InstallDir\mplayer.zip $InstallDir\mplayer <ALL>
  Delete $InstallDir\mplayer.zip
  ; URLs
  WriteIniStr "$InstallDir\mplayer_docs.url" "InternetShortcut" "URL" "http://www.mplayerhq.hu/DOCS/HTML/en/index.html"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Help\MPlayer Documentation.lnk" "$InstallDir\mplayer_docs.url" "" "$SYSDIR\SHELL32.dll" 175
SectionEnd

Section "un.Mplayer" un.section2
  RMDir /r "$INSTDIR\mplayer"
  Delete "$INSTDIR\mplayer_docs.url"
  Delete "$SMPROGRAMS\get_iplayer\Help\MPlayer Documentation.lnk"
SectionEnd

LangString DESC_Section2 ${LANG_ENGLISH} "Download and install Mplayer - Used for RealAudio and MMS recording modes (~10.5MB)"



Section "Lame" section3
  AddSize 550
  Call SetInstallDir
  Call ConnectInternet ;Make an internet connection (if no connection available)
  download:
  inetc::get /USERAGENT "${USERAGENT}" "http://linuxcentre.net/winredirect/lame" "$InstallDir\lame.zip" /END
  Pop $R0 ;Get the return value
  StrCmp $R0 "OK" install
     MessageBox MB_YESNO|MB_ICONQUESTION "Download of Lame failed: $R0, Do you wish to try again?" IDYES download
     Return
  install:
  ; pre-clear
  RMDir /r "$InstallDir\lame"
  CreateDirectory "$InstallDir\lame"
  ZipDLL::extractall $InstallDir\lame.zip $InstallDir\lame <ALL>
  Delete $InstallDir\lame.zip
  ; start menu
  WriteIniStr "$InstallDir\lame_docs.url" "InternetShortcut" "URL" "http://lame.sourceforge.net/using.php"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Help\Lame Documentation.lnk" "$InstallDir\lame_docs.url" "" "$SYSDIR\SHELL32.dll" 175
SectionEnd

Section "un.Lame" un.section3
  RMDir /r "$INSTDIR\lame"
  Delete "$INSTDIR\lame_docs.url" 
  Delete "$SMPROGRAMS\get_iplayer\Help\Lame Documentation.lnk"
SectionEnd

LangString DESC_Section3 ${LANG_ENGLISH} "Download and install Lame - Used for transcoding RealAudio recordings to MP3 (~550k)"



Section "ffmpeg" section4
  AddSize 6500
  Call SetInstallDir
  Call ConnectInternet ;Make an internet connection (if no connection available)
  download:
  inetc::get /USERAGENT "${USERAGENT}" "http://linuxcentre.net/winredirect/ffmpeg" "$InstallDir\ffmpeg.tbz" /END
  Pop $R0 ;Get the return value
  StrCmp $R0 "OK" install
     MessageBox MB_YESNO|MB_ICONQUESTION "Download of FFmpeg failed: $R0, Do you wish to try again?" IDYES download
     Return
  install:
  ; pre-clear
  RMDir /r "$InstallDir\ffmpeg"
  CreateDirectory "$InstallDir\ffmpeg"
  untgz::extract -zbz2 -d "$InstallDir\ffmpeg" "$InstallDir\ffmpeg.tbz" 
  DetailPrint "untgz returned ($R0)"
  Delete "$InstallDir\ffmpeg.tbz"
  ; start menu
  WriteIniStr "$InstallDir\ffmpeg_docs.url" "InternetShortcut" "URL" "http://ffmpeg.org/ffmpeg-doc.html"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Help\FFmpeg Documentation.lnk" "$InstallDir\ffmpeg_docs.url" "" "$SYSDIR\SHELL32.dll" 175
SectionEnd

Section "un.ffmpeg" un.section4
  RMDir /r "$INSTDIR\ffmpeg"
  Delete "$INSTDIR\ffmpeg_docs.url"
  Delete "$SMPROGRAMS\get_iplayer\Help\FFmpeg Documentation.lnk"
SectionEnd

LangString DESC_Section4 ${LANG_ENGLISH} "Download and install ffmpeg - Used for losslessly converting Flash Video into useful video/audio files formats (~6.5MB)"



Section "VLC" section5
  AddSize 15000
  Call SetInstallDir
  Call ConnectInternet ;Make an internet connection (if no connection available)
  download:
  inetc::get /USERAGENT "${USERAGENT}" "http://linuxcentre.net/winredirect/vlc103" "$InstallDir\vlc.7z" /END
  Pop $R0 ;Get the return value
  StrCmp $R0 "OK" install
     MessageBox MB_YESNO|MB_ICONQUESTION "Download of VLC failed: $R0, Do you wish to try again?" IDYES download
     Return
  install:
  Nsis7z::Extract "$InstallDir\vlc.7z"
  Delete $InstallDir\vlc.7z
  ; pre-clear
  RMDir /r "$InstallDir\vlc"
  Rename "$InstallDir\vlc-1.0.3" "$InstallDir\vlc"
  ; start menu
  CreateShortCut "$SMPROGRAMS\VLC Media Player.lnk" "$InstallDir\vlc\vlc.exe" "" "$InstallDir\vlc\vlc.ico"
  WriteIniStr "$InstallDir\vlc_docs.url" "InternetShortcut" "URL" "http://wiki.videolan.org/Documentation:Documentation"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Help\VLC Documentation.lnk" "$InstallDir\vlc_docs.url" "" "$SYSDIR\SHELL32.dll" 175
SectionEnd

Section "un.VLC" un.section5
  RMDir /r "$INSTDIR\vlc"
  Delete "$SMPROGRAMS\VLC Media Player.lnk"
  Delete "$INSTDIR\vlc_docs.url"
  Delete "$SMPROGRAMS\get_iplayer\Help\VLC Documentation.lnk"
SectionEnd

LangString DESC_Section5 ${LANG_ENGLISH} "Download and install VLC - Required for playback of playlists and content from Web PVR Manager (~15MB)"



Section "flvstreamer (non-cygwin)" section6
  AddSize 500
  Call SetInstallDir
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ; pre-clear
  Delete "$InstallDir\flvstreamer.exe"
  download:
  inetc::get /USERAGENT "${USERAGENT}" "http://linuxcentre.net/winredirect/flvstreamer" "$InstallDir\flvstreamer.exe" /END
  Pop $R0 ;Get the return value
  StrCmp $R0 "OK" install
     MessageBox MB_YESNO|MB_ICONQUESTION "Download of flvstreamer failed: $R0, Do you wish to try again?" IDYES download
     Return
  install:
  ; start menu
  WriteIniStr "$InstallDir\flvstreamer_docs.url" "InternetShortcut" "URL" "http://savannah.nongnu.org/projects/flvstreamer/"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Help\flvstreamer Documentation.lnk" "$InstallDir\flvstreamer_docs.url" "" "$SYSDIR\SHELL32.dll" 175
SectionEnd

Section "un.flvstreamer (non-cygwin)" un.section6
  Delete "$INSTDIR\flvstreamer.exe"
  Delete "$INSTDIR\flvstreamer_docs.url"
  Delete "$SMPROGRAMS\get_iplayer\Help\flvstreamer Documentation.lnk"
SectionEnd

LangString DESC_Section6 ${LANG_ENGLISH} "Download and install flvstreamer - Used for recording Flash video modes (~500k)"



Section "flvstreamer (using cygwin library)" section7
  AddSize 2500
  Call SetInstallDir
  Call ConnectInternet ;Make an internet connection (if no connection available)
  ; pre-clear
  Delete "$InstallDir\flvstreamer.exe"
  download1:
  inetc::get /USERAGENT "${USERAGENT}" "http://linuxcentre.net/winredirect/flvstreamer-cygwin" "$InstallDir\flvstreamer.exe" /END
  Pop $R0 ;Get the return value
  StrCmp $R0 "OK" install1
     MessageBox MB_YESNO|MB_ICONQUESTION "Download of flvstreamer (cygwin) failed: $R0, Do you wish to try again?" IDYES download1
     Return
  install1:
  ; pre-clear
  Delete "$InstallDir\cygwin1.dll"
  download2:
  inetc::get /USERAGENT "${USERAGENT}" "http://linuxcentre.net/winredirect/cygwindll" "$InstallDir\cygwin1.dll" /END
  Pop $R0 ;Get the return value
  StrCmp $R0 "OK" install2
     MessageBox MB_YESNO|MB_ICONQUESTION "Download of cygwin DLL failed: $R0, Do you wish to try again?" IDYES download2
     Return
  install2:
  ; start menu
  WriteIniStr "$InstallDir\flvstreamer_docs.url" "InternetShortcut" "URL" "http://savannah.nongnu.org/projects/flvstreamer/"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Help\flvstreamer Documentation.lnk" "$InstallDir\flvstreamer_docs.url" "" "$SYSDIR\SHELL32.dll" 175
SectionEnd

Section "un.flvstreamer (using cygwin library)" un.section7
  Delete "$INSTDIR\flvstreamer.exe"
  Delete "$INSTDIR\cygwin1.dll"
  Delete "$INSTDIR\flvstreamer_docs.url"
  Delete "$SMPROGRAMS\get_iplayer\Help\flvstreamer Documentation.lnk"
SectionEnd

LangString DESC_Section7 ${LANG_ENGLISH} "Download and install flvstreamer(cygwin alternative) - Used for recording Flash video modes (~2.5M)"



Section "AtomicParsley" section8
  AddSize 500
  Call SetInstallDir
  Call ConnectInternet ;Make an internet connection (if no connection available)
  download:
  inetc::get /USERAGENT "${USERAGENT}" "http://linuxcentre.net/winredirect/atomicparsley" "$InstallDir\atomicparsley.zip" /END
  Pop $R0 ;Get the return value
  StrCmp $R0 "OK" install
     MessageBox MB_YESNO|MB_ICONQUESTION "Download of AtomicParsley failed: $R0, Do you wish to try again?" IDYES download
     Return
  install:
  CreateDirectory "$InstallDir\atomicparsley-tmp"
  ZipDLL::extractall $InstallDir\atomicparsley.zip $InstallDir\atomicparsley-tmp <ALL>
  Delete $InstallDir\atomicparsley.zip
  ; pre-clear
  RMDir /r "$InstallDir\atomicparsley"  
  Rename "$InstallDir\atomicparsley-tmp\AtomicParsley-win32-0.9.0" "$InstallDir\atomicparsley"
  RMDir /r "$InstallDir\atomicparsley-tmp"
  ; start menu
  WriteIniStr "$InstallDir\atomicparsley_docs.url" "InternetShortcut" "URL" "http://atomicparsley.sourceforge.net/"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Help\AtomicParsley Documentation.lnk" "$InstallDir\atomicparsley_docs.url" "" "$SYSDIR\SHELL32.dll" 175
SectionEnd

Section "un.AtomicParsley" un.section8
  RMDir /r "$INSTDIR\atomicparsley"  
  Delete "$INSTDIR\atomicparsley_docs.url"
  Delete "$SMPROGRAMS\get_iplayer\Help\AtomicParsley Documentation.lnk"
SectionEnd

LangString DESC_Section8 ${LANG_ENGLISH} "Download and install AtomicParsley - Used for Tagging MP4 files (~500k)"



!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${Section1} $(DESC_Section1)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section2} $(DESC_Section2)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section3} $(DESC_Section3)  
  !insertmacro MUI_DESCRIPTION_TEXT ${Section4} $(DESC_Section4)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section5} $(DESC_Section5)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section6} $(DESC_Section6)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section7} $(DESC_Section7)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section8} $(DESC_Section8)
!insertmacro MUI_FUNCTION_DESCRIPTION_END



;#######################################
;# Before Installation
;#######################################

Function .onInit
  ; Must set $INSTDIR here to avoid adding ${PRODUCT} to the end of the
  ; path when user selects a new directory using the 'Browse' button.
  StrCpy $INSTDIR "$PROGRAMFILES\${PRODUCT}"

  ; skip uninstaller if not already installed
  ReadRegStr $R0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}" "UninstallString"
  StrCmp $R0 "" done

  ; Skip the uninstall check now
  Goto done
  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
    "${PRODUCT} is already installed. $\n$\nClick `OK` to remove components of the previous version or `Cancel` to continue this upgrade without uninstalling." \
    IDOK uninst
  Goto done
 
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
    ; first check to see if all the components have been removed
    IfFileExists "$INSTDIR\docleanup" 0 done
      Delete "$R0"
      Delete "$INSTDIR\docleanup"
      RMDir "$INSTDIR"
  done:

  ; Check for newer installer
  ClearErrors
  Delete "$INSTDIR\Installer-ver.txt"
  inetc::get /USERAGENT "get_iplayer windows installer v${VERSION}" /SILENT "http://linuxcentre.net/winredirect/installerver" "$INSTDIR\Installer-ver.txt" /END
  Pop $R0 ;Get the return value
  ; abort checking new installer and just continue if not OK
  StrCmp $R0 "OK" 0 nonew
  ClearErrors
  ; Read contents of version file and compare with this one
  FileOpen $fh "$INSTDIR\Installer-ver.txt" r
  IfErrors nonew
  ; only read 4 bytes x.xx - this avoids getting the problematic \r\n
  FileRead $fh $Test 4
  FileClose $fh
  Delete "$INSTDIR\Installer-ver.txt"
  ; if version matches then don't download
  StrCmp $Test "${VERSION}" nonew
  MessageBox MB_YESNO|MB_ICONQUESTION "A newer installer version $Test is available, Do you wish to download and run it?" IDYES download IDNO nonew
  download:
  ClearErrors
  inetc::get /USERAGENT "get_iplayer windows installer v${VERSION}" "http://linuxcentre.net/winredirect/newinstaller" "$DESKTOP\get_iplayer_Setup_$Test.exe" /END
  Pop $R0 ;Get the return value
  StrCmp $R0 "OK" newinstall
    MessageBox MB_YESNO|MB_ICONQUESTION "Download of get_iplayer installer failed: $R0, Do you wish to try again?" IDYES download
    Goto nonew
  newinstall:
    MessageBox MB_OK "New Installer will now run."
    Exec '"$DESKTOP\get_iplayer_setup_$Test.exe"'
    Quit
  nonew:

  ; Detect Installed Components
  SectionSetFlags ${Section1} ${SF_SELECTED}
  SectionSetFlags ${Section2} ${SF_SELECTED}
  SectionSetFlags ${Section3} ${SF_SELECTED}
  SectionSetFlags ${Section4} ${SF_SELECTED}
  SectionSetFlags ${Section5} ${SF_SELECTED}
  SectionSetFlags ${Section6} ${SF_SELECTED}
  SectionSetFlags ${Section7} ${SF_SELECTED}
  SectionSetFlags ${Section8} ${SF_SELECTED}
  # set section 'get_iplayer' as unselected if already installed
  IfFileExists "$INSTDIR\get_iplayer.pl" 0 Next1
    SectionSetFlags ${Section1} 0
    ; Check for newer get_iplayer ver
    ClearErrors
    ; get the last version installed
    FileOpen $fh "$INSTDIR\get_iplayer-ver.txt" r
    IfErrors nonew2
    ; only read 4 bytes x.xx - this avoids getting the problematic \r\n
    FileRead $fh $TestOrig 4
    FileClose $fh
    ; check the latest ver
    Delete "$INSTDIR\get_iplayer-ver-check.txt"
    inetc::get /USERAGENT "get_iplayer windows installer v${VERSION}" /SILENT "http://linuxcentre.net/get_iplayer/VERSION-get_iplayer" "$INSTDIR\get_iplayer-ver-check.txt" /END
    Pop $R0 ;Get the return value
    ; abort checking new ver and just continue if not OK
    StrCmp $R0 "OK" 0 nonew2
    ClearErrors
    ; Read contents of version file and compare with this one
    FileOpen $fh "$INSTDIR\get_iplayer-ver-check.txt" r
    IfErrors nonew2
    ; only read 4 bytes x.xx - this avoids getting the problematic \r\n
    FileRead $fh $Test 4
    FileClose $fh
    ; if version matches then don't tell user etc
    StrCmp $Test $TestOrig nonew2
    MessageBox MB_OK "A newer get_iplayer script version $Test is available. To update ensure the get_iplayer component is checked."
    SectionSetFlags ${Section1} ${SF_SELECTED}
    Delete "$INSTDIR\get_iplayer-ver.txt"
    Rename "$INSTDIR\get_iplayer-ver-check.txt" "$INSTDIR\get_iplayer-ver.txt"
    nonew2:
  Next1:
  # set section 'Mplayer' as unselected if already installed
  IfFileExists "$INSTDIR\mplayer\MPlayer-1.0rc2\mplayer.exe" 0 Next2
    SectionSetFlags ${Section2} 0
  Next2:
  # set section 'Lame' as unselected if already installed
  IfFileExists "$INSTDIR\lame\lame.exe" 0 Next3
    SectionSetFlags ${Section3} 0
  Next3:
  # set section 'ffmpeg' as unselected if already installed
  IfFileExists "$INSTDIR\ffmpeg\bin\ffmpeg.exe" 0 Next4
    SectionSetFlags ${Section4} 0
  Next4:
  # set section 'VLC' as unselected if already installed
  IfFileExists "$INSTDIR\vlc\vlc.exe" 0 Next5
    SectionSetFlags ${Section5} 0
  Next5:
  # set section 'flvstreamer (non-cygwin)' as unselected if already installed
  IfFileExists "$INSTDIR\flvstreamer.exe" 0 Next6
    SectionSetFlags ${Section6} 0
  Next6:
  # set section 'flvstreamer (using cygwin library)' as unselected
  SectionSetFlags ${Section7} 0
  # set section 'AtomicParsley' as unselected if already installed
  IfFileExists "$INSTDIR\atomicparsley\AtomicParsley.exe" 0 Next8
    SectionSetFlags ${Section8} 0
  Next8:
  ; start menu dirs
  CreateDirectory "$SMPROGRAMS\get_iplayer\Updates"
  CreateDirectory "$SMPROGRAMS\get_iplayer\Help"
FunctionEnd



;#######################################
;# After Successful Installation
;#######################################

Function .onInstSuccess
  ; URLs
  WriteIniStr "$InstallDir\linuxcentre.url" "InternetShortcut" "URL" "http://linuxcentre.net/getiplayer/"
  WriteIniStr "$InstallDir\download_latest_installer.url" "InternetShortcut" "URL" "http://linuxcentre.net/get_iplayer/contrib/get_iplayer_setup_latest.exe"
  WriteIniStr "$InstallDir\nsis_docs.url" "InternetShortcut" "URL" "http://nsis.sourceforge.net/"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Recordings Folder.lnk" "$DataDir"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Help\NSIS Installer Home.lnk" "$InstallDir\nsis_docs.url" "" "$SYSDIR\SHELL32.dll" 175
  CreateShortCut "$SMPROGRAMS\get_iplayer\Updates\Download Latest Installer.lnk" "$InstallDir\download_latest_installer.url" "" "$SYSDIR\SHELL32.dll" 175
  ; Put uninstall info in registry
  CreateShortCut "$SMPROGRAMS\get_iplayer\Uninstall Components.lnk" "$InstallDir\uninst.exe" "" "$InstallDir\uninst.exe" 0
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "DisplayName" "${PRODUCT} ${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "URLInfoAbout" "http://linuxcentre.net/getiplayer"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "Publisher" "Phil Lewis"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "UninstallString" "$InstallDir\Uninst.exe"
  WriteRegStr HKCU "Software\${PRODUCT}" "" $InstallDir
  WriteUninstaller "$InstallDir\Uninst.exe"
FunctionEnd



;#######################################
;# Before Uninstallation
;#######################################
Function un.onInit
  CopyFiles "$INSTDIR\Uninst-orig.exe" "$INSTDIR\Uninst-orig.exe" 
  ; Detect Installed Components
  SectionSetFlags ${Section1} ${SF_RO}
  SectionSetFlags ${Section2} ${SF_RO}
  SectionSetFlags ${Section3} ${SF_RO}
  SectionSetFlags ${Section4} ${SF_RO}
  SectionSetFlags ${Section5} ${SF_RO}
  SectionSetFlags ${Section6} ${SF_RO}
  SectionSetFlags ${Section7} ${SF_RO}
  SectionSetFlags ${Section8} ${SF_RO}
  # set section 'get_iplayer' as selected if already installed
  IfFileExists "$INSTDIR\get_iplayer.pl" 0 Next1
    SectionSetFlags ${Section1} ${SF_SELECTED}
  Next1:
  # set section 'Mplayer' as selected if already installed
  IfFileExists "$INSTDIR\mplayer\MPlayer-1.0rc2\mplayer.exe" 0 Next2
    SectionSetFlags ${Section2} ${SF_SELECTED}
  Next2:
  # set section 'Lame' as selected if already installed
  IfFileExists "$INSTDIR\lame\lame.exe" 0 Next3
    SectionSetFlags ${Section3} ${SF_SELECTED}
  Next3:
  # set section 'ffmpeg' as selected if already installed
  IfFileExists "$INSTDIR\ffmpeg\bin\ffmpeg.exe" 0 Next4
    SectionSetFlags ${Section4} ${SF_SELECTED}
  Next4:
  # set section 'VLC' as selected if already installed
  IfFileExists "$INSTDIR\vlc\vlc.exe" 0 Next5
    SectionSetFlags ${Section5} ${SF_SELECTED}
  Next5:
  # set section 'flvstreamer (using cygwin library)' as selected if already installed
  IfFileExists "$INSTDIR\cygwin1.dll" 0 Next6
    SectionSetFlags ${Section7} ${SF_SELECTED}
    Goto Next7
  Next6:
  # set section 'flvstreamer (non-cygwin)' as selected if already installed
  IfFileExists "$INSTDIR\flvstreamer.exe" 0 Next7
    SectionSetFlags ${Section6} ${SF_SELECTED}
  Next7:
  # set section 'AtomicParsley' as selected if already installed
  IfFileExists "$INSTDIR\atomicparsley\AtomicParsley.exe" 0 Next8
    SectionSetFlags ${Section8} ${SF_SELECTED}
  Next8:

FunctionEnd



;#######################################
;# After Successful Uninstallation
;#######################################

Function un.onUninstSuccess
  ; Only remove the reg entry if all components are removed
  IfFileExists "$INSTDIR\get_iplayer.pl" NoClean
  IfFileExists "$INSTDIR\mplayer\MPlayer-1.0rc2\mplayer.exe" NoClean
  IfFileExists "$INSTDIR\lame\lame.exe" NoClean
  IfFileExists "$INSTDIR\ffmpeg\bin\ffmpeg.exe" NoClean
  IfFileExists "$INSTDIR\vlc\vlc.exe" NoClean
  IfFileExists "$INSTDIR\cygwin1.dll" NoClean
  IfFileExists "$INSTDIR\flvstreamer.exe" NoClean
  IfFileExists "$INSTDIR\atomicparsley\AtomicParsley.exe" NoClean
  ; remove startmenu dirs and all contents
  RMDir /r "$SMPROGRAMS\get_iplayer"
  ; Remove installed status in registry 
  DeleteRegKey HKCU "SOFTWARE\get_iplayer"
  DeleteRegKey HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer"
  Delete "$INSTDIR\linuxcentre.url"
  Delete "$INSTDIR\download_latest_installer.url"
  Delete "$INSTDIR\nsis_docs.url"
  Delete "$INSTDIR\get_iplayer-ver-check.txt"
  ;; Create file to indicate to cleanup afterwards
  ;FileOpen $fh "$INSTDIR\docleanup" "w"
  ;FileWrite $fh "This tells the installer to completely remove all files and this dir"
  ;FileClose "$fh"
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer.."
  Delete "$INSTDIR\Uninst.exe"
  RMDir "$INSTDIR"
  Goto Done
  NoClean:
    HideWindow
    MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) selected components were successfully removed from your computer.."
    ; Create uninstall exe start menu link
    CreateShortCut "$SMPROGRAMS\get_iplayer\Uninstall Components.lnk" "$INSTDIR\uninst.exe" "" "$INSTDIR\uninst.exe" 0
    ; Put uninstall info in registry
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "DisplayName" "${PRODUCT} ${VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "DisplayVersion" "${VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "URLInfoAbout" "http://linuxcentre.net/getiplayer"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "Publisher" "Phil Lewis"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "UninstallString" "$INSTDIR\Uninst.exe"
    WriteRegStr HKCU "Software\${PRODUCT}" "" $INSTDIR
    Rename "$INSTDIR\Uninst-orig.exe" "$INSTDIR\Uninst.exe" 
  Done:
FunctionEnd

  

;#######################################
;# Custom Page Functions
;#######################################

Function LicensePre
  ; skip license if already installed
  ; Read install dir from registry
  ReadRegStr $Test HKCU "Software\${PRODUCT}" ""
  StrCmp $Test "" noSkip
    Abort
  noSkip:
FunctionEnd



Function ComponentsShow
  !insertmacro MUI_HEADER_TEXT "Choose Components" "Choose Components for Installation or Updating"
  !insertmacro MUI_INNERDIALOG_TEXT 1006 "Check the components you want to install and uncheck the components you don't want to install. You can update a component to the latest recommended version by checking it."
FunctionEnd



Function DirectoryPre
  ; skip destination selection if already installed
  ; Read install dir from registry
  ReadRegStr $Test HKCU "Software\${PRODUCT}" ""
  StrCmp $Test "" noSkip
    StrCpy $InstallDir $INSTDIR
    Abort
  noSkip:
FunctionEnd



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


               
Function RecordingsDirectoryPre
  ; skip destination selection if get_iplayer is not a selected section
  SectionGetFlags ${section1} $Test
  ; bitwise AND
  IntOp $Test $Test & ${SF_SELECTED}
  ; test if equal
  IntCmp $Test ${SF_SELECTED} noSkip
    Abort
  noSkip:
  ;DirText text subtext browse_button_text browse_dlg_text
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



;#######################################
;# Misc Functions
;#######################################

Function SetInstallDir
  SetOutPath "$InstallDir"
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
