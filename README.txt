BBC iplayer Downloader (get_iplayer)
------------------------------------

Features:

* Downloads Mov (mp4) streams from BBC iplayer site in much better quality than Flash player streams
* Allow multiple programmes to be downloaded using a single command
* Indexing of all available (i.e. listed) iplayer programs
* Automatic XOR decoding/byte-swappng of files
* XOR decoding/byte-swappng of previously downloaded files with autodetect
* Available Programme Index listing
* Caching of Index (default 24hrs)
* Creation of a basic html index file (in '<download_dir>/iplayer.html')
* De-duplication of programme index
* Full HTTP Proxy support (tested on Squid)
* Regex search on programme name capability (makes it useful to run this from crontab)
* Regex search on long programme description and episode capability
* Tested on Linux (Fedora 6/7/8/9, Centos/RHEL 5, MacOSX, Ubuntu)
* Requires: perl 5.8, perl-LWP
* Latest Version: http://linuxcentre.net/get_iplayer/get_iplayer

Usage: See 'get_iplayer -h'


Notes:

* After downloading the script you can make it executable using:

	chmod 755 ./get_iplayer

* You can set the default dowload directory by putting the following in
  your shell environment (e.g. ~/.bashrc):

	export IPLAYER_OUTDIR="/path/to/my/output/dir"

* The first time you run the script it will access the BBC website and
  download an index of all programmes currently on iplayer.

* Sometimes you will not be able to download a programme listed due to BBC
  not encoding it yet for H.264 format (usually happens within 24hrs of airing).
  Also BBC don't seem to create an H.264 version for some programmes at all.


Examples:

* List all programmes (either from BBC site or cached):

	./get_iplayer

* Automatically XOR decode/byte-swap existing file(s)

	./get_iplayer -d <files>

* List all programmes with long descriptions:

	./get_iplayer -l

* Download programme number 123 (see index list):

	./get_iplayer 123

* Download all programmes with 'blue peter' in the title/episode:

 	./get_iplayer 'blue peter'

* Download all programmes with 'blue peter' in the title/episode, and
  programme index 123:

	./get_iplayer 'blue peter' 123

* Download all programmes with URL that conatns a programme ID (pid) b002a23a:

	./get_iplayer http://blah.blah.blah/b002a23a.shtml

* Download all programmes with 'comedy' in the title, episode or long description:

	./get_iplayer -l comedy



BBC iplayer XOR Decoder (iplayer_decode) - ****deprecated**** - PLEASE USE get_iplayer -d <files>
--------------------------------------------------------------------------------------------------
* Already integrated into get_iplayer (i.e. you don't need this if you already have get_iplayer)
* XOR decoding of previously downloaded files
* Fast, In-place conversion (4 seconds on 100MB file on Celeron/3GHz)
* Low memory requirements
* Reversible, lossless
* Tested on Linux (Fedora 6/7/8/9, Centos/RHEL 5, MacOSX)
* Requires: perl 5.8
