## get_iplayer: BBC iPlayer Indexing Tool and PVR

## Features

* Downloads MP4 streams from BBC iPlayer site with better quality than Flash player streams
* Downloads Flash AAC streams for radio programmes
* Allow multiple programmes to be downloaded using a single command
* Indexing of all available iPlayer programs
* Caching of Index (default 4h)
* Regex search on programme name 
* Regex search on programme description and episode title
* PVR capability (may be used from crontab)
* Full HTTP Proxy support
* Runs on Linux (Debian, Ubuntu, openSUSE and many others), OS X (10.5+) and Windows (XP/Vista/7/8)
* Requires perl 5.8.8+ with LWP, URI and XML::Simple modules

**NOTE: get_iplayer can only search programmes broadcast within the previous 7 days, even if they are available for 30 days on the iPlayer web site.**  See [FAQ #1](https://github.com/get-iplayer/get_iplayer/wiki/faq).

## Documentation

<https://github.com/get-iplayer/get_iplayer/wiki>
	
## Support

<https://github.com/get-iplayer/get_iplayer/wiki/help>

## Installation (Linux/Unix/OS X)

* Download latest release:

	<https://raw.github.com/get-iplayer/get_iplayer/latest/get_iplayer>

* After downloading the script make it executable:

	`chmod 755 ./get_iplayer`
  
	The script may optionally be installed to a location in PATH.

* You can set the default download directory by putting the following in your shell environment (e.g. ~/.bashrc):

	`export IPLAYER_OUTDIR="/path/to/my/output/dir"`

* The first time you run the script it will create a settings directory (`$HOME/.get_iplayer` [Linux/Unix/OSX] `%USERPROFILE%\.get_iplayer` [Windows]) and download plugins.  It will then access the BBC website and create an index of all TV programmes currently on iPlayer.

## Installation (Windows)

See documentation for Windows installation information.

## Usage 
  
	get_iplayer --help
	get_iplayer --basic-help
	get_iplayer --long-help

## Examples

* List all TV programmes (--type=tv set by default):

	`get_iplayer`

	Search output appears in this format:

		...
		208:  Doctor Who: Series 7 Part 2 - 1. The Bells of Saint John, BBC One, Drama,SciFi & Fantasy,TV, default
		209:  Doctor Who: Series 7 Part 2 - 2. The Rings Of Akhaten, BBC One, Audio Described,Drama,SciFi & Fantasy,TV, default,audiodescribed
		210:  Doctor Who: Series 7 Part 2 - 3. Cold War, BBC One, Audio Described,Drama,SciFi & Fantasy,TV, default,audiodescribed
		...

	Format = index: name - episode, channel, categories, versions 
  
* List all TV programmes with long descriptions:

	`get_iplayer --long`

* List all radio programmes:

	`get_iplayer --type=radio`

* List all TV programmes with "doctor who" in the title/episode:

	`get_iplayer "doctor who"`

* List all TV and radio programmes with "doctor who" in the title/episode:

	`get_iplayer --type tv,radio "doctor who"`

* List all BBC One TV programmes:

	`get_iplayer --channel= "BBC One"`

* List all Radio 4 Extra programmes:

	`get_iplayer --type=radio --channel "Radio 4 Extra"`
	
* List all Radio 4 programmes:

	`get_iplayer --type=radio --channel "Radio 4$"`

	*(The `$` regular expression metacharacter matches "Radio 4" only at the end of the channel name, thus avoiding matches against "Radio 4 Extra")*

* Record programme number 208 (index from search results) in SD:

	`get_iplayer --get 208`

* Record programme number 208 in HD (if available), with SD fallback:

	`get_iplayer --modes=best --get 208`

* Record programme number 208 and download subtitles in SubRip (SRT) format:

	`get_iplayer --get 208 --subtitles`

* Record all TV programmes with "doctor who' in the title/episode:

	`get_iplayer --get "doctor who"`

* Record a programme using its iPlayer URL:

	`get_iplayer http://www.bbc.co.uk/iplayer/episode/b01sc0wf/Doctors_Series_15_Perfect/`

* Record a programme using the PID (b01sc0wf) from its iPlayer URL:

	`get_iplayer --pid=b01sc0wf`
  
* Refresh the cached index of available TV programmes:

	`get_iplayer --refresh`

* Refresh the cached index of available TV and radio programmes:

	`get_iplayer --type=tv,radio --refresh`


Notes:

* Sometimes you may not be able to download a listed programme immediately after broadcast (usually available within 24hrs of airing). Some BBC  programmes may not be available from iPlayer.
