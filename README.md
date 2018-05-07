## get_iplayer: BBC iPlayer Indexing Tool and PVR

## Features

* Downloads TV and radio programmes from BBC iPlayer
* Allows multiple programmes to be downloaded using a single command
* Indexing of most available iPlayer catch-up programmes from previous 30 days (not BBC Three, Red Button or iPlayer Exclusive)
* Caching of programme index with automatic updating
* Regex search on programme name 
* Regex search on programme description and episode title
* Filter search results by channel
* Direct download via programme ID or URL
* PVR capability (may be used with cron or Task Scheduler)
* HTTP proxy support
* Perl 5.10.1+ required, plus LWP, LWP::Protocol::https, XML::LibXML and Mojolicious modules
* Requires ffmpeg for conversion to MP4 and AtomicParsley for metadata tagging
* Runs on Linux/BSD (Ubuntu, Fedora, OpenBSD and others), macOS (10.10+), Windows (7/8/10 - XP/Vista not supported)

**NOTE:** 

- **get_iplayer can only search for programmes that were scheduled for broadcast on BBC linear services within the previous 30 days, even if some are available for more than 30 days on the iPlayer site. It may be possible to download other content directly via PID or URL, but such use is not supported.**
- **get_iplayer does not support downloading news/sport videos, other embedded media, archive sites, special collections, educational material, programme clips or any content other than whole episodes of programmes broadcast on BBC linear services within the previous 30 days, plus episodes of BBC Three programmes posted within the same period. It may be possible to download other content directly via PID or URL, but such use is not supported.**

## Documentation

<https://github.com/get-iplayer/get_iplayer/wiki>
	
## Support

<https://squarepenguin.co.uk/forums/>

## Installation

<https://github.com/get-iplayer/get_iplayer/wiki/installation>

## Usage 
  
	get_iplayer --help
	get_iplayer --basic-help
	get_iplayer --long-help

## Examples

* List all TV programmes (`--type=tv` set by default):

	`get_iplayer ".*"`

	Search output appears in this format:

		...
		208:  Doctor Who: Series 7 Part 2 - 1. The Bells of Saint John, BBC One, b01rryzz
		209:  Doctor Who: Series 7 Part 2 - 2. The Rings Of Akhaten, BBC One, b01rx0lj
		210:  Doctor Who: Series 7 Part 2 - 3. Cold War, BBC One, b01s1cz7
		...

	Format = `<index>: <name> - <episode>, <channel>, <pid>`
  
* List all TV programmes with long descriptions:

	`get_iplayer --long ".*"`

* List all radio programmes:

	`get_iplayer --type=radio ".*"`

* List all TV programmes with "doctor who" in the name (matching is case-insensitive):

	`get_iplayer "doctor who"`

* List all TV and radio programmes with "doctor who" in the name:

	`get_iplayer --type tv,radio "doctor who"`

* List all BBC One programmes:

	`get_iplayer --channel="BBC One" ".*"`

* List Radio 4 and Radio 4 Extra programmes with "Book at Bedtime" in the title:

	`get_iplayer --type=radio --channel="Radio 4" "Book at Bedtime"`
	
* List only Radio 4 programmes with "Book at Bedtime" in the title:

	`get_iplayer --type=radio --channel="Radio 4$" "Book at Bedtime"`

	*(The `$` regular expression metacharacter matches "Radio 4" only at the end of the channel name, thus avoiding matches against "Radio 4 Extra")*

* Record TV programme number 208 (index from search results) in HD, with SD fallback if HD not available:

	`get_iplayer --get 208` [default is to download best available]
	
	OR	

	`get_iplayer --get 208 --tvmode=best`

* Record TV programme number 208 with lower resolution (704x396):

	`get_iplayer --get 208 --tvmode=good`

* Record TV programme number 208 and download subtitles in SubRip (SRT) format:

	`get_iplayer --get 208 --subtitles`

* Record multiple TV programmes (using index numbers from search results): 

	`get_iplayer --get 208 209 210`

* Record a TV programme using its iPlayer URL:

	`get_iplayer http://www.bbc.co.uk/iplayer/episode/b01sc0wf/Doctors_Series_15_Perfect/`

* Record a TV programme using the PID (b01sc0wf) from its iPlayer URL:

	`get_iplayer --pid=b01sc0wf`
	
* Record a radio programme using its iPlayer URL:

    `get_iplayer http://www.bbc.co.uk/programmes/b07gcv34`	
* Record a radio programme using the PID (b07gcv34) from its iPlayer URL in highest quality (320k), with fallback to lower quality if not available:

	`get_iplayer --pid=b07gcv34` [default is to download best available]
	
	OR	

	`get_iplayer --pid=b07gcv34 --radiomode=best`

* Record a radio programme using the PID (b07gcv34) from its iPlayer URL with lower bit rate (96k):

	`get_iplayer --pid=b07gcv34 --radiomode=good`

* Record multiple radio programmes (using PIDs from iPlayer URLs): 

	`get_iplayer --pid=b07gcv34,b07h60ld` [comma-separated list]

	OR	

	`get_iplayer --pid=b07gcv34 --pid=b07h60ld` [multiple arguments]

NOTE: Sometimes you may not be able to download a listed programme immediately after broadcast (usually available within 24hrs of airing). Some BBC programmes may not be available from iPlayer.
