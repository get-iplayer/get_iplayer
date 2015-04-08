get_iplayer Web PVR Manager
-----------------------

The world's most insecure web-based PVR manager and streaming proxy for get_iplayer
** WARNING ** Never run this in an untrusted environment or facing the internet

Copyright (C) 2009-2010 Phil Lewis

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Author: Phil Lewis
Email: iplayer2 (at sign) linuxcentre.net
License: GPLv3 (see LICENSE.txt)


Features
--------
* Search for programmes
* List/Add/Remove PVR entries
* Acts as a proxy to stream any programme over HTTP
* Automatically generates playlists for any programme type
* See web site:

http://www.infradead.org/get_iplayer/html/get_iplayer.html


Run with embedded web server
----------------------------

* By default this will run as the user you start the script with

* Start with:

./get_iplayer.cgi -p 1935 [-g /path/to/get_iplayer] [-l 127.0.0.1] [--ffmpeg /path/to/ffmpeg]

* On Win32 start with:

perl.exe .\get_iplayer.cgi -p 1935 [-g \path\to\get_iplayer] [-l 127.0.0.1] [--ffmpeg \path\to\ffmpeg]

* Access using:
	
http://localhost:1935/

To allow access from remote machines
------------------------------------
This capability should only be used on a secure, trusted network. If this UI is exposed to the internet then the computer running the code will quickly be compromised.

1) Unix based hosts
Edit /etc/default/get_iplayer_web_pvr and comment the line
# LISTEN=127.0.0.1
and uncomment the line 
LISTEN=0.0.0.0
start the web server with the command 
kevin$ get_iplayer_web_pvr

2) Windows

edit "get_iplayer.cgi.cmd", which on XP is in C:\Program Files\get_iplayer\

change --listen=127.0.0.1 to --listen=0.0.0.0
after a restart of the web ui it will then listen for incoming connections on all adapters not just localhost


Installation as Apache CGI script
---------------------------------

* Run the below commands as root

* Create dirs in /var/www/get_iplayer/:

mkdir -p /var/www/get_iplayer/output /var/www/get_iplayer/.get_iplayer

* Allow apache user to write to these dirs:

chown apache.apache /var/www/get_iplayer/output /var/www/get_iplayer/.get_iplayer

* Copy get_iplayer.cgi and get_iplayer into /var/www/get_iplayer/

cp -p get_iplayer.cgi get_iplayer /var/www/get_iplayer/

* Ensure they are executable:

chmod 755 /var/www/get_iplayer/get_iplayer.cgi /var/www/get_iplayer/get_iplayer

* Perform one-off plugins setup:

 /var/www/get_iplayer/get_iplayer --profile-dir /var/www/get_iplayer/.get_iplayer --plugins-update

* Ensure you have the following lines in Apache's httpd.conf:

ScriptAlias /iplayer "/var/www/get_iplayer/get_iplayer.cgi" 
SetEnv HOME /var/www/get_iplayer/ 

* This will run as apache's user/group and save all settings files in /var/www/get_iplayer/.get_iplayer

* Ensure that ffmpeg is in the default system PATH that apache exports such as /usr/bin/

* Ensure that rtmpdump (and other binaries) are in the default system PATH that apache exports such as /usr/bin/ or
  specify their locations in /var/www/get_iplayer/.get_iplayer/options, and specify a default output directory in 
  /var/www/get_iplayer/.get_iplayer/options, e.g.:

output /var/www/get_iplayer/output	
ffmpeg /usr/bin/ffmpeg	
rtmpdump /path/to/rtmpdump	
mplayer /path/to/mplayer	
atomicparsley /path/to/atomicparsley
id3v2 /path/to/id3v2

* Make sure that apache user can see and execute the binaries

* Access using http://<your web server>/iplayer

* Recordings will be in /var/www/get_iplayer/output/


Usage
------

* Assumes web server is running with script at 'http://localhost/iplayer'

* Embedded web server can be accessed (assuming port 1935) as 'http://localhost:1935/' or 'http://localhost:1935/iplayer' 

* Valid OUTTYPE values are: wav,mp3,rm,flv,mov

* You can open most of these URLs as 'vlc <URL>' or 'mplayer -cache=<kb> <URL>'

* Note: Ensure you open the playlist window in VLC


Streaming URLs
--------------

* Stream flash AAC liveradio as 320k mp3 stream:
 
mplayer -cache 1024 "http://localhost/iplayer?ACTION=stream&PROGTYPES=liveradio&PID=<PID>&BITRATE=320&MODES=flashaac&OUTTYPE=nnn.mp3"

* Stream flash livetv as flv stream:

mplayer -cache 1024 "http://localhost/iplayer?ACTION=stream&PROGTYPES=livetv&PID=<PID>&MODES=flashnormal&OUTTYPE=nnn.flv"
	
* Stream flash AAC liveradio as an uncompressed wav stream:

mplayer -cache 1024 "http://localhost/iplayer?ACTION=stream&PROGTYPES=liveradio&PID=<PID>&MODES=flashaac&OUTTYPE=nnn.wav"

* Stream flash mp3 radio as http mp3 stream:

mplayer -cache 1024 "http://localhost/iplayer?ACTION=stream&PROGTYPES=radio&PID=<PID>&MODES=flashaudio&OUTTYPE=nnn.mp3"

* Stream flash mp3 radio as http flac stream:

mplayer -cache 1024 "http://localhost/iplayer?ACTION=stream&PROGTYPES=radio&PID=<PID>&MODES=flashaudio&OUTTYPE=nnn.flac"


Direct Streaming of Recorded Content
------------------------------------

* Stream Pre-recorded <TYPE> Programme with <PID> and <MODE>

http://localhost/?ACTION=direct&PROGTYPES=<TYPE>&PID=<PID>&MODES=<MODE>


Playlists of Recorded Content
-----------------------------

* Create an M3U playlist with pre-recorded <TYPE> programmes with <SEARCH> in the PID (open this in vlc)

http://localhost/?ACTION=playlistfiles&SEARCHFIELDS=pid&SEARCH=<SEARCH>&PROGTYPES=<TYPE>

* Create an M3U playlist with pre-recorded 'tv' programmes with 'news' in the 'name' field (open this in vlc)

http://localhost/?ACTION=playlistfiles&SEARCHFIELDS=name&SEARCH=news&PROGTYPES=tv


Automatic Playlists
-------------------

* All radio programmes - all modes (flashaac,flashaudio,wma):

http://127.0.0.1/iplayer?ACTION=playlist&PROGTYPES=radio

* All TV programmes - all modes (flashhigh,flashstd,flashnormal,flashlow):

http://127.0.0.1/iplayer?ACTION=playlist&PROGTYPES=tv

* All livetv channels:

http://127.0.0.1/iplayer?ACTION=playlist&PROGTYPES=livetv

* All liveradio channels:

http://127.0.0.1/iplayer?ACTION=playlist&PROGTYPES=liveradio

More specific examples:

* All live radio channels (e.g. flashaac as flv):

http://127.0.0.1/iplayer?ACTION=playlist&PROGTYPES=liveradio&MODES=flashaac&OUTTYPE=flv

* All live radio channels (e.g. flashaac as wav):

http://127.0.0.1/iplayer?ACTION=playlist&PROGTYPES=liveradio&MODES=flashaac&OUTTYPE=wav

* All radio programmes (e.g. flash):

http://127.0.0.1/iplayer?ACTION=playlist&PROGTYPES=radio&MODES=flash&OUTTYPE=flv

* All live radio channels with a single digit in their name

http://127.0.0.1/iplayer?ACTION=playlist&PROGTYPES=liveradio&SEARCH=\d

* All TV programmes with the word 'news' in their name:

http://127.0.0.1/iplayer?ACTION=playlist&PROGTYPES=tv&SEARCH=news


Automatic OPML Playlists (works with Squeezebox)
------------------------------------------------

See: http://wiki.slimdevices.com/index.php/OPMLSupport for details on syntax

In Squeezecenter, Add this URL to 'Favourites' and you will be able to navigate the programmes:

* BBC iPlayer Listen Again:

http://<SERVER IP>/iplayer?ACTION=opml&PROGTYPES=radio&LIST=channel

* BBC iPlayer Live Flash AAC:

http://<SERVER IP>/iplayer?ACTION=opml&PROGTYPES=liveradio&OUTTYPE=wav

* BBC iPlayer Live Flash AAC (Numbered Channels only)

http://<SERVER IP>/iplayer?ACTION=opml&PROGTYPES=liveradio&MODES=flash&SEARCH=%20\d&OUTTYPE=wav


Set up crontab for PVR to run
----------------------------

* Add a line in /etc/crontab to run the pvr: 

0 * * * * apache /usr/bin/get_iplayer --pvr 2>/dev/null


Caveats
--------

* Sometimes takes a while to load page while refreshing caches

* If a boolean param is in the cookies then it overrides the unchecked status on
  the form regardless

* When using the stream, playlist or play links directly, cookies are not sent 
  and the settings are not applied


Todo
-----

* Manual flush of indices (maybe normally set --expiry to 99999999 and warn that indices are out of date)
* in general, take presentation data out of the html and into css, take scripting out of the html and into the js
* Add a button to save the playlist in M3U or OPML (playlist of selected progs?)
