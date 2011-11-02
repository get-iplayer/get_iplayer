;#######################################
;# Product Info
;#######################################

!define PRODUCT "get_iplayer"
!define VERSION "4.5"
; VERSION where Perl support last changed
!define PERLVER "4.4"

;#######################################
;# Build Setup
;#######################################

!ifndef BUILDPATH
!define BUILDPATH "."
!endif
!ifndef SOURCEPATH
!define SOURCEPATH ".."
!endif
!ifndef PERLFILES
!define PERLFILES "${BUILDPATH}\perlfiles"
!endif
!ifndef HELPERS
!define HELPERS "${BUILDPATH}\helpers"
!endif
!ifdef STANDALONE
!ifndef WITHSCRIPTS
!define WITHSCRIPTS
!endif
!ifndef WITHHELPERS
!define WITHHELPERS
!endif
!ifndef NOCONFIG
!define NOCONFIG
!endif
!endif

;#######################################
;# Configuration
;#######################################

Name "get_iplayer"
SetCompressor /SOLID lzma
OutFile "${BUILDPATH}\get_iplayer_setup_${VERSION}.exe"
; default install location
InstallDir "$PROGRAMFILES\${PRODUCT}\"
; remember install folder
InstallDirRegKey HKCU "Software\${PRODUCT}" ""

;#######################################
;# Includes
;#######################################
!include "MUI2.nsh"
!include "Sections.nsh"
!include "FileFunc.nsh"
!include "StrFunc.nsh"
!include "TextFunc.nsh"
!include "Locate.nsh"
; StrFunc functions must be declared before use
${StrRep}
${StrCase}
${StrTrimNewLines}

;#######################################
;# Install Locations
;#######################################

; declare here for MUI_DIRECTORYPAGE_VARIABLE below
Var RecDir

;#######################################
;# Pages
;#######################################

; show warning on cancel
!define MUI_ABORTWARNING
; define the setup EXE logo
!define MUI_ICON "${SOURCEPATH}\windows\installer_files\iplayer_logo.ico"
!define MUI_UNICON "${SOURCEPATH}\windows\installer_files\iplayer_uninst.ico"
; welcome page
!insertmacro MUI_PAGE_WELCOME
; license page
!define MUI_PAGE_CUSTOMFUNCTION_PRE LicensePre
!insertmacro MUI_PAGE_LICENSE "${SOURCEPATH}\windows\installer_files\LICENSE.txt"
!ifndef NOCONFIG
; updates page
Page custom UpdatesPage
!endif
; components page
;!define MUI_PAGE_CUSTOMFUNCTION_PRE ComponentsPre
!define MUI_PAGE_HEADER_TEXT "Choose Components"
!define MUI_PAGE_HEADER_SUBTEXT "Choose Components for Installation or Updating"
!define MUI_COMPONENTSPAGE_TEXT_TOP "Check the components you want to install and uncheck the \
  components you don't want to install. You can update a component to the latest recommended version by checking it."
!insertmacro MUI_PAGE_COMPONENTS
; install directory page
!define MUI_PAGE_CUSTOMFUNCTION_PRE DirectoryPre
!define MUI_PAGE_HEADER_TEXT "Choose Install Destination"
!define MUI_PAGE_HEADER_SUBTEXT "Choose the folder in which ${PRODUCT} will be installed."
!define MUI_DIRECTORYPAGE_TEXT_TOP "${PRODUCT} will be installed into the following folder.$\r$\n$\r$\n\
    To use a different folder, click Browse and select another folder. Click Next to continue."
!define MUI_DIRECTORYPAGE_TEXT_DESTINATION "Destination Folder"
!insertmacro MUI_PAGE_DIRECTORY
; recordings directory page
!define MUI_PAGE_CUSTOMFUNCTION_PRE RecordingsDirectoryPre
!define MUI_PAGE_HEADER_TEXT "Choose Recordings Location"
!define MUI_PAGE_HEADER_SUBTEXT "Choose the folder in which ${PRODUCT} will save all the recordings."
!define MUI_DIRECTORYPAGE_TEXT_TOP "${PRODUCT} will record all programmes into the following folder.$\r$\n$\r$\n\
    To use a different folder, click Browse and select another folder. Click Next to continue."
!define MUI_DIRECTORYPAGE_TEXT_DESTINATION "Recordings Folder"
; use $RecDir to avoid overwriting $INSTDIR
!define MUI_DIRECTORYPAGE_VARIABLE $RecDir
!insertmacro MUI_PAGE_DIRECTORY
; instfiles page
!define MUI_PAGE_CUSTOMFUNCTION_PRE InstFilesPre
!insertmacro MUI_PAGE_INSTFILES
; finish page
!insertmacro MUI_PAGE_FINISH
; uninstall pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_COMPONENTS
!insertmacro MUI_UNPAGE_INSTFILES

;#######################################
;# Language
;#######################################

!insertmacro MUI_LANGUAGE "English"

;#######################################
;# get_iplayer host site
;#######################################

!define MOTHERSHIP "http://www.infradead.org"
!define MOTHERSHIP_NAME "infradead.org"

;#######################################
;# Updates and Version Checks
;#######################################

Var UpdatedComponents

; user agent strings for downloads
!define USERAGENT "curl/7.21.7 (i386-pc-win32) libcurl/7.21.7 OpenSSL/0.9.8r zlib/1.2.5"
!define SETUP_UA "get_iplayer windows installer v${VERSION}"
; URLs and file names for updates and version checks
!define SETUPVER "get_iplayer_setup-ver.txt"
!define SETUPVER_CHECK "get_iplayer_setup-ver-check.txt"
!define SETUPVER_URL "${MOTHERSHIP}/get_iplayer_win/VERSION-get_iplayer-win-installer"
!define SETUP_URL "${MOTHERSHIP}/get_iplayer_win/get_iplayer_setup_latest.exe"
!define GIPVER "get_iplayer-ver.txt"
!define GIPVER_CHECK "get_iplayer-ver-check.txt"
!define GIPVER_URL "${MOTHERSHIP}/get_iplayer/VERSION-get_iplayer"
!define GIPPL_URL "${MOTHERSHIP}/get_iplayer/latest/get_iplayer"
!define GIPCGI_URL "${MOTHERSHIP}/get_iplayer/latest/get_iplayer.cgi"
!ifndef NOCONFIG
!define CONFIG "get_iplayer_config.ini"
!define CONFIG_CHECK "get_iplayer_config-check.ini"
!define CONFIG_URL "${MOTHERSHIP}/get_iplayer_win/get_iplayer_config_latest.ini"

; Checks for new version of helper app in config
!macro _CheckHelperUpdate _name _id
  ; old version
  ReadINIStr $8 "$INSTDIR\${CONFIG}" "${_name}" "version"
  ; new version
  ClearErrors
  ReadINIStr $9  "$INSTDIR\${CONFIG_CHECK}" "${_name}" "version"
  IfErrors no_update_${_name}
    StrCmp $9 "" no_update_${_name}
      ; versions equal, no update
      StrCmp $8 $9  no_update_${_name}
        SectionSetFlags ${_id} ${SF_SELECTED}
        ; add notice if versions different
        StrCpy $UpdatedComponents "$UpdatedComponents$\r$\n${_name} ($8 -> $9)"
  no_update_${_name}:
!macroend
!define CheckHelperUpdate '!insertmacro _CheckHelperUpdate'
!endif

;#######################################
;# Helper Section Updates
;#######################################

!macro _UpdateHelperSection _name _id
  ; special case from 4.2
  StrCmp "${_name}" "${RTMPDUMP}" 0 +3
    IfFileExists "$INSTDIR\${RTMPDUMP_OLD}\*.*" 0 +2
      SectionSetFlags ${_id} 0
  IfFileExists "$INSTDIR\${_name}\*.*" 0 +2
    SectionSetFlags ${_id} 0
!macroend
!define UpdateHelperSection '!insertmacro _UpdateHelperSection'

!macro _un.UpdateHelperSection _name _id
  ; special case from 4.2
  StrCmp "${_name}" "${RTMPDUMP}" 0 +3
    IfFileExists "$INSTDIR\${RTMPDUMP_OLD}\*.*" 0 +2
      SectionSetFlags ${_id} ${SF_SELECTED}
  IfFileExists "$INSTDIR\${_name}\*.*" 0 +2
    SectionSetFlags ${_id} ${SF_SELECTED}
!macroend
!define un.UpdateHelperSection '!insertmacro _un.UpdateHelperSection'

;#######################################
;# Helper Apps
;#######################################

Var HelperName
Var HelperKey
Var HelperFile
Var HelperDir
Var HelperExe
Var HelperPath
Var HelperVal
Var HelperVer
Var HelperUrl
Var HelperDoc

; for checking helper EXE binary type
!define SCS_32BIT_BINARY 0
!define SCS_64BIT_BINARY 6

; helper app names for folder/file naming, UI text
!define MPLAYER "MPlayer"
!define LAME "LAME"
!define FFMPEG "FFmpeg"
!define VLC "VLC"
!define RTMPDUMP "RTMPDump"
!define ATOMICPARSLEY "AtomicParsley"

; options file keys for helper apps
!define MPLAYER_KEY "mplayer"
!define LAME_KEY "lame"
!define FFMPEG_KEY "ffmpeg"
!define VLC_KEY "vlc"
!define RTMPDUMP_KEY "flvstreamer"
!define ATOMICPARSLEY_KEY "atomicparsley"

; URLs for helper app downloads (only if config file not used)
!define MPLAYER_URL "${MOTHERSHIP}/cgi-bin/get_iplayer_setup.cgi?mplayer"
!define LAME_URL "${MOTHERSHIP}/cgi-bin/get_iplayer_setup.cgi?lame"
!define FFMPEG_URL "${MOTHERSHIP}/cgi-bin/get_iplayer_setup.cgi?ffmpeg"
!define VLC_URL "${MOTHERSHIP}/cgi-bin/get_iplayer_setup.cgi?vlc"
!define RTMPDUMP_URL "${MOTHERSHIP}/cgi-bin/get_iplayer_setup.cgi?rtmpdump"
!define ATOMICPARSLEY_URL "${MOTHERSHIP}/cgi-bin/get_iplayer_setup.cgi?atomicparsley"

; documentation URLs for helper apps (only if config file not used)
!define MPLAYER_DOC "http://www.mplayerhq.hu/DOCS/HTML/en/index.html"
!define LAME_DOC "http://lame.sourceforge.net/using.php"
!define FFMPEG_DOC "http://ffmpeg.org/ffmpeg-doc.html"
!define VLC_DOC "http://wiki.videolan.org/Documentation:Documentation"
!define RTMPDUMP_DOC "http://rtmpdump.mplayerhq.hu/"
!define ATOMICPARSLEY_DOC "http://atomicparsley.sourceforge.net/"

; common extension for downloaded helpers (may be ZIP or 7Z format, or EXE)
!define HELPER_EXT "zip"

; identifies old rtmpdump from 4.2 that doesn't conform to naming convention
!define RTMPDUMP_OLD "rtmpdump-2.2d"

; Wrapper macros for helper app install/uninstall
!macro _InstallHelper _name _key _url _doc
  StrCpy $HelperName "${_name}"
  StrCpy $HelperKey "${_key}"
  StrCpy $HelperFile "$INSTDIR\${_name}.${HELPER_EXT}"
  StrCpy $HelperDir "$INSTDIR\${_name}"
  StrCpy $HelperExe "${_name}.exe"
  StrCpy $HelperPath ""
  StrCpy $HelperVal ""
!ifndef NOCONFIG
  ; get install params from downloaded config file
  ReadINIStr $HelperVer "$INSTDIR\${CONFIG_CHECK}" "${_name}" "version"
  ReadINIStr $HelperUrl "$INSTDIR\${CONFIG_CHECK}" "${_name}" "url"
  ReadINIStr $HelperDoc "$INSTDIR\${CONFIG_CHECK}" "${_name}" "doc"
!else
  StrCpy $HelperVer "unknown"
  StrCpy $HelperUrl "${_url}"
  StrCpy $HelperDoc "${_doc}"
!endif
  Call InstallHelper
!macroend
!define InstallHelper '!insertmacro _InstallHelper'

!macro un._InstallHelper _name _key
  StrCpy $HelperName "${_name}"
  StrCpy $HelperKey "${_key}"
  StrCpy $HelperFile "$INSTDIR\${_name}.${HELPER_EXT}"
  StrCpy $HelperDir "$INSTDIR\${_name}"
  Call un.InstallHelper
!macroend
!define un.InstallHelper '!insertmacro un._InstallHelper'

; Macros for helper app doc install/uninstall
!macro _InstallHelperDoc _name _doc
  WriteIniStr "$INSTDIR\${_name}_docs.url" "InternetShortcut" "URL" "${_doc}"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Help\${_name} Documentation.lnk" \
    "$INSTDIR\${_name}_docs.url" "" "$SYSDIR\SHELL32.dll" 175
!macroend
!define InstallHelperDoc '!insertmacro _InstallHelperDoc'

!macro un._InstallHelperDoc _name
  Delete "$INSTDIR\${_name}_docs.url"
  Delete "$SMPROGRAMS\get_iplayer\Help\${_name} Documentation.lnk"
!macroend
!define un.InstallHelperDoc '!insertmacro un._InstallHelperDoc'

;#######################################
;# Options File
;#######################################

Var OptionsDir
Var OptionsFile
Var OptionKey
Var OptionVal

; Wrapper macros for creating/deleting options file settings
!macro _InstallOption _key _val
  StrCpy $OptionKey "${_key}"
  StrCpy $OptionVal "${_val}"
  Call InstallOption
!macroend
!define InstallOption '!insertmacro _InstallOption'

!macro un._InstallOption _key
  StrCpy $OptionKey "${_key}"
  Call un.InstallOption
!macroend
!define un.InstallOption '!insertmacro un._InstallOption'

;#######################################
;# Virtual Store-Aware Cleanup
;#######################################

; Remove all get_iplayer files for un/re-install
!macro RemoveGetIPlayer _un
Function ${_un}RemoveGetIPlayer
  StrCpy $1 $INSTDIR
  RMDir /r "$1\lib"
  RMDir /r "$1\perl-license"
  Delete "$1\*.dll"
  Delete "$1\perl.exe"
  Delete "$1\get_iplayer.cgi.cmd"
  Delete "$1\get_iplayer.cmd"
  Delete "$1\iplayer_logo.ico"
  Delete "$1\pvr_manager.cmd"
  Delete "$1\get_iplayer.cgi"
  Delete "$1\get_iplayer.pl"
  Delete "$1\get_iplayer.pl.old"
  Delete "$1\get_iplayer--pvr.bat"
  Delete "$1\run_pvr_scheduler.bat"
  ; URLs
  Delete "$1\command_examples.url"
  Delete "$1\pvr_manager.url"
  Delete "$1\strawberry_docs.url"
  ; clean files in VirtualStore (Win7/Vista) that may have been updated directly by get_iplayer.pl
  StrCpy $2 "$LOCALAPPDATA\VirtualStore\Program Files\get_iplayer"
  Delete "$2\get_iplayer.pl"
  Delete "$2\get_iplayer.pl.old"
FunctionEnd
!macroend
!insertmacro RemoveGetIPlayer ""
!insertmacro RemoveGetIPlayer "un."

;#######################################
;# Section Sizes/Descriptions
;#######################################

; section sizes - update descriptions below if changed
!define MPLAYER_SIZE 26300
!define LAME_SIZE 1200
!define FFMPEG_SIZE 43500
!define VLC_SIZE 81900
!define RTMPDUMP_SIZE 1900
!define ATOMICPARSLEY_SIZE 500

; section descriptions
!define GET_IPLAYER_DESC "Install get_iplayer and required Strawberry Perl - Required for all recordings. \
  Also bundled with Web PVR Manager (~25.9MB)"
!define MPLAYER_DESC "Download and install ${MPLAYER} - Used for RealAudio and MMS recording modes (~26.3MB)"
!define LAME_DESC "Download and install ${LAME} - Used for transcoding RealAudio recordings to MP3 (~1.2MB)"
!define FFMPEG_DESC "Download and install ${FFMPEG} - Used for losslessly converting Flash Video into useful \
  video/audio files formats (~43.5MB)"
!define VLC_DESC "Download and install ${VLC} - Required for playback of playlists and content from \
    Web PVR Manager (~81.9MB)"
!define RTMPDUMP_DESC "Download and install ${RTMPDUMP} - Used for recording Flash video modes (~1.9MB)"
!define ATOMICPARSLEY_DESC "Download and install ${ATOMICPARSLEY} - Used for Tagging MP4 files (~0.5MB)"

;#######################################
;# Sections
;#######################################

Section "get_iplayer" section1
  ; clear files before (re)install
  Call RemoveGetIPlayer
  ; copy files into place
  File "${SOURCEPATH}\windows\get_iplayer\get_iplayer.cgi.cmd"
  File "${SOURCEPATH}\windows\get_iplayer\get_iplayer.cmd"
  File "${SOURCEPATH}\windows\get_iplayer\iplayer_logo.ico"
  File "${SOURCEPATH}\windows\get_iplayer\pvr_manager.cmd"
!ifndef WITHOUTPERL
  File /r "${PERLFILES}\lib"
  File /r "${PERLFILES}\perl-license"
  File "${PERLFILES}\*.dll"
  File "${PERLFILES}\perl.exe"
!endif
!ifdef WITHSCRIPTS
  ; embedded main scripts
  File "/oname=get_iplayer.pl" "${SOURCEPATH}\get_iplayer"
  File "${SOURCEPATH}\get_iplayer.cgi"
  ; embedded plugins
  CreateDirectory "$PROFILE\.get_iplayer"
  SetOutPath "$PROFILE\.get_iplayer"
  File /r "${SOURCEPATH}\plugins"
  SetOutPath $INSTDIR
!else
  ; download get_iplayer
  download1:
  inetc::get /USERAGENT "${USERAGENT}" "${GIPPL_URL}" "$INSTDIR\get_iplayer.pl" /END
  Pop $R0
  StrCmp $R0 "OK" install1
     MessageBox MB_YESNO|MB_ICONQUESTION \
     "Download of get_iplayer failed: $R0, Do you wish to try again?" \
     IDYES download1
     Return
  install1:
  ; update the plugins (with installer privs)
  ExecWait 'perl.exe get_iplayer.pl --plugins-update'
  ; download get_iplayer.cgi
  download2:
  inetc::get /USERAGENT "${USERAGENT}" "${GIPCGI_URL}" "$INSTDIR\get_iplayer.cgi" /END
  Pop $R0
  StrCmp $R0 "OK" install2
     MessageBox MB_YESNO|MB_ICONQUESTION \
     "Download of get_iplayer Web PVR Manager failed: $R0, Do you wish to try again?" \
     IDYES download2
     Return
  install2:
  IfFileExists "$INSTDIR\${GIPVER_CHECK}" got_gipver
    ; another try to download get_iplayer version file
    inetc::get /USERAGENT "${SETUP_UA}" /SILENT "${GIPVER_URL}" "$INSTDIR\${GIPVER_CHECK}" /END
    Pop $R0
    StrCmp $R0 "OK" 0 no_gipver
  got_gipver:
!ifndef NOCONFIG
  ${LineRead} "$INSTDIR\${GIPVER_CHECK}" 1 $1
  ${StrTrimNewLines} $1 $1
  ; update config file
  WriteINIStr "$INSTDIR\${CONFIG}" "get_iplayer" "version" $1
  WriteINIStr "$INSTDIR\${CONFIG}" "perlfiles" "version" ${PERLVER}
!else
  CopyFiles "$INSTDIR\${GIPVER_CHECK}" "$INSTDIR\${GIPVER}"
!endif
  no_gipver:
!endif
  ; create recordings folder
  CreateDirectory $RecDir
  ; set default options
  ${InstallOption} "output" $RecDir
  ${InstallOption} "mmsnothread" "1"
  ${InstallOption} "nopurge" "1"
  ; create run_pvr_scheduler batch file
  FileOpen $0 "$INSTDIR\run_pvr_scheduler.bat" "w"
  FileWrite $0 "cd $INSTDIR$\r$\n"
  FileWrite $0 "perl.exe get_iplayer.pl --pvrschedule 14400$\r$\n"
  FileWrite $0 "$\r$\n"
  FileClose $0
  ; create Windows scheduler batch file
  FileOpen $0 "$INSTDIR\get_iplayer--pvr.bat" "w"
  FileWrite $0 "cd $INSTDIR$\r$\n"
  FileWrite $0 "perl.exe get_iplayer.pl --pvr$\r$\n"
  FileWrite $0 "$\r$\n"
  FileClose $0
  ; URLs
  WriteINIStr "$INSTDIR\command_examples.url" "InternetShortcut" "URL" "http://wiki.github.com/jjl/get_iplayer/"
  WriteINIStr "$INSTDIR\pvr_manager.url" "InternetShortcut" "URL" "http://127.0.0.1:1935"
  WriteINIStr "$INSTDIR\strawberry_docs.url" "InternetShortcut" "URL" "http://strawberryperl.com/"
  ; root start menu items
  CreateShortCut "$SMPROGRAMS\get_iplayer\Get_iPlayer.lnk" "$SYSDIR\cmd.exe" \
    "/k get_iplayer.cmd --search dontshowanymatches && get_iplayer.cmd --help" "$INSTDIR\iplayer_logo.ico"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Recordings Folder.lnk" "$RecDir"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Web PVR Manager.lnk" "$SYSDIR\cmd.exe" \
    "/c pvr_manager.cmd" "$INSTDIR\iplayer_logo.ico"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Run PVR Scheduler Now.lnk" "$SYSDIR\cmd.exe" \
    "/k run_pvr_scheduler.bat" "$INSTDIR\iplayer_logo.ico"
  ; help start menu items
  CreateShortCut "$SMPROGRAMS\get_iplayer\Help\get_iplayer Example Commands.lnk" \
    "$INSTDIR\command_examples.url" "" "$SYSDIR\SHELL32.dll" 175
  CreateShortCut "$SMPROGRAMS\get_iplayer\Help\Strawberry Perl Home.lnk" \
    "$INSTDIR\strawberry_docs.url" "" "$SYSDIR\SHELL32.dll" 175
SectionEnd

Section "un.get_iplayer" un.section1
  MessageBox MB_YESNO|MB_ICONQUESTION|MB_DEFBUTTON2 \
    "Remove User Preferences, PVR Searches, Presets and Recording History?" \
    IDNO clean_files
    ; delete the local user data
    RMDir /r $PROFILE\.get_iplayer
!ifndef NOCONFIG
  ; update config file
  DeleteINISec "$INSTDIR\${CONFIG}" "get_iplayer"
  DeleteINISec "$INSTDIR\${CONFIG}" "perlfiles"
!endif
  clean_files:
  ; clear files on uninstall
  Call un.RemoveGetIPlayer
  ; start menu items
  Delete "$SMPROGRAMS\get_iplayer\Get_iPlayer.lnk"
  Delete "$SMPROGRAMS\get_iplayer\Recordings Folder.lnk"
  Delete "$SMPROGRAMS\get_iplayer\Web PVR Manager.lnk"
  Delete "$SMPROGRAMS\get_iplayer\Run PVR Scheduler Now.lnk"
  Delete "$SMPROGRAMS\get_iplayer\Help\get_iplayer Example Commands.lnk"
  Delete "$SMPROGRAMS\get_iplayer\Help\Strawberry Perl Home.lnk"
SectionEnd

LangString DESC_Section1 ${LANG_ENGLISH} "${GET_IPLAYER_DESC}"

Section ${MPLAYER} section2
!ifdef WITHHELPERS
  ; embedded helper file
  File "${HELPERS}\${MPLAYER}.${HELPER_EXT}"
!endif
  AddSize ${MPLAYER_SIZE}
  ${InstallHelper} ${MPLAYER} ${MPLAYER_KEY} ${MPLAYER_URL} ${MPLAYER_DOC}
SectionEnd

Section "un.${MPLAYER}" un.section2
  ${un.InstallHelper} ${MPLAYER} ${MPLAYER_KEY}
SectionEnd

LangString DESC_Section2 ${LANG_ENGLISH} "${MPLAYER_DESC}"

Section ${LAME} section3
!ifdef WITHHELPERS
  ; embedded helper file
  File "${HELPERS}\${LAME}.${HELPER_EXT}"
!endif
  AddSize ${LAME_SIZE}
  ${InstallHelper} ${LAME} ${LAME_KEY} ${LAME_URL} ${LAME_DOC}
SectionEnd

Section "un.${LAME}" un.section3
  ${un.InstallHelper} ${LAME} ${LAME_KEY}
SectionEnd

LangString DESC_Section3 ${LANG_ENGLISH} "${LAME_DESC}"

Section ${FFMPEG} section4
!ifdef WITHHELPERS
  ; embedded helper file
  File "${HELPERS}\${FFMPEG}.${HELPER_EXT}"
!endif
  AddSize ${FFMPEG_SIZE}
  ${InstallHelper} ${FFMPEG} ${FFMPEG_KEY} ${FFMPEG_URL} ${FFMPEG_DOC}
SectionEnd

Section "un.${FFMPEG}" un.section4
  ${un.InstallHelper} ${FFMPEG} ${FFMPEG_KEY}
SectionEnd

LangString DESC_Section4 ${LANG_ENGLISH} "${FFMPEG_DESC}"

Section ${VLC} section5
!ifdef WITHHELPERS
  ; embedded helper file
  File "${HELPERS}\${VLC}.${HELPER_EXT}"
!endif
  AddSize ${VLC_SIZE}
  ${InstallHelper} ${VLC} ${VLC_KEY} ${VLC_URL} ${VLC_DOC}
  StrCmp $HelperPath "" done
    ${StrRep} $1 $HelperPath ".exe" ".ico"
    CreateShortCut "$SMPROGRAMS\${VLC} Media Player.lnk" $HelperPath "" $1
  done:
SectionEnd

Section "un.${VLC}" un.section5
  Delete "$SMPROGRAMS\${VLC} Media Player.lnk"
  ${un.InstallHelper} ${VLC} ${VLC_KEY}
SectionEnd

LangString DESC_Section5 ${LANG_ENGLISH} "${VLC_DESC}"

Section ${RTMPDUMP} section6
!ifdef WITHHELPERS
  ; embedded helper file
  File "${HELPERS}\${RTMPDUMP}.${HELPER_EXT}"
!endif
  AddSize ${RTMPDUMP_SIZE}
  ${InstallHelper} ${RTMPDUMP} ${RTMPDUMP_KEY} ${RTMPDUMP_URL} ${RTMPDUMP_DOC}
SectionEnd

Section "un.${RTMPDUMP}" un.section6
  ${un.InstallHelper} ${RTMPDUMP} ${RTMPDUMP_KEY}
SectionEnd

LangString DESC_Section6 ${LANG_ENGLISH} "${RTMPDUMP_DESC}"

Section ${ATOMICPARSLEY} section7
!ifdef WITHHELPERS
  ; embedded helper file
  File "${HELPERS}\${ATOMICPARSLEY}.${HELPER_EXT}"
!endif
  AddSize ${ATOMICPARSLEY_SIZE}
  ${InstallHelper} ${ATOMICPARSLEY} ${ATOMICPARSLEY_KEY} ${ATOMICPARSLEY_URL} ${ATOMICPARSLEY_DOC}
SectionEnd

Section "un.${ATOMICPARSLEY}" un.section7
  ${un.InstallHelper} ${ATOMICPARSLEY} ${ATOMICPARSLEY_KEY}
SectionEnd

LangString DESC_Section7 ${LANG_ENGLISH} "${ATOMICPARSLEY_DESC}"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${Section1} $(DESC_Section1)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section2} $(DESC_Section2)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section3} $(DESC_Section3)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section4} $(DESC_Section4)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section5} $(DESC_Section5)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section6} $(DESC_Section6)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section7} $(DESC_Section7)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

;#######################################
;# Before Installation
;#######################################


Function .onInit
  ; init recordings dir
  StrCpy $RecDir "$DESKTOP\iPlayer Recordings\"
!ifdef PRERELEASE
  MessageBox MB_YESNO|MB_ICONQUESTION|MB_DEFBUTTON2 \
    "This is a pre-release build of get_iplayer ${VERSION} for Windows.$\r$\n$\r$\n \
    It may not work properly, and some features may be incomplete.$\r$\n$\r$\n \
    Are you sure you wish to proceed?" \
    IDYES proceed
      Quit
  proceed:
!endif
!ifndef NOCHECK
  ; check for newer installer
  Delete "$TEMP\${SETUPVER_CHECK}"
  ClearErrors
  inetc::get /USERAGENT "${SETUP_UA}" /SILENT "${SETUPVER_URL}" "$TEMP\${SETUPVER_CHECK}" /END
  Pop $R0
  ; abort check and continue if not OK
  StrCmp $R0 "OK" 0 no_new_setup
    ClearErrors
    ${LineRead} "$TEMP\${SETUPVER_CHECK}" 1 $1
    IfErrors no_new_setup
      ${StrTrimNewLines} $1 $1
      Delete "$TEMP\${SETUPVER_CHECK}"
      ; compare versions
      StrCmp $1 ${VERSION} no_new_setup
        MessageBox MB_YESNO|MB_ICONQUESTION \
          "A newer installer version $1 is available. Do you wish to download and run it?" \
          IDYES dl_setup IDNO no_new_setup
  dl_setup:
        ; download new installer
        ClearErrors
        inetc::get /USERAGENT "${SETUP_UA}" "${SETUP_URL}" "$DESKTOP\get_iplayer_setup_$1.exe" /END
        Pop $R0
        StrCmp $R0 "OK" new_setup
          MessageBox MB_YESNO|MB_ICONQUESTION \
          "Download of get_iplayer installer failed$\r$\n$\r$\nError: $R0$\r$\n$\r$\nDo you wish to try again?" \
          IDYES dl_setup
          Goto no_new_setup
  new_setup:
        ; notify user of new installer location
        MessageBox MB_OK|MB_ICONINFORMATION "Installer version $1 has been downloaded to your desktop.  The new installer will now run."
        Exec '"$DESKTOP\get_iplayer_setup_$1.exe"'
        Quit
  no_new_setup:
!endif
  ; default all sections selected
  SectionSetFlags ${Section1} ${SF_SELECTED}
  SectionSetFlags ${Section2} ${SF_SELECTED}
  SectionSetFlags ${Section3} ${SF_SELECTED}
  SectionSetFlags ${Section4} ${SF_SELECTED}
  SectionSetFlags ${Section5} ${SF_SELECTED}
  SectionSetFlags ${Section6} ${SF_SELECTED}
  SectionSetFlags ${Section7} ${SF_SELECTED}
  ; nothing more to do for fresh install
  IfFileExists "$INSTDIR\*.*" +2
    Return
  ; proceed with re-install
  SetOutPath $INSTDIR
!ifndef NOCONFIG
  ; ensure config file exists on re-install
  ; InstFilesPre will create config file on fresh install
  Call InitConfigFile
!endif
  ; set section 'get_iplayer' as unselected if already installed
  IfFileExists "$INSTDIR\get_iplayer.pl" 0 +2
    SectionSetFlags ${Section1} 0
!ifndef WITHSCRIPTS
  ; check for newer get_iplayer version
!ifndef NOCONFIG
  ; check perl support version from config file
  ReadINIStr $2 "$INSTDIR\${CONFIG}" "perlfiles" "version"
  StrCmp $2 ${PERLVER} no_new_perl
    ; new perl means get_iplayer component should be updated
    SectionSetFlags ${Section1} ${SF_SELECTED}
    StrCpy $UpdatedComponents "$UpdatedComponents$\r$\nget_iplayer (Perl Support $2 -> ${PERLVER})"
  no_new_perl:
  ReadINIStr $3 "$INSTDIR\${CONFIG}" "get_iplayer" "version"
!else
  ${LineRead} "$INSTDIR\${GIPVER}" 1 $3
  ${StrTrimNewLines} $3 $3
!endif
  Delete "$INSTDIR\${GIPVER_CHECK}"
  inetc::get /USERAGENT "${SETUP_UA}" /SILENT "${GIPVER_URL}" "$INSTDIR\${GIPVER_CHECK}" /END
  Pop $R0
  ; abort checking new ver and continue if not OK
  StrCmp $R0 "OK" 0 no_new_gip
  ; read contents of version file and compare with current version
  ClearErrors
  ${LineRead} "$INSTDIR\${GIPVER_CHECK}" 1 $4
  IfErrors no_new_gip
    ${StrTrimNewLines} $4 $4
    StrCmp $4 "" no_new_gip
      StrCmp $3 $4 no_new_gip
        SectionSetFlags ${Section1} ${SF_SELECTED}
        ; add notice if versions different
        StrCpy $UpdatedComponents "$UpdatedComponents$\r$\nget_iplayer (Main Script $3 -> $4)"
  no_new_gip:
!endif
  ; set helper app sections as unselected if already installed
  ${UpdateHelperSection} ${MPLAYER} ${section2}
  ${UpdateHelperSection} ${LAME} ${section3}
  ${UpdateHelperSection} ${FFMPEG} ${section4}
  ${UpdateHelperSection} ${VLC} ${section5}
  ${UpdateHelperSection} ${RTMPDUMP} ${section6}
  ${UpdateHelperSection} ${ATOMICPARSLEY} ${section7}
!ifndef WITHHELPERS
!ifndef NOCONFIG
  ; check for newer helper app versions
  Delete "$INSTDIR\${CONFIG_CHECK}"
  inetc::get /USERAGENT "${SETUP_UA}" /SILENT "${CONFIG_URL}" "$INSTDIR\${CONFIG_CHECK}" /END
  Pop $R0
  ; abort checking new ver and continue if not OK
  StrCmp $R0 "OK" 0 no_new_config
    ; check for helper updates
    ${CheckHelperUpdate} ${MPLAYER} ${Section2}
    ${CheckHelperUpdate} ${LAME} ${Section3}
    ${CheckHelperUpdate} ${FFMPEG} ${Section4}
    ${CheckHelperUpdate} ${VLC} ${Section5}
    ${CheckHelperUpdate} ${RTMPDUMP} ${Section6}
    ${CheckHelperUpdate} ${ATOMICPARSLEY} ${Section7}
  no_new_config:
!endif
!endif
FunctionEnd

;#######################################
;# After Successful Installation
;#######################################

Function .onInstSuccess
  ; remove items obsolete in 4.3+
  RMDir /r "$INSTDIR\Downloads"
  Delete "$INSTDIR\linuxcentre.url"
  Delete "$INSTDIR\get_iplayer_setup.nsi"
  Delete "$INSTDIR\update_get_iplayer.cmd"
  ; URLs
  WriteINIStr "$INSTDIR\get_iplayer_home.url" "InternetShortcut" "URL" "${MOTHERSHIP}/get_iplayer/"
  WriteINIStr "$INSTDIR\nsis_docs.url" "InternetShortcut" "URL" "http://nsis.sourceforge.net/"
  WriteINIStr "$INSTDIR\download_latest_installer.url" "InternetShortcut" "URL" "${SETUP_URL}"
  CreateShortCut "$SMPROGRAMS\get_iplayer\Help\Get_iPlayer Home.lnk" "$INSTDIR\get_iplayer_home.url" "" "$SYSDIR\SHELL32.dll" 175
  CreateShortCut "$SMPROGRAMS\get_iplayer\Help\NSIS Installer Home.lnk" "$INSTDIR\nsis_docs.url" "" "$SYSDIR\SHELL32.dll" 175
  CreateShortCut "$SMPROGRAMS\get_iplayer\Updates\Download Latest Installer.lnk" "$INSTDIR\download_latest_installer.url" "" "$SYSDIR\SHELL32.dll" 220
  ; put uninstall info in registry
  CreateShortCut "$SMPROGRAMS\get_iplayer\Uninstall Components.lnk" "$INSTDIR\Uninst.exe" "" "$INSTDIR\Uninst.exe" 0
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "DisplayName" "${PRODUCT} ${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "URLInfoAbout" "${MOTHERSHIP}/get_iplayer/"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "Publisher" "${MOTHERSHIP_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "UninstallString" "$INSTDIR\Uninst.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer" "DisplayIcon" "$INSTDIR\Uninst.exe"
  WriteRegStr HKCU "Software\${PRODUCT}" "" "$INSTDIR"
  WriteUninstaller "$INSTDIR\Uninst.exe"
FunctionEnd

;#######################################
;# Before Uninstallation
;#######################################

Function un.onInit
  ; ensure options file path is defined
  Call un.CreateOptionsPaths
!ifndef NOCONFIG
  Call un.InitConfigFile
!endif
  ; default all components unselected
  SectionSetFlags ${Section1} ${SF_RO}
  SectionSetFlags ${Section2} ${SF_RO}
  SectionSetFlags ${Section3} ${SF_RO}
  SectionSetFlags ${Section4} ${SF_RO}
  SectionSetFlags ${Section5} ${SF_RO}
  SectionSetFlags ${Section6} ${SF_RO}
  SectionSetFlags ${Section7} ${SF_RO}
  ; set section 'get_iplayer' as selected if already installed
  IfFileExists "$INSTDIR\get_iplayer.pl" 0 helper_sections
  SectionSetFlags ${Section1} ${SF_SELECTED}
  helper_sections:
  ; set helper app sections as selected if already installed
  ${un.UpdateHelperSection} ${MPLAYER} ${section2}
  ${un.UpdateHelperSection} ${LAME} ${section3}
  ${un.UpdateHelperSection} ${FFMPEG} ${section4}
  ${un.UpdateHelperSection} ${VLC} ${section5}
  ${un.UpdateHelperSection} ${RTMPDUMP} ${section6}
  ${un.UpdateHelperSection} ${ATOMICPARSLEY} ${section7}
FunctionEnd

;#######################################
;# After Successful Uninstallation
;#######################################

Function un.onUninstSuccess
  IfFileExists "$INSTDIR\get_iplayer.pl" no_clean
  IfFileExists "$INSTDIR\${MPLAYER}\*.*" no_clean
  IfFileExists "$INSTDIR\${LAME}\*.*" no_clean
  IfFileExists "$INSTDIR\${FFMPEG}\*.*" no_clean
  IfFileExists "$INSTDIR\${VLC}\*.*" no_clean
  IfFileExists "$INSTDIR\${RTMPDUMP}\*.*" no_clean
  IfFileExists "$INSTDIR\${ATOMICPARSLEY}\*.*" no_clean
    ; remove shortcuts
    Delete "$INSTDIR\get_iplayer_home.url"
    Delete "$INSTDIR\nsis_docs.url"
    Delete "$INSTDIR\download_latest_installer.url"
    ; remove start menu dirs and all contents
    RMDir /r "$SMPROGRAMS\get_iplayer"
    ; remove the global options file
    Delete $OptionsFile
    RMDir $OptionsDir
    ; remove version files
    Delete "$INSTDIR\${GIPVER}"
    Delete "$INSTDIR\${GIPVER_CHECK}"
!ifndef NOCONFIG
    ; remove config files
    Delete "$INSTDIR\${CONFIG}"
    Delete "$INSTDIR\${CONFIG_CHECK}"
!endif
    ; remove installed status in registry
    DeleteRegKey HKCU "SOFTWARE\get_iplayer"
    DeleteRegKey HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\get_iplayer"
    HideWindow
    MessageBox MB_OK|MB_ICONINFORMATION "$(^Name) was successfully removed from your computer.."
    ; remove uninstaller and install dir
    Delete "$INSTDIR\Uninst.exe"
    RMDir $INSTDIR
    Return
  no_clean:
  HideWindow
  MessageBox MB_OK|MB_ICONINFORMATION "$(^Name) selected components were successfully removed from your computer.."
FunctionEnd

;#######################################
;# Custom Page Functions
;#######################################

Function LicensePre
  ; read install dir from registry
  ReadRegStr $1 HKCU "Software\${PRODUCT}" ""
  ; skip license if already installed
  StrCmp $1 "" done
    Abort
  done:
FunctionEnd

!ifndef NOCONFIG
Function UpdatesPage
  ; skip if no updated components
  StrCmp $UpdatedComponents "" 0 +2
    Abort
  !insertmacro MUI_HEADER_TEXT "Updates Available" "Updates are available for ${PRODUCT} components."
	nsDialogs::Create 1018
	Pop $0
	StrCmp $0 error 0 +2
		Abort
  nsDialogs::CreateControl EDIT ${DEFAULT_STYLES}|${ES_MULTILINE}|${ES_READONLY} 0 0 0 100% 100% \
    "The updated components below have automatically been selected for installation. \
    Updating is strongly recommended, but you may uncheck any components you do not wish to update on the following page.$\r$\n\
    $UpdatedComponents"
	Pop $0
	StrCmp $0 error 0 +2
		Abort
	nsDialogs::Show
FunctionEnd
!endif

Function DirectoryPre
  ; read install dir from registry
  ReadRegStr $1 HKCU "Software\${PRODUCT}" ""
  ; skip destination selection if already installed
  StrCmp $1 "" done
    Abort
  done:
FunctionEnd

Function RecordingsDirectoryPre
  ; skip destination selection if get_iplayer is not a selected section
  SectionGetFlags ${section1} $1
  IntOp $1 $1 & ${SF_SELECTED}
  IntCmp $1 ${SF_SELECTED} done
    Abort
  done:
FunctionEnd

Function InstFilesPre
  SetOutPath $INSTDIR
  ; start menu dirs
  CreateDirectory "$SMPROGRAMS\get_iplayer\Updates"
  CreateDirectory "$SMPROGRAMS\get_iplayer\Help"
  ; ensure options file exists
  Call CreateOptionsFile
!ifndef NOCONFIG
  ; ensure config files exist on fresh install
  Call InitConfigFile
  IfFileExists "$INSTDIR\${CONFIG_CHECK}" got_config_check
    inetc::get /USERAGENT "${SETUP_UA}" /SILENT "${CONFIG_URL}" "$INSTDIR\${CONFIG_CHECK}" /END
    Pop $R0
    StrCmp $R0 "OK" got_config_check
    ; use built-in config on error
    File "/oname=${CONFIG_CHECK}" "${SOURCEPATH}\windows\${CONFIG}"
  got_config_check:
!endif
FunctionEnd

;#######################################
;# Config File Functions
;#######################################

!ifndef NOCONFIG
Function InitConfigFile
  IfFileExists "$INSTDIR\${CONFIG}" got_config
    FileOpen $0 "$INSTDIR\${CONFIG}" w
    FileClose $0
  got_config:
  WriteINIStr "$INSTDIR\${CONFIG}" "get_iplayer_setup" "lastinstallversion" ${VERSION}
  ${GetTime} "" "LS" $R0 $R1 $R2 $R3 $R4 $R5 $R6
  WriteINIStr "$INSTDIR\${CONFIG}" "get_iplayer_setup" "lastinstalltime" "$R2-$R1-$R0T$R4:$R5:$R6Z"
FunctionEnd

Function un.InitConfigFile
  ; skip if config file not found
  IfFileExists "$INSTDIR\${CONFIG}" 0 no_config
    WriteINIStr "$INSTDIR\${CONFIG}" "get_iplayer_setup" "lastuninstallversion" ${VERSION}
    ${GetTime} "" "LS" $R0 $R1 $R2 $R3 $R4 $R5 $R6
    WriteINIStr "$INSTDIR\${CONFIG}" "get_iplayer_setup" "lastuninstalltime" "$R2-$R1-$R0T$R4:$R5:$R6Z"
  no_config:
FunctionEnd
!endif

;#######################################
;# Options File Functions
;#######################################

; Define paths to global options dir/file
!macro CreateOptionsPaths _un
Function ${_un}CreateOptionsPaths
  ReadEnvStr $1 "ALLUSERSPROFILE"
  StrCpy $OptionsDir "$1\get_iplayer"
  StrCpy $OptionsFile "$OptionsDir\options"
 FunctionEnd
!macroend
!insertmacro CreateOptionsPaths ""
!insertmacro CreateOptionsPaths "un."

; Create global options file if necessary
Function CreateOptionsFile
  Call CreateOptionsPaths
  ; create global options folder if needed
  IfFileExists "$OptionsDir\*.*" check_file
  ClearErrors
  CreateDirectory $OptionsDir
  IfErrors 0 check_file
    MessageBox MB_OK|MB_ICONSTOP "Could not create global options directory:$\r$\n$\r$\n$OptionsDir$\r$\n$\r$\nAborting installation."
    Abort
  check_file:
  ; create global options file if needed
  IfFileExists $OptionsFile done
    ClearErrors
    FileOpen $0 $OptionsFile "w"
    FileClose $0
    IfErrors 0 done
      MessageBox MB_OK|MB_ICONSTOP "Could not create global options file:$\r$\n$\r$\n$OptionsFile$\r$\n$\r$\nAborting installation."
      Abort
  done:
  Push "OK"
FunctionEnd

; Write entry in global options file
; Wrapped by _InstallOption
Function InstallOption
  ${ConfigWrite} $OptionsFile "$OptionKey " $OptionVal $0
  Push $0
FunctionEnd

; Delete entry in global options file
; Wrapped by un._InstallOption
Function un.InstallOption
  ${ConfigWrite} $OptionsFile "$OptionKey " "" $0
  Push $0
FunctionEnd

;#######################################
;# Helper App Utility Functions
;#######################################

!ifndef WITHHELPERS
; Download $HelperUrl to $HelperFile
Function DownloadHelper
  download:
  inetc::get /USERAGENT "${USERAGENT}" $HelperUrl $HelperFile /END
  Pop $R0
  StrCmp $R0 "OK" success
    MessageBox MB_YESNO|MB_ICONQUESTION \
      "Download failed: $HelperUrl$\r$\n$\r$\nError: $R0$\r$\n$\r$\nDo you wish to try again?" \
      IDYES download
    Push "EFAIL"
    Return
  success:
  Push "OK"
FunctionEnd
!endif

; Extract $HelperFile to $OUTDIR
Function UnpackHelper
  ; MUST try ZipDLL first regardless of file extension (Nsis7z doesn't return error code)
  ; ZIP format file will be extracted, 7Z format file will error and fall through
  ZipDLL::extractall $HelperFile $OUTDIR
  Pop $R0
  StrCmp $R0 "success" done
    ; else fall through to Nsis7z
    Nsis7z::ExtractWithDetails $HelperFile "Installing $HelperName %s..."
  done:
FunctionEnd

;#######################################
;# Helper App Install Functions
;#######################################

; Download and unpack helper app archive and locate EXE
; Wrapped by _InstallHelper
Function InstallHelper
!ifndef WITHHELPERS
  ; helper app archive to download
  ; download helper app archive
  StrCmp $HelperUrl "" 0 got_url
    MessageBox MB_OK|MB_ICONEXCLAMATION "Missing download URL$\r$\n$\r$\nSkipped installation: $HelperName"
    Push "ENOURL"
    Return
  got_url:
  Call DownloadHelper
  Pop $R0
  StrCmp $R0 "OK" create_dir
    MessageBox MB_OK|MB_ICONEXCLAMATION "Download failed$\r$\n$\r$\nSkipped installation: $HelperName"
    Push "ENODL"
    Return
  create_dir:
!endif
  ; special case from 4.2
  StrCmp $HelperName ${RTMPDUMP} 0 +3
    IfFileExists "$INSTDIR\${RTMPDUMP_OLD}\*.*" 0 +2
      RMDir /r "$INSTDIR\${RTMPDUMP_OLD}"
  ; create target dir for helper app
  RMDir /r $HelperDir
  SetOutPath $HelperDir
  ; unpack archive
  Call UnpackHelper
  ; restore $OUTDIR
  SetOutPath $INSTDIR
  ; check for empty dir
  ${DirState} $HelperDir $R0
  IntCmp $R0 1 delete_file
    ; might be just EXE that was downloaded
    StrCpy $R1 $HelperFile
    System::Call "kernel32::GetBinaryType(t R1, *i .R2) i .R0"
    ; rename and save if 32-bit EXE
    IntCmp $R2 ${SCS_32BIT_BINARY} 0 not_exe
    ; generate lower case EXE name
    ${StrCase} $R0 $HelperName "L"
    StrCpy $R1 "$HelperDir\$R0.exe"
    Rename $HelperFile $R1
    Goto got_exe
    not_exe:
    MessageBox MB_OK|MB_ICONEXCLAMATION "Extract failed: $HelperFile$\r$\n$\r$\nSkipped installation: $HelperName"
    RMDir /r $HelperDir
    Delete $HelperFile
    Push "ENOFILE"
    Return
  delete_file:
  ; remove archive after unpacking
  Delete $HelperFile
  ; $R1 = helper EXE
  StrCpy $R1 ""
	${locate::Open} $HelperDir "/F=1 /D=0 /N=$HelperExe" $0
	StrCmp $0 0 0 loop_locate
    MessageBox MB_OK|MB_ICONEXCLAMATION "Could not open $HelperDir for search$\r$\n$\r$\nSkipped installation: $HelperName"
    ${locate::Close} $0
    ${locate::Unload}
    RMDir /r $HelperDir
    Return
	loop_locate:
	${locate::Find} $0 $R9 $R8 $R7 $R6 $R5 $R4
  StrCmp $R9 "" stop_locate
    ; get binary type of located EXE
    System::Call "kernel32::GetBinaryType(t R9, *i .R2) i .R0"
    ; must be 32-bit Windows EXE
    IntCmp $R2 ${SCS_32BIT_BINARY} 0 +2
      ; save EXE path
      StrCpy $R1 $R9
    Goto loop_locate
	stop_locate:
	${locate::Close} $0
	${locate::Unload}
  StrCmp $R1 "" 0 got_exe
    MessageBox MB_OK|MB_ICONEXCLAMATION "Could not locate $HelperExe in $HelperDir$\r$\n$\r$\nSkipped installation: $HelperName"
    RMDir /r $HelperDir
    Push "ENOEXE"
    Return
  got_exe:
  StrCpy $HelperPath $R1
  ; use relative EXE path for options file
  ${StrRep} $HelperVal $HelperPath $INSTDIR "."
  ${InstallOption} $HelperKey $HelperVal
  ; skip empty doc url
  StrCmp $HelperDoc "" no_doc
    ${InstallHelperDoc} $HelperName $HelperDoc
  no_doc:
!ifndef NOCONFIG
  WriteINIStr "$INSTDIR\${CONFIG}" $HelperName "version" $HelperVer
  WriteINIStr "$INSTDIR\${CONFIG}" $HelperName "url" $HelperUrl
  WriteINIStr "$INSTDIR\${CONFIG}" $HelperName "doc" $HelperDoc
!endif
FunctionEnd

; Remove helper app and option setting
; Wrapped by un._InstallHelper
Function un.InstallHelper
!ifndef NOCONFIG
  DeleteINISec "$INSTDIR\${CONFIG}" $HelperName
!endif
  ${un.InstallHelperDoc} $HelperName
  ${un.InstallOption} $HelperKey
  ; special case from 4.2
  StrCmp $HelperName ${RTMPDUMP} 0 +3
    IfFileExists "$INSTDIR\${RTMPDUMP_OLD}\*.*" 0 +2
      RMDir /r "$INSTDIR\${RTMPDUMP_OLD}"
  RMDir /r $HelperDir
  Delete $HelperFile
FunctionEnd
