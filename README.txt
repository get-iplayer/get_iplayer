BBC iPlayer Indexing Tool and PVR (get_iplayer)
-----------------------------------------------

Website:

http://www.infradead.org/get_iplayer/html/get_iplayer.html

Features:

* Downloads MP4 streams from BBC iPlayer site in much better quality than Flash player streams
* Downloads Flash MP3 and WMA streams for radio programmes
* Allow multiple programmes to be downloaded using a single command
* Indexing of all available iPlayer programs
* Caching of Index (default 4h)
* Regex search on programme name 
* Regex search on programme description and episode title
* PVR capability (may be used from crontab)
* Full HTTP Proxy support
* Runs on Linux (Debian, Ubuntu, openSUSE and many others), MacOSX (10.5+) and Windows (XP/Vista/7/8)
* Requires: perl 5.8 with LWP module


Installation (Linux/Unix/OSX):

* Download Latest Version:

http://www.infradead.org/get_iplayer/get_iplayer

* After downloading the script make it executable:

chmod 755 ./get_iplayer
  
The script may optionally be installed to a location in $PATH.

* You can set the default download directory by putting the following in your
  shell environment (e.g. ~/.bashrc):

export IPLAYER_OUTDIR="/path/to/my/output/dir"

* The first time you run the script it will create a settings directory
  (~/.get_iplayer) and download plugins.  It will then access the BBC website
  and create an index of all TV programmes currently on iPlayer.


Usage: 
  
get_iplayer -h


Examples:

* List all TV programmes (--type tv set by default):

get_iplayer

Search output appears in this format:

...
208:  Doctor Who: Series 7 Part 2 - 1. The Bells of Saint John, BBC One, Drama,SciFi & Fantasy,TV, default
209:  Doctor Who: Series 7 Part 2 - 2. The Rings Of Akhaten, BBC One, Audio Described,Drama,SciFi & Fantasy,TV, default,audiodescribed
210:  Doctor Who: Series 7 Part 2 - 3. Cold War, BBC One, Audio Described,Drama,SciFi & Fantasy,TV, default,audiodescribed
...

Format: index: name - episode, channel, categories, versions 
  
* List all TV programmes with long descriptions:

get_iplayer --long

* List all radio programmes:

get_iplayer --type radio

* List all TV programmes with "doctor who" in the title/episode:

get_iplayer "doctor who"

* List all TV and radio programmes with "doctor who" in the title/episode:

get_iplayer --type tv,radio "doctor who"

* List all TV programmes categorised as "comedy":

get_iplayer --category comedy

* List all BBC One TV programmes categorised as "sport":

get_iplayer --channel "BBC One" --category sport

* List all Radio 4 Extra programmes categorised as "drama":

get_iplayer --type radio --channel "Radio 4 Extra" --category drama

* Record programme number 208 (index from search results) in SD:

get_iplayer --get 208

* Record programme number 208 in HD (if available), with SD fallback:

get_iplayer --modes best --get 208

* Record all TV programmes with "doctor who' in the title/episode:

get_iplayer --get "doctor who"

* Record a programme using its iPlayer URL:

get_iplayer http://www.bbc.co.uk/iplayer/episode/b01rryzz/Doctor_Who_Series_7_Part_2_The_Bells_of_Saint_John/

* Record a programme using the PID (b01rryzz) from its iPlayer URL:

get_iplayer --pid b01rryzz
  
* Refresh the cached index of available TV programmes:

get_iplayer --refresh

* Refresh the cached index of available TV and radio programmes:

get_iplayer --type tv,radio --refresh


Notes:

* Sometimes you may not be able to download a listed programme immediately
  after broadcast (usually available within 24hrs of airing). Some BBC
  programmes may not be available from iPlayer.


