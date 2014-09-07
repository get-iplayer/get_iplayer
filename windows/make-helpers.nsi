; CHANGE URLS TO MATCH CURRENT INSTALLER!

!ifndef BUILDPATH
!define BUILDPATH "."
!endif

Name "make-helpers"
OutFile "${BUILDPATH}\make-helpers.exe"
InstallDir "$EXEDIR\helpers"

Page directory
Page instfiles

!define USERAGENT "curl/7.21.7 (i386-pc-win32) libcurl/7.21.7 OpenSSL/0.9.8r zlib/1.2.5"

; Helper app names - used for folder/file naming, UI text
!define MPLAYER "MPlayer"
!define LAME "LAME"
!define FFMPEG "FFmpeg"
!define VLC "VLC"
!define RTMPDUMP "RTMPDump"
!define ATOMICPARSLEY "AtomicParsley"

; TODO: finalise URLs
; URLs for helper app downloads

!define MPLAYER_URL "http://sourceforge.net/projects/get-iplayer/files/win32/utils/mplayer-svn-r32050-4.5.0/mplayer.exe/download"
!define LAME_URL "http://www.rarewares.org/files/mp3/lame3.99.5.zip"
!define FFMPEG_URL "http://ffmpeg.zeranoe.com/builds/win32/static/ffmpeg-2.2.3-win32-static.7z"
!define VLC_URL "http://get.videolan.org/vlc/2.1.5/win32/vlc-2.1.5-win32.7z"
!define RTMPDUMP_URL "http://ffmpeg.zeranoe.com/builds/win32/external_libs/rtmpdump-20140302-git-79459a2-win32.7z"
!define ATOMICPARSLEY_URL "https://bitbucket.org/jonhedgerows/atomicparsley/downloads/AtomicParsley-0.9.6-hg109.9183fff907bf.zip"

; !define MPLAYER_URL "http://www.infradead.org/cgi-bin/get_iplayer.cgi?mplayer"
; !define LAME_URL "http://www.infradead.org/cgi-bin/get_iplayer.cgi?lame"
; !define FFMPEG_URL "http://www.infradead.org/cgi-bin/get_iplayer.cgi?ffmpeg"
; !define VLC_URL "http://www.infradead.org/cgi-bin/get_iplayer.cgi?vlc"
; !define RTMPDUMP_URL "http://www.infradead.org/cgi-bin/get_iplayer.cgi?rtmpdump"
; !define ATOMICPARSLEY_URL "http://www.infradead.org/cgi-bin/get_iplayer.cgi?atomicparsley"

Section
  SetOutPath $INSTDIR
  Push ${MPLAYER}
  Push ${MPLAYER_URL}
  Call DownloadHelper
  Push ${LAME}
  Push ${LAME_URL}
  Call DownloadHelper
  Push ${FFMPEG}
  Push ${FFMPEG_URL}
  Call DownloadHelper
  Push ${VLC}
  Push ${VLC_URL}
  Call DownloadHelper
  Push ${RTMPDUMP}
  Push ${RTMPDUMP_URL}
  Call DownloadHelper
  Push ${ATOMICPARSLEY}
  Push ${ATOMICPARSLEY_URL}
  Call DownloadHelper
SectionEnd

Function DownloadHelper
  Pop $2
  Pop $1
  download:
  inetc::get /USERAGENT "${USERAGENT}" $2 "$1.zip" /END
  Pop $R0
  StrCmp $R0 "OK" done
    MessageBox MB_YESNO|MB_ICONQUESTION \
      "Download of $2 failed$\n$\nError: $R0$\n$\nDo you wish to try again?" \
      IDYES download
    MessageBox MB_ICONEXCLAMATION "Download of $2 failed$\nSkipping $1"
  done:
FunctionEnd
