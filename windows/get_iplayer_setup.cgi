#!/bin/sh

# CGI script to support get_iplayer Windows installer
# Redirects to download URLs for Win32 helper applications
# corresponding to pre-defined keys passed as query string.
# This script must be available at:
#   http://www.infradead.org/cgi-bin/get_iplayer_setup.cgi
# Example:
#   Request : http://www.infradead.org/cgi-bin/get_iplayer_setup.cgi?lame
#   Redirect: http://www.exe64.com/mirror/rarewares/lame3.98.4.zip

TARGET=

case "$QUERY_STRING" in
    mplayer)
        TARGET="http://www8.mplayerhq.hu/MPlayer/releases/win32/MPlayer-mingw32-1.0rc2.zip"
    ;;
    lame)
        TARGET="http://www.exe64.com/mirror/rarewares/lame3.98.4.zip"
    ;;
    ffmpeg)
        TARGET="http://ffmpeg.zeranoe.com/builds/win32/static/ffmpeg-0.8-win32-static.7z"
    ;;
    vlc)
        TARGET="http://www.grangefields.co.uk/mirrors/videolan/vlc/1.1.11/win32/vlc-1.1.11-win32.7z"
    ;;
    rtmpdump)
        TARGET="http://rtmpdump.mplayerhq.hu/download/rtmpdump-20110723-git-b627335-win32.zip"
    ;;
    atomicparsley)
        TARGET="http://bitbucket.org/jonhedgerows/atomicparsley/downloads/AtomicParsley-0.9.4.zip"
    ;;
esac

if [ "$TARGET" == "" ]; then
    cat <<EOF
Content-Type: text/html

<HTML><TITLE>Error</TITLE></HEAD>
<BODY><H1>Error</H1>
You requested '$QUERY_STRING' but that isn't one of the known downloads.
EOF
fi

cat <<EOF
Location: $TARGET
Content-Type: text/plain

Redirecting to $TARGET
EOF
