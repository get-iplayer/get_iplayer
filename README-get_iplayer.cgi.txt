# get_iplayer PVR Manager
# -----------------------
#
# The Worlds most insecure web-based PVR Manager adn streaming proxy for get_iplayer
# ** WARNING ** Never run this in an untrusted environment or facing the internet
#
#    Copyright (C) 2009 Phil Lewis
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Phil Lewis
# Email: iplayer2 (at sign) linuxcentre.net
# Web: http://linuxcentre.net/iplayer
# License: GPLv3 (see LICENSE.txt)
#

# Features:
# * Search for progs
# * Lists/Adds/Removes PVR entries
# * Acts as a proxy to stream any programme over HTTP
# * Automatically generates playlists for any programme type
#
# Run with embedded web server (preferred method):
# * By default this will run as the user you start the script with
# * Start with: ./get_iplayer.cgi 1935 /path/to/get_iplayer
# * On Win32 Start with: perl.exe .\get_iplayer.cgi 1935 .\get_iplayer.cmd
# * Access using: http://localhost:1935/
#
# Installation as Apache CGI script (not the preferred method):
# * By default this will run as apache user and save all settings files in /var/www/.get_iplayer
# * Change the $get_iplayer variable to tell this script where get_iplayer can be found (may need to set $HOME also)
# * Ensure that the output dir is writable by apache user
# * in apache config, add a line like: ScriptAlias /get_iplayer.cgi "/path/to/get_iplayer.cgi"
# * Access using http://<your web server>/get_iplayer.cgi
#
# Direct Streaming from embedded web server (not win32)
# -----------------------------------------------------
# * Use these URLs directly to stream the mov file
# * Record Stream: http://localhost:1935/record?PID=tv:<PID>&FILENAME=<filename>
# * Stream flash AAC liveradio as 320k mp3 stream: 
#	mplayer -cache 1024 "http://localhost:1935/stream?PID=liveradio:<PID>&BITRATE=320&MODES=flashaac&OUTTYPE=nnn.mp3"
# * Stream flash livetv as flv stream:
#	mplayer -cache 1024 "http://localhost:1935/stream?PID=livetv:<PID>&MODES=flashnormal&OUTTYPE=nnn.flv"
# * Stream flash AAC liveradio as raw wav stream:
#	mplayer -cache 1024 "http://localhost:1935/stream?PID=liveradio:<PID>&MODES=flashaac&OUTTYPE=nnn.wav"
# * Stream tv as http quicktime stream:
#	mplayer -cache 2048 "http://localhost:1935/stream?PID=tv:<PID>&MODES=iphone&OUTTYPE=nnn.mov"
# * Stream iphone radio as http mp3 stream:
#	mplayer -cache 1024 "http://localhost:1935/stream?PID=radio:<PID>&MODES=iphone&OUTTYPE=nnn.mp3"
# * Stream flash mp3 radio as http flac stream:
#	mplayer -cache 1024 "http://localhost:1935/stream?PID=radio:<PID>&MODES=flashaudio&OUTTYPE=nnn.flac"
#
# Valid OUTTYPE values are: wav,mp3,rm,flv,mov
#
#
# Automatic Playlists
# -------------------
# Notes: - Ensure you open the playlist window in VLC
#	 - Tested in mplayer, vlc
#
# * All radio programmes - all modes (flashaac,flashaudio,iphone,realaudio):
#	vlc "http://127.0.0.1:1935/playlist?PROGTYPES=radio"
# * All tv programmes - all modes (flashhigh,iphone,flashnormal):
#	vlc "http://127.0.0.1:1935/playlist?PROGTYPES=tv"
# * All livetv channels:
#	vlc "http://127.0.0.1:1935/playlist?PROGTYPES=livetv"
# * All liveradio channels:
#	vlc "http://127.0.0.1:1935/playlist?PROGTYPES=liveradio"
# More specific examples:
# * All liveradio channels (e.g. flashaac as flv):
#	vlc "http://127.0.0.1:1935/playlist?PROGTYPES=liveradio&MODES=flashaac&OUTTYPE=flv"
# * All liveradio channels (e.g. flashaac as wav):
#	vlc "http://127.0.0.1:1935/playlist?PROGTYPES=liveradio&MODES=flashaac&OUTTYPE=wav"
# * All liveradio channels (e.g. realaudio):
#	vlc "http://127.0.0.1:1935/playlist?PROGTYPES=liveradio&MODES=realaudio&OUTTYPE=rm"
# * All liveradio channels (e.g. flashaac,realaudio):
#	vlc "http://127.0.0.1:1935/playlist?PROGTYPES=liveradio&MODES=flashaac,realaudio&OUTTYPE=flv"
# * All radio programmes (e.g. flash):
#	vlc "http://127.0.0.1:1935/playlist?PROGTYPES=radio&MODES=flash&OUTTYPE=flv"
# * All liveradio channels with a single digit in their name
#	vlc "http://127.0.0.1:1935/playlist?PROGTYPES=liveradio&SEARCH=' \d '"
# * All tv programmes with the word 'news' in their name:
#	vlc "http://127.0.0.1:1935/playlist?PROGTYPES=tv&SEARCH='news'"
#
#
# Automatic OPML Playlists (works with Squeezebox)
# ------------------------------------------------
# See: http://wiki.slimdevices.com/index.php/OPMLSupport for details on syntax
# Note: Programmes that are realaudio mode only will not work yet - only flashaudio, flashaac and iphone work
#
# In Squeezecenter, Add this URL to 'Favourites' and you will be able to navigate the programmes:
# * BBC iPlayer Listen Again:
#	http://<SERVER IP>:1935/opml?PROGTYPES=radio&MODES=flash,iphone&LIST=channel
# * BBC iPlayer Live Flash AAC:
#	http://<SERVER IP>:1935/opml?PROGTYPES=liveradio&OUTTYPE=wav
# * BBC iPlayer Live Flash AAC (Numbered Channels only)
#	http://<SERVER IP>:1935/opml?PROGTYPES=liveradio&MODES=flash&SEARCH=%20\d&OUTTYPE=wav
#
#
# Setup crontab for PVR to run
# ----------------------------
# * Add a line in /etc/crontab to run the pvr: "0 * * * * apache /usr/bin/get_iplayer --pvr 2>/dev/null"
#
# Caveats:
# --------
# * Sometimes takes a while to load page while refreshing caches
# * Streaming link seems to fail with a SIGPIPE on firefox/Linux - works OK if you use the link in vlc or 'mplayer -cache 3000'
# * If a boolean param is in the cookies then it overrides the unchecked status on the form regardless
# * When using the stream or record links directly, cookies are not sent and the settings are not applied such as SCRIPTPATH
#
# Todo:
# * Manual flush of Indicies (maybe normally set --expiry to 99999999 and warn that indicies are out of date)
# * Add loads of options
# * in general, take presentation data out of the html and into css, take scripting out of the html and into the js
# * Add a button to save the playlist in M3U or OPML (playlist of selected progs?)
