#!/usr/bin/env perl
#
# get_iplayer - Lists, Records and Streams BBC iPlayer TV and Radio programmes + other Programmes via 3rd-party plugins
#
#    Copyright (C) 2008-2010 Phil Lewis
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
# Web: https://github.com/get-iplayer/get_iplayer/wiki
# License: GPLv3 (see LICENSE.txt)
#
#
package main;
my $version = 2.94;
my $version_text;
$version_text = sprintf("v%.2f", $version) unless $version_text;
#
# Help:
#	./get_iplayer --help | --longhelp
#
# Changelog:
# 	https://github.com/get-iplayer/get_iplayer/commits/master
#
# Example Usage and Examples:
# 	https://github.com/get-iplayer/get_iplayer/wiki/documentation
#
# Todo:
# * Fix non-uk detection - iphone auth?
# * Index/Record live radio streams w/schedule feeds to assist timing
# * Remove all rtsp/mplayer/lame/tee dross when realaudio streams become obselete (not quite yet)
# ** all global vars into a class???
# ** Cut down 'use' clauses in each class
# * stdout streaming with mms
# * Add podcast links to web pvr manager
# * Add PVR search src to recording history
# * Fix unicode / wide chars in rdf
#
# Known Issues:
# * CAVEAT: The filenames and modes in the history are comma-separated if there was a multimode download. For now it just uses the first one.
#
use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::stat;
use File::Spec;
use Getopt::Long;
use HTML::Entities;
use HTTP::Cookies;
use HTTP::Headers;
use IO::Seekable;
use IO::Socket;
use LWP::ConnCache;
use LWP::UserAgent;
use POSIX qw(mkfifo);
use POSIX qw(:termios_h);
use strict;
#use warnings;
use Time::Local;
use Unicode::Normalize;
use URI;
use open qw(:utf8);
use Encode qw(:DEFAULT :fallback_all);
use PerlIO::encoding;
$PerlIO::encoding::fallback = XMLCREF;
use constant FB_EMPTY => sub { '' };

my %SIGORIG;
# Save default SIG actions
$SIGORIG{$_} = $SIG{$_} for keys %SIG;
$|=1;
# Save proxy env var
my $ENV_HTTP_PROXY = $ENV{HTTP_PROXY} || $ENV{http_proxy};

# Hash of where plugin files were found so that the correct ones can be updated
my %plugin_files;

# Hash of all prog types => Programme class
# Add an entry here if another Programme class is added
my %prog_types = (
	tv		=> 'Programme::tv',
	radio		=> 'Programme::radio',
	liveradio	=> 'Programme::liveradio',
	livetv		=> 'Programme::livetv',
);


# Programme instance data
# $prog{$pid} = Programme->new (
#	'index'		=> <index number>,
#	'name'		=> <programme short name>,
#	'episode'	=> <Episode info>,
#	'desc'		=> <Long Description>,
#	'available'	=> <Date/Time made available or remaining>,
#	'duration'	=> <duration in free text form>
#	'versions'	=> <comma separated list of versions, e.g default, signed, audiodescribed>
#	'thumbnail'	=> <programme thumbnail url>
#	'channel	=> <channel>
#	'categories'	=> <Comma separated list of categories>
# 	'type'		=> <prog_type>
#	'timeadded'	=> <timestamp when programme was added to cache>
#	'version'	=> <selected version e.g default, signed, audiodescribed, etc - only set before recording>
#	'filename'	=> <Path and Filename of saved file - set only while recording>
#	'dir'		=> <Filename Directory of saved file - set only while recording>
#	'fileprefix'	=> <Filename Prefix of saved file - set only while recording>
#	'ext'		=> <Filename Extension of saved file - set only while recording>
#);


# Define general 'option names' => ( <help mask>, <option help section>, <option cmdline format>, <usage text>, <option help> )
# <help mask>: 0 for normal help, 1 for advanced help, 2 for basic help
# If you want the option to be hidden then don't specify <option help section>, use ''
# Entries with keys starting with '_' are not parsed only displayed as help and in man pages.
my $opt_format = {
	# Recording
	attempts	=> [ 1, "attempts=n", 'Recording', '--attempts <number>', "Number of attempts to make or resume a failed connection.  --attempts is applied per-stream, per-mode.  TV modes typically have two streams available."],
	checkduration		=> [ 1, "checkduration|check-duration!", 'Recording', '--check-duration', "Print message showing recorded duration, expected duration and difference between them."],
	excludesupplier	=> [ 1, "excludesupplier|exclude-supplier=s", 'Recording', '--exclude-supplier <suppliers>', "Comma-delimited list of media stream suppliers to skip.  Possible values: akamai,limelight,level3,bidi"],
	force		=> [ 1, "force|force-download!", 'Recording', '--force', "Ignore programme history (unsets --hide option also). Forces a script update if used with -u"],
	get		=> [ 2, "get|record|g!", 'Recording', '--get, -g', "Start recording matching programmes. Search terms required unless --pid specified. Use  --search=.* to force download of all available programmes."],
	hash		=> [ 1, "hash!", 'Recording', '--hash', "Show recording progress as hashes"],
	mediaselector	=> [ 1, "mediaselector|media-selector=s", 'Recording', '--mediaselector <identifier>', "Identifier of mediaselector API to use when searching for media streams. One of: 4,5 Default: 5"],
	metadataonly	=> [ 1, "metadataonly|metadata-only!", 'Recording', '--metadata-only', "Create specified metadata info file without any recording or streaming (can also be used with thumbnail option)."],
	mmsnothread	=> [ 1, "mmsnothread!", 'Recording', '--mmsnothread', "Disable parallel threaded recording for mms"],
	modes		=> [ 0, "modes=s", 'Recording', '--modes <mode>,<mode>,...', "Recording modes.  See --tvmode and --radiomode for available modes and defaults. Shortcuts: default,good,better(=default),best. Use --modes=best to select highest quality available (incl. HD TV)."],
	multimode	=> [ 1, "multimode!", 'Recording', '--multimode', "Allow the recording of more than one mode for the same programme - WARNING: will record all specified/default modes!!"],
	noproxy	=> [ 1, "noproxy|no-proxy!", 'Recording', '--no-proxy', "Ignore --proxy setting in preferences"],
	overwrite	=> [ 1, "overwrite|over-write!", 'Recording', '--overwrite', "Overwrite recordings if they already exist"],
	partialproxy	=> [ 1, "partial-proxy!", 'Recording', '--partial-proxy', "Only uses web proxy where absolutely required (try this extra option if your proxy fails). If specified, value of http_proxy environment variable (if any) in parent process is retained and passed to child processes."],
	_url		=> [ 2, "", 'Recording', '--url "<url>"', "Record the embedded media player in the specified URL. Use with --type=<type>."],
	pid		=> [ 2, "pid|url=s@", 'Recording', '--pid <pid>', "Record an arbitrary pid that does not necessarily appear in the index."],
	pidrecursive	=> [ 1, "pidrecursive|pid-recursive!", 'Recording', '--pid-recursive', "When used with --pid record all the embedded pids if the pid is a series or brand pid."],
	proxy		=> [ 0, "proxy|p=s", 'Recording', '--proxy, -p <url>', "Web proxy URL e.g. 'http://USERNAME:PASSWORD\@SERVER:PORT' or 'http://SERVER:PORT'. Sets http_proxy environment variable for child processes (e.g., ffmpeg) unless --partial-proxy is specified."],
	raw		=> [ 0, "raw!", 'Recording', '--raw', "Don't transcode or change the recording/stream in any way (i.e. radio/realaudio, rtmp/flv)"],
	start		=> [ 1, "start=s", 'Recording', '--start <secs|hh:mm:ss>', "Recording/streaming start offset (rtmp and realaudio only)"],
	stop		=> [ 1, "stop=s", 'Recording', '--stop <secs|hh:mm:ss>', "Recording/streaming stop offset (can be used to limit live rtmp recording length) rtmp and realaudio only"],
	suboffset	=> [ 1, "suboffset=n", 'Recording', '--suboffset <offset>', "Offset the subtitle timestamps by the specified number of milliseconds"],
	subtitles	=> [ 2, "subtitles|subs!", 'Recording', '--subtitles', "Download subtitles into srt/SubRip format if available and supported"],
	subsfmt		=> [ 1, "subsfmt=s", 'Recording', '--subsfmt <format>', "Subtitles format.  One of: default, compact.  Default: 'default'"],
	subsonly	=> [ 1, "subtitlesonly|subsonly|subtitles-only|subs-only!", 'Recording', '--subtitles-only', "Only download the subtitles, not the programme"],
	subsraw		=> [ 1, "subsraw!", 'Recording', '--subsraw', "Additionally save the raw subtitles file"],
	subsrequired		=> [ 1, "subsrequired|subs-required|subtitles-required!", 'Recording', '--subtitles-required', "Do not download TV programme if subtitles are not available."],
	tagonly		=> [ 1, "tagonly|tag-only!", 'Recording', '--tag-only', "Only update the programme tag and not download the programme (can also be used with --history)"],
	test		=> [ 1, "test|t!", 'Recording', '--test, -t', "Test only - no recording (will show programme type)"],
	thumb		=> [ 1, "thumb|thumbnail!", 'Recording', '--thumb', "Download Thumbnail image if available"],
	thumbonly	=> [ 1, "thumbonly|thumbnailonly|thumbnail-only|thumb-only!", 'Recording', '--thumbnail-only', "Only Download Thumbnail image if available, not the programme"],

	# Search
	before		=> [ 1, "before=n", 'Search', '--before', "Limit search to programmes added to the cache before N hours ago"],
	category 	=> [ 0, "category=s", 'Search', '--category <string>', "Narrow search to matched categories (regex or comma separated values). Supported only for podcasts (not tv or radio programmes)."],
	channel		=> [ 0, "channel=s", 'Search', '--channel <string>', "Narrow search to matched channel(s) (regex or comma separated values)"],
	exclude		=> [ 0, "exclude=s", 'Search', '--exclude <string>', "Narrow search to exclude matched programme names (regex or comma separated values)"],
	excludecategory	=> [ 0, "xcat|exclude-category=s", 'Search', '--exclude-category <string>', "Narrow search to exclude matched categories (regex or comma separated values). Supported only for podcasts (not tv or radio programmes)."],
	excludechannel	=> [ 0, "xchan|exclude-channel=s", 'Search', '--exclude-channel <string>', "Narrow search to exclude matched channel(s) (regex or comma separated values)"],
	fields		=> [ 0, "fields=s", 'Search', '--fields <field1>,<field2>,..', "Searches only in the specified comma separated fields"],
	future		=> [ 1, "future!", 'Search', '--future', "Additionally search future programme schedule if it has been indexed (refresh cache with: --refresh --refresh-future)."],
	long		=> [ 0, "long|l!", 'Search', '--long, -l', "Additionally search in programme descriptions and episode names (same as --fields=name,episode,desc )"],
	search		=> [ 1, "search=s", 'Search', '--search <search term>', "GetOpt compliant way of specifying search args"],
	history		=> [ 1, "history!", 'Search', '--history', "Search/show recordings history"],
	since		=> [ 0, "since=n", 'Search', '--since', "Limit search to programmes added to the cache in the last N hours"],
	type		=> [ 2, "type=s", 'Search', '--type <type>', "Only search in these types of programmes: ".join(',', sort keys %prog_types).",all (tv is default)"],
	versionlist	=> [ 1, "versionlist|versions|version-list=s", 'Search', '--versions <versions>', "Version of programme to search or record.  List is processed from left to right and first version found is downloaded.  Example: '--versions signed,audiodescribed,default' will prefer signed and audiodescribed programmes if available.  Default: 'default,signed,audiodescribed'"],

	# Output
	aactomp3	=> [ 1, "aactomp3|mp3", 'Output', '--aactomp3', "Transcode AAC audio to MP3 with ffmpeg/avconv (CBR 128k unless --mp3vbr is specified).  Applied only to radio programmes. (Synonyms: --mp3)"],
	mp3vbr		=> [ 1, "mp3vbr=n", 'Output', '--mp3vbr', "Set LAME VBR mode to N (0 to 9) for AAC transcoding. 0 = target bitrate 245 Kbit/s, 9 = target bitrate 65 Kbit/s (requires --aactomp3). Applied only to radio programmes."],
	avi			=> [ 1, "avi", 'Output', '--avi', "Output video in AVI container instead of MP4. There is no metadata tagging support for AVI output."],
	command		=> [ 1, "c|command=s", 'Output', '--command, -c <command>', "Run user command after successful recording using args such as <pid>, <name> etc"],
	email		=> [ 1, "email=s", 'Output', '--email <address>', "Email HTML index of matching programmes to specified address"],
	emailsmtp	=> [ 1, "emailsmtpserver|email-smtp=s", 'Output', '--email-smtp <hostname>', "SMTP server IP address to use to send email (default: localhost)"],
	emailsender	=> [ 1, "emailsender|email-sender=s", 'Output', '--email-sender <address>', "Optional email sender address"],
	emailsecurity	=> [ 1, "emailsecurity|email-security=s", 'Output', '--email-security <TLS|SSL>', "Email security TLS, SSL (default: none)"],
	emailpassword	=> [ 1, "emailpassword|email-password=s", 'Output', '--email-password <password>', "Email password"],
	emailport       => [ 1, "emailport|email-port=s", 'Output', '--email-port <port number>', "Email port number (default: appropriate port for --email-security)"],
	emailuser	=> [ 1, "emailuser|email-user=s", 'Output', '--email-user <username>', "Email username"],
	fatfilename	=> [ 1, "fatfilenames|fatfilename!", 'Output', '--fatfilename', "Remove FAT forbidden characters in file and directory names.  Always applied on Windows. Overrides --punctuation."],
	fileprefix	=> [ 1, "file-prefix|fileprefix=s", 'Output', '--file-prefix <format>', "The filename prefix (excluding dir and extension) using formatting fields. e.g. '<name>-<episode>-<pid>'"],
	fxd		=> [ 1, "fxd=s", 'Output', '--fxd <file>', "Create Freevo FXD XML of matching programmes in specified file"],
	hfsfilename	=> [ 1, "hfsfilenames|hfsfilename!", 'Output', '--hfsfilename', "Remove colons in file and directory names. Prevents OS X Finder displaying colon as forward slash. Always applied on OS X. Overrides --punctuation."],
	html		=> [ 1, "html=s", 'Output', '--html <file>', "Create basic HTML index of matching programmes in specified file"],
	isodate		=> [ 1, "isodate!",  'Output', '--isodate', "Use ISO8601 dates (YYYY-MM-DD) in filenames and subdirectory paths"],
	keepall		=> [ 1, "keepall|keep-all!", 'Output', '--keep-all', "Keep whitespace, all possible punctuation and non-ASCII characters in file and directory names. Shortcut for: --whitespace --non-ascii --punctuation."],
	metadata	=> [ 1, "metadata=s", 'Output', '--metadata <type>', "Create metadata info file after recording. Valid types are: xbmc (or kodi), xbmc_movie (or kodi_movie), freevo, generic"],
	mkv			=> [ 1, "mkv", 'Output', '--mkv', "Output video in MKV container instead of MP4. There is no metadata tagging support for MKV output."],
	mythtv		=> [ 1, "mythtv=s", 'Output', '--mythtv <file>', "Create Mythtv streams XML of matching programmes in specified file"],
	nonascii	=> [ 1, "na|nonascii|non-ascii!", 'Output', '--non-ascii, --na', "Keep non-ASCII characters in file and directory names. Default behaviour is to remove all non-ASCII characters."],
	nowrite		=> [ 1, "no-write|nowrite|n!", 'Output', '--nowrite, -n', "No writing of file to disk (use with -x to prevent a copy being stored on disk)"],
	output		=> [ 2, "output|o=s", 'Output', '--output, -o <dir>', "Recording output directory"],
	player		=> [ 0, "player=s", 'Output', "--player \'<command> <options>\'", "Use specified command to directly play the stream"],
	punctuation	=> [ 1, "symbols|pu|punct|punctuation!", 'Output', '--punctuation, --pu', "Keep punctuation characters and symbols in file and directory names, with ellipsis always replaced by underscore. Default behaviour is to remove all punctuation and symbols except underscore, hyphen and full stop. Overridden by --fatfilename and --hfsfilename."],
	stdout		=> [ 1, "stdout|x", 'Output', '--stdout, -x', "Additionally stream to STDOUT (so you can pipe output to a player)"],
	stream		=> [ 0, "stream!", 'Output', '--stream', "Stream to STDOUT (so you can pipe output to a player)"],
	subdir		=> [ 1, "subdirs|subdir|s!", 'Output', '--subdir, -s', "Put Recorded files into Programme name subdirectory"],
	subdirformat	=> [ 1, "subdirformat|subdirsformat|subdir-format=s", 'Output', '--subdir-format <format>', "The format to be used for the subdirectory naming using formatting fields. e.g. '<nameshort>-<seriesnum>'"],
	symlink		=> [ 1, "symlink|freevo=s", 'Output', '--symlink <file>', "Create symlink to <file> once we have the header of the recording"],
	thumbext	=> [ 1, "thumbext|thumb-ext=s", 'Output', '--thumb-ext <ext>', "Thumbnail filename extension to use"],
	thumbsizecache	=> [ 1, "thumbsizecache=n", 'Output', '--thumbsizecache <index|width>', "Default thumbnail size/index to use when building cache. index: 1-11 or width: 86,150,178,512,528,640,832,1024,1280,1600,1920"],
	thumbsize	=> [ 1, "thumbsize|thumbsizemeta=n", 'Output', '--thumbsize <index|width>', "Default thumbnail size/index to use for the current recording and metadata. index: 1-11 or width: 86,150,178,512,528,640,832,1024,1280,1600,1920"],
	whitespace	=> [ 1, "whitespace|ws|w!", 'Output', '--whitespace, -w', "Keep whitespace in file and directory names. Default behaviour is to replace whitespace with underscores."],
	xmlchannels	=> [ 1, "xml-channels|fxd-channels!", 'Output', '--xml-channels', "Create freevo/Mythtv menu of channels -> programme names -> episodes"],
	xmlnames	=> [ 1, "xml-names|fxd-names!", 'Output', '--xml-names', "Create freevo/Mythtv menu of programme names -> episodes"],
	xmlalpha	=> [ 1, "xml-alpha|fxd-alpha!", 'Output', '--xml-alpha', "Create freevo/Mythtv menu sorted alphabetically by programme name"],

	# Config
	expiry		=> [ 1, "expiry|e=n", 'Config', '--expiry, -e <secs>', "Cache expiry in seconds (default 4hrs)"],
	refresh		=> [ 2, "refresh|flush|f!", 'Config', '--refresh, --flush, -f', "Refresh cache"],
	limitmatches	=> [ 1, "limitmatches|limit-matches=n", 'Config', '--limit-matches <number>', "Limits the number of matching results for any search (and for every PVR search)"],
	nopurge		=> [ 1, "no-purge|nopurge!", 'Config', '--nopurge', "Don't ask to delete programmes recorded over 30 days ago"],	
	packagemanager	=> [ 1, "packagemanager=s", 'Config', '--packagemanager <string>', "Tell the updater that we were installed using a package manager and don't update (use either: apt,rpm,deb,yum,disable)"],
	pluginsupdate	=> [ 1, "pluginsupdate|plugins-update!", 'Config', '--plugins-update', "Update get_iplayer plugins to the latest versions. get_iplayer main script also will be updated if a newer version is available.)"],
	prefsadd	=> [ 0, "addprefs|add-prefs|prefsadd|prefs-add!", 'Config', '--prefs-add', "Add/Change specified saved user or preset options"],
	prefsdel	=> [ 0, "del-prefs|delprefs|prefsdel|prefs-del!", 'Config', '--prefs-del', "Remove specified saved user or preset options"],
	prefsclear	=> [ 0, "clear-prefs|clearprefs|prefsclear|prefs-clear!", 'Config', '--prefs-clear', "Remove *ALL* saved user or preset options"],
	prefsshow	=> [ 0, "showprefs|show-prefs|prefsshow|prefs-show!", 'Config', '--prefs-show', "Show saved user or preset options"],
	preset		=> [ 1, "preset|z=s", 'Config', '--preset, -z <name>', "Use specified user options preset"],
	presetlist	=> [ 1, "listpresets|list-presets|presetlist|preset-list!", 'Config', '--preset-list', "Show all valid presets"],
	profiledir	=> [ 1, "profiledir|profile-dir=s", 'Config', '--profile-dir <dir>', "Override the user profile directory/folder"],
	refreshabortonerror	=> [ 1, "refreshabortonerror|refresh-abortonerror!", 'Config', '--refresh-abortonerror', "Abort cache refresh for programme type if data for any channel fails to download. Use --refresh-exclude to temporarily skip failing channels."],
	refreshinclude	=> [ 1, "refreshinclude|refresh-include=s", 'Config', '--refresh-include <string>', "Include matched channel(s) when refreshing cache (regex or comma separated values)"],
	refreshexclude	=> [ 1, "refreshexclude|refresh-exclude|ignorechannels=s", 'Config', '--refresh-exclude <string>', "Exclude matched channel(s) when refreshing cache (regex or comma separated values)"],
	refreshexcludegroups	=> [ 1, "refreshexcludegroups|refresh-exclude-groups=s", 'Config', '--refresh-exclude-groups', "Exclude channel groups when refreshing radio or tv cache (comma-separated values).  Valid values: 'national', 'regional', 'local'"],
	refreshexcludegroupsradio	=> [ 1, "refreshexcludegroupsradio|refresh-exclude-groups-radio=s", 'Config', '--refresh-exclude-groups-radio', "Exclude channel groups when refreshing radio cache (comma-separated values).  Valid values: 'national', 'regional', 'local'"],
	refreshexcludegroupstv	=> [ 1, "refreshexcludegroupstv|refresh-exclude-groups-tv=s", 'Config', '--refresh-exclude-groups-tv', "Exclude channel groups when refreshing tv cache (comma-separated values).  Valid values: 'national', 'regional', 'local'"],
	refreshfeeds	=> [ 1, "refreshfeeds|refresh-feeds=s", 'Config', '--refresh-feeds <string>', "Alternate source for programme data.  Valid values: 'ion','ion2','schedule'"],
	refreshfeedsradio	=> [ 1, "refreshfeedsradio|refresh-feeds-radio=s", 'Config', '--refresh-feeds-radio <string>', "Alternate source for radio programme data.  Valid values: 'ion','ion2','schedule'"],
	refreshfeedstv	=> [ 1, "refreshfeedstv|refresh-feeds-tv=s", 'Config', '--refresh-feeds-tv <string>', "Alternate source for TV programme data.  Valid values: 'ion','ion2','schedule'"],
	refreshfuture	=> [ 1, "refreshfuture|refresh-future!", 'Config', '--refresh-future', "Obtain future programme schedule when refreshing cache (between 7-14 days)"],
	refreshlimit	=> [ 1, "refreshlimit|refresh-limit=n", 'Config', '--refresh-limit <integer>', "Number of days of programmes to cache. Only applied with --refresh-feeds=schedule. Makes cache updates VERY slow. Default: 7 Min: 1 Max: 30"],
	refreshlimitradio	=> [ 1, "refreshlimitradio|refresh-limit-radio=n", 'Config', '--refresh-limit-radio <integer>', "Number of days of radio programmes to cache. Only applied with --refresh-feeds=schedule. Makes cache updates VERY slow. Default: 7 Min: 1 Max: 30"],
	refreshlimittv	=> [ 1, "refreshlimittv|refresh-limit-tv=n", 'Config', '--refresh-limit-tv <integer>', "Number of days of TV programmes to cache. Only applied with --refresh-feeds=schedule. Makes cache updates VERY slow. Default: 7 Min: 1 Max: 30"],
	skipdeleted	=> [ 1, "skipdeleted!", 'Config', "--skipdeleted", "Skip the download of metadata/thumbs/subs if the media file no longer exists. Use with --history & --metadataonly/subsonly/thumbonly."],
	update		=> [ 2, "update|u!", 'Config', '--update, -u', "Update get_iplayer if a newer version is available. If so, plugins also will be updated if newer versions available."],
	webrequest	=> [ 1, "webrequest=s", 'Config', '--webrequest <urlencoded string>', 'Specify all options as a urlencoded string of "name=val&name=val&..."' ],

	# Display
	conditions	=> [ 1, "conditions!", 'Display', '--conditions', 'Shows GPLv3 conditions'],
	debug		=> [ 1, "debug!", 'Display', '--debug', "Debug output"],
	dumpoptions	=> [ 1, "dumpoptions|dumpopts|dump-options|dump-opts!", 'Display', '--dump-options', 'Dumps all options with their internal option key names'],
	helpbasic	=> [ 2, "help-basic|usage|bh|hb|helpbasic|basichelp|basic-help!", 'Display', '--helpbasic, --usage', "Basic help text"],
	help		=> [ 2, "help|h!", 'Display', '--help, -h', "Intermediate help text"],
	helplong	=> [ 2, "help-long|advanced|long-help|longhelp|lh|hl|helplong!", 'Display', '--helplong', "Advanced help text"],
	hide		=> [ 1, "hide!", 'Display', '--hide', "Hide previously recorded programmes"],
	info		=> [ 2, "i|info!", 'Display', '--info, -i', "Show full programme metadata and availability of modes and subtitles (max 50 matches)"],
	list		=> [ 1, "list=s", 'Display', '--list <categories|channel>', "Show a list of available categories/channels for the selected type and exit"],
	listformat	=> [ 1, "listformat=s", 'Display', '--listformat <format>', "Display programme data based on a user-defined format string (such as <pid>, <name> etc)"],
	listplugins	=> [ 1, "listplugins!", 'Display', '--listplugins', "Display a list of currently available plugins or programme types"],
	_long		=> [ 0, "", 'Display', '--long, -l', "Show long programme info"],
	manpage		=> [ 1, "manpage=s", 'Display', '--manpage <file>', "Create man page based on current help text"],
	nocopyright	=> [ 1, "nocopyright!", 'Display', '--nocopyright', "Don't display copyright header"],
	page		=> [ 1, "page=n", 'Display', '--page <number>', "Page number to display for multipage output"],
	pagesize	=> [ 1, "pagesize=n", 'Display', '--pagesize <number>', "Number of matches displayed on a page for multipage output"],
	quiet		=> [ 1, "q|quiet!", 'Display', '--quiet, -q', "Reduce logging output"],
	series		=> [ 1, "series!", 'Display', '--series', "Display Programme series names only with number of episodes"],
	showcacheage	=> [ 1, "showcacheage|show-cache-age!", 'Display', '--show-cache-age', "Displays the age of the selected programme caches then exit"],
	showoptions	=> [ 1, "showoptions|showopts|show-options!", 'Display', '--show-options', 'Shows options which are set and where they are defined'],
	silent		=> [ 1, "silent!", 'Display', '--silent', "No logging output except PVR download report.  Cannot be saved in preferences or PVR searches."],
	sortmatches	=> [ 1, "sortmatches|sort=s", 'Display', '--sort <fieldname>', "Field to use to sort displayed matches"],
	sortreverse	=> [ 1, "sortreverse!", 'Display', '--sortreverse', "Reverse order of sorted matches"],
	streaminfo	=> [ 1, "streaminfo!", 'Display', '--streaminfo', "Returns all of the media stream urls of the programme(s)"],
	terse		=> [ 0, "terse!", 'Display', '--terse', "Only show terse programme info (does not affect searching)"],
	tree		=> [ 0, "tree!", 'Display', '--tree', "Display Programme listings in a tree view"],
	verbose		=> [ 1, "verbose|v!", 'Display', '--verbose, -v', "Verbose"],
	showver		=> [ 1, "V!", 'Display', '-V', "Show get_iplayer version and exit."],
	warranty	=> [ 1, "warranty!", 'Display', '--warranty', 'Displays warranty section of GPLv3'],

	# External Program
	atomicparsley	=> [ 1, "atomicparsley|atomic-parsley=s", 'External Program', '--atomicparsley <path>', "Location of AtomicParsley tagger binary"],
	id3v2		=> [ 1, "id3tag|id3v2=s", 'External Program', '--id3v2 <path>', "Location of id3v2 or id3tag binary"],
	mplayer		=> [ 1, "mplayer=s", 'External Program', '--mplayer <path>', "Location of mplayer binary"],

	# Tagging
	noartwork => [ 1, "noartwork|no-artwork!", 'Tagging', '--no-artwork', "Do not embed thumbnail image in output file.  All other metadata values will be written."],
	notag => [ 1, "notag|no-tag!", 'Tagging', '--no-tag', "Do not tag downloaded programmes"],
	tag_cnid => [ 1, "tagcnid|tag-cnid!", 'Tagging', '--tag-cnid', "Use AtomicParsley --cnID argument (if supported) to add catalog ID used for combining HD and SD versions in iTunes"],
	tag_fulltitle => [ 1, "tagfulltitle|tag-fulltitle!", 'Tagging', '--tag-fulltitle', "Prepend album/show title to track title"],
	tag_hdvideo => [ 1, "taghdvideo|tag-hdvideo!", 'Tagging', '--tag-hdvideo', "AtomicParsley accepts --hdvideo argument for HD video flag"],
	tag_id3sync => [ 1, "tagid3sync|tag-id3sync!", 'Tagging', '--tag-id3sync', "Save ID3 tags for MP3 files in synchronised form. Provides workaround for corruption of thumbnail images in Windows. Has no effect unless using MP3::Tag Perl module."],
	tag_isodate		=> [ 1, "tagisodate|tag-isodate!",  'Tagging', '--tag-isodate', "Use ISO8601 dates (YYYY-MM-DD) in album/show names and track titles"],
	tag_longdesc => [ 1, "taglongdesc|tag-longdesc!", 'Tagging', '--tag-longdesc', "AtomicParsley accepts --longdesc argument for long description text"],
	tag_longdescription => [ 1, "taglongdescription|tag-longdescription!", 'Tagging', '--tag-longdescription', "AtomicParsley accepts --longDescription argument for long description text"],
	tag_longepisode => [ 1, "taglongepisode|tag-longepisode!", 'Tagging', '--tag-longepisode', "Use <episode> (incl. episode number) instead of <episodeshort> for track title"],
	tag_longtitle => [ 1, "taglongtitle|tag-longtitle!", 'Tagging', '--tag-longtitle', "Prepend <series> (if available) to track title. Ignored with --tag-fulltitle."],
	tag_podcast => [ 1, "tagpodcast|tag-podcast!", 'Tagging', '--tag-podcast', "Tag downloaded radio and tv programmes as iTunes podcasts (requires MP3::Tag module for AAC/MP3 files)"],
	tag_podcast_radio => [ 1, "tagpodcastradio|tag-podcast-radio!", 'Tagging', '--tag-podcast-radio', "Tag only downloaded radio programmes as iTunes podcasts (requires MP3::Tag module for AAC/MP3 files)"],
	tag_podcast_tv => [ 1, "tagpodcasttv|tag-podcast-tv!", 'Tagging', '--tag-podcast-tv', "Tag only downloaded tv programmes as iTunes podcasts"],
	tag_shortname => [ 1, "tagshortname|tag-shortname!", 'Tagging', '--tag-shortname', "Use <nameshort> instead of <name> for album/show title"],
	tag_utf8 => [ 1, "tagutf8|tag-utf8!", 'Tagging', '--tag-utf8', "AtomicParsley accepts UTF-8 input"],

	# Misc
	encodingconsolein	=> [ 1, "encodingconsolein|encoding-console-in=s", 'Misc', '--encoding-console-in <name>', "Character encoding for standard input (currently unused). Encoding name must be known to Perl Encode module. Default (only if auto-detect fails): Linux/Unix/OSX = UTF-8, Windows = cp850"],
	encodingconsoleout	=> [ 1, "encodingconsoleout|encoding-console-out=s", 'Misc', '--encoding-console-out <name>', "Character encoding used to encode search results and other output. Encoding name must be known to Perl Encode module. Default (only if auto-detect fails): Linux/Unix/OSX = UTF-8, Windows = cp850"],
	encodinglocale	=> [ 1, "encodinglocale|encoding-locale=s", 'Misc', '--encoding-locale <name>', "Character encoding used to decode command-line arguments. Encoding name must be known to Perl Encode module. Default (only if auto-detect fails): Linux/Unix/OSX = UTF-8, Windows = cp1252"],
	encodinglocalefs	=> [ 1, "encodinglocalefs|encoding-locale-fs=s", 'Misc', '--encoding-locale-fs <name>', "Character encoding used to encode file and directory names. Encoding name must be known to Perl Encode module. Default (only if auto-detect fails): Linux/Unix/OSX = UTF-8, Windows = cp1252"],
	noscrapeversions	=> [ 1, "noscrapeversions|no-scrape-versions!", 'Misc', '--no-scrape-versions', "Do not scrape episode web pages as extra measure to find audiodescribed/signed versions (only applies with --playlist-metadata)."],
	playlistmetadata	=> [ 1, "playlistmetadata|playlist-metadata!", 'Misc', '--playlist-metadata (IGNORED)', "Force use of playlists (XML and JSON) for programme metadata instead of /programmes data endpoints."],
	trimhistory	=> [ 1, "trimhistory|trim-history=s", 'Misc', '--trim-history <# days to retain>', "Remove download history entries older than number of days specified in option value.  Cannot specify 0 - use 'all' to completely delete download history"],

};


# Pre-processed options instance
my $opt_pre = Options->new();
# Final options instance
my $opt = Options->new();
# Command line options instance
my $opt_cmdline = Options->new();
# Options file instance
my $opt_file = Options->new();
# Bind opt_format to Options class
Options->add_opt_format_object( $opt_format );

# Set Programme/Pvr/Streamer class global var refs to the Options instance
History->add_opt_object( $opt );
Programme->add_opt_object( $opt );
Pvr->add_opt_object( $opt );
Pvr->add_opt_file_object( $opt_file );
Pvr->add_opt_cmdline_object( $opt_cmdline );
Streamer->add_opt_object( $opt );
# Kludge: Create dummy Streamer, History and Programme instances (without a single instance, none of the bound options work)
History->new();
Programme->new();
Streamer->new();

# Print to STDERR/STDOUT if not quiet unless verbose or debug
sub logger(@) {
	my $msg = shift || '';
	# Make sure quiet can be overridden by verbose and debug options
	if ( $opt->{verbose} || $opt->{debug} || ! $opt->{silent} ) {
		# Only send messages to STDERR if pvr or stdout options are being used.
		if ( $opt->{stdout} || $opt->{pvr} || $opt->{stderr} || $opt->{stream} ) {
			print STDERR $msg;
		} else {
			print STDOUT $msg;
		}
	}
}


# fallback encodings
$opt->{encodinglocale} = $opt->{encodinglocalefs} = default_encodinglocale();
$opt->{encodingconsoleout} = $opt->{encodingconsolein} = default_encodingconsoleout();
# attempt to automatically determine encodings
eval {
	require Encode::Locale;
};
if (!$@) {
	# set encodings unless already set by PERL_UNICODE or perl -C
	$opt->{encodinglocale} = $Encode::Locale::ENCODING_LOCALE unless (${^UNICODE} & 32);
	$opt->{encodinglocalefs} = $Encode::Locale::ENCODING_LOCALE_FS unless (${^UNICODE} & 32);
	$opt->{encodingconsoleout} = $Encode::Locale::ENCODING_CONSOLE_OUT unless (${^UNICODE} & 6);
	$opt->{encodingconsolein} = $Encode::Locale::ENCODING_CONSOLE_IN unless (${^UNICODE} & 1);
}

# Pre-Parse the cmdline using the opt_format hash so that we know some of the options before we properly parse them later
# Parse options with passthru mode (i.e. ignore unknown options at this stage) 
# need to save and restore @ARGV to allow later processing)
my @argv_save = @ARGV;
$opt_pre->parse( 1 );
@ARGV = @argv_save;

# set encodings ASAP
my @encoding_opts = ('encodinglocale', 'encodinglocalefs', 'encodingconsoleout', 'encodingconsolein');
foreach ( @encoding_opts ) {
	$opt->{$_} = $opt_pre->{$_} if $opt_pre->{$_};
}
binmode(STDOUT, ":encoding($opt->{encodingconsoleout})");
binmode(STDERR, ":encoding($opt->{encodingconsoleout})");
binmode(STDIN, ":encoding($opt->{encodingconsolein})");

# decode @ARGV unless already decoded by PERL_UNICODE or perl -C
unless ( ${^UNICODE} & 32 ) {
	@ARGV = map { decode($opt->{encodinglocale}, $_) } @ARGV;
}
# compose UTF-8 args if necessary
if ( $opt->{encodinglocale} =~ /UTF-?8/i ) {
	@ARGV = map { NFKC($_) } @ARGV;
}

# Copy a few options over to opt so that logger works
$opt->{debug} = $opt->{verbose} = 1 if $opt_pre->{debug};
$opt->{verbose} = 1 if $opt_pre->{verbose};
$opt->{silent} = $opt->{quiet} = 1 if $opt_pre->{silent};
$opt->{quiet} = 1 if $opt_pre->{quiet};
$opt->{pvr} = 1 if $opt_pre->{pvr};
$opt->{stdout} = 1 if $opt_pre->{stdout} || $opt_pre->{stream};

# show version and exit
if ( $opt_pre->{showver} ) {
	print STDERR Options->copyright_notice;
	exit 0;
}

# This is where all profile data/caches/cookies etc goes
my $profile_dir;
# This is where system-wide default options are specified
my $optfile_system;

# Options directories specified by env vars
if ( defined $ENV{GETIPLAYERUSERPREFS} ) {
	$profile_dir = $opt_pre->{profiledir} || $ENV{GETIPLAYERUSERPREFS};
# Otherwise look for windows style file locations
} elsif ( defined $ENV{USERPROFILE} && $^O eq "MSWin32" ) {
	$profile_dir = $opt_pre->{profiledir} || $ENV{USERPROFILE}.'/.get_iplayer';
# Options on unix-like systems
} elsif ( defined $ENV{HOME} ) {
	$profile_dir = $opt_pre->{profiledir} || $ENV{HOME}.'/.get_iplayer';
}

# System options file specified by env var
if ( defined $ENV{GETIPLAYERSYSPREFS} ) {
	$optfile_system = $ENV{GETIPLAYERSYSPREFS};
# Otherwise look for windows style file locations
} elsif ( defined $ENV{ALLUSERSPROFILE} && $^O eq "MSWin32" ) {
	$optfile_system = $ENV{ALLUSERSPROFILE}.'/get_iplayer/options';
# System options on unix-like systems
} else {
	$optfile_system = '/etc/get_iplayer/options';
	# Show warning if this deprecated location exists and is not a symlink
	if ( -f '/var/lib/get_iplayer/options' && ! -l '/var/lib/get_iplayer/options' ) {
		logger "WARNING: System-wide options file /var/lib/get_iplayer/options will be deprecated in future, please use /etc/get_iplayer/options instead\n";
	}
}
# Make profile dir if it doesnt exist
mkpath $profile_dir if ! -d $profile_dir;


# get list of additional user plugins and load plugin
my $plugin_dir_system;
if ( defined $ENV{ALLUSERSPROFILE} && $^O eq "MSWin32" ) {
    $plugin_dir_system = $ENV{ALLUSERSPROFILE}.'/get_iplayer/plugins';
} else {
    $plugin_dir_system = '/usr/share/get_iplayer/plugins';
}
my $plugin_dir_user = "$profile_dir/plugins";
for my $plugin_dir ( ( $plugin_dir_user, $plugin_dir_system ) ) {
	if ( opendir( DIR, $plugin_dir ) ) {
		#logger "INFO: Checking for plugins in $plugin_dir\n";
		my @plugin_file_list = grep /^.+\.plugin$/, readdir DIR;
		closedir DIR;
		for ( @plugin_file_list ) {
			#logger "INFO: Got $_\n";
			chomp();
			$_ = "$plugin_dir/$_";
			m{^.*\/(.+?).plugin$};
			# keep in a hash for update
			$plugin_files{$_} = $1.'.plugin';
			# Skip if we have this plugin already
			next if (! $1) || $prog_types{$1};
			# Register the plugin
			$prog_types{$1} = "Programme::$1";
			#logger "INFO: Loading $_\n";
			require $_;
			# Kludge: Create dummy instance (without a single instance, none of the bound options work)
			$prog_types{$1}->new();
		}
	}
}


# Set the personal options according to the specified preset
my $optfile_default = "${profile_dir}/options";
my $optfile_preset;
if ( $opt_pre->{preset} ) {
	# create dir if it does not exist
	mkpath "${profile_dir}/presets/" if ! -d "${profile_dir}/presets/";
        # Sanitize preset file name
	my $presetname = StringUtils::sanitize_path( $opt_pre->{preset}, 0, 1 );
	$optfile_preset = "${profile_dir}/presets/${presetname}";
	logger "INFO: Using user options preset '${presetname}'\n";
}
logger "DEBUG: User Preset Options File: $optfile_preset\n" if defined $optfile_preset && $opt->{debug};


# Parse cmdline opts definitions from each Programme class/subclass
Options->get_class_options( $_ ) for qw( Streamer Programme Pvr );
Options->get_class_options( progclass($_) ) for progclass();
Options->get_class_options( "Streamer::$_" ) for qw( rtmp hls shoutcast rtsp iphone mms 3gp http ddl );


# Parse the cmdline using the opt_format hash
Options->usage( 0 ) if not $opt_cmdline->parse();

# process --start and --stop if necessary
foreach ('start', 'stop') {
	if ($opt_cmdline->{$_} && $opt_cmdline->{$_} =~ /(\d\d):(\d\d)(:(\d\d))?/) {
		$opt_cmdline->{$_} = $1 * 3600 +  $2 * 60 + $4;
	}
}

# Parse options if we're not saving/adding/deleting options (system-wide options are overridden by personal options)
if ( ! ( $opt_pre->{prefsadd} || $opt_pre->{prefsdel} || $opt_pre->{prefsclear} ) ) {
	# Load options from files into $opt_file
	# system, Default, './.get_iplayer/options' and Preset options in that order should they exist
	$opt_file->load( $opt, '/var/lib/get_iplayer/options', $optfile_system, $optfile_default, './.get_iplayer/options', $optfile_preset );
	# Copy these loaded options into $opt
	$opt->copy_set_options_from( $opt_file );
}


# Copy to $opt from opt_cmdline those options which are actually set 
$opt->copy_set_options_from( $opt_cmdline );


# Update or show user opts file (or preset if defined) if required
if ( $opt_cmdline->{presetlist} ) {
	$opt->preset_list( "${profile_dir}/presets/" );
	exit 0;
} elsif ( $opt_cmdline->{prefsadd} ) {
	$opt->add( $opt_cmdline, $optfile_preset || $optfile_default, @ARGV );
	exit 0;
} elsif ( $opt_cmdline->{prefsdel} ) {
	$opt->del( $opt_cmdline, $optfile_preset || $optfile_default, @ARGV );
	exit 0;
} elsif ( $opt_cmdline->{prefsshow} ) {
	$opt->show( $optfile_preset || $optfile_default );
	exit 0;
} elsif ( $opt_cmdline->{prefsclear} ) {
	$opt->clear( $optfile_preset || $optfile_default );
	exit 0;
}


# List all valid programme type plugins (and built-ins)
if ( $opt->{listplugins} ) {
	main::logger join(',', keys %prog_types)."\n";
	exit 0;
}

# Show copyright notice
logger Options->copyright_notice if not $opt->{nocopyright};

# show encodings in use
if ( $opt->{verbose} ) {
	logger "INFO: $_ = $opt->{$_}\n" for @encoding_opts;
	logger "INFO: \${^UNICODE} = ${^UNICODE}\n" if $opt->{verbose};
}

# Display prefs dirs if required
main::logger "INFO: User prefs dir: $profile_dir\n" if $opt->{verbose};
main::logger "INFO: System options dir: $optfile_system\n" if $opt->{verbose};


# Display Usage
Options->usage( 2 ) if $opt_cmdline->{helpbasic};
Options->usage( 0 ) if $opt_cmdline->{help};
Options->usage( 1 ) if $opt_cmdline->{helplong};

# Dump all option keys and descriptions if required
Options->usage( 1, 0, 1 ) if $opt_pre->{dumpoptions};

# Generate man page
Options->usage( 1, $opt_cmdline->{manpage} ) if $opt_cmdline->{manpage};

# Display GPLv3 stuff
if ( $opt_cmdline->{warranty} || $opt_cmdline->{conditions}) {
	# Get license from GNU
	logger request_url_retry( create_ua( 'get_iplayer', 1 ), 'http://www.gnu.org/licenses/gpl-3.0.txt'."\n", 1);
	exit 1;
}

# Force plugins update if no plugins found
if ( ! keys %plugin_files && ! $opt->{packagemanager}) {
	logger "WARNING: Running the updater again to obtain plugins.\n";
	$opt->{pluginsupdate} = 1;
}
# Update this script if required
update_script() if $opt->{update} || $opt->{pluginsupdate};



########## Global vars ###########

#my @cache_format = qw/index type name pid available episode versions duration desc channel categories thumbnail timeadded guidance web/;
my @history_format = qw/pid name episode type timeadded mode filename versions duration desc channel categories thumbnail guidance web episodenum seriesnum/;
# Ranges of numbers used in the indicies for each programme type
my $max_index = 0;
for ( progclass() ) {
	# Set maximum index number
	$max_index = progclass($_)->index_max if progclass($_)->index_max > $max_index;
}

# Setup signal handlers
$SIG{INT} = $SIG{PIPE} = \&cleanup;

# Other Non option-dependant vars
my $historyfile		= "${profile_dir}/download_history";
my $cookiejar		= "${profile_dir}/cookies.";
my $namedpipe 		= "${profile_dir}/namedpipe.$$";
my $lwp_request_timeout	= 20;
my $info_limit		= 40;
my $proxy_save;

# Option dependant var definitions
my $bin;
my $binopts;
my @search_args = @ARGV;
my $memcache = {};

########### Main processing ###########

# Use --webrequest to specify options in urlencoded format
if ( $opt->{webrequest} ) {
	# parse GET args
	my @webopts = split /[\&\?]/, $opt->{webrequest};
	for (@webopts) {
		# URL decode it (value should then be decoded as UTF-8)
		$_ = decode($opt->{encodinglocale}, main::url_decode( $_ ), FB_EMPTY);
		my ( $optname, $value );
		# opt val pair
		if ( m{^\s*([\w\-]+?)[\s=](.+)$} ) {
			( $optname, $value ) = ( $1, $2 );
		# flag only
		} elsif ( m{^\s*([\w\-]+)$} ) {
			( $optname, $value ) = ( $1, 1 );
		}
		# if the option is valid then add it
		if ( defined $opt_format->{$optname} ) {
			$opt_cmdline->{$optname} = $value;
			logger "INFO: webrequest OPT: $optname=$value\n" if $opt->{verbose};
		# Ignore invalid opts
		} else {
			logger "ERROR: Invalid webrequest OPT: $optname=$value\n" if $opt->{verbose};
		}
	}
	# Copy to $opt from opt_cmdline those options which are actually set - allows pvr-add to work which only looks at cmdline args
	$opt->copy_set_options_from( $opt_cmdline );
	# Remove this option now we've processed it
	delete $opt->{webrequest};
	delete $opt_cmdline->{webrequest};
}

# Add --search option to @search_args if specified
if ( defined $opt->{search} ) {
	push @search_args, $opt->{search};
	# Remove this option now we've processed it
	delete $opt->{search};
	delete $opt_cmdline->{search};
}
# check if no search term(s) specified
my $no_search_args = $#search_args < 0;
# Assume search term is '.*' if nothing is specified - i.e. lists all programmes
push @search_args, '.*' if ! $search_args[0] && ! $opt->{pid};

# Auto-detect http:// url or <type>:http:// in a search term and set it as a --pid option (disable if --fields is used).
if ( $search_args[0] =~ m{^(\w+:)?http://} && ( ! $opt->{pid} ) && ( ! $opt->{fields} ) ) {
	$opt->{pid} = $search_args[0];
}

if ( ! $opt->{pid} ) {
	# default live streams are BBC One London and BBC Two England
	if ( $opt->{type} =~ "livetv" ) {
		@search_args = map { /(One|Two)$/i ? "$_\$" : $_ } @search_args;
		if ( $opt->{channel} ) {
			$opt->{channel} =~ s/(One|Two)$/$1\$/i;
			$opt_cmdline->{channel} = $opt->{channel} if $opt_cmdline->{channel};
		}
	}
}

if ( $opt->{pid} ) {
	my @search_pids;
	if ( ref($opt->{pid}) eq 'ARRAY' ) {
		push @search_pids, @{$opt->{pid}};
	} else {
		push @search_pids, $opt->{pid};
	}
	$opt->{pid} = join( ',', @search_pids );
	$opt_cmdline->{pid} = $opt->{pid};
}

# PVR Lockfile location (keep global so that cleanup sub can unlink it)
my $lockfile;
$lockfile = $profile_dir.'/pvr_lock' if $opt->{pvr} || $opt->{pvrsingle} || $opt->{pvrscheduler};

# Delete cookies each session
unlink($cookiejar.'desktop');
unlink($cookiejar.'safari');
unlink($cookiejar.'coremedia');

# Create new PVR instance
# $pvr->{searchname}->{<option>} = <value>;
my $pvr = Pvr->new();
# Set some class-wide values
$pvr->setvar('pvr_dir', "${profile_dir}/pvr/" );

my $retcode = 0;
# Trim history
if ( defined($opt->{trimhistory}) ) {
	my $hist = History->new();
	$hist->trim();
# PVR functions
} elsif ( $opt->{pvradd} ) {
	if ( ! $opt->{pid} && $no_search_args ) {
		main::logger "ERROR: Search term(s) or PID required for recording\n";
		exit 1;
	}
	$pvr->add( $opt->{pvradd}, @search_args );

} elsif ( $opt->{pvrdel} ) {
	$pvr->del( $opt->{pvrdel} );

} elsif ( $opt->{pvrdisable} ) {
	$pvr->disable( $opt->{pvrdisable} );

} elsif ( $opt->{pvrenable} ) {
	$pvr->enable( $opt->{pvrenable} );

} elsif ( $opt->{pvrlist} ) {
	$pvr->display_list();

} elsif ( $opt->{pvrqueue} ) {
	if ( ! $opt->{pid} && $no_search_args ) {
		main::logger "ERROR: Search term(s) or PID required for recording\n";
		exit 1;
	}
	$pvr->queue( @search_args );

} elsif ( $opt->{pvrscheduler} ) {
	if ( $opt->{pvrscheduler} < 1800 ) {
		main::logger "ERROR: PVR schedule duration must be at least 1800 seconds\n";
		unlink $lockfile;
		exit 5;
	};
	# PVR Lockfile detection (with 12 hrs stale lockfile check)
	lockfile( 43200 ) if ! $opt->{test};
	$pvr->run_scheduler();

} elsif ( $opt->{pvr} ) {
	# PVR Lockfile detection (with 12 hrs stale lockfile check)
	lockfile( 43200 ) if ! $opt->{test};
	$retcode = $pvr->run( @search_args );
	unlink $lockfile;

} elsif ( $opt->{pvrsingle} ) {
	# PVR Lockfile detection (with 12 hrs stale lockfile check)
	lockfile( 43200 ) if ! $opt->{test};
	$retcode = $pvr->run( '^'.$opt->{pvrsingle}.'$' );
	unlink $lockfile;

# Record prog specified by --pid option
} elsif ( $opt->{pid} ) {
	my $hist = History->new();
	my @pids = split( /,/, $opt->{pid} );	
	for ( @pids ) {
		$opt->{pid} = $_;
		$retcode += find_pid_matches( $hist );
	}

# Show history
} elsif ( $opt->{history} ) {
	my $hist = History->new();
	$hist->list_progs( @search_args );

# Else just process command line args
} else {
	if ( $opt->{get} && $no_search_args ) {
		main::logger "ERROR: Search term(s) required for recording\n";
		exit 1;
	}
	my $hist = History->new();
	$retcode = download_matches( $hist, find_matches( $hist, @search_args ) );
	purge_downloaded_files( $hist, 30 );
}
exit $retcode;



sub init_search {
	if ( $opt->{keepall} ) {
		$opt->{whitespace} = 1;
		$opt->{nonascii} = 1;
		$opt->{punctuation} = 1;
	}
	
	# Set --subtitles if --subsonly is used
	if ( $opt->{subsonly} ) {
		$opt->{subtitles} = 1;
	}

	# Set --thumbnail if --thumbonly is used
	if ( $opt->{thumbonly} ) {
		$opt->{thumb} = 1;
	}

	# Ensure lowercase types
	$opt->{type} = lc( $opt->{type} );
	# Expand 'all' type to comma separated list all prog types
	$opt->{type} = join( ',', progclass() ) if $opt->{type} =~ /(all|any)/i;

	# --stream is the same as --stdout --nowrite
	if ( $opt->{stream} ) {
		$opt->{nowrite} = 1;
		$opt->{stdout} = 1;
		delete $opt->{stream};
	}

	# Force nowrite if metadata/subs/thumb-only
	if ( $opt->{metadataonly} || $opt->{subsonly} || $opt->{thumbonly} || $opt->{tagonly} ) {
		$opt->{nowrite} = 1;
	}

	# List all options and where they are set from then exit
	if ( $opt_cmdline->{showoptions} ) {
		# Show all options andf where set from
		$opt_file->display('Options from Files');
		$opt_cmdline->display('Options from Command Line');
		$opt->display('Options Used');
		logger "Search Args: ".join(' ', @search_args)."\n\n";
	}

	# Web proxy
	if ( $opt->{noproxy} ) {
		delete $opt->{proxy};
		$ENV{http_proxy} = $ENV_HTTP_PROXY;
	} else {
		(my $proxy = $opt->{proxy}) =~ s/^prepend://i;
		$opt->{proxy} = $ENV_HTTP_PROXY if not $opt->{proxy};
		# set proxy env var for child processes unless --partial-proxy
		$ENV{http_proxy} = $proxy if $proxy && ! $opt->{partialproxy};
		logger "INFO: Using Proxy $opt->{proxy}\n" if $opt->{proxy};
		logger "INFO: \$ENV{http_proxy} = $ENV{http_proxy}\n" if $ENV{http_proxy} && $opt->{verbose};
	}


	# Set --get && --nowrite if --metadataonly is used
	if ( $opt->{metadataonly} ) {
		if ( ! $opt->{metadata} ) {
			main::logger "ERROR: Please specify metadata type using --metadata=<type>\n";
			exit 2;
		}
	}

	# Sanity check some conflicting options
	if ( $opt->{nowrite} && ! $opt->{stdout} ) {
		if ( ! ( $opt->{metadataonly} || $opt->{subsonly} || $opt->{thumbonly} || $opt->{tagonly} ) ) {
			logger "ERROR: Cannot record to nowhere\n";
			exit 1;
		}
	}

	# hash of prog types specified
	my $type = {};
	$type->{$_} = 1 for split /,/, $opt->{type};

	# Default to type=tv if no type option is set
	$type->{tv}		= 1 if keys %{ $type } == 0;

	# Sanity check valid --type specified
	for (keys %{ $type }) {
		if ( not progclass($_) ) {
			logger "ERROR: Invalid type '$_' specified. Valid types are: ".( join ',', progclass() )."\n";
			exit 3;
		}
	}

	# exit if only showing options
	exit 0 if ( $opt_cmdline->{showoptions} );

	# Display the ages of the selected caches in seconds
	if ( $opt->{showcacheage} ) {
		for ( keys %{ $type } ) {
			my $cachefile = "${profile_dir}/${_}.cache";
			main::logger "INFO: $_ cache age: ".( time() - stat($cachefile)->mtime )." secs\n" if -f $cachefile;
		}
		exit 0;
	}

	# Show options
	$opt->display('Current options') if $opt->{verbose};
	# $prog->{pid}->object hash
	my $prog = {};
	# obtain prog object given index. e.g. $index_prog->{$index_no}->{element};
	my $index_prog = {};
	logger "INFO: Search args: '".(join "','", @search_args)."'\n" if $opt->{verbose};

	# External Binaries
	$bin->{mplayer}		= $opt->{mplayer} || 'mplayer';
	delete $binopts->{mplayer};
	push @{ $binopts->{mplayer} }, '-nolirc';
	if ( $opt->{debug} ) {
		push @{ $binopts->{mplayer} }, '-v';
	} elsif ( $opt->{verbose} ) {
		push @{ $binopts->{mplayer} }, '-v';
	} elsif ( $opt->{quiet} || $opt->{silent}  ) {
		push @{ $binopts->{mplayer} }, '-really-quiet';
	}

	$bin->{ffmpeg}		= $opt->{ffmpeg} || 'avconv';
	if (! main::exists_in_path('ffmpeg') ) {
		$bin->{ffmpeg} = 'ffmpeg';
	}
	delete $binopts->{ffmpeg};
	push @{ $binopts->{ffmpeg} },  ();
	if ( ! $opt->{ffmpegobsolete} ) {
		if ( $opt->{debug} ) {
			push @{ $binopts->{ffmpeg} }, ('-loglevel', 'debug');
		} elsif ( $opt->{verbose} ) {
			push @{ $binopts->{ffmpeg} }, ('-loglevel', 'verbose');
		} elsif ( $opt->{quiet} || $opt->{silent}  ) {
			push @{ $binopts->{ffmpeg} }, ('-loglevel', 'quiet');
		}
	}


	$bin->{lame}		= $opt->{lame} || 'lame';
	delete $binopts->{lame};
	$binopts->{lame}	= '-f';
	$binopts->{lame}	.= ' --quiet ' if $opt->{quiet} || $opt->{silent} ;

	$bin->{vlc}		= $opt->{vlc} || 'cvlc';
	delete $binopts->{vlc};
	push @{ $binopts->{vlc} }, '-vv' if $opt->{debug};

	$bin->{id3v2}		= $opt->{id3v2} || 'id3v2';
	$bin->{atomicparsley}	= $opt->{atomicparsley} || 'AtomicParsley';

	$bin->{tee}		= 'tee';

	$bin->{rtmpdump}	= $opt->{rtmpdump} || 'rtmpdump';
	if (! main::exists_in_path('rtmpdump') ) {
		$bin->{rtmpdump} = 'rtmpdump';
	}

	delete $binopts->{rtmpdump};
	push @{ $binopts->{rtmpdump} }, ( '--timeout', 10 );
	if ( $opt->{debug} ) {
		push @{ $binopts->{rtmpdump}	}, '--debug';
	} elsif ( $opt->{verbose} ) {
		push @{ $binopts->{rtmpdump}	}, '--verbose';
	} elsif ( $opt->{quiet} || $opt->{silent} ) {
		push @{ $binopts->{rtmpdump}	}, '--quiet';
	}

	# quote binaries which allows for spaces in the path (only required if used via a shell)
	for ( $bin->{lame}, $bin->{tee} ) {
		s!^(.+)$!"$1"!g;
	}
	
	# Redirect STDOUT to player command if one is specified
	if ( $opt->{player} && $opt->{nowrite} && $opt->{stdout} ) {
		open (STDOUT, "| $opt->{player}") || die "ERROR: Cannot open player command\n";
		STDOUT->autoflush(1);
		binmode STDOUT;
	}

	return ( $type, $prog, $index_prog );
}



sub find_pid_matches {
	my $hist = shift;
	my @search_args = @_;
	my ( $type, $prog, $index_prog ) = init_search( @search_args );

	# Get prog by arbitrary '<type>:<pid>' or just '<pid>' (using the specified types)(then exit)
	my @try_types;
	my $pid;

	# If $opt->{pid} is in the form of '<type>:<pid>' and <type> is a valid type
	if ( $opt->{pid} =~ m{^(.+?)\:(.+?)$} && progclass(lc($1)) ) {
		my $prog_type;
		( $prog_type, $pid )= ( lc($1), $2 );
		# Only try to recording using this prog type
		@try_types = ($prog_type);
			
	# $opt->{pid} is in the form of '<pid>'
	} else {
		$pid = $opt->{pid};
		@try_types = (keys %{ $type });
	}
	logger "INFO: Will try prog types: ".(join ',', @try_types)."\n" if $opt->{verbose};
	return 0 if ( ! ( $opt->{multimode} || $opt->{metadataonly} || $opt->{info} || $opt->{thumbonly} || $opt->{tagonly} || $opt->{subsonly} ) ) && $hist->check( $pid );	

	# Maybe we don't want to populate caches - this slows down --pid recordings ...
	# Populate cache with all specified prog types (strange perl bug?? - @try_types is empty after these calls if done in a $_ 'for' loop!!)
	# only get links and possibly refresh caches if > 1 type is specified
	# else only load cached data from file if it exists.
	my $load_from_file_only;
	$load_from_file_only = 1 if $#try_types == 0;
	for my $t ( @try_types ) {
		get_links( $prog, $index_prog, $t, $load_from_file_only );
	}

	# Simply record pid if we find it in the caches
	if ( $prog->{$pid}->{pid} ) {
		return download_pid_in_cache( $hist, $prog->{$pid} );
	}

	my $totalretcode = 0;
	my $quit_attempt = 0;
	my %done_pids;
	for my $prog_type ( @try_types ) {
		last if $quit_attempt;
	
		# See if the specified pid has other episode pids embedded - results in another list of pids.
		my $dummy = progclass($prog_type)->new( 'pid' => $pid, 'type' => $prog_type );
		my @pids = $dummy->get_pids_recursive();

		# Try to get pid using each speficied prog type
		# process all pids in @pids
		for my $pid ( @pids ) {
			# skip this pid if we have already completed it
			next if $done_pids{$pid};
			main::logger "INFO: Trying pid: $pid using type: $prog_type\n";
			my $retcode;
			if ( not $prog->{$pid}->{pid} ) {
				$retcode = download_pid_not_in_cache( $hist, $pid, $prog_type );
				# don't try again for other types because it was recorded successfully
				$done_pids{$pid} = 1 if ! $retcode;
			} else {
				$retcode = download_pid_in_cache( $hist, $prog->{$pid} );
				# if it's in the cache then there is no need to try this pid for other types
				$done_pids{$pid} = 1;
			}
			$totalretcode += $retcode;
		}
	}

	# return zero on success of all pid recordings (used for PVR queue)
	return $totalretcode;
}



sub download_pid_not_in_cache {
	my $hist = shift;
	my $pid = shift;
	my $prog_type = shift;
	my $retcode;

	# Force prog type and create new prog instance if it doesn't exist
	my $this;
	logger "INFO: Trying to stream pid using type $prog_type\n";
	logger "INFO: pid not found in $prog_type cache\n";
	$this = progclass($prog_type)->new( 'pid' => $pid, 'type' => $prog_type );
	# if only one type is specified then we can clean up the pid which might actually be a url
	#if ( $#try_types == 0 ) {
		logger "INFO: Cleaning pid Old: '$this->{pid}', " if $opt->{verbose};
		$this->clean_pid;
		logger " New: '$this->{pid}'\n" if $opt->{verbose};
	#}
	# Display pid match for recording
	if ( $opt->{history} ) {
		$hist->list_progs( 'pid:'.$pid );
	} else {
		list_progs( { $this->{type} => 1 }, $this );
	}
	# Don't do a pid recording if metadataonly or thumbonly were specified
	if ( !( $opt->{metadataonly} || $opt->{thumbonly} || $opt->{subsonly} || $opt->{info} ) ) {
		return $this->download_retry_loop( $hist );
	}
}



sub download_pid_in_cache {
	my $hist = shift;
	my $this = shift;
	my $retcode;

	# Prune future scheduled match if not specified
	if ( (! $opt->{future}) && Programme::get_time_string( $this->{available} ) > time() ) {
		# If the prog object exists with pid in history delete it from the prog list
		logger "INFO: Ignoring Future Prog: '$this->{index}: $this->{name} - $this->{episode} - $this->{available}'\n" if $opt->{verbose};
		# Don't attempt to download
		return 1;
	}
	logger "INFO Trying to stream pid using type $this->{type}\n";
	logger "INFO: pid found in cache\n";
	# Display pid match for recording
	if ( $opt->{history} ) {
		$hist->list_progs( 'pid:'.$this->{pid} );
	} else {
		list_progs( { $this->{type} => 1 }, $this );
	}
	# Don't do a pid recording if metadataonly or thumbonly were specified
	if ( !( $opt->{metadataonly} || $opt->{thumbonly} || $opt->{subsonly} || $opt->{info} ) ) {
		$retcode = $this->download_retry_loop( $hist );
	}
	return $retcode;
}



# Use the specified options to process the matches in specified array
# Usage: find_matches( $pids_history_ref, @search_args )
# Returns: array of objects to be downloaded
#      or: number of failed/remaining programmes to record using the match (excluding previously recorded progs) if --pid is specified
sub find_matches {
	my $hist = shift;
	my @search_args = @_;
	my ( $type, $prog, $index_prog ) = init_search( @search_args );

	# We don't actually need to get the links first for the specifiied type(s) if we have only index number specified (and not --list)
	my %got_cache;
	my $need_get_links = 0;
	if ( (! $opt->{list} ) ) {
		for ( @search_args ) {
			if ( (! /^[\d]+$/) || $_ > $max_index || $_ < 1 ) {
				logger "DEBUG: arg '$_' is not a programme index number - load specified caches\n" if $opt->{debug};
				$need_get_links = 1;
				last;
			}
		}
	}

	# Pre-populate caches if --list option used or there was a non-index specified
	if ( $need_get_links || $opt->{list} ) {
		# Get stream links from web site or from cache (also populates all hashes) specified in --type option
		for my $t ( keys %{ $type } ) {
			get_links( $prog, $index_prog, $t );
			$got_cache{ $t } = 1;
		}
	}

	# Parse remaining args
	my @match_list;
	my @index_search_args;
	for ( @search_args ) {
		chomp();

		# If Numerical value < $max_index and the object exists from loaded prog types
		if ( /^[\d]+$/ && $_ <= $max_index ) {
			if ( defined $index_prog->{$_} ) {
				logger "INFO: Search term '$_' is an Index value\n" if $opt->{verbose};
				push @match_list, $index_prog->{$_};
			} else {
				# Add to another list to search in other prog types
				push @index_search_args, $_;
			}

		# If PID then find matching programmes with 'pid:<pid>'
		} elsif ( m{^\s*pid:(.+?)\s*$}i ) {
			if ( defined $prog->{$1} ) {
				logger "INFO: Search term '$1' is a pid\n" if $opt->{verbose};
				push @match_list, $prog->{$1};
			} else {
				logger "INFO: Search term '$1' is a non-existent pid, use --pid instead and/or specify the correct programme type\n";
			}

		# Else assume this is a programme name regex
		} else {
			logger "INFO: Search term '$_' is a substring\n" if $opt->{verbose};
			push @match_list, get_regex_matches( $prog, $_ );
		}
	}
	
	# List elements (i.e. 'channel' 'categories') if required and exit
	if ( $opt->{list} ) {
		list_unique_element_counts( $type, $opt->{list}, @match_list );
		exit 0;
	}

	# Go get the cached data for other programme types if the index numbers require it
	for my $index ( @index_search_args ) {
		# see if this index number falls into a valid range for a prog type
		for my $prog_type ( progclass() ) {
			if ( $index >= progclass($prog_type)->index_min && $index <= progclass($prog_type)->index_max && ( ! $got_cache{$prog_type} ) ) {
				logger "DEBUG: Looking for index $index in $prog_type type\n" if $opt->{debug};
				# Get extra required programme caches
				logger "INFO: Additionally getting cached programme data for $prog_type\n" if $opt->{verbose};
				# Add new prog types to the type list
				$type->{$prog_type} = 1;
				# Get $prog_type stream links
				get_links( $prog, $index_prog, $prog_type );
				$got_cache{$prog_type} = 1;
			}
		}
		# Now check again if the index number exists in the cache before adding this prog to the match list
		if ( defined $index_prog->{$index}->{pid} ) {
			push @match_list, $index_prog->{$index} if defined $index_prog->{$index}->{pid};
		} else {
			logger "WARNING: Unmatched programme index '$index' specified - ignoring\n";
		}
	}

	# De-dup matches and retain order
	@match_list = main::make_array_unique_ordered( @match_list );

	# Prune out pids already recorded if opt{hide} is specified (cannot hide for multimode)
	if ( $opt->{hide} && ( not $opt->{force} ) && ( not $opt->{multimode} ) ) {
		my @pruned;
		for my $this (@match_list) {
			# If the prog object exists with pid in history delete it from the prog list
			if ( $hist->check( $this->{pid}, undef, 1 ) ) {
				logger "DEBUG: Ignoring Prog: '$this->{index}: $this->{name} - $this->{episode}'\n" if $opt->{debug};
			} else {
				push @pruned, $this;
			}
		}
		@match_list = @pruned;
	}

	# Prune future scheduled matches if not specified
	if ( ! $opt->{future} ) {
		my $now = time();
		my @pruned;
		for my $this (@match_list) {
			# If the prog object exists with pid in history delete it from the prog list
			my $available = Programme::get_time_string( $this->{available} );
			if ( $available && $available > $now ) {
				logger "DEBUG: Ignoring Future Prog: '$this->{index}: $this->{name} - $this->{episode} - $this->{available}'\n" if $opt->{debug};
			} else {
				push @pruned, $this;
			}
		}
		@match_list = @pruned;		
	}
		
	# Truncate the array of matches if --limit-matches is specified
	if ( $opt->{limitmatches} && $#match_list > $opt->{limitmatches} - 1 ) {
		$#match_list = $opt->{limitmatches} - 1;
		main::logger "WARNING: The list of matching results was limited to $opt->{limitmatches} by --limit-matches\n";
	}

	# Display list for recording
	list_progs( $type, @match_list );

	# Write HTML and XML files if required (with search options applied)
	create_html_file( @match_list ) if $opt->{html};
	create_html_email( (join ' ', @search_args), @match_list ) if $opt->{email};
	create_xml( $opt->{fxd}, @match_list ) if $opt->{fxd};
	create_xml( $opt->{mythtv}, @match_list ) if $opt->{mythtv};

	return @match_list;
}



sub download_matches {
	my $hist = shift;
	my @match_list = @_;

	# Do the recordings based on list of index numbers if required
	my $failcount = 0;
	if ( $opt->{get} || $opt->{stdout} ) {
		for my $this (@match_list) {
			$failcount += $this->download_retry_loop( $hist );
		}
	}

	return $failcount;
}



# Usage: list_progs( \%type, @prog_refs )
# Lists progs given an array of index numbers
sub list_progs {
	my $typeref = shift;
	# Use a rogue value if undefined
	my $number_of_types = keys %{$typeref} || 2;
	my $ua = create_ua( 'desktop', 1 );
	my %names;
	my ( @matches ) = ( @_ );
	

	# Setup user agent for a persistent connection to get programme metadata
	if ( $opt->{info} ) {
		# Truncate array if were lisiting info and > $info_limit entries are requested - be nice to the beeb!
		if ( $#matches >= $info_limit ) {
			$#matches = $info_limit - 1;
			logger "WARNING: Only processing the first $info_limit matches\n";
		}
	}

	# Sort array by specified field
	if ( $opt->{sortmatches} ) {
		# disable tree mode
		delete $opt->{tree};

		# Lookup table for numeric search fields
		my %sorttype = (
			index		=> 1,
			duration	=> 1,
			timeadded	=> 1,
		);
		my $sort_prog;
		for my $this ( @matches ) {
			# field needs to be made to be unique by adding '|pid'
			$sort_prog->{ "$this->{ $opt->{sortmatches} }|$this->{pid}" } = $this;
		}
		@matches = ();
		# Numeric search
		if ( defined $sorttype{ $opt->{sortmatches} } ) {
			for my $key ( sort {$a <=> $b} keys %{ $sort_prog } ) {
				push @matches, $sort_prog->{$key};
			}
		# alphanumeric search
		} else {
			for my $key ( sort {lc $a cmp lc $b} keys %{ $sort_prog } ) {
				push @matches, $sort_prog->{$key};
			}
		}
	}
	# Reverse sort?
	if ( $opt->{sortreverse} ) {
		my @tmp = reverse @matches;
		@matches = @tmp;
	}

	# Determine number of episodes for each name
	my %episodes;
	my $episode_width;
	if ( $opt->{series} ) {
		for my $this (@matches) {
			$episodes{ $this->{name} }++;
			$episode_width = length( $this->{name} ) if length( $this->{name} ) > $episode_width;
		}
	}

	# Sort display order by field (won't work in tree mode)
	

	# Calculate page sizes etc if required
	my $items = $#matches+1;
	my ( $pages, $page, $pagesize, $first, $last );
	if ( ! $opt->{page} ) {
		logger "Matches:\n" if $#matches >= 0;
	} else {
		$pagesize = $opt->{pagesize} || 25;
		# Calc first and last programme numbers
		$first = $pagesize * ( $opt->{page} - 1 );
		$last = $first + $pagesize;
		# How many pages
		$pages = int( $items / $pagesize ) + 1;
		# If we request a page that is too high
		$opt->{page} = $pages if $page > $pages;
		logger "Matches (Page $opt->{page}/${pages}".()."):\n" if $#matches >= 0;
	}
	# loop through all programmes in match
	for ( my $count=0; $count < $items; $count++ ) {
		my $this = $matches[$count];
		# Only display if the prog name is set
		if ( ( ! $opt->{page} ) || ( $opt->{page} && $count >= $first && $count < $last ) ) {
			if ( $this->{name} || ! ( $opt->{series} || $opt->{tree} ) ) {
				# Tree mode
				if ( $opt->{tree} ) {
					if (! defined $names{ $this->{name} }) {
						$this->list_entry( '', 0, $number_of_types );
						$names{ $this->{name} } = 1;
					} else {
						$this->list_entry( '', 1, $number_of_types );
					}
				# Series mode
				} elsif ( $opt->{series} ) {
					if (! defined $names{ $this->{name} }) {
						$this->list_entry( '', 0, $number_of_types, $episodes{ $this->{name} }, $episode_width );
						$names{ $this->{name} } = 1;
					}
				# Normal mode
				} else {
					$this->list_entry( '', 0, $number_of_types ) if ( $this->{name} );
				}
			}
		}
		# Get info, create metadata, subtitles, tag and/or thumbnail file (i.e. don't stream/record)
		if ( $opt->{info} || $opt->{metadataonly} || $opt->{thumbonly} || $opt->{subsonly} || $opt->{tagonly} || $opt->{streaminfo} ) {
			$this->get_metadata_general();
			if ( $this->get_metadata( $ua ) ) {
				main::logger "ERROR: Could not get programme metadata\n" if $opt->{verbose};
				next;
			}
			# Search versions for versionlist versions
			my @versions = $this->generate_version_list;

			# Use first version in list if a version list is not specified
			$this->{version} = $versions[0] || 'default';
			$this->generate_filenames( $ua, $this->file_prefix_format() );
			# info
			$this->display_metadata( sort keys %{ $this } ) if $opt->{info};
			# subs (only for tv)
			if ( $opt->{subsonly} && $this->{type} eq 'tv') {
				$this->create_dir();
				$this->download_subtitles( $ua, "$this->{dir}/$this->{fileprefix}.srt" );
			}
			# metadata
			if ( $opt->{metadataonly} ) {
				$this->create_dir();
				$this->create_metadata_file;
			}
			# thumbnail
			if ( $opt->{thumbonly} && $this->{thumbnail} ) {
				$this->create_dir();
				$this->download_thumbnail();
			}
			# tag
			if ( $opt->{tagonly} && ! $opt->{notag} ) {
				# this probably needs to be initialised earlier - needed for tagging
				$bin->{atomicparsley} = $opt->{atomicparsley} || 'AtomicParsley';
				$this->create_dir();
				$this->tag_file;
			}
			# streaminfo
			if ( $opt->{streaminfo} ) {
				main::display_stream_info( $this, $this->{verpids}->{$this->{version}}, $this->{version} );
			}
			# remove offending metadata
			delete $this->{filename};
			delete $this->{filepart};
			delete $this->{ext};
		}
	}
	logger "\nINFO: ".($#matches + 1)." Matching Programmes\n" if ( $opt->{pvr} && $#matches >= 0 ) || ! $opt->{pvr};
}



# Returns matching programme objects using supplied regex
# Usage: get_regex_matches ( \%prog, $regex )
sub get_regex_matches {
	my $prog = shift;
	my $download_regex = shift;

	my %download_hash;
	my ( $channel_regex, $category_regex, $versions_regex, $channel_exclude_regex, $category_exclude_regex, $exclude_regex );

	if ( $opt->{channel} ) {
		$channel_regex = '('.(join '|', ( split /,/, $opt->{channel} ) ).')';
	} else {
		$channel_regex = '.*';
	}
	if ( $opt->{category} ) {
		$category_regex = '('.(join '|', ( split /,/, $opt->{category} ) ).')';
	} else {
		$category_regex = '.*';
	}
	if ( $opt->{versionlist} ) {
		$versions_regex = '('.(join '|', ( split /,/, $opt->{versionlist} ) ).')';
	} else {
		$versions_regex = '.*';
	}
	if ( $opt->{excludechannel} ) {
		$channel_exclude_regex = '('.(join '|', ( split /,/, $opt->{excludechannel} ) ).')';
	} else {
		$channel_exclude_regex = '^ROGUE$';
	}
	if ( $opt->{excludecategory} ) {
		$category_exclude_regex = '('.(join '|', ( split /,/, $opt->{excludecategory} ) ).')';
	} else {
		$category_exclude_regex = '^ROGUE$';
	}
	if ( $opt->{exclude} ) {
		$exclude_regex = '('.(join '|', ( split /,/, $opt->{exclude} ) ).')';
	} else {
		$exclude_regex = '^ROGUE$';
	}
	my $since = $opt->{since} || 999999;
	my $before = $opt->{before} || -999999;
	my $now = time();

	if ( $opt->{verbose} ) {
		main::logger "DEBUG: Search download_regex = $download_regex\n";
		main::logger "DEBUG: Search channel_regex = $channel_regex\n";
		main::logger "DEBUG: Search category_regex = $category_regex\n";
		main::logger "DEBUG: Search versions_regex = $versions_regex\n";
		main::logger "DEBUG: Search exclude_regex = $exclude_regex\n";
		main::logger "DEBUG: Search channel_exclude_regex = $channel_exclude_regex\n";
		main::logger "DEBUG: Search category_exclude_regex = $category_exclude_regex\n";
		main::logger "DEBUG: Search since = $since\n";
		main::logger "DEBUG: Search before = $before\n";
	}
	
	# Determine fields to search
	my @searchfields;
	# User-defined fields list
	if ( $opt->{fields} ) {
		@searchfields = split /\s*,\s*/, lc( $opt->{fields} );
	# Also search long descriptions and episode data if -l is specified
	} elsif ( $opt->{long} ) {
		@searchfields = ( 'name', 'episode', 'desc' );
	# Default to name search only
	} else {
		@searchfields = ( 'name' );
	}

	# Loop through each prog object
	for my $this ( values %{ $prog } ) {
		# Only include programmes matching channels and category regexes
		if ( $this->{channel} =~ /$channel_regex/i
		  && $this->{categories} =~ /$category_regex/i
		  && ( ( not defined $this->{versions} ) || $this->{versions} =~ /$versions_regex/i )
		  && $this->{channel} !~ /$channel_exclude_regex/i
		  && $this->{categories} !~ /$category_exclude_regex/i
		  && ( ( not defined $this->{timeadded} ) || $this->{timeadded} >= $now - ($since * 3600) )
		  && ( ( not defined $this->{timeadded} ) || $this->{timeadded} < $now - ($before * 3600) )
		) {
			# Add included matches
			my @compund_fields;
			push @compund_fields, $this->{$_} for @searchfields;
			$download_hash{ $this->{index} } = $this if (join ' ', @compund_fields) =~ /$download_regex/i;
		}
	}
	# Remove excluded matches
	for my $field ( @searchfields ) {
		for my $index ( keys %download_hash ) {
			my $this = $download_hash{$index};
			delete $download_hash{$index} if $this->{ $field } =~ /$exclude_regex/i;
		}
	}
	my @match_list;
	# Add all matching prog objects to array
	for my $index ( sort {$a <=> $b} keys %download_hash ) {
		push @match_list, $download_hash{$index};
	}

	return @match_list;
}



# Usage: sort_index( \%prog, \%index_prog, [$prog_type], [sortfield] )
# Populates the index if the prog hash as well as creating the %index_prog hash
# Should be run after any number of get_links methods
sub sort_index {
	my $prog = shift;
	my $index_prog = shift;
	my $prog_type = shift;
	my $sortfield = shift || 'name';
	my $counter = 1;
	my @sort_key;
	
	# Add index field based on alphabetical sorting by $sortfield
	# Start index counter at 'min' for this prog type
	$counter = progclass($prog_type)->index_min if defined $prog_type;

	# Create unique array of '<$sortfield|pid>' for this prog type
	for my $pid ( keys %{$prog} ) {
		# skip prog not of correct type and type is defined
		next if defined $prog_type && $prog->{$pid}->{type} ne $prog_type;
		push @sort_key, "$prog->{$pid}->{$sortfield}|$pid";
	}
	# Sort by $sortfield and index 
	for (sort @sort_key) {
		# Extract pid
		my $pid = (split /\|/)[1];

		# Insert prog instance var of the index number
		$prog->{$pid}->{index} = $counter;

		# Add the object reference into %index_prog hash
		$index_prog->{ $counter } = $prog->{$pid};

		# Increment the index counter for this prog type
		$counter++;
	}
	return 0;
}



sub make_array_unique_ordered {
	# De-dup array and retain order (don't ask!)
	my ( @array ) = ( @_ );
	my %seen = ();
	my @unique = grep { ! $seen{ $_ }++ } @array;
	return @unique;
}



# User Agents
# Uses global $ua_cache
my $ua_cache = {};
sub user_agent {
	my $id = shift || 'desktop';

	# Create user agents lists
	my $user_agent = {
		update		=> [ "get_iplayer updater (v${version} - $^O - $^V)" ],
		get_iplayer	=> [ "get_iplayer/$version $^O/$^V" ],
		desktop		=> [
				'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.56 Safari/537.17',
				'Mozilla/5.0 (Windows NT 6.1; rv:12.0) Gecko/20100101 Firefox/12.0',
				'Opera/9.80 (Windows NT 5.1) Presto/2.12.388 Version/12.12',
				'Mozilla/5.0 (Windows NT 7.1; rv:2.0) Gecko/20100101 Firefox/4.0 Opera 12.12',
				'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0) Opera 12.12',
				'Mozilla/5.0 (Windows NT 5.1; rv:18.0) Gecko/20100101 Firefox/18.0',
				'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2',
				'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
				'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 7.1; Trident/5.0)',
				'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)',
				],
		safari		=> [
				'Mozilla/5.0 (iPhone; U; CPU iPhone OS 2_0 like Mac OS X; en-us) AppleWebKit/525.18.1 (KHTML, like Gecko) Version/3.1.1 Mobile/5A345 Safari/525.20',
				'Mozilla/5.0 (iPhone; U; CPU iPhone OS 2_0_1 like Mac OS X; en-us) AppleWebKit/525.18.1 (KHTML, like Gecko) Version/3.1.1 Mobile/5B108 Safari/525.20',
				'Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16',
				'Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0_1 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A400 Safari/528.16',
				'Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_1_2 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7D11 Safari/528.16',
				'Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_1_3 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7E18 Safari/528.16',
				],
		coremedia	=> [
				'Apple iPhone v1.1.4 CoreMedia v1.0.0.4A102',
				'Apple iPhone v1.1.5 CoreMedia v1.0.0.4B1',
				'Apple iPhone OS v2.0 CoreMedia v1.0.0.5A347',
				'Apple iPhone OS v2.0.1 CoreMedia v1.0.0.5B108',
				'Apple iPhone OS v2.1 CoreMedia v1.0.0.5F136',
				'Apple iPhone OS v2.1 CoreMedia v1.0.0.5F137',
				'Apple iPhone OS v2.1.1 CoreMedia v1.0.0.5F138',
				'Apple iPhone OS v2.2 CoreMedia v1.0.0.5G77',
				'Apple iPhone OS v2.2 CoreMedia v1.0.0.5G77a',
				'Apple iPhone OS v2.2.1 CoreMedia v1.0.0.5H11',
				'Apple iPhone OS v3.0 CoreMedia v1.0.0.7A341',
				'Apple iPhone OS v3.1.2 CoreMedia v1.0.0.7D11',
				],
	};

	# Remember the ua string for the entire session
	my $uas = $ua_cache->{$id};
	if ( ! $uas ) {
		# Randomize strings
		my @ualist = @{ $user_agent->{$id} };
		$uas = $ualist[rand @ualist];
		my $code = sprintf( "%03d", int(rand(1000)) );
		$uas =~ s/<RAND>/$code/g;
		$ua_cache->{$id} = $uas;
	}
	logger "DEBUG: Using $id user-agent string: '$uas'\n" if $opt->{debug};
	return $uas || '';
}



# Returns classname for prog type or if not specified, an array of all prog types
sub progclass {
	my $prog_type = shift;
	if ( $prog_type ) {
		return $prog_types{$prog_type};
	} elsif ( not defined $prog_type ) {
		return keys %prog_types;
	} else {
		main::logger "ERROR: Programe Type '$prog_type' does not exist. Try using --refresh\n";
		exit 3;
	}
}



# Returns classname for prog type or if not specified, an array of all prog types
sub is_prog_type {
	my $prog_type = shift;
	return 1 if defined $prog_types{$prog_type};
	return 0;
}



# Feed Info:
#	# aod index
#	http://www.bbc.co.uk/radio/aod/index_noframes.shtml
# 	# schedule feeds
#	http://www.bbc.co.uk/bbcthree/programmes/schedules.xml
#	# These need drill-down to get episodes:
#	# TV schedules by date
#	http://www.bbc.co.uk/iplayer/widget/schedule/service/cbeebies/date/20080704
#	# TV schedules in JSON, Yaml or XML
#	http://www.bbc.co.uk/<channel>/programmes/schedules.(json|yaml|xml)
#	# prog schedules by channel / date
#	http://www.bbc.co.uk/<channel>/programmes/schedules/(this_week|next_week|last_week|yesterday|today|tomorrow).(json|yaml|xml)
#	http://www.bbc.co.uk/<channel>/programmes/schedules/<year>/<month>/<day>[/ataglance].(json|yaml|xml)
#	http://www.bbc.co.uk/<channel>/programmes/schedules/<year>/<week>.(json|yaml|xml)
#	# TV index on programmes tv
#	http://www.bbc.co.uk/tv/programmes/a-z/by/*/player
#	# TV + Radio
#	http://www.bbc.co.uk/programmes/a-z/by/*/player
#	# All TV (limit has effect of limiting to 2.? times number entries kB??)
#	# seems that only around 50% of progs are available here compared to programmes site:
#	http://feeds.bbc.co.uk/iplayer/categories/tv/list/limit/200
#	# Search feed
#	http://feeds.bbc.co.uk/iplayer/<channel>/<searchword>/list
#	# All Radio
#	http://feeds.bbc.co.uk/iplayer/categories/radio/list/limit/999
#	# New:
#	# iCal feeds see: http://www.bbc.co.uk/blogs/radiolabs/2008/07/some_ical_views_onto_programme.shtml
#	http://bbc.co.uk/programmes/b0079cmw/episodes/player.ics
#	# Other data
#	http://www.bbc.co.uk/cbbc/programmes/genres/childrens/player
#	http://www.bbc.co.uk/programmes/genres/childrens/schedules/upcoming.ics
#
# Usage: get_links( \%prog, \%index_prog, <prog_type>, <only load from file flag> )
# Globals: $memcache
sub get_links {
	my $prog = shift;
	my $index_prog = shift;
	my $prog_type = shift;
	my $only_load_from_cache = shift;
	# Define cache file format (this is overridden by the header line of the cache file)
	my @cache_format = qw/index type name pid available episode seriesnum episodenum versions duration desc channel categories thumbnail timeadded guidance web/;

	my $now = time();
	my $cachefile = "${profile_dir}/${prog_type}.cache";

	# Read cache into $pid_old and $index_prog_old hashes if cache exists
	my $prog_old = {};
	my $index_prog_old = {};

	# By pass re-sorting and get straight from memcache if possible
	if ( keys %{ $memcache->{$prog_type} } && -f $cachefile && ! $opt->{refresh} ) {
		for my $pid ( keys %{ $memcache->{$prog_type} } ) {
			# Create new prog instance
			$prog->{$pid} = progclass( lc($memcache->{$prog_type}->{$pid}->{type}) )->new( 'pid' => $pid );
			# Deep-copy of elements in memcache prog instance to %prog
			$prog->{$pid}->{$_} = $memcache->{$prog_type}->{$pid}->{$_} for @cache_format;
			# Copy object reference into index_prog hash
			$index_prog->{ $prog->{$pid}->{index} } = $prog->{$pid};
		}
		logger "INFO: Got (quick) ".(keys %{ $memcache->{$prog_type} })." memcache entries for $prog_type\n" if $opt->{verbose};
		return 0;
	}

	# Open cache file (need to verify we can even read this)
	if ( -f $cachefile && open(CACHE, "< $cachefile") ) {
		my @cache_format_old = @cache_format;
		# Get file format and contents less any comments
		while (<CACHE>) {
			chomp();
			# Get cache format if specified
			if ( /^\#(.+?\|){3,}/ ) {
				@cache_format_old = split /[\#\|]/;
				shift @cache_format_old;
				logger "INFO: Cache format from existing $prog_type cache file: ".(join ',', @cache_format_old)."\n" if $opt->{debug};
				next;
			}
			# Ignore comments
			next if /^[\#\s]/;
			# Populate %prog_old from cache
			# Get cache line
			my @record = split /\|/;
			my $record_entries;
			# Update fields in %prog_old hash for $pid
			$record_entries->{$_} = shift @record for @cache_format_old;
			$prog_old->{ $record_entries->{pid} } = $record_entries;
			# Copy pid into index_prog_old hash
			$index_prog_old->{ $record_entries->{index} }  = $record_entries->{pid};
		}
		close (CACHE);
		logger "INFO: Got ".(keys %{ $prog_old })." file cache entries for $prog_type\n" if $opt->{verbose};

	# Else no mem or file cache
	} else {
		logger "INFO: No file cache exists for $prog_type\n" if $opt->{verbose};
	}


	# Do we need to refresh the cache ?
	# if a cache file doesn't exist/corrupted/empty, refresh option is specified or original file is older than $cache_sec then download new data
	my $cache_secs = $opt->{expiry} || main::progclass( $prog_type )->expiry() || 14400;
	main::logger "DEBUG: Cache expiry time for $prog_type is ${cache_secs} secs - refresh in ".( stat($cachefile)->mtime + $cache_secs - $now )." secs\n" if $opt->{debug} && -f $cachefile && ! $opt->{refresh};
	if ( (! $only_load_from_cache) && 
		( (! keys %{ $prog_old } ) || (! -f $cachefile) || $opt->{refresh} || ($now >= ( stat($cachefile)->mtime + $cache_secs )) )
	) {

		# Get links for specific type of programme class into %prog 
		if ( progclass( $prog_type )->get_links( $prog, $prog_type ) != 0 ) {
			# failed - leave cache unchanged
			main::logger "ERROR: Errors encountered when retrieving $prog_type programmes - skipping\n";
			return 0;
		}

		# Sort index for this prog type from cache file
		# sorts and references %prog objects into %index_prog
		sort_index( $prog, $index_prog, $prog_type );

		# Open cache file for writing
		unlink $cachefile;
		my $now = time();
		if ( open(CACHE, "> $cachefile") ) {
			print CACHE "#".(join '|', @cache_format)."\n";
			# loop through all progs just obtained through get_links above (in numerical index order)
			for my $index ( sort {$a <=> $b} keys %{$index_prog} ) {
				# prog object
				my $this = $index_prog->{ $index };
				# Only write entries for correct prog type
				if ( $this->{type} eq $prog_type ) {
					# Merge old and new data to retain timestamps
					# if the entry was in old cache then retain timestamp from old entry
					if ( $prog_old->{ $this->{pid} }->{timeadded} ) {
						$this->{timeadded} = $prog_old->{ $this->{pid} }->{timeadded};
					# Else this is a new entry
					} else {
						$this->{timeadded} = $now;
						$this->list_entry( 'Added: ' ) unless $opt->{quiet};
					}
					# Write each field into cache line
					print CACHE $this->{$_}.'|' for @cache_format;
					print CACHE "\n";
				}
			}
			close (CACHE);
		} else {
			logger "WARNING: Couldn't open cache file '$cachefile' for writing\n";
		}

		# Copy new progs into memcache
		for my $index ( keys %{ $index_prog } ) {
			my $pid = $index_prog->{ $index }->{pid};
			# Update fields in memcache from %prog hash for $pid
			$memcache->{$prog_type}->{$pid}->{$_} = $index_prog->{$index}->{$_} for @cache_format;
		}

		# purge pids in memcache that aren't in %prog
		for my $pid ( keys %{ $memcache->{$prog_type} } ) {
			if ( ! defined $prog->{$pid} ) {
				delete $memcache->{$prog_type}->{$pid};
				main::logger "DEBUG: Removed PID $pid from memcache\n" if $opt->{debug};
			}
		}


	# Else copy data from existing cache file into new prog instances and memcache
	} else {
		for my $pid ( keys %{ $prog_old } ) {

			# Create new prog instance
			$prog->{$pid} = progclass( lc($prog_old->{$pid}->{type}) )->new( 'pid' => $pid );

			# Deep-copy the data from %prog_old into %prog and $memcache->{$prog_type}
			for (@cache_format) {
				$prog->{$pid}->{$_} = $prog_old->{$pid}->{$_};
				# Update fields in memcache from %prog_old hash for $pid
				$memcache->{$prog_type}->{$pid}->{$_} = $prog_old->{$pid}->{$_};
			}

		}
		# Add prog objects to %index_prog hash
		$index_prog->{$_} = $prog->{ $index_prog_old->{$_} } for keys %{ $index_prog_old };
	}

	return 0;
}



# Generic
# Returns an offset timestamp given an srt begin or end timestamp and offset in ms
sub subtitle_offset {
	my ( $timestamp, $offset ) = @_;
	my ( $hr, $min, $sec, $ms ) = split /[:,\.]/, $timestamp;
	# split into hrs, mins, secs, ms
	my $ts = $ms + $sec*1000 + $min*60*1000 + $hr*60*60*1000 + $offset;
	$hr = int( $ts/(60*60*1000) );
	$ts -= $hr*60*60*1000;
	$min = int( $ts/(60*1000) );
	$ts -= $min*60*1000;
	$sec = int( $ts/1000 );
	$ts -= $sec*1000;
	$ms = $ts;
	return sprintf( '%02d:%02d:%02d,%03d', $hr, $min, $sec, $ms );
}



# Generic
sub display_stream_info {
	my ($prog, $verpid, $version) = (@_);
	# default version is 'default'
	$version = 'default' if not defined $verpid;
	# Get stream data if not defined
	if ( not defined $prog->{streams}->{$version} ) {
		logger "INFO: Getting media stream metadata for $prog->{name} - $prog->{episode}, $verpid ($version)\n" if $prog->{pid};
		$prog->{streams}->{$version} = $prog->get_stream_data( $verpid );
	}
	for my $prog_type ( sort keys %{ $prog->{streams}->{$version} } ) {
		logger "stream:     $prog_type\n";
		for my $entry ( sort keys %{ $prog->{streams}->{$version}->{$prog_type} } ) {
			logger sprintf("%-11s %s\n", $entry.':', $prog->{streams}->{$version}->{$prog_type}->{$entry} );
		}
		logger "\n";
	}
	return 0;
}



sub proxy_disable {
	my $ua = shift;
	$ua->proxy( ['http'] => undef );
	$proxy_save = $opt->{proxy};
	delete $opt->{proxy};
	main::logger "INFO: Disabled proxy: $proxy_save\n" if $opt->{verbose};
}



sub proxy_enable {
	my $ua = shift;
	$ua->proxy( ['http'] => $opt->{proxy} ) if $opt->{proxy} && $opt->{proxy} !~ /^prepend:/;
	$opt->{proxy} = $proxy_save;
	main::logger "INFO: Restored proxy to $opt->{proxy}\n" if $opt->{verbose};
}



# Generic
# Usage download_block($file, $url_2, $ua, $start, $end, $file_len, $fh);
#  ensure filehandle $fh is open in append mode
# or, $content = download_block(undef, $url_2, $ua, $start, $end, $file_len);
# Called in 4 ways:
# 1) write to real file			=> download_block($file, $url_2, $ua, $start, $end, $file_len, $fh);
# 2) write to real file + STDOUT	=> download_block($file, $url_2, $ua, $start, $end, $file_len, $fh); + $opt->{stdout}==true
# 3) write to STDOUT only		=> download_block($file, $url_2, $ua, $start, $end, $file_len, $fh); + $opt->{stdout}==true + $opt->{nowrite}==false
# 4) write to memory (and return data)  => download_block(undef, $url_2, $ua, $start, $end, $file_len, undef);
# 4) write to memory (and return data)  => download_block(undef, $url_2, $ua, $start, $end);
sub download_block {

	my ($file, $url, $ua, $start, $end, $file_len, $fh) = @_;
	my $orig_length;
	my $buffer;
	my $lastpercent = 0;
	my $now = time();
	
	# If this is an 'append to file' mode call
	if ( defined $file && $fh && (!$opt->{nowrite}) ) {
		# Stage 3b: Record File
		$orig_length = tell $fh;
		logger "INFO: Appending to $file\n" if $opt->{verbose};
	}

	# Setup request headers
	my $h = new HTTP::Headers(
		'User-Agent'	=> main::user_agent( 'coremedia' ),
		'Accept'	=> '*/*',
		'Range'        => "bytes=${start}-${end}",
	);

	# Use url prepend if required
	if ( defined $opt->{proxy} && $opt->{proxy} =~ /^prepend:/ ) {
		$url = $opt->{proxy}.main::url_encode( $url );
		$url =~ s/^prepend://g;
	}

	my $req = HTTP::Request->new ('GET', $url, $h);

	# Set time to use for download rate calculation
	# Define callback sub that gets called during download request
	# This sub actually writes to the open output file and reports on progress
	my $callback = sub {
		my ($data, $res, undef) = @_;
		# Don't write the output to the file if there is no content-length header
		return 0 if ( ! $res->header("Content-Length") );
		# If we don't know file length in advanced then set to size reported reported from server upon download
		$file_len = $res->header("Content-Length") + $start if ! defined $file_len;
		# Write output
		print $fh $data if ! $opt->{nowrite};
		print STDOUT $data if $opt->{stdout};
		# return if streaming to stdout - no need for progress
		return if $opt->{stdout} && $opt->{nowrite};
		return if $opt->{quiet} || $opt->{silent};
		# current file size
		my $size = tell $fh;
		# Download percent
		my $percent = 100.0 * $size / $file_len;
		# Don't update display if we haven't dowloaded at least another 0.1%
		if ( not $opt->{hash} ) {
			return if ($percent - $lastpercent) < 0.1;
		} else {
			return if ($percent - $lastpercent) < 1;
		}
		$lastpercent = $percent;
		if ( $opt->{hash} ) {
			logger '#';
		} else {
			# download rates in bytes per second and time remaining
			my $rate_bps;
			my $rate;
			my $time;
			my $timecalled = time();
			if ($timecalled - $now < 1) {
				$rate = '-----kbps';
				$time = '--:--:--';
			} else {
				$rate_bps = ($size - $orig_length) / ($timecalled - $now);
				$rate = sprintf("%5.0fkbps", (8.0 / 1024.0) * $rate_bps);
				$time = sprintf("%02d:%02d:%02d", ( gmtime( ($file_len - $size) / $rate_bps ) )[2,1,0] );
			}
			logger sprintf "%8.2fMB / %.2fMB %s %5.1f%%, %s remaining         \r", 
				$size / 1024.0 / 1024.0, 
				$file_len / 1024.0 / 1024.0,
				$rate,
				$percent,
				$time,
			;
		}
	};

	my $callback_memory = sub {
		my ($data, $res, undef) = @_;
		# append output to buffer
		$buffer .= $data;
		return if $opt->{quiet} || $opt->{silent};
		# current buffer size
		my $size = length($buffer);
		# download rates in bytes per second
		my $timecalled = time();
		my $rate_bps;
		my $rate;
		my $time;
		my $percent;
		# If we can get Content_length then display full progress
		if ($res->header("Content-Length")) {
			$file_len = $res->header("Content-Length") if ! defined $file_len;
			# Download percent
			$percent = 100.0 * $size / $file_len;
			if ( not $opt->{hash} ) {
				return if ($percent - $lastpercent) < 0.1;
			} else {
				return if ($percent - $lastpercent) < 1;
			}
			$lastpercent = $percent;
			if ( $opt->{hash} ) {
				logger '#';
			} else {
				# Block length
				$file_len = $res->header("Content-Length");
				if ($timecalled - $now < 0.1) {
					$rate = '-----kbps';
					$time = '--:--:--';
				} else {
					$rate_bps = $size / ($timecalled - $now);
					$rate = sprintf("%5.0fkbps", (8.0 / 1024.0) * $rate_bps );
					$time = sprintf("%02d:%02d:%02d", ( gmtime( ($file_len - $size) / $rate_bps ) )[2,1,0] );
				}
				# time remaining
				logger sprintf "%8.2fMB / %.2fMB %s %5.1f%%, %s remaining         \r", 
					$size / 1024.0 / 1024.0,
					$file_len / 1024.0 / 1024.0,
					$rate,
					$percent,
					$time,
				;
			}
		# Just used simple for if we cannot determine content length
		} else {
			if ($timecalled - $now < 0.1) {
				$rate = '-----kbps';
			} else {
				$rate = sprintf("%5.0fkbps", (8.0 / 1024.0) * $size / ($timecalled - $now) );
			}
			logger sprintf "%8.2fMB %s         \r", $size / 1024.0 / 1024.0, $rate;
		}
	};

	# send request
	logger "\nINFO: Downloading range ${start}-${end}\n" if $opt->{verbose};
	logger "\r                              \r" if not $opt->{hash};
	my $res;

	# If $fh undefined then get block to memory (fh always defined for stdout or file d/load)
	if (defined $fh) {
		logger "DEBUG: writing stream to stdout, Range: $start - $end of $url\n" if $opt->{verbose} && $opt->{stdout};
		logger "DEBUG: writing stream to $file, Range: $start - $end of $url\n" if $opt->{verbose} && !$opt->{nowrite};
		$res = $ua->request($req, $callback);
		if (  (! $res->is_success) || (! $res->header("Content-Length")) ) {
			logger "ERROR: Failed to Download block\n\n";
			return 5;
		}
                logger "INFO: Content-Length = ".$res->header("Content-Length")."                               \n" if $opt->{verbose};
		return 0;
		   
	# Memory Block
	} else {
		logger "DEBUG: writing stream to memory, Range: $start - $end of $url\n" if $opt->{debug};
		$res = $ua->request($req, $callback_memory);
		if ( (! $res->is_success) ) {
			logger "ERROR: Failed to Download block\n\n";
			return '';
		} else {
			return $buffer;
		}
	}
}



# Generic
# create_ua( <agentname>|'', [<cookie mode>] )
# cookie mode:	0: retain cookies
#		1: no cookies
#		2: retain cookies but discard if site requires it
sub create_ua {
	my $id = shift || '';
	my $nocookiejar = shift || 0;
	# Use either the key from the function arg if it exists or a random ua string
	my $agent = main::user_agent( $id ) || main::user_agent( 'desktop' );
	my $ua = LWP::UserAgent->new;
	$ua->timeout( $lwp_request_timeout );
	$ua->proxy( ['http'] => $opt->{proxy} ) if $opt->{proxy} && $opt->{proxy} !~ /^prepend:/;
	$ua->agent( $agent );
	# Using this slows down stco parsing!!
	#$ua->default_header( 'Accept-Encoding', 'gzip,deflate' );
	$ua->conn_cache(LWP::ConnCache->new());
	#$ua->conn_cache->total_capacity(50);
	$ua->cookie_jar( HTTP::Cookies->new( file => $cookiejar.$id, autosave => 1, ignore_discard => 1 ) ) if not $nocookiejar;
	$ua->cookie_jar( HTTP::Cookies->new( file => $cookiejar.$id, autosave => 1 ) ) if $nocookiejar == 2;
	main::logger "DEBUG: Using ".($nocookiejar ? "NoCookies " : "cookies.$id " )."user-agent '$agent'\n" if $opt->{debug};
	return $ua;
};	



# Generic
# Converts a string of chars to it's HEX representation
sub get_hex {
        my $buf = shift || '';
        my $ret = '';
        for (my $i=0; $i<length($buf); $i++) {
                $ret .= " ".sprintf("%02lx", ord substr($buf, $i, 1) );
        }
	logger "DEBUG: HEX string value = $ret\n" if $opt->{verbose};
        return $ret;
}



# Generic
# version of unix tee
# Usage tee ($infile, $outfile)
# If $outfile is undef then just cat file to STDOUT
sub tee {
	my ( $infile, $outfile ) = @_;
	# Open $outfile for writing, $infile for reading
	if ( $outfile) {
		if ( ! open( OUT, "> $outfile" ) ) {
			logger "ERROR: Could not open $outfile for writing\n";
			return 1;
		} else {
			logger "INFO: Opened $outfile for writing\n" if $opt->{verbose};
		}
	}
	if ( ! open( IN, "< $infile" ) ) {
		logger "ERROR: Could not open $infile for reading\n";
		return 2;
	} else {
		logger "INFO: Opened $infile for reading\n" if $opt->{verbose};
	}
	# Read and redirect IN
	while ( <IN> ) {
		print $_;
		print OUT $_ if $outfile;
	}
	# Close output file
	close OUT if $outfile;
	close IN;
	return 0;
}



# Generic
# Usage: $fh = open_file_append($filename);
sub open_file_append {
	local *FH;
	my $file = shift;
	# Just in case we actually write to the file - make this /dev/null
	$file = File::Spec->devnull() if $opt->{nowrite};
	if ($file) {
		if ( ! open(FH, ">>:raw", $file) ) {
			logger "ERROR: Cannot write or append to $file\n\n";
			exit 1;
		}
	}
	# Fix for binary - needed for Windows
	binmode FH;
	return *FH;
}



# Generic
# Updates and overwrites this script - makes backup as <this file>.old
# Update logic:
# If the get_iplayer script is unwritable then quit - makes it harder for deb/rpm installed scripts to be overwritten
# If any available plugins in $plugin_dir_system are not writable then abort
# If all available plugins in $plugin_dir_system are writable then:
#	if any available plugins in $plugin_dir_user are not writable then abort
#	if all available plugins in $plugin_dir_user are writable then:
#		update script
#		update matching plugins in $plugin_dir_system
#		update matching plugins in $plugin_dir_user
#		warn of any plugins that are not in $plugin_dir_system or $plugin_dir_user and not available
sub update_script {
	my $version_url	= 'http://www.infradead.org/get_iplayer/VERSION-get_iplayer';
	my $update_url	= 'http://www.infradead.org/get_iplayer/';
	my $changelog_url = 'http://www.infradead.org/get_iplayer/CHANGELOG-get_iplayer';
	my $latest_ver;
	# Get version URL
	my $script_file = $0;
	my $script_url;
	my %plugin_url;
	my $ua = create_ua( 'update', 1 );

	# Are we flagged as installed using a pkg manager?
	if ( $opt->{packagemanager} ) {
		if ( $opt->{packagemanager} =~ /installer/i ) {
			logger "ERROR: get_iplayer should only be updated using the Windows installer: http://www.infradead.org/get_iplayer_win/get_iplayer_setup_latest.exe\n";
		} elsif ( $opt->{packagemanager} =~ /disable/i ) {
			logger "ERROR: get_iplayer should only be updated using your local package management system.  Please refer to your system documentation.\n";
		} else {
			logger "ERROR: get_iplayer was installed using the '$opt->{packagemanager}' package manager.  Please refer to the package manager documentation.\n";
		}
		exit 1;
	} 

	# Force update if no plugins dir
	if ( ! -d "$profile_dir/plugins" ) {
		mkpath "$profile_dir/plugins";
		if ( ! -d "$profile_dir/plugins" ) {
			logger "ERROR: Cannot create '$profile_dir/plugins' - no plugins will be downloaded.\n";
			return 1;
		}
		$opt->{pluginsupdate} = 1;
	}

	logger "INFO: Current version is ".(sprintf '%.2f', $version)."\n";
	logger "INFO: Checking for latest version from www.infradead.org\n";
	if ( $latest_ver = request_url_retry($ua, $version_url, 3 ) ) {
		chomp($latest_ver);
		# Compare version numbers
		if ( $latest_ver > $version || $opt->{force} || $opt->{pluginsupdate} ) {
			# reformat version number
			$latest_ver = sprintf('%.2f', $latest_ver);
			logger "INFO: Newer version $latest_ver available\n" if $latest_ver > $version;
			
			# Get the manifest of files to be updated
			my $base_url = "${update_url}/${latest_ver}";
			my $res;
			if ( not $res = request_url_retry($ua, "${update_url}/MANIFEST.v${latest_ver}", 3 ) ) {
				logger "ERROR: Failed to obtain update file manifest - Update aborted\n";
				exit 3;
			}

			# get a list of plugins etc from the manifest
			for ( split /\n/, $res ) {
				chomp();
				my ( $type, $url) = split /\s/;
				if ( $type eq 'bin' ) {
					$script_url =  $url;
				} elsif ( $type eq 'plugins' ) {
					my $filename = $url;
					$filename =~ s|^.+/(.+?)$|$1|g;
					$plugin_url{$filename} = $url;
				}
			}

			# Now decide whether to update based on write permissions
			# %plugin_files:      contains hash of current full_path_to_plugin_file -> plugin_filename
			# %plugin_url:      contains a hash of plugin_filename -> update_url for available plugins from the update site

			# If any available plugins in $plugin_dir_system are not writable then abort
			# if any available plugins in $plugin_dir_user are not writable then abort

			# loop through each currently installed plugin
			for my $path ( keys %plugin_files ) {
				my $file = $plugin_files{$path};
				# If this in the list of available plugins
				if ( $plugin_url{$file} ) {
					if ( ! -w $path ) {
						logger "ERROR: Cannot write plugin $path - aborting update\n";
						exit 1;
					}
				# warn of any plugins that are not in $plugin_dir_system or $plugin_dir_user and not available
				} else {
					logger "WARNING: Plugin $path is not managed - not updating this plugin\n";
				}
			}

			# All available plugins in all plugin dirs are writable:
			# update script if required
			if ( $latest_ver > $version || $opt->{force} ) {
				# If the get_iplayer script is unwritable then quit - makes it harder for deb/rpm installed scripts to be overwritten
				if ( ! -w $script_file ) {
					logger "ERROR: $script_file is not writable - aborting update (maybe a package manager was used to install get_iplayer?)\n";
					exit 1;
				}
				logger "INFO: Updating $script_file (from $version to $latest_ver)\n";
				update_file( $ua, $script_url, $script_file ) if ! $opt->{test};
			}
			for my $path ( keys %plugin_files ) {
				my $file = $plugin_files{$path};
				# If there is an update available for this plugin file...
				if ( $plugin_url{$file} ) {
					logger "INFO: Updating $path\n";
					# update matching plugin
					update_file( $ua, $plugin_url{$file}, $path ) if ! $opt->{test};
				}
			}

			# Install plugins which are currently not installed
			for my $file ( keys %plugin_url ) {
				# Not found in either system or user plugins dir
				if ( ( ! -f "$plugin_dir_system/$file" ) && ( ! -f "$plugin_dir_user/$file" ) ) {
					logger "INFO: Found new plugin $file\n";
					# Is the system plugin dir writable?
					if ( -d $plugin_dir_system && -w $plugin_dir_system ) {
						logger "INFO: Installing $file in $plugin_dir_system\n";
						update_file( $ua, $plugin_url{$file}, "$plugin_dir_system/$file" ) if ! $opt->{test};
					} elsif ( -d $plugin_dir_user && -w $plugin_dir_user ) {
						logger "INFO: Installing $file in $plugin_dir_user\n";
						update_file( $ua, $plugin_url{$file}, "$plugin_dir_user/$file" ) if ! $opt->{test};
					} else {
						logger "INFO: Cannot install $file, plugin dirs are not writable\n";
					}
				}
			}

			# Show changelog since last version if this is an upgrade
			if ( $version < $latest_ver ) {
				logger "INFO: Change Log: ${changelog_url}\n";
				my $changelog = request_url_retry($ua, $changelog_url, 3 );
				my $current_ver = sprintf('%.2f', $version);
				$changelog =~ s|^(.*)Version\s+$current_ver.+$|$1|s;
				logger "INFO: Changes since version $current_ver:\n\n$changelog\n";
			}

		} else {
			logger "INFO: No update is necessary (latest version = $latest_ver)\n";
		}
				
	} else {
		logger "ERROR: Failed to connect to update site - Update aborted\n";
		exit 2;
	}

	exit 0;
}



# Updates a file:
# Usage: update_file( <ua>, <url>, <dest filename> )
sub update_file {
	my $ua = shift;
	my $url = shift;
	my $dest_file = shift;
	my $res;
	# Download the file
	if ( not $res = request_url_retry($ua, $url, 3) ) {
		logger "ERROR: Could not download update for ${dest_file} - Update aborted\n";
		exit 1;
	}
	# If the download was successful then copy over this file and make executable after making a backup of this script
	if ( -f $dest_file ) {
		if ( ! copy($dest_file, $dest_file.'.old') ) {
			logger "ERROR: Could not create backup file ${dest_file}.old - Update aborted\n";
			exit 1;
		}
	}
	# Check if file is writable
	if ( not open( FILE, "> $dest_file" ) ) {
		logger "ERROR: $dest_file is not writable by the current user - Update aborted\n";
		exit 1;
	}
	# Windows needs this
	binmode FILE;
	# Write contents to file
	print FILE $res;
	close FILE;
	chmod 0755, $dest_file;
	logger "INFO: Downloaded $dest_file\n";
}



# Usage: create_xml( @prog_objects )
# Creates the Freevo FXD or MythTV Streams meta data (and pre-downloads graphics - todo)
sub create_xml {
	my $xmlfile = shift;

	if ( ! open(XML, "> $xmlfile") ) {
		logger "ERROR: Couldn't open xml file $xmlfile for writing\n";
		return 1;
	}
	print XML "<?xml version=\"1.0\" ?>\n";
	print XML "<freevo>\n" if $opt->{fxd};
	print XML "<MediaStreams>\n" if $opt->{mythtv};

	if ( $opt->{xmlnames} ) {
		# containers sorted by prog names
		print XML "\t<container title=\"Programmes by Name\">\n" if $opt->{fxd};
		my %program_index;
		my %program_count;
		# create hash of programme_name -> index
	        for my $this (@_) {
	        	$program_index{ $this->{name} } = $_;
			$program_count{ $this->{name} }++;
		}
		for my $name ( sort keys %program_index ) {
			print XML "\t\t<container title=\"".encode_entities( $name, '&<>"\'' )." ($program_count{$name})\">\n" if $opt->{fxd};
			print XML "\t<Streams>\n" if $opt->{mythtv};
			print XML "\t\t<Name>".encode_entities( $name, '&<>"\'' )."</Name>\n" if $opt->{mythtv};
			for my $this (@_) {
				my $pid = $this->{pid};
				# loop through and find matches for each progname
				if ( $this->{name} eq $name ) {
					my $episode = encode_entities( $this->{episode}, '&<>"\'' );
					my $desc = encode_entities( $this->{desc}, '&<>"\'' );
					my $title = "${episode}";
					$title .= " ($this->{available})" if $this->{available} !~ /^(unknown|)$/i;
					if ( $opt->{fxd} ) {
						print XML "\t\t\t<movie title=\"${title}\">\n";
						print XML "\t\t\t\t<video>\n";
						print XML "\t\t\t\t\t<url id=\"p1\">${pid}.mov<playlist/></url>\n";
						print XML "\t\t\t\t</video>\n";
						print XML "\t\t\t\t<info>\n";
						print XML "\t\t\t\t\t<description>${desc}</description>\n";
						print XML "\t\t\t\t</info>\n";
						print XML "\t\t\t</movie>\n";
					} elsif ( $opt->{mythtv} ) {
						print XML "\t\t<Stream>\n";
						print XML "\t\t\t<Name>${title}</Name>\n";
						print XML "\t\t\t<type>$this->{type}</type>\n";
						print XML "\t\t\t<index>$this->{index}</index>\n";
						print XML "\t\t\t<url>${pid}.mov</url>\n";
						print XML "\t\t\t<Subtitle></Subtitle>\n";
						print XML "\t\t\t<Synopsis>${desc}</Synopsis>\n";
						print XML "\t\t\t<StreamImage>$this->{thumbnail}</StreamImage>\n";
						print XML "\t\t</Stream>\n";
					}
				}
			}			
			print XML "\t\t</container>\n" if $opt->{fxd};
			print XML "\t</Streams>\n" if $opt->{mythtv};
		}
		print XML "\t</container>\n" if $opt->{fxd};
	}


	if ( $opt->{xmlchannels} ) {
		# containers for prog names sorted by channel
		print XML "\t<container title=\"Programmes by Channel\">\n" if $opt->{fxd};
		my %program_index;
		my %program_count;
		my %channels;
		# create hash of unique channel names and hash of programme_name -> index
	        for my $this (@_) {
	        	$program_index{ $this->{name} } = $_;
			$program_count{ $this->{name} }++;
			push @{ $channels{ $this->{channel} } }, $this->{name};
		}
		for my $channel ( sort keys %channels ) {
			print XML "\t\t<container title=\"".encode_entities( $channel, '&<>"\'' )."\">\n" if $opt->{fxd};
			print XML
				"\t<Feed>\n".
				"\t\t<Name>".encode_entities( $channel, '&<>"\'' )."</Name>\n".
				"\t\t<Provider>BBC</Provider>\n".
				"\t\t<Streams>\n" if $opt->{mythtv};
			for my $name ( sort keys %program_index ) {
				# Do we have any of this prog $name on this $channel?
				my $match;
				for ( @{ $channels{$channel} } ) {
					$match = 1 if $_ eq $name;
				}
				if ( $match ) {
					print XML "\t\t\t<container title=\"".encode_entities( $name, '&<>"\'' )." ($program_count{$name})\">\n" if $opt->{fxd};
					#print XML "\t\t<Stream>\n" if $opt->{mythtv};
					for my $this (@_) {
						# loop through and find matches for each progname for this channel
						my $pid = $this->{pid};
						if ( $this->{channel} eq $channel && $this->{name} eq $name ) {
							my $episode = encode_entities( $this->{episode}, '&<>"\'' );
							my $desc = encode_entities( $this->{desc}, '&<>"\'' );
							my $title = "${episode} ($this->{available})";
							if ( $opt->{fxd} ) {
								print XML
									"\t\t\t\t<movie title=\"${title}\">\n".
									"\t\t\t\t\t<video>\n".
									"\t\t\t\t\t\t<url id=\"p1\">${pid}.mov<playlist/></url>\n".
									"\t\t\t\t\t</video>\n".
									"\t\t\t\t\t<info>\n".
									"\t\t\t\t\t\t<description>${desc}</description>\n".
									"\t\t\t\t\t</info>\n".
									"\t\t\t\t</movie>\n";
							} elsif ( $opt->{mythtv} ) {
								print XML 
									"\t\t\t<Stream>\n".
									"\t\t\t\t<Name>".encode_entities( $name, '&<>"\'' )."</Name>\n".
									"\t\t\t\t<index>$this->{index}</index>\n".
									"\t\t\t\t<type>$this->{type}</type>\n".
									"\t\t\t\t<Url>${pid}.mov</Url>\n".
									"\t\t\t\t<StreamImage>$this->{thumbnail}</StreamImage>\n".
									"\t\t\t\t<Subtitle>${episode}</Subtitle>\n".
									"\t\t\t\t<Synopsis>${desc}</Synopsis>\n".
									"\t\t\t</Stream>\n";
							}
						}
					}
					print XML "\t\t\t</container>\n" if $opt->{fxd};
				}
			}
			print XML "\t\t</container>\n" if $opt->{fxd};
			print XML "\t\t</Streams>\n\t</Feed>\n" if $opt->{mythtv};
		}
		print XML "\t</container>\n" if $opt->{fxd};
	}


	if ( $opt->{xmlalpha} ) {
		my %table = (
			'A-C' => '[abc]',
			'D-F' => '[def]',
			'G-I' => '[ghi]',
			'J-L' => '[jkl]',
			'M-N' => '[mn]',
			'O-P' => '[op]',
			'Q-R' => '[qr]',
			'S-T' => '[st]',
			'U-V' => '[uv]',
			'W-Z' => '[wxyz]',
			'0-9' => '[\d]',
		);
		print XML "\t<container title=\"Programmes A-Z\">\n";
		for my $folder (sort keys %table) {
			print XML "\t\t<container title=\"$folder\">\n";
			for my $this (@_) {
				my $pid = $this->{pid};
				my $name = encode_entities( $this->{name}, '&<>"\'' );
				my $episode = encode_entities( $this->{episode}, '&<>"\'' );
				my $desc = encode_entities( $this->{desc}, '&<>"\'' );
				my $title = "${name} - ${episode} ($this->{available})";
				my $regex = $table{$folder};
				if ( $name =~ /^$regex/i ) {
					if ( $opt->{fxd} ) {
						print XML
							"\t\t\t<movie title=\"${title}\">\n".
							"\t\t\t\t<video>\n".
							"\t\t\t\t\t<url id=\"p1\">${pid}.mov<playlist/></url>\n".
							"\t\t\t\t</video>\n".
							"\t\t\t\t<info>\n".
							"\t\t\t\t\t<description>${desc}</description>\n".
							"\t\t\t\t</info>\n".
							"\t\t\t</movie>\n";
					} elsif ( $opt->{mythtv} ) {
						print XML
							"\t\t\t<Stream>\n".
							"\t\t\t\t<Name>${title}</Name>\n".
							"\t\t\t\t<index>$this->{index}</index>\n".
							"\t\t\t\t<type>$this->{type}</type>\n".
							"\t\t\t\t<Url>${pid}.mov</Url>\n".
							"\t\t\t\t<StreamImage>$this->{thumbnail}</StreamImage>\n".
							"\t\t\t\t<Subtitle>${episode}</Subtitle>\n".
							"\t\t\t\t<Synopsis>${desc}</Synopsis>\n".
							"\t\t\t</Stream>\n";
					}
				}
			}
			print XML "\t\t</container>\n";
		}
		print XML "\t</container>\n";
	}

	print XML '</freevo>' if $opt->{fxd};
	print XML '</MediaStreams>' if $opt->{mythtv};
	close XML;
}



# Usage: create_html_file( @prog_objects )
sub create_html_file {
	# Create local web page
	if ( open(HTML, "> $opt->{html}") ) {
		print HTML create_html( @_ );
		close (HTML);
	} else {
		logger "WARNING: Couldn't open html file $opt->{html} for writing\n";
	}
}



# Usage: create_email( @prog_objects )
# References: http://sial.org/howto/perl/Net-SMTP/, http://cpansearch.perl.org/src/RJBS/Email-Send-2.198/lib/Email/Send/SMTP.pm
# Credit: Network Ned, andy <AT SIGN> networkned.co.uk, http://networkned.co.uk
sub create_html_email {
	# Check if we have Net::SMTP::TLS::ButMaintained/Net::SMTP::TLS/Net::SMTP::SSL/Net::SMTP installed
	my $smtpclass;
	if ( $opt->{emailsecurity} eq "TLS" ) {
		# prefer Net::SMTP::TLS::ButMaintained if installed
		$smtpclass = 'Net::SMTP::TLS::ButMaintained';
		eval "use $smtpclass";
		if ($@) {
			$smtpclass = 'Net::SMTP::TLS';
		}
	} elsif ( $opt->{emailsecurity} eq "SSL" ) {
		$smtpclass = 'Net::SMTP::SSL';
		eval "use Authen::SASL";
		if ($@) {
			main::logger "WARNING: Authen::SASL Perl module is required for --email-security=$opt->{emailsecurity}.\n";
			return 0;
		}
	} else {
		$smtpclass = 'Net::SMTP';
	}
	eval "use $smtpclass";
	if ($@) {
		main::logger "WARNING: Please download and run latest installer or install the $smtpclass Perl module to use --email-security=$opt->{emailsecurity}.\n";
		return 0;
	};
	my $search_args = shift;
	my $recipient = $opt->{email};
	my $sender = $opt->{emailsender} || 'get_iplayer <>';
	my $smtphost = $opt->{emailsmtp} || 'localhost';
	my $password = $opt->{emailpassword};
	my $user = $opt->{emailuser};
	my $port = $opt->{emailport};
	if ( ! $port ) {
		$port = ( $opt->{emailsecurity} eq "SSL" ) ? 465
			: ( $opt->{emailsecurity} eq "TLS" ) ? 587 : 25;
	}
	my @mail_failure;
	my @subject;
	# Set the subject using the currently set cmdline options
	push @subject, "get_iplayer Search Results for: $search_args ( ";
	for my $optkey ( grep !/^email.*/, sort keys %{ $opt_cmdline } ) {
		push @subject, "$optkey='$opt_cmdline->{$optkey}' " if $opt_cmdline->{$optkey};
	}
	push @subject, " )";

	my $message = "MIME-Version: 1.0\n"
		."Content-Type: text/html\n"
		."From: $sender\n"
		."To: $recipient\n"
		."Subject: @subject\n\n\n"
		.create_html( @_ )."\n";
	main::logger "DEBUG: Email message to $recipient:\n$message\n\n" if $opt->{debug};

	my $smtp;
	if ( $opt->{emailsecurity} ne 'TLS' ) {
		$smtp = $smtpclass->new($smtphost, Port => $port);
	} else {
		eval {
			$smtp = $smtpclass->new(
				$smtphost,
				Port => $port,
				User => $user,
				Password=> $password
			);
		};
	}
	if ( ! $smtp ) {
		main::logger "ERROR: Could not find or connect to specified SMTP server\n";
		return 1;
	};

	if ( $opt->{emailsecurity} ne 'TLS' && $user ) {
		if ( ! $smtp->auth($user, $password) ) {
			main::logger "ERROR: Could not authenticate to specified SMTP server\n";
			return 1;
		}
	}

	if ( $opt->{emailsecurity} ne 'TLS' ) {
		$smtp->mail( $sender ) || push @mail_failure, "MAIL FROM: $sender";
		$smtp->to( $recipient ) || push @mail_failure, "RCPT TO: $recipient";
		$smtp->data() || push @mail_failure, 'DATA';
		$smtp->datasend( $message ) || push @mail_failure, 'Message Data';
		$smtp->dataend() || push @mail_failure, 'End of DATA';
		$smtp->quit() || push @mail_failure, 'QUIT';
	} else {
		# ::TLS has no useful return value, but will croak on failure.
		eval { $smtp->mail( $sender ) };
		push @mail_failure, "MAIL FROM: $sender" if $@;
		eval { $smtp->to( $recipient ) };
		push @mail_failure, "RCPT TO: $recipient" if $@;
		eval { $smtp->data() };
		push @mail_failure, 'DATA' if $@;
		eval { $smtp->datasend( $message ) };
		push @mail_failure, 'Message Data' if $@;
		eval { $smtp->dataend() };
		push @mail_failure, 'End of DATA' if $@;
		eval { $smtp->quit() };
		push @mail_failure, 'QUIT' if $@;
	}

	if ( @mail_failure ) {
		main::logger "ERROR: Sending of email failed with $mail_failure[0]\n";
	}
	return 0;
}



# Usage: create_html( @prog_objects )
sub create_html {
	my @html;
	my %name_channel;
	# Create local web page
	push @html, '<html><head></head><body><table border=1>';
	for my $this ( @_ ) {
		# Skip if pid isn't in index
		my $pid = $this->{pid} || next;
		# Skip if already recorded and --hide option is specified
		if (! defined $name_channel{ "$this->{name}|$this->{channel}" }) {
			push @html, $this->list_entry_html();
		} else {
			push @html, $this->list_entry_html( 1 );
		}
		$name_channel{ "$this->{name}|$this->{channel}" } = 1;
	}
	push @html, '</table></body>';
	return join "\n", @html;
}



# Generic
# Gets the contents of a URL and retries if it fails, returns '' if no page could be retrieved
# Usage <content> = request_url_retry(<ua>, <url>, <retries>, <succeed message>, [<fail message>], <1=mustproxy> );
sub request_url_retry {

	my %OPTS = @LWP::Protocol::http::EXTRA_SOCK_OPTS;
	$OPTS{SendTE} = 0;
	@LWP::Protocol::http::EXTRA_SOCK_OPTS = %OPTS;
	
	my ($ua, $url, $retries, $succeedmsg, $failmsg, $mustproxy) = @_;
	my $res;


	# Use url prepend if required
	if ( defined $opt->{proxy} && $opt->{proxy} =~ /^prepend:/ ) {
		$url = $opt->{proxy}.main::url_encode( $url );
		$url =~ s/^prepend://g;
	}

	# Malformed URL check
	if ( $url !~ m{^\s*http\:\/\/}i ) {
		logger "ERROR: Malformed URL: '$url'\n";
		return '';
	}

	# Disable proxy unless mustproxy is flagged
	main::proxy_disable($ua) if $opt->{partialproxy} && ! $mustproxy;
	my $i;
	logger "INFO: Getting page $url\n" if $opt->{verbose};
	for ($i = 0; $i < $retries; $i++) {
		$res = $ua->request( HTTP::Request->new( GET => $url ) );
		if ( ! $res->is_success ) {
			logger $failmsg;
		} else {
			logger $succeedmsg;
			last;
		}
	}
	# Re-enable proxy unless mustproxy is flagged
	main::proxy_enable($ua) if $opt->{partialproxy} && ! $mustproxy;
	# Return empty string if we failed
	return '' if $i == $retries;

	# Only return decoded content if gzip is used - otherwise this severely slows down stco scanning! Perl bug?
	main::logger "DEBUG: ".($res->header('Content-Encoding') || 'No')." Encoding used on $url\n" if $opt->{debug};
	# this appears to be obsolete
	# return $res->decoded_content if defined $res->header('Content-Encoding') && $res->header('Content-Encoding') eq 'gzip';
	# return $res->content;
	return $res->decoded_content;
}



# Generic
# Checks if a particular program exists (or program.exe) in the $ENV{PATH} or if it has a path already check for existence of file
sub exists_in_path {
	my $name = shift;
	my $bin = $bin->{$name};
	# Strip quotes around binary if any just for checking
	$bin =~ s/^"(.+)"$/$1/g;
	# If this has a path specified, does file exist
	return 1 if $bin =~ /[\/\\]/ && (-x ${bin} || -x "${bin}.exe");
	# Search PATH
	for (@PATH) {
		return 1 if -x "${_}/${bin}" || -x "${_}/${bin}.exe";
	}
	return 0;
}



# Generic
# Checks history for files that are over 30 days old and asks user if they should be deleted
# "$prog->{pid}|$prog->{name}|$prog->{episode}|$prog->{type}|".time()."|$prog->{mode}|$prog->{filename}\n";
sub purge_downloaded_files {
	my $hist = shift;
	my @delete;
	my @proglist;
	my $days = shift;
			
	# Return if disabled or running in a typically non-interactive mode
	return 0 if $opt->{nopurge} || $opt->{stdout} || $opt->{nowrite} || $opt->{quiet} || $opt->{silent};
	
	for my $pid ( $hist->get_pids() ) {
		my $record = $hist->get_record( $pid );
		if ( $record->{timeadded} < (time() - $days*86400) && $record->{filename} && -f $record->{filename} ) {
			# Calculate the seconds difference between epoch_now and epoch_datestring and convert back into array_time
			my @t = gmtime( time() - $record->{timeadded} );
			push @proglist, "$record->{name} - $record->{episode}, Recorded: $t[7] days $t[2] hours ago";
			push @delete, $record->{filename};
		}
	}
	
	if ( @delete ) {
		main::logger "\nThese programmes should be deleted:\n";
		main::logger "-----------------------------------\n";
		main::logger join "\n", @proglist;
		main::logger "\n-----------------------------------\n";
		main::logger "Do you wish to delete them now (Yes/No) ?\n";
		my $answer = <STDIN>;
		if ($answer =~ /^yes$/i ) {
			for ( @delete ) {
				main::logger "INFO: Deleting $_\n";
				unlink $_;
			}
			main::logger "Programmes deleted\n";
		} else {
			main::logger "No Programmes deleted\n";
		}
	}
	
	return 0;
}



# Returns url decoded string
sub url_decode {
	my $str = shift;
	$str =~ s/\%([A-Fa-f0-9]{2})/pack('C', hex($1))/seg;
	return $str;
}



# Returns url encoded string
sub url_encode {
	my $str = shift;
	$str =~ s/([^A-Za-z0-9])/sprintf("%%%02X", ord($1))/seg;
	return $str;
}



# list_unique_element_counts( \%type, $element_name, @matchlist);
# Show channels for currently specified types in @matchlist - an array of progs
sub list_unique_element_counts {
	my $typeref = shift;
	my $element_name = shift;
	my @match_list = @_;
	my %elements;
	logger "INFO: ".(join ',', keys %{ $typeref })." $element_name List:\n" if $opt->{verbose};
	# Get list to count from matching progs
	for my $prog ( @match_list ) {
		my @element;
		# Need to separate the categories
		if ($element_name eq 'categories') {
			@element = split /,/, $prog->{$element_name};
		} else {
			$element[0] = $prog->{$element_name};
		}
		for my $element (@element) {
			$elements{ $element }++;
		}
	}
	# display element + prog count
	logger "$_ ($elements{$_})\n" for sort keys %elements;
	return 0;
}



# Invokes command in @args as a system call (hopefully) without using a shell
#  Can also redirect all stdout and stderr to either: STDOUT, STDERR or unchanged
# Usage: run_cmd( <normal|STDERR|STDOUT>, @args )
# Returns: exit code
sub run_cmd {
	my $mode = shift;
	my @cmd = ( @_ );
	my $rtn;
	my $USE_SYSTEM = 0;
	#my $system_suffix;
	local *DEVNULL;
	
	my $log_str;
	my @log_cmd = @cmd;
	if ( $#log_cmd > 0 ) {
		$log_str = (join ' ', map {s/\"/\\\"/g; "\"$_\"";} @log_cmd)
	} else {
		$log_str = $log_cmd[0]
	}
	main::logger "\n\nINFO: Command: $log_str\n\n" if $opt->{verbose};

	# Define what to do with STDOUT and STDERR of the child process
	my $fh_child_out = ">&STDOUT";
	my $fh_child_err = ">&STDERR";

	$mode = 'QUIET' if ( $opt->{quiet} || $opt->{silent} ) && ! ($opt->{stdout} || $opt->{debug} || $opt->{verbose});

	if ( $mode eq 'STDOUT' ) {
		$fh_child_out = $fh_child_err = ">&STDOUT";
		#$system_suffix = '2>&1';
	} elsif ( $mode eq 'STDERR' ) {
		$fh_child_out = $fh_child_err = ">&STDERR";
		#$system_suffix = '1>&2';
	} elsif ( $mode eq 'QUIET' ) {
		open(DEVNULL, ">", File::Spec->devnull()) || die "ERROR: Cannot open null device\n";
		$fh_child_out = $fh_child_err = ">&DEVNULL";
	}	

	# Check if we have IPC::Open3 otherwise fallback on system()
	eval "use IPC::Open3";

	# use system(); - probably only likely in win32
	if ($@) {
		main::logger "WARNING: Please download and run latest installer - 'IPC::Open3' is not available\n";
		#push @cmd, $system_suffix;
		my $rtn = system( @cmd );

	# use system() regardless
	} elsif ( $USE_SYSTEM ) {
		#push @cmd, $system_suffix;
		my $rtn = system( @cmd );

	# Use open3()
	} else {

		my $procid;
		# Don't create zombies - unfortunately causes open3 to return -1 exit code regardless!
		##### local $SIG{CHLD} = 'IGNORE';
		# Setup signal handler for SIGTERM/INT/KILL - kill, kill, killlllll
		$SIG{TERM} = $SIG{PIPE} = $SIG{INT} = sub {
			my $signal = shift;
			main::logger "\nINFO: Cleaning up (signal = $signal), killing PID=$procid:";
			for my $sig ( qw/INT TERM KILL/ ) {
				# Kill process with SIGs (try to allow proper handling of kill by child process)
				if ( $opt->{verbose} ) {
					main::logger "\nINFO: $$ killing cmd PID=$procid with SIG${sig}";
				} else {
					main::logger '.';
				}
				kill $sig, $procid;
				sleep 1;
				if ( ! kill 0, $procid ) {
					main::logger "\nINFO: $$ killed cmd PID=$procid\n";
					last;
				}
				sleep 1;
			}
			main::logger "\n";
			exit 0;
		};

		# Don't use NULL for the 1st arg of open3 otherwise we end up with a messed up STDIN once it returns
		$procid = open3( 0, $fh_child_out, $fh_child_err, @cmd );

		# Wait for child to complete
		waitpid( $procid, 0 );
		$rtn = $?;

		# Restore old signal handlers
		$SIG{TERM} = $SIGORIG{TERM};
		$SIG{PIPE} = $SIGORIG{PIPE};
		$SIG{INT} = $SIGORIG{INT};
		#$SIG{CHLD} = $SIGORIG{CHLD};
	}
	close(DEVNULL);

	# Interpret return code	and force return code 2 upon error      
	my $return = $rtn >> 8;
	if ( $rtn == -1 ) {
		main::logger "ERROR: Command failed to execute: $!\n" if $opt->{verbose};
		$return = 2 if ! $return;
	} elsif ( $rtn & 128 ) {
		main::logger "WARNING: Command executed but coredumped\n" if $opt->{verbose};
		$return = 2 if ! $return;
	} elsif ( $rtn & 127 ) {
		main::logger sprintf "WARNING: Command executed but died with signal %d\n", $rtn & 127 if $opt->{verbose};
		$return = 2 if ! $return;
	}
	main::logger sprintf "INFO: Command exit code %d (raw code = %d)\n", $return, $rtn if $return || $opt->{verbose};
	return $return;
}



# Generic
# Escape chars in string for shell use
sub StringUtils::esc_chars {
	# will change, for example, a!!a to a\!\!a
	$_[0] =~ s/([;<>\*\|&\$!#\(\)\[\]\{\}:'"])/\\$1/g;
}



sub StringUtils::clean_utf8_and_whitespace {
	# Remove non utf8
	$_[0] =~ s/[^\x{21}-\x{7E}\s\t\n\r]//g;
	# Strip beginning/end/extra whitespace
	$_[0] =~ s/\s+/ /g;
	$_[0] =~ s/(^\s+|\s+$)//g;
}

# Remove diacritical marks
sub StringUtils::remove_marks {
	my $string = shift;
	$string = NFKD($string);
	$string =~ s/\pM//g;
	return $string;
}

# Convert unwanted punctuation to ASCII
sub StringUtils::convert_punctuation {
	my $string = shift;
	# die smart quotes die
	$string =~ s/[\x{0060}\x{00B4}\x{2018}\x{2019}\x{201A}\x{2039}\x{203A}]/'/g;
	$string =~ s/[\x{201C}\x{201D}\x{201E}]/"/g;
	$string =~ s/[\x{2013}\x{2014}]/-/g;
	$string =~ s/[\x{2026}]/.../g;
	return $string;
}

# Generic
# Make a filename/path sane
sub StringUtils::sanitize_path {
	my $string = shift;
	my $is_path = shift || 0;
	my $force_default = shift || 0;
	my $default_bad = '[^a-zA-Z0-9_\-\.\/\s]';
	my $punct_bad = '[!"#$%&\'()*+,:;<=>?@[\]^`{|}~]';
	my $fat_bad = '["*:<>?|]';
	my $hfs_bad = '[:]';
	# Replace forward slashes with _ if not path
	$string =~ s/\//_/g unless $is_path;
	# Replace backslashes with _ if not Windows path
	$string =~ s/\\/_/g unless $^O eq "MSWin32" && $is_path;
	# ASCII-fy some punctuation
	$string = StringUtils::convert_punctuation($string);
	# Replace ellipsis with _
	$string =~ s/\.{3}/_/g;
	# Truncate duplicate colon/semi-colon/comma
	$string =~ s/([:;,])(\1)+/$1/g;
	# Add whitespace behind colon/semi-colon/comma if not present
	$string =~ s/([:;,])(\S)/$1 $2/g;
	# Remove extra/leading/trailing whitespace
	$string =~ s/\s+/ /g;
	$string =~ s/(^\s+|\s+$)//g;
	# Replace whitespace with _ unless --whitespace
	$string =~ s/\s/_/g unless $opt->{whitespace};
	# Truncate multiple replacement chars
	$string =~ s/_+/_/g;
	# Remove non-ASCII chars unless --nonascii or force default
	if ( $force_default || ! $opt->{nonascii} ) {
		$string = StringUtils::remove_marks($string);
		$string =~ s/[^\x{20}-\x{7e}]//g;
	}
	# Remove most punctuation chars unless --punctuation or force default
	if ( $force_default || ! $opt->{punctuation} ) {
		$string =~ s/$punct_bad//g
	}
	# Remove FAT-unfriendly chars if --fatfilename or Windows and not force default
	if ( ! $force_default && ( $opt->{fatfilename} || $^O eq "MSWin32" ) ) {
		$string =~ s/$fat_bad//g;
	}
	# Remove HFS-unfriendly chars if --hfsfilename or OS X and not force default
	if ( ! $force_default && ( $opt->{hfsfilename} || $^O eq "darwin" ) ) {
		$string =~ s/$hfs_bad//g;
	}
	return $string;
}


# Generic
# Signal handler to clean up after a ctrl-c or kill
sub cleanup {
	my $signal = shift;
	logger "\nINFO: Cleaning up $0 (got signal $signal)\n"; # if $opt->{verbose};
	unlink $namedpipe;
	unlink $lockfile;
	# Execute default signal handler
	$SIGORIG{$signal}->() if ref($SIGORIG{$signal}) eq 'CODE';
	exit 1;
}


# Uses: global $lockfile
# Lock file detection (<stale_secs>)
# Global $lockfile
sub lockfile {
	my $stale_time = shift || 86400;
	my $now = time();
	# if lockfile exists then quit as we are already running
	if ( -T $lockfile ) {
		if ( ! open (LOCKFILE, $lockfile) ) {
			main::logger "ERROR: Cannot read lockfile '$lockfile'\n";
			exit 1;
		}
		my @lines = <LOCKFILE>;
		close LOCKFILE;

		# If the process is still running and the lockfile is newer than $stale_time seconds
		if ( kill(0,$lines[0]) > 0 && $now < ( stat($lockfile)->mtime + $stale_time ) ) {
				main::logger "ERROR: Quitting - process is already running ($lockfile)\n";
				# redefine cleanup sub so that it doesn't delete $lockfile
				$lockfile = '';
				exit 0;
		} else {
			main::logger "INFO: Removing stale lockfile\n" if $opt->{verbose};
			unlink ${lockfile};
		}
	}
	# write our PID into this lockfile
	if (! open (LOCKFILE, "> $lockfile") ) {
		main::logger "ERROR: Cannot write to lockfile '${lockfile}'\n";
		exit 1;
	}
	print LOCKFILE $$;
	close LOCKFILE;
	return 0;
}



sub expand_list {
	my $list = shift;
	my $search = shift;
	my $replace = shift;
	my @elements = split /,/, $list;
	for (@elements) {
		$_ = $replace if $_ eq $search;
	}
	return join ',', @elements;	
}



sub get_playlist_url {
	my $ua = shift;
	my $url = shift;
	my $filter = shift;
	# Don't recurse more than 5 times
	my $depth = 5;

	# Resolve the MMS url if it is an http ref
	while ( $url =~ /^http/i && $depth ) {
		my $content = main::request_url_retry($ua, $url, 2, '', '');
		# Reference list
		if ( $content =~ m{\[reference\]}i ) {
			my @urls;
			# [Reference]
			# Ref1=http://wm.bbc.co.uk/wms/england/radioberkshire/aod/andrewpeach_thu.wma?MSWMExt=.asf
			# Ref2=http://wm.bbc.co.uk/wms/england/radioberkshire/aod/andrewpeach_thu.wma?MSWMExt=.asf
			for ( split /ref\d*=/i, $content ) {
				#main::logger "DEBUG: LINE: $_\n" if $opt->{debug};
				s/[\s]//g;
				# Rename http:// to mms:// - don't really know why but this seems to be necessary with such playlists
				s|http://|mms://|g;
				push @urls, $_ if m{^(http|mms|rtsp)://};
				main::logger "DEBUG: Got Reference URL: $_\n" if $opt->{debug};
			}
			# use first URL for now??
			$url = $urls[0];

		# ASX XML based playlist
		} elsif ( $content =~ m{<asx}i ) {
			my @urls;
			# <ASX version="3.0">
			#  <ABSTRACT>http://www.bbc.co.uk/</ABSTRACT>
			#  <TITLE>BBC support</TITLE>
			#  <AUTHOR>BBC</AUTHOR>
			#  <COPYRIGHT>(c) British Broadcasting Corporation</COPYRIGHT>
			#  <MoreInfo href="http://www.bbc.co.uk/" />
			#  <Entry>
			#    <ref href="rtsp://wm.bbc.co.uk/wms/england/radioberkshire/aod/andrewpeach_thu.wma" />
			#    <ref href="http://wm.bbc.co.uk/wms/england/radioberkshire/aod/andrewpeach_thu.wma" />
			#    <ref href="rtsp://wm.bbc.co.uk/wms2/england/radioberkshire/aod/andrewpeach_thu.wma" />
			#    <ref href="http://wm.bbc.co.uk/wms2/england/radioberkshire/aod/andrewpeach_thu.wma" />
			#    <MoreInfo href="http://www.bbc.co.uk/" />
			#    <Abstract>BBC</Abstract>
			#  </Entry>
			# </ASX>
			for ( split /</i, $content ) {
				#main::logger "DEBUG: LINE: $_\n" if $opt->{debug};
				# Ignore anything except mms or http from this playlist
				push @urls, $1 if m{ref\s+href=\"((http|$filter)://.+?)\"}i;
			}
			for ( @urls ) {
				main::logger "DEBUG: Got ASX URL: $_\n" if $opt->{debug};
			}
			# use first URL for now??
			$url = $urls[0];

		# RAM format urls
		} elsif ( $content =~ m{rtsp://}i ) {
			my @urls;
			for ( split /[\n\r\s]/i, $content ) {
				main::logger "DEBUG: LINE: $_\n" if $opt->{debug};
				# Ignore anything except $filter or http from this playlist
				push @urls, $1 if m{((http|$filter)://.+?)[\n\r\s]?$}i;
			}
			for ( @urls ) {
				main::logger "DEBUG: Got RAM URL: $_\n" if $opt->{debug};
			}
			# use first URL for now??
			$url = $urls[0];			

		} else {	
			chomp( $url = $content );
		}
		$depth--;
	}

	return $url;
}



# Converts any number words (or numbers) 0 - 99 to a number
sub convert_words_to_number {
	my $text = shift;
	$text = lc($text);
	my $number = 0;
	# Regex for mnemonic numbers
	my %lookup_0_19 = qw(
		zero		0
		one		1
		two		2
		three		3
		four		4
		five		5
		six		6
		seven		7
		eight		8
		nine		9
		ten		10
		eleven		11
		twelve		12
		thirteen	13
		fourteen	14
		fifteen		15
		sixteen		16
		seventeen	17
		eighteen	18
		nineteen	19
	);
	my %lookup_tens = qw(
		twenty	20
		thirty	30
		forty 	40
		fifty	50
		sixty	60
		seventy	70
		eighty	80
		ninety	90
	);
	my $regex_units = '(zero|one|two|three|four|five|six|seven|eight|nine)';
	my $regex_ten_to_nineteen = '(ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen)';
	my $regex_tens = '(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)';
	my $regex_numbers = '(\d+|'.$regex_units.'|'.$regex_ten_to_nineteen.'|'.$regex_tens.'((\s+|\-|)'.$regex_units.')?)';
	#print "REGEX: $regex_numbers\n";
	#my $text = 'seventy two'
	$number += $text if $text =~ /^\d+$/;
	my $regex = $regex_numbers.'$';
	if ( $text =~ /$regex/ ) {
		# trailing zero -> nineteen
		$regex = '('.$regex_units.'|'.$regex_ten_to_nineteen.')$';
		$number += $lookup_0_19{ $1 } if $text =~ /($regex)/;
		# leading tens
		$regex = '^('.$regex_tens.')(\s+|\-|_||$)';
		$number += $lookup_tens{ $1 } if $text =~ /$regex/;
	}
	return $number;
}



# Returns a regex string that matches all number words (or numbers) 0 - 99
sub regex_numbers {
	my $regex_units = '(zero|one|two|three|four|five|six|seven|eight|nine)';
	my $regex_ten_to_nineteen = '(ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen)';
	my $regex_tens = '(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)';
	return '(\d+|'.$regex_units.'|'.$regex_ten_to_nineteen.'|'.$regex_tens.'((\s+|\-|)'.$regex_units.')?)';
}


sub default_encodinglocale {
	return 'UTF-8' if (${^UNICODE} & 32);
	return ($^O eq "MSWin32" ? 'cp1252' : 'UTF-8');
}


sub default_encodingconsoleout {
	return 'UTF-8' if (${^UNICODE} & 6);
	return ($^O eq "MSWin32" ? 'cp850' : 'UTF-8');
}


sub encode_fs {
	my $string = shift;
	return $string if $opt->{encodinglocalefs} =~ /UTF-?8/i;
	return encode($opt->{encodinglocalefs}, $string, FB_EMPTY);
}


############## OO ################

############## Options default class ################
package Options;

use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::stat;
use Getopt::Long;
use strict;

# Class vars
# Global options
my $opt_format_ref;
# Constructor
# Usage: $opt = Options->new( 'optname' => 'testing 123', 'myopt2' => 'myval2', <and so on> );
sub new {
	my $type = shift;
	my %params = @_;
	my $self = {};
	for (keys %params) {
		$self->{$_} = $params{$_};
	}
	bless $self, $type;
}


# Use to bind a new options ref to the class global $opt_format_ref var
sub add_opt_format_object {
	my $self = shift;
	$Options::opt_format_ref = shift;
}


# Parse cmdline opts using supplied hash
# If passthru flag is set then no error will result if there are unrecognised options etc
# Usage: $opt_cmdline->parse( [passthru] );
sub parse {
	my $this = shift;
	my $pass_thru = shift;
	my $opt_format_ref = $Options::opt_format_ref;
	# Build hash for passing to GetOptions module
	my %get_opts;

	for my $name ( grep !/^_/, keys %{$opt_format_ref} ) {
		my $format = @{ $opt_format_ref->{$name} }[1];
		$get_opts{ $format } = \$this->{$name};
	}

	# Allow bundling of single char options
	Getopt::Long::Configure("bundling");
	if ( $pass_thru ) {
		Getopt::Long::Configure("pass_through");
	} else {
		Getopt::Long::Configure("no_pass_through");
	}
	
	# cmdline opts take precedence
	# get options
	return GetOptions(%get_opts);
}



sub copyright_notice {
	shift;
	my $text = "get_iplayer $version_text, ";
	$text .= <<'EOF';
Copyright (C) 2008-2010 Phil Lewis
  This program comes with ABSOLUTELY NO WARRANTY; for details use --warranty.
  This is free software, and you are welcome to redistribute it under certain
  conditions; use --conditions for details.

EOF
	return $text;
}



# Usage: $opt_cmdline->usage( <helplevel>, <manpage>, <dump> );
sub usage {
	my $this = shift;
	# Help levels: 0:Intermediate, 1:Advanced, 2:Basic
	my $helplevel = shift;
	my $manpage = shift;
	my $dumpopts = shift;
	my $opt_format_ref = $Options::opt_format_ref;
	my %section_name;
	my %name_syntax;
	my %name_desc;
	my @usage;
	my @man;
	my @dump;
	push @man, 
		'.TH GET_IPLAYER "1" "June 2015" "Phil Lewis" "get_iplayer Manual"',
		'.SH NAME', 'get_iplayer - Stream Recording tool and PVR for BBC iPlayer, BBC Podcasts and more',
		'.SH SYNOPSIS',
		'\fBget_iplayer\fR [<options>] [<regex|index> ...]',
		'.PP',
		'\fBget_iplayer\fR \fB--get\fR [<options>] <regex|index> ...',
		'.br',
		'\fBget_iplayer\fR <url> \fB--type\fR=<type> [<options>]',
		'.PP',
		'\fBget_iplayer\fR <pid|url> [\fB--type\fR=<type> <options>]',
		'.PP',
		'\fBget_iplayer\fR \fB--stream\fR [<options>] <regex|index> | mplayer \fB-cache\fR 3072 -',
		'.PP',
		'\fBget_iplayer\fR \fB--stream\fR [<options>] \fB--type\fR=<type> <pid|url> | mplayer \fB-cache\fR 3072 -',
		'.PP',
		'\fBget_iplayer\fR \fB--stream\fR [<options>] \fB--type\fR=livetv,liveradio <regex|index> \fB--player\fR="mplayer -cache 128 -"',
		'.PP',
		'\fBget_iplayer\fR \fB--refresh\fR',
		'.SH DESCRIPTION',
		'\fBget_iplayer\fR lists, searches and records BBC iPlayer TV/Radio, BBC Podcast programmes. Other 3rd-Party plugins may be available.',
		'.PP',
		'\fBget_iplayer\fR has three modes: recording a complete programme for later playback, streaming a programme',
		'directly to a playback application, such as mplayer; and as a Personal Video Recorder (PVR), subscribing to',
		'search terms and recording programmes automatically. It can also stream or record live BBC iPlayer output',
		'.PP',
		'If given no arguments, \fBget_iplayer\fR updates and displays the list of currently available programmes.',
		'Each available programme has a numerical identifier, \fBpid\fR.',
		'\fBget_iplayer\fR utilises the \fBrtmpdump\fR tool to record BBC iPlayer programmes from RTMP flash streams at various qualities.',
		'.PP',
		'In PVR mode, \fBget_iplayer\fR can be called from cron to record programmes to a schedule.',
		'.SH "OPTIONS"' if $manpage;
	push @usage, 'Usage ( Also see https://github.com/get-iplayer/get_iplayer/wiki/documentation ):';
	push @usage, ' List All Programmes:            get_iplayer [--type=<TYPE>]';
	push @usage, ' Search Programmes:              get_iplayer <REGEX>';
	push @usage, ' Record Programmes by Search:    get_iplayer <REGEX> --get';
	push @usage, ' Record Programmes by Index:     get_iplayer <INDEX> --get';
	push @usage, ' Record Programmes by URL:       get_iplayer [--type=<TYPE>] "<URL>"';
	push @usage, ' Record Programmes by PID:       get_iplayer [--type=<TYPE>] --pid=<PID>';
	push @usage, ' Stream Programme to Player:     get_iplayer --stream <INDEX> | mplayer -cache 3072 -' if $helplevel == 1;
	push @usage, ' Stream BBC Embedded Media URL:  get_iplayer --stream --type=<TYPE> "<URL>" | mplayer -cache 128 -' if $helplevel != 2;
	push @usage, ' Stream Live iPlayer Programme:  get_iplayer --stream --type=livetv,liveradio <REGEX|INDEX> --player="mplayer -cache 128 -"' if $helplevel != 2;
	push @usage, '';
	push @usage, ' Update get_iplayer cache:       get_iplayer --refresh [--force]';
	push @usage, '';
	push @usage, ' Basic Help:                     get_iplayer --basic-help' if $helplevel != 2;
	push @usage, ' Intermediate Help:              get_iplayer --help' if $helplevel == 2;
	push @usage, ' Advanced Help:                  get_iplayer --long-help' if $helplevel != 1;

	for my $name (keys %{$opt_format_ref} ) {
		next if not $opt_format_ref->{$name};
		my ( $helpmask, $format, $section, $syntax, $desc ) = @{ $opt_format_ref->{$name} };
		# Skip advanced options if not req'd
		next if $helpmask == 1 && $helplevel != 1;
		# Skip internediate options if not req'd
		next if $helpmask != 2 && $helplevel == 2;
		push @{$section_name{$section}}, $name if $syntax;
		$name_syntax{$name} = $syntax;
		$name_desc{$name} = $desc;
	}

	# Build the help usage text
	# Each section
	for my $section ( 'Search', 'Display', 'Recording', 'Download', 'Output', 'PVR', 'Config', 'External Program', 'Tagging', 'Misc' ) {
		next if not defined $section_name{$section};
		my @lines;
		my @manlines;
		my @dumplines;
		#Runs the PVR using all saved PVR searches (intended to be run every hour from cron etc)
		push @man, ".SS \"$section Options:\"" if $manpage;
		push @dump, '', "$section Options:" if $dumpopts;
		push @usage, '', "$section Options:";
		# Each name in this section array
		for my $name ( sort @{ $section_name{$section} } ) {
			push @manlines, '.TP'."\n".'\fB'.$name_syntax{$name}."\n".$name_desc{$name} if $manpage;
			my $dumpname = $name;
			$dumpname =~ s/^_//g;
			push @dumplines, sprintf(" %-30s %-32s %s", $dumpname, $name_syntax{$name}, $name_desc{$name} ) if $dumpopts;
			push @lines, sprintf(" %-32s %s", $name_syntax{$name}, $name_desc{$name} );
		}
		push @usage, sort @lines;
		push @man, sort @manlines;
		push @dump, sort @dumplines;
	}

	# Create manpage
	if ( $manpage ) {
		push @man,
			'.SH AUTHOR',
			'get_iplayer was written by Phil Lewis <iplayer2 (at sign) linuxcentre.net> and is now maintained by the contributors at http://www.infradead.org/get_iplayer/html/get_iplayer.html',
			'.PP',
			'This manual page was originally written by Jonathan Wiltshire <jmw@debian.org> for the Debian project (but may be used by others).',
			'.SH COPYRIGHT NOTICE';
		push @man, Options->copyright_notice;
		# Escape '-'
		s/\-/\\-/g for @man;
		# Open manpage file and write contents
		if (! open (MAN, "> $manpage") ) {
			main::logger "ERROR: Cannot write to manpage file '$manpage'\n";
			exit 1;
		}
		print MAN join "\n", @man, "\n";
		close MAN;
		main::logger "INFO: Wrote manpage file '$manpage'\n";
		exit 0;

	# Print options dump and quit
	} elsif ( $dumpopts ) {
		main::logger join "\n", @dump, "\n";
	
	# Print usage and quit
	} else {
		main::logger join "\n", @usage, "\n";
	}

	exit 0;
}


# Add all the options into supplied hash from specified class
# Usage: Options->get_class_options( 'Programme:tv' );
sub get_class_options {
	shift;
	my $classname = shift;
	my $opt_format_ref = $Options::opt_format_ref;
	# If the method exists...
	eval { $classname->opt_format() };
	if ( ! $@ ) {
		my %tmpopt = %{ $classname->opt_format() };
		for my $thisopt ( keys %tmpopt ) {
			$opt_format_ref->{$thisopt} = $tmpopt{$thisopt}; 
		}	
	}
}


# Copies values in one instance to another only if they are set with a value/defined
# Usage: $opt->copy_set_options_from( $opt_cmdline );
sub copy_set_options_from {
	my $this_to = shift;
	my $this_from = shift;
	# Merge cmdline options into $opt instance (only those options defined)
	for ( keys %{$this_from} ) {
		$this_to->{$_} = $this_from->{$_} if defined $this_from->{$_};
	}
}



# specify regex of options that cannot be saved
sub excludeopts {
	return '^(encoding|silent|help|debug|get|pvr|prefs|preset|warranty|conditions)';
}


# List all available presets in the specified dir
sub preset_list {
	my $opt = shift;
	my $dir = shift;
	main::logger "INFO: Valid presets: ";
	if ( opendir( DIR, "${profile_dir}/presets/" ) ) {
		my @preset_list = grep !/(^\.|~$)/, readdir DIR;
		closedir DIR;
		main::logger join ',', @preset_list;
	}
	main::logger "\n";
}


# Clears all option entries for a particular preset (i.e. deletes the file)
sub clear {
	my $opt = shift;
	my $prefsfile = shift;
	$opt->show( $prefsfile );
	unlink $prefsfile;
	main::logger "INFO: Removed all above options from $prefsfile\n";
}


# $opt->add( $opt_cmdline, $optfile, @search_args )
# Add/change cmdline-only options to file
sub add {
	my $opt = shift;
	my $this_cmdline = shift;
	my $optfile = shift;
	my @search_args = @_;

	# Load opts file
	my $entry = get( $opt, $optfile );

	# Add search args to opts
	if ( defined $this_cmdline->{search} ) {
		push @search_args, $this_cmdline->{search};
	}
	$this_cmdline->{search} = '('.(join '|', @search_args).')' if @search_args;

	# Merge all cmdline opts into $entry except for these
	my $regex = $opt->excludeopts;
	for ( grep !/$regex/, keys %{ $this_cmdline } ) {
		# if this option is on the cmdline
		if ( defined $this_cmdline->{$_} ) {
			main::logger "INFO: Changed option '$_' from '$entry->{$_}' to '$this_cmdline->{$_}'\n" if defined $entry->{$_} && $this_cmdline->{$_} ne $entry->{$_};
			main::logger "INFO: Added option '$_' = '$this_cmdline->{$_}'\n" if not defined $entry->{$_};
			$entry->{$_} = $this_cmdline->{$_};
		}
	}

	# Save opts file
	put( $opt, $entry, $optfile );
}



# $opt->add( $opt_cmdline, $optfile )
# Add/change cmdline-only options to file
sub del {
	my $opt = shift;
	my $this_cmdline = shift;
	my $optfile = shift;
	my @search_args = @_;
	return 0 if ! -f $optfile;

	# Load opts file
	my $entry = get( $opt, $optfile );

	# Add search args to opts
	$this_cmdline->{search} = '('.(join '|', @search_args).')' if @search_args;

	# Merge all cmdline opts into $entry except for these
	my $regex = $opt->excludeopts;
	for ( grep !/$regex/, keys %{ $this_cmdline } ) {
		main::logger "INFO: Deleted option '$_' = '$entry->{$_}'\n" if defined $this_cmdline->{$_} && defined $entry->{$_};
		delete $entry->{$_} if defined $this_cmdline->{$_};
	}

	# Save opts file
	put( $opt, $entry, $optfile );
}



# $opt->show( $optfile )
# show options from file
sub show {
	my $opt = shift;
	my $optfile = shift;
	return 0 if ! -f $optfile;

	# Load opts file
	my $entry = get( $opt, $optfile );

	# Merge all cmdline opts into $entry except for these
	main::logger "Options in '$optfile'\n";
	my $regex = $opt->excludeopts;
	for ( keys %{ $entry } ) {
		main::logger "\t$_ = $entry->{$_}\n";
	}
}



# $opt->save( $opt_cmdline, $optfile )
# Save cmdline-only options to file
sub put {
	my $opt = shift;
	my $entry = shift;
	my $optfile = shift;

	unlink $optfile;
	main::logger "DEBUG: adding/changing options to $optfile:\n" if $opt->{debug};
	open (OPT, "> $optfile") || die ("ERROR: Cannot save options to $optfile\n");
	for ( keys %{ $entry } ) {
		if ( defined $entry->{$_} ) {
			print OPT "$_ $entry->{$_}\n";
			main::logger "DEBUG: Saving option $_ = $entry->{$_}\n" if $opt->{debug};
		}
	}
	close OPT;

	main::logger "INFO: Options file $optfile updated\n";
	return;
}



# Returns a hashref of 'optname => internal_opt_name' for all options
sub get_opt_map {
	my $opt_format_ref = $Options::opt_format_ref;

	# Get a hash or optname -> internal_opt_name
	my $optname;
	for my $optint ( keys %{ $opt_format_ref } ) {
		my $format = @{ $opt_format_ref->{$optint} }[1];
		#main::logger "INFO: Opt Format '$format'\n";
		$format =~ s/=.*$//g;
		# Parse each option format
		for ( split /\|/, $format ) {
			next if /^$/;
			#main::logger "INFO: Opt '$_' -> '$optint'\n";
			if ( defined $optname->{$_} ) {
				main::logger "ERROR: Duplicate Option defined '$_' -> '$optint' and '$optname->{$_}'\n";
				exit 11;
			}
			$optname->{$_} = $optint;
		}
	}
	for my $optint ( keys %{ $opt_format_ref } ) {
		$optname->{$optint} = $optint;
	}
	return $optname;
}


# $entry = get( $opt, $optfile )
# get all options from file into $entry ($opt is used just to get access to general options like debug)
sub get {
	my $opt = shift;
	my $optfile = shift;
	my $opt_format_ref = $Options::opt_format_ref;
	my $entry;
	return $entry if ( ! defined $optfile ) || ( ! -f $optfile );

	my $optname = get_opt_map();

	# Load opts
	main::logger "DEBUG: Parsing options from $optfile:\n" if $opt->{debug};
	my $opt_encoding = ( $^O eq "MSWin32" && $optfile eq $optfile_system ) ? $opt->{encodinglocalefs} : "utf8";
	open (OPT, "<:encoding($opt_encoding)",  $optfile) || die ("ERROR: Cannot read options file $optfile\n");
	while(<OPT>) {
		/^\s*([\w\-_]+)\s+(.*)\s*$/;
		next if not defined $1;
		# Error if the option is not valid
		if ( not defined $optname->{$1} ) {
			# Force error to go to STDERR (prevents PVR runs getting STDOUT warnings)
			$opt->{stderr} = 1;
			main::logger "WARNING: Ignoring invalid option in $optfile: '$1 = $2'\n";
			main::logger "INFO: Please remove and use 'get_iplayer --dump-options' to display all valid options\n";
			delete $opt->{stderr};
			next;
		}
		# Warn if it is listed as a deprecated internal option name
		if ( defined @{ $opt_format_ref->{$1} }[2] && @{ $opt_format_ref->{$1} }[2] eq 'Deprecated' ) {
			main::logger "WARNING: Deprecated option in $optfile: '$1 = $2'\n";
			main::logger "INFO: Use --dump-opts to display all valid options\n";
		}
		chomp( $entry->{ $optname->{$1} } = $2 );
		main::logger "DEBUG: Loaded option $1 ($optname->{$1}) = $2\n" if $opt->{debug};
	}
	close OPT;
	return $entry;
}



# $opt_file->load( $opt, $optfile )
# Load default options from file(s) into instance
sub load {
	my $this_file = shift;
	my $opt = shift;
	my @optfiles = ( @_ );

	# If multiple files are specified, load them in order listed
	for my $optfile ( @optfiles ) {
		# Load opts
		my $entry = get( $opt, $optfile );
		# Copy to $this_file instance
		$this_file->copy_set_options_from( $entry );
	}

	return;
}



# Usage: $opt_file->display( [<exclude regex>], [<title>] );
# Display options
sub display {
	my $this = shift;
	my $title = shift || 'Options';
	my $excluderegex = shift || 'ROGUEVALUE';
	my $regex = $this->excludeopts;
	main::logger "$title:\n";
	for ( sort keys %{$this} ) {
		if ( defined $this->{$_} && $this->{$_} ) {
			if ( ref($this->{$_}) eq 'ARRAY' ) {
				main::logger "\t$_ = ".(join(',', @{$this->{$_}}))."\n";
			} else {
				main::logger "\t$_ = $this->{$_}\n";
			}
		}
	}
	main::logger "\n";
	return 0;
}




########################################################

################ History default class #################
package History;

use Encode;
use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::stat;
use strict;

# Class vars
# Global options

# Constructor
# Usage: $hist = History->new();
sub new {
	my $type = shift;
	my %params = @_;
	my $self = {};
	for (keys %params) {
		$self->{$_} = $params{$_};
	}
	## Ensure the subclass $opt var is pointing to the Superclass global optref
	$opt = $History::optref;
	bless $self, $type;
}


# $opt->{<option>} access method
sub opt {
	my $self = shift;
	my $optname = shift;
	return $opt->{$optname};
}


# Use to bind a new options ref to the class global $opt_ref var
sub add_opt_object {
	my $self = shift;
	$History::optref = shift;
}


sub trim {
	my $oldhistoryfile = "$historyfile.old";
	my $newhistoryfile = "$historyfile.new";
	if ( $opt->{trimhistory} =~ /^all$/i ) {
		if ( ! copy($historyfile, $oldhistoryfile) ) {
			die "ERROR: Cannot copy $historyfile to $oldhistoryfile: $!\n";
		}
		if ( ! unlink($historyfile) ) {
			die "ERROR: Cannot delete $historyfile: $! \n";
		}
		main::logger "INFO: Deleted all entries from download history\n";
		return;
	}
	if ( $opt->{trimhistory} !~ /^\d+$/ ) {
		die "ERROR: --trim-history option must have a positive integer value, or use 'all' to completely delete download history.\n";
	}
	if ( $opt->{trimhistory} =~ /^0+$/ ) {
		die "ERROR: Cannot specify 0 for --trim-history option.  Use 'all' to completely delete download history.\n";
	}
	if ( ! open(HIST, "< $historyfile") ) {
		die "ERROR: Cannot read from $historyfile\n";
	}
	if ( ! open(NEWHIST, "> $newhistoryfile") ) {
		die "ERROR: Cannot write to $newhistoryfile\n";
	}
	my $trim_limit = time() - ($opt->{trimhistory} * 86400);
	my $deleted_count = 0;
	while (<HIST>) {
		chomp();
		next if /^[\#\s]/;
		my @record = split /\|/;
		my $timeadded = $record[4];
		if ( $timeadded >= $trim_limit ) {
			print NEWHIST "$_\n";
		} else {
			$deleted_count++;
		}
	}
	close HIST;
	close NEWHIST;
	if ( ! copy($historyfile, $oldhistoryfile) ) {
		die "ERROR: Cannot copy $historyfile to $oldhistoryfile: $!\n";
	}
	if ( ! move($newhistoryfile, $historyfile) ) {
		die "ERROR: Cannot move $newhistoryfile to $historyfile: $!\n";
	}
	main::logger "INFO: Deleted $deleted_count entries from download history\n";
}

# Uses global @history_format
# Adds prog to history file (with a timestamp) so that it is not rerecorded after deletion
sub add {
	my $hist = shift;
	my $prog = shift;

	# Only add if a pid is specified
	return 0 if ! $prog->{pid};
	# Don't add to history if nowrite is used
	return 0 if $opt->{nowrite};

	# Add to history
	if ( ! open(HIST, ">> $historyfile") ) {
		main::logger "ERROR: Cannot write or append to $historyfile\n";
		exit 11;
	}
	# Update timestamp
	$prog->{timeadded} = time();
	# Write each field into a line in the history file
	print HIST $prog->{$_}.'|' for @history_format;
	print HIST "\n";
	close HIST;

	# (re)load whole hist
	# Would be nicer to just add the entry to the history object but this is safer.
	$hist->load();

	return 0;
}



# Uses global @history_format
# returns, for all the pids in the history file, $history->{pid}->{key} = value
sub load {
	my $hist = shift;

	# Return if force option specified or stdout streaming only
	return 0 if ( $opt->{force} && ! $opt->{pid} ) || $opt->{stdout} || $opt->{nowrite};

	# clear first
	$hist->clear();

	main::logger "INFO: Loading recordings history\n" if $opt->{verbose};
	if ( ! open(HIST, "< $historyfile") ) {
		main::logger "WARNING: Cannot read $historyfile\n\n" if $opt->{verbose} && -f $historyfile;
		return 0;
	}

	# Slow. Needs to be faster
	while (<HIST>) {
		chomp();
		# Ignore comments
		next if /^[\#\s]/;
		# Populate %prog_old from cache
		# Get history line
		my @record = split /\|/;
		my $record_entries;
		# Update fields in %history hash for $pid
		for ( @history_format ) {
			$record_entries->{$_} = ( shift @record ) || '';
			if ( /^filename$/ ) {
				$record_entries->{$_} = main::encode_fs($record_entries->{$_});
			}
		}
		# Create new history entry
		if ( defined $hist->{ $record_entries->{pid} } ) {
 			main::logger "WARNING: duplicate pid $record_entries->{pid} in history\n" if $opt->{debug};
			# Append filename and modes - could be a multimode entry
			$hist->{ $record_entries->{pid} }->{mode} .= ','.$record_entries->{mode} if defined $record_entries->{mode};
			$hist->{ $record_entries->{pid} }->{filename} .= ','.$record_entries->{filename} if defined $record_entries->{filename};
			main::logger "DEBUG: Loaded and merged '$record_entries->{pid}' = '$record_entries->{name} - $record_entries->{episode}' from history\n" if $opt->{debug};
		} else {
			# workaround empty names
			#$record_entries->{name} = 'pid:'.$record_entries->{pid} if ! $record_entries->{name};
			$hist->{ $record_entries->{pid} } = History->new();
			$hist->{ $record_entries->{pid} } = $record_entries;
			main::logger "DEBUG: Loaded '$record_entries->{pid}' = '$record_entries->{name} - $record_entries->{episode}' from history\n" if $opt->{debug};
		}
	}
	close (HIST);
	return 0;
}



# Clear the history in %{$hist}
sub clear {
	my $hist = shift;
	# There is probably a faster way
	delete $hist->{$_} for keys %{ $pvr };
	return 0;
}



# Loads hist from file if required
sub conditional_load {
	my $hist = shift;

	# Load if empty
	if ( ! keys %{ $hist } ) {
		main::logger "INFO: Loaded history for first check.\n" if $opt->{verbose};
		$hist->load();
	}
	return 0;
}



# Returns a history pid instance ref
sub get_record {
	my $hist = shift;
	my $pid = shift;
	$hist->conditional_load();
	if ( defined $hist->{$pid} ) {
		return $hist->{$pid};
	}
	return undef;
}



# Returns a list of current history pids
sub get_pids {
	my $hist = shift;
	$hist->conditional_load();
	return keys %{ $hist };
}



# Lists current history items
# Requires a load()
sub list_progs {
	my $hist = shift;
	my $prog = {};
	my ( @search_args ) = ( @_ );

	# Load if empty
	$hist->conditional_load();

	# This is a 'well dirty' hack to allow all the Programme class methods to be used on the history objects
	# Basically involves copying all history objects into prog objects and then calling the required method

	# Sort index by timestamp
	my %index_hist;
	main::sort_index( $hist, \%index_hist, undef, 'timeadded' );

	for my $index ( sort {$a <=> $b} keys %index_hist ) {
		my $record = $index_hist{$index};
		my $progrec;
		if ( not main::is_prog_type( $record->{type} ) ) {
			main::logger "WARNING: Programme type '$record->{type}' does not exist - using generic class\n" if $opt->{debug};
			$progrec = Programme->new();
		} else {
			# instantiate a new Programme object and copy all metadata from this history object into it
			$progrec = main::progclass( $record->{type} )->new();
		}
		for my $key ( keys %{ $record } ) {
			$progrec->{$key} = $record->{$key};
		}
		$prog->{ $progrec->{pid} } = $progrec;
		# CAVEAT: The filename is comma-separated if there is a multimode download. For now just use the first one
		if ( $prog->{ $progrec->{pid} }->{mode} =~ /\w+,\w+/ ) {
			$prog->{ $progrec->{pid} }->{mode} =~ s/,.+$//g;
			$prog->{ $progrec->{pid} }->{filename} =~ s/,.+$//g;
		}
	}

	# Parse remaining args
	my @match_list;
	for ( @search_args ) {
		chomp();

		# If Numerical value < $max_index and the object exists from loaded prog types
		if ( /^[\d]+$/ && $_ <= $max_index ) {
			if ( defined $index_hist{$_} ) {
				main::logger "INFO: Search term '$_' is an Index value\n" if $opt->{verbose};
				push @match_list, $prog->{ $index_hist{$_}->{pid} };
			}

		# If PID then find matching programmes with 'pid:<pid>'
		} elsif ( m{^\s*pid:(.+?)\s*$}i ) {
			if ( defined $prog->{$1} ) {
				main::logger "INFO: Search term '$1' is a pid\n" if $opt->{verbose};
				push @match_list, $prog->{$1};
			} else {
				main::logger "INFO: Search term '$1' is a non-existent pid in the history\n";
			}

		# Else assume this is a programme name regex
		} else {
			main::logger "INFO: Search term '$_' is a substring\n" if $opt->{verbose};
			push @match_list, main::get_regex_matches( $prog, $_ );
		}
	}

	# force skipdeleted if --tagonly is specified
	$opt->{skipdeleted} = 1 if $opt->{tagonly};

	# Prune list of history entries with non-existant media files
	if ( $opt->{skipdeleted} ) {
		my @pruned = ();
		for my $this ( @match_list ) {
			# Skip if no filename in history
			if ( defined $this->{filename} && $this->{filename} ) {
				# Skip if the originally recorded file no longer exists
				if ( ! -f $this->{filename} ) {
					main::logger "DEBUG: Skipping metadata/thumbnail/tagging - file no longer exists: '$this->{filename}'\n" if $opt->{verbose};
				} else {
					push @pruned, $this;
				}
			}
		}
		@match_list = @pruned;
	}

	# De-dup matches and retain order then list matching programmes in history
	main::list_progs( undef, main::make_array_unique_ordered( @match_list ) );

	return 0;
}



# Generic
# Checks history for previous download of this pid
sub check {
	my $hist = shift;
	my $pid = shift;
	my $mode = shift;
	my $silent = shift;
	return 0 if ! $pid;

	# Return if force option specified or stdout streaming only
	return 0 if $opt->{force} || $opt->{stdout} || $opt->{nowrite};

	# Load if empty
	$hist->conditional_load();

	if ( defined $hist->{ $pid } ) {
		my ( $name, $episode, $histmode ) = ( $hist->{$pid}->{name}, $hist->{$pid}->{episode}, $hist->{$pid}->{mode} );
		main::main::logger "DEBUG: Found PID='$pid' with MODE='$histmode' in history\n" if $opt->{debug};
		if ( $opt->{multimode} ) {
			# Strip any number off the end of the mode names for the comparison
			$mode =~ s/\d+$//g;
			# Check against all modes in the comma separated list
			my @hmodes = split /,/, $histmode;
			for ( @hmodes ) {
				s/\d+$//g;
				if ( $mode eq $_ ) {
					main::logger "INFO: $name - $episode ($pid / $mode) Already in history ($historyfile) - use --force to override\n" if ! $silent;
					return 1;
				}
			}
		} else {
			main::logger "INFO: $name - $episode ($pid) Already in history ($historyfile) - use --force to override\n" if ! $silent;
			return 1;
		}
	}

	main::logger "INFO: Programme not in history\n" if $opt->{verbose} && ! $silent;
	return 0;
}




#################### Programme class ###################

package Programme;

use Encode;
use Env qw[@PATH];
use Fcntl;
use File::Basename;
use File::Copy;
use File::Path;
use File::Spec;
use File::stat;
use HTML::Entities;
use HTTP::Cookies;
use HTTP::Headers;
use IO::Seekable;
use IO::Socket;
use LWP::ConnCache;
use LWP::UserAgent;
use POSIX qw(mkfifo);
use strict;
use Time::Local;
use URI;
use Cwd 'abs_path';

# Class vars
# Global options
my $optref;
my $opt;
# File format
sub file_prefix_format { return '<name> - <episode> <pid> <version>' };
# index min/max
sub index_min { return 0 }
sub index_max { return 9999999 };
# Class cmdline Options
sub opt_format {
	return {
	};
}


# Filter channel names matched with options --refreshexclude/--refreshinclude
sub channels_filtered {
	my $prog = shift;
	my $channelsref = shift;
	# assume class method call
	(my $prog_type = $prog) =~ s/Programme:://;
	my $exclude = $opt->{'refreshexcludegroups'.$prog_type} || $opt->{'refreshexcludegroups'};
	if ( $prog_type eq "tv" ) {
		$exclude = "local" unless $exclude;
	}
	my %channels;
	for my $x ( qw(national regional local) ) {
		@channels{ keys %{$channelsref->{$x}} } = values %{$channelsref->{$x}} unless $exclude =~ /\b$x\b/;
	}
	# include/exclude matching channels as required
	my $include_regex = '.*';
	my $exclude_regex = '^ROGUEVALUE$';
	# Create a regex from any comma separated values
	$exclude_regex = '('.(join '|', ( split /,/, $opt->{refreshexclude} ) ).')' if $opt->{refreshexclude};
	$include_regex = '('.(join '|', ( split /,/, $opt->{refreshinclude} ) ).')' if $opt->{refreshinclude};
	for my $channel ( keys %channels ) {
		if ( $channels{$channel} !~ /$exclude_regex/i && $channels{$channel} =~ /$include_regex/i ) {
			main::logger "INFO: Will refresh channel $channels{$channel}\n" if $opt->{verbose};
		} else {
			delete $channels{$channel};
		}
	}
	return \%channels;
}


sub channels {
	return {};
}


sub channels_schedule {
        return {};
}


# Method to return optional list_entry format
sub optional_list_entry_format {
	my $prog = shift;
	return '';
}


# Returns the modes to try for this prog type
sub modelist {
	return '';
}


# Default minimum expected download size for a programme type
sub min_download_size {
	return 1024000;
}


# Default cache expiry in seconds
sub expiry {
	return 14400;
}


# Constructor
# Usage: $prog{$pid} = Programme->new( 'pid' => $pid, 'name' => $name, <and so on> );
sub new {
	my $type = shift;
	my %params = @_;
	my $self = {};
	for (keys %params) {
		$self->{$_} = $params{$_};
	}
	## Ensure that all instances reference the same class global $optref var
	# $self->{optref} = $Programme::optref;
	# Ensure the subclass $opt var is pointing to the Superclass global optref
	$opt = $Programme::optref;
	bless $self, $type;
}


# Use to bind a new options ref to the class global $optref var
sub add_opt_object {
	my $self = shift;
	$Programme::optref = shift;
}


# $opt->{<option>} access method
sub opt {
	my $self = shift;
	my $optname = shift;
	return $opt->{$optname};

	#return $Programme::optref->{$optname};	
	#my $opt = $self->{optref};
	#return $self->{optref}->{$optname};
}


# Cleans up a pid and removes url parts that might be specified
sub clean_pid {
}


# This gets run before the download retry loop if this class type is selected
sub init {
}


# Create dir if it does not exist
sub create_dir {
	my $prog = shift;
	if ( (! -d "$prog->{dir}") && (! $opt->{test}) ) {
		main::logger "INFO: Creating dir '$prog->{dir}'\n" if $opt->{verbose};
		eval { mkpath("$prog->{dir}") };
		if ( $@ ) {
			main::logger "ERROR: Could not create dir '$prog->{dir}': $@";
			exit 1;
		}
	}
}


# Return metadata of the prog
sub get_metadata {
	my $prog = shift;
	my $ua = shift;
	$prog->{modes}->{default} = $prog->modelist();
	if ( keys %{ $prog->{verpids} } == 0 ) {
		if ( $prog->get_verpids( $ua ) ) {
			main::logger "ERROR: Could not get version pid metadata\n" if $opt->{verbose};
			return 1;
		}
	}
	$prog->{versions} = join ',', sort keys %{ $prog->{verpids} };
	return 0;
}


# Return metadata which is generic such as time and date
sub get_metadata_general {
	my $prog = shift;
	my @t;

	# Special case for history mode, use {timeadded} to generate these two fields as this represents the time of recording
	if ( $opt->{history} && $prog->{timeadded} ) {
		@t = localtime( $prog->{timeadded} );

	# Else use current time
	} else {
		@t = localtime();
	}

	#($second, $minute, $hour, $dayOfMonth, $month, $yearOffset, $dayOfWeek, $dayOfYear, $daylightSavings) = localtime();
	$prog->{dldate} = sprintf "%02s-%02s-%02s", $t[5] + 1900, $t[4] + 1, $t[3];
	$prog->{dltime} = sprintf "%02s:%02s:%02s", $t[2], $t[1], $t[0];

	return 0;
}


# Displays specified metadata from supplied object
# Usage: $prog->display_metadata( <array of elements to display> )
sub display_metadata {
	my %data = %{$_[0]};
	shift;
	my @keys = @_;
	@keys = keys %data if $#_ < 0;
	main::logger "\n";
	for (@keys) {
		# Format timeadded field nicely
		if ( /^timeadded$/ ) {
			if ( $data{$_} ) {
				my @t = gmtime( time() - $data{$_} );
				main::logger sprintf "%-15s %s\n", $_.':', "$t[7] days $t[2] hours ago ($data{$_})";
			}
		# Streams data
		} elsif ( /^streams$/ ) {
			# skip these
		# If hash then list keys
		} elsif ( ref$data{$_} eq 'HASH' ) {
			for my $key ( sort keys %{$data{$_}} ) {
				main::logger sprintf "%-15s ", $_.':';
				if ( ref$data{$_}->{$key} ne 'HASH' ) {
					main::logger "$key: $data{$_}->{$key}";
				# This is the same as 'modes' list
				#} else {
				#	main::logger "$key: ".(join ',', sort keys %{ $data{$_}->{$key} } );
				}
				main::logger "\n";
			}
		} elsif ( /^desclong$/ ) {
			# strip line breaks
			if ( $data{$_} ) {
				(my $data_out = $data{$_}) =~ s|[\n\r]| |g;
				main::logger sprintf "%-15s %s\n", $_.':', $data_out;
			}
		# else just print out key value pair
		} else {
			main::logger sprintf "%-15s %s\n", $_.':', $data{$_} if $data{$_};		
		}
	}
	main::logger "\n";
	return 0;
}



# Return a list of episode pids from the given contents page/pid
sub get_pids_recursive {
	my $prog = shift;
	return '';
}



# Return hash of version => verpid given a pid
# Also put verpids in $prog->{verpids}->{<version>} = <verpid>
sub get_verpids {
	my $prog = shift;
	$prog->{verpids}->{'default'} = 1;
	return 0;
}



# Download Subtitles, convert to srt(SubRip) format and apply time offset
sub download_subtitles {
	# return failed...
	return 1;
}


sub default_version_list {
	return qw/ default original iplayer technical editorial lengthened shortened opensubtitles other signed audiodescribed /;
}


# Usage: generate_version_list ($prog)
# Returns sorted array of versions
sub generate_version_list {
	my $prog = shift;
	
	# Default Order with which to search for programme versions (can be overridden by --versionlist option)
	my @version_search_order = default_version_list();
	@version_search_order = split /,/, $opt->{versionlist} if $opt->{versionlist};

	# check here for no matching verpids for specified version search list???
	my $got = 0;
	my @version_list;
	for my $version ( @version_search_order ) {
		if ( defined $prog->{verpids}->{$version} ) {
			$got++;
			push @version_list, $version;
		}
	}

	if ( $got == 0 ) {
		main::logger "INFO: No versions of this programme were selected (available versions: ".(join ',', sort keys %{ $prog->{verpids} }).")\n";
	} else {
		main::logger "INFO: Will search for versions: ".(join ',', @version_list)."\n" if $opt->{verbose};
	}
	return @version_list;
}



# Retry the recording of a programme
# Usage: download_retry_loop ( $prog )
sub download_retry_loop {
	my $prog = shift;
	my $hist = shift;

	# Run the type init
	$prog->init();

	# If already downloaded then return (unless its for multimode)
	return 0 if ( ! $opt->{multimode} ) && $hist->check( $prog->{pid} );

	# Skip and warn if there is no pid
	if ( ! $prog->{pid} ) {
		main::logger "ERROR: No PID for index $_ (try using --type option ?)\n";
		return 1;
	}

	# Setup user-agent
	my $ua = main::create_ua( 'desktop' );

	# This pre-gets all the metadata - necessary to avoid get_verpids() below if possible
	$prog->get_metadata_general();
	if ( $prog->get_metadata( $ua ) ) {
		main::logger "ERROR: Could not get programme metadata\n" if $opt->{verbose};
		return 1;
	}

	# Look up version pids for this prog - this does nothing if above get_metadata has alredy completed
	if ( keys %{ $prog->{verpids} } == 0 ) {
		if ( $prog->get_verpids( $ua ) ) {
			main::logger "ERROR: Could not get version pid metadata\n" if $opt->{verbose};
			return 1;
		}
	}

	# Re-check history because get_verpids() can update the pid (e.g. BBC /programmes/ URLs)
	return 0 if ( ! $opt->{multimode} ) && $hist->check( $prog->{pid} );

	# if %{ $prog->{verpids} } is empty then skip this programme recording attempt
	if ( (keys %{ $prog->{verpids} }) == 0 ) {
		main::logger "INFO: No versions exist for this programme\n";
		return 1;
	}


	my @version_search_list = $prog->generate_version_list;
	return 1 if $#version_search_list < 0;

	# Get all possible (or user overridden) modes for this prog recording
	my $modelist = $prog->modelist;
	main::logger "INFO: Mode list: $modelist\n" if $opt->{verbose};

	######## version loop #######
	# Do this for each version tried in this order (if they appeared in the content)
	for my $version ( @version_search_list ) {
		my $retcode = 1;
		main::logger "DEBUG: Trying version '$version'\n" if $opt->{debug};
		if ( $prog->{verpids}->{$version} ) {
			main::logger "INFO: Checking existence of $version version\n";
			$prog->{version} = $version;
			main::logger "INFO: Version = $prog->{version}\n" if $opt->{verbose};

			# Try to get stream data for this version if not already populated
			if ( not defined $prog->{streams}->{$version} ) {
				$prog->{streams}->{$version} = $prog->get_stream_data( $prog->{verpids}->{$version} );
			}

			########## mode loop ########
			# record prog depending on the prog type

			# only use modes that exist
			my @modes;
			my @available_modes = sort keys %{ $prog->{streams}->{$version} };
			for my $modename ( split /,/, $modelist ) {
				# find all numbered modes starting with this modename
				push @modes, sort { $a cmp $b } grep /^$modename(\d+)?$/, @available_modes;
			}

			# Check for no applicable modes - report which ones are available if none are specified
			if ($#modes < 0) {
				my %available_modes_short;
				# Strip the number from the end of the mode name and make a unique array
				for ( @available_modes ) {
					my $modename = $_;
					$modename =~ s/\d+$//g;
					$available_modes_short{$modename}++;
				}
				main::logger "INFO: No specified modes ($modelist) available for this programme with version '$version'\n";
				main::logger "INFO: Try using --modes=".(join ',', sort keys %available_modes_short)."\n";
				main::logger "INFO: You may receive this message if you are using get_iplayer outside the UK\n" if $#available_modes < 0;
				next;
			}
			main::logger "INFO: ".join(',', @modes)." modes will be tried for version $version\n";

			# Expand the modes into a loop
			for my $mode ( @modes ) {
				chomp( $mode );
				(my $modeshort = $mode) =~ s/\d+$//g;
				# force regeneration of file name if mode changed
				if ( $prog->{modeshort} ne $modeshort ) {
					undef $prog->{filename};
					main::logger "INFO: Regenerate filename for mode change: $prog->{modeshort} -> $modeshort\n" if ( $prog->{modeshort} && $opt->{verbose} );
				}
				$prog->{mode} = $mode;
				# Keep short mode name for substitutions
				$prog->{modeshort} = $modeshort;

				# If multimode is used, skip only modes which are in the history
				next if $opt->{multimode} && $hist->check( $prog->{pid}, $mode );

				main::logger "INFO: Trying $mode mode to record $prog->{type}: $prog->{name} - $prog->{episode}\n";

				# try the recording for this mode (rtn==0 -> success, rtn==1 -> next mode, rtn==2 -> next prog)
				$retcode = mode_ver_download_retry_loop( $prog, $hist, $ua, $mode, $version, $prog->{verpids}->{$version} );
				main::logger "DEBUG: mode_ver_download_retry_loop retcode = $retcode\n" if $opt->{debug};

				# quit if successful or skip (unless --multimode selected)
				last if ( $retcode == 0 || $retcode == 2 ) && ! $opt->{multimode};
			}
		}
		# Break out of loop if we have a successful recording for this version and mode
		return 0 if not $retcode;
	}

	if (! $opt->{test}) {
		main::logger "ERROR: Failed to record '$prog->{name} - $prog->{episode} ($prog->{pid})'\n";
	}
	return 1;
}



# returns 1 on fail, 0 on success
sub mode_ver_download_retry_loop {
	my ( $prog, $hist, $ua, $mode, $version, $version_pid ) = ( @_ );
	my $retries = $opt->{attempts} || 3;
	my $count = 0;
	my $retcode;

	# Use different number of retries for flash modes
	$retries = $opt->{attempts} || 50 if $mode =~ /^flash/;

	# Retry loop
	for ($count = 1; $count <= $retries; $count++) {
		main::logger "INFO: Attempt number: $count / $retries\n" if $opt->{verbose};

		# for live streams update <dldate> and <dltime> for each download attempt
		# creates new output file if <dldate> or <dltime> in <fileprefix>
		if ( $prog->{type} =~ /live/ ) {
			my @t = localtime();
			$prog->{dldate} = sprintf "%02s-%02s-%02s", $t[5] + 1900, $t[4] + 1, $t[3];
			$prog->{dltime} = sprintf "%02s:%02s:%02s", $t[2], $t[1], $t[0];					
		}
		$retcode = $prog->download( $ua, $mode, $version, $version_pid );
		main::logger "DEBUG: Record using $mode mode return code: '$retcode'\n" if $opt->{verbose};

		# Exit
		if ( $retcode eq 'abort' ) {
			main::logger "ERROR: aborting get_iplayer\n";
			exit 1;

		# Try Next prog
		} elsif ( $retcode eq 'skip' ) {
			main::logger "INFO: skipping this programme\n";
			return 2;

		# Try Next mode
		} elsif ( $retcode eq 'next' ) {
			# break out of this retry loop
			main::logger "INFO: skipping $mode mode\n";
			last;

		# Success
		} elsif ( $retcode eq '0' ) {
			# No need to do all these post-tasks if its streaming-only
			if ( $opt->{stdout} ) {
				# Run user command if streaming-only or a stream was writtem
				$prog->run_user_command( $opt->{command} ) if $opt->{command};
				# Skip
			} else {
				# Add to history, tag file, and run post-record command if a stream was written
				main::logger "\n";
				if ( $opt->{thumb} ) {
					$prog->create_dir();
					$prog->download_thumbnail();
				}
				if ( $opt->{metadata} ) {
					$prog->create_dir();
					$prog->create_metadata_file();
				}
				if ( ! $opt->{nowrite} ) {
					$hist->add( $prog );
					$prog->tag_file if ! $opt->{notag} && ! $opt->{raw};
				} elsif ( $opt->{tagonly} ) {
					$prog->tag_file;
				}
				if ( $opt->{command} && ! $opt->{nowrite} ) {
					$prog->run_user_command( $opt->{command} );
				}
			}
			$prog->report() if $opt->{pvr};
			return 0;

		# Retry this mode
		} elsif ( $retcode eq 'retry' && $count < $retries ) {
			main::logger "WARNING: Retry recording for '$prog->{name} - $prog->{episode} ($prog->{pid})'\n";
			# Try to get stream data for this version/mode - retries require new auth data
			$prog->{streams}->{$version} = $prog->get_stream_data( $version_pid );
		}
	}
	return 1;
}



# Send a message to STDOUT so that cron can use this to email 
sub report {
	my $prog = shift;
	print STDOUT "New $prog->{type} programme: '$prog->{name} - $prog->{episode}', '$prog->{desc}'\n";
	return 0;
}



# create metadata for tagging
sub tag_metadata {
	my $prog = shift;
	my $meta;
	while ( my ($key, $val) = each %{$prog} ) {
		if ( ref($val) eq 'HASH' ) {
			$meta->{$key} = $prog->{$key}->{$prog->{version}};
		} else {
			$meta->{$key} = $val;
		}
	}
	return $meta;
}

# add metadata tags to file
sub tag_file {
	my $prog = shift;
	# return if file does not exist
	return if ! -f $prog->{filename};
	# download thumbnail if necessary
	$prog->download_thumbnail if ( ! -f $prog->{thumbfile} && ! $opt->{noartwork} );
	# create metadata
	my $meta = $prog->tag_metadata;
	# tag file
	my $tagger = Tagger->new();
	$tagger->tag_file($meta);
	# clean up thumbnail if necessary
	unlink $prog->{thumbfile} if ! $opt->{thumb};
}



# Create a metadata file if required
sub create_metadata_file {
	my $prog = shift;
	my $template;
	my $filename;

	# XML template for XBMC/Kodi movies - Ref: http://xbmc.org/wiki/?title=Import_-_Export_Library#Movies
	$filename->{xbmc_movie} = "$prog->{dir}/$prog->{fileprefix}.nfo";
	($template->{xbmc_movie} = <<'	XBMC_MOVIE') =~ s/^\s{2}//gm;
		<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
		<movie>
			<title>[name]</title>
			<plot>[desclong]</plot>
			<outline>[descmedium]</outline>
			<tagline>[descshort]</tagline>
			<thumb>[thumbnail]</thumb>
			<genre>[categories]</genre>
			<id>[pid]</id>
		</movie>
	XBMC_MOVIE
	$filename->{kodi_movie} = $filename->{xbmc_movie};
	$template->{kodi_movie} = $template->{xbmc_movie};

	# XML template for XBMC - Ref: http://xbmc.org/wiki/?title=Import_-_Export_Library#TV_Episodes
	$filename->{xbmc} = "$prog->{dir}/$prog->{fileprefix}.nfo";
	($template->{xbmc} = <<'	XBMC') =~ s/^\s{2}//gm;
		<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
		<episodedetails>
			<title>[episodeshort]</title>
			<plot>[desclong]</plot>
			<thumb>[thumbnail]</thumb>
			<aired>[lastbcastdate]</aired>
			<season>[seriesnum]</season>
			<episode>[episodenum]</episode>
			<studio>[channel]</studio>
			<genre>[categories]</genre>
			<id>[pid]</id>
		</episodedetails>
	XBMC
	$filename->{kodi} = $filename->{xbmc};
	$template->{kodi} = $template->{xbmc};

	# XML template for Freevo - Ref: http://doc.freevo.org/MovieFxd
	$filename->{freevo} = "$prog->{dir}/$prog->{fileprefix}.fxd";
	$template->{freevo} = '<?xml version="1.0" ?>
	<freevo>
		<FREEVOTYPE title="[longname]">
			<video>
				<file id="f1">[fileprefix].[ext]</file>
			</video>
			<info>
				<rating></rating>
				<userdate>[dldate] [dltime]</userdate>
				<plot>[desclong]</plot>
				<tagline>[episode]</tagline>
				<year>[firstbcast]</year>
				<genre>[categories]</genre>
				<runtime>[runtime] minutes</runtime>
				<channel>[channel]</channel>
			</info>
		</FREEVOTYPE>
	</freevo>
	';

	# Generic XML template for all info
	$filename->{generic} = "$prog->{dir}/$prog->{fileprefix}.xml";
	$template->{generic}  = '<?xml version="1.0" encoding="UTF-8" ?>'."\n";
	$template->{generic} .= '<program_meta_data xmlns="http://linuxcentre.net/xmlstuff/get_iplayer" revision="1">'."\n";
	$template->{generic} .= "\t<$_>[$_]</$_>\n" for ( sort keys %{$prog} );
	$template->{generic} .= "</program_meta_data>\n";

	return if ! -d $prog->{dir};
	if ( not defined $template->{ $opt->{metadata} } ) {
		main::logger "WARNING: metadata type '$opt->{metadata}' is not valid - must be one of ".(join ',', keys %{$template} )."\n";
		return;
	}

	main::logger "INFO: Writing $opt->{metadata} metadata to file '$filename->{ $opt->{metadata} }'\n";

	if ( open(XML, "> $filename->{ $opt->{metadata} }") ) {
		my $text = $prog->substitute( $template->{ $opt->{metadata} }, 3, '\[', '\]' );
		# Strip out unsubstituted tags
		$text =~ s/<.+?>\[.+?\]<.+?>[\s\n\r]*//g;
		# Hack: substitute here because freevo needs either <audio> or <movie> depending on filetype
		if ( $opt->{metadata} eq 'freevo' ) {
			if ( $prog->{type} =~ /radio/i ) {
				$text =~ s/FREEVOTYPE/audio/g;
			} else {
				$text =~ s/FREEVOTYPE/movie/g;
			}
		}
		if ( $opt->{metadata} =~ /(xbmc|kodi)/ ) {
			my $cats = $1 if $text =~ /<genre>(.+?)<\/genre>/;
			if ( $cats ) {
				$cats =~ s/,/<\/genre><genre>/g;
				$text =~ s/<genre>.+?<\/genre>/<genre>$cats<\/genre>/;
			}
		}
		print XML $text;
		close XML;
	} else {
		main::logger "WARNING: Couldn't write to metadata file '$filename->{ $opt->{metadata} }'\n";
	}
}



# Usage: print $prog{$pid}->substitute('<name>-<pid>-<episode>', [mode], [begin regex tag], [end regex tag]);
# Return a string with formatting fields substituted for a given pid
# sanitize_mode == 0 then sanitize final string and also sanitize '/' in field values
# sanitize_mode == 1 then sanitize final string but don't sanitize '/' (and '\' on Windows) in field values
# sanitize_mode == 2 then just substitute only
# sanitize_mode == 3 then substitute then use encode entities for fields only
# sanitize_mode == 4 then substitute then escape characters in fields only for use in double-quoted shell text.
#
# Also if it find a HASH type then the $prog->{<version>} element is searched and used
# Likewise, if a ARRAY type is found, elements are joined with commas
sub substitute {
	my ( $self, $string, $sanitize_mode, $tag_begin, $tag_end ) = ( @_ );
	$sanitize_mode = 0 if not defined $sanitize_mode;
	$tag_begin = '\<' if not defined $tag_begin;
	$tag_end = '\>' if not defined $tag_end;
	my $version = $self->{version} || 'unknown';
	my $replace = '';

	# Make 'duration' == 'length' for the selected version
	$self->{duration} = $self->{durations}->{$version} if $self->{durations}->{$version};
	$self->{runtime} = int($self->{duration} / 60);

	# Tokenize and substitute $format
	for my $key ( keys %{$self} ) {

		my $value = $self->{$key};

		# Get version specific value if this key is a hash
		if ( ref$value eq 'HASH' ) {
			if ( ref$value->{$version} ne 'HASH' ) {
				$value = $value->{$version};
			} else {
				$value = 'unprintable';
			}
		}

		# Join array elements if value is ARRAY type
		if ( ref$value eq 'ARRAY' ) {
			$value = join ',', @{ $value };
		}

		$value = '' if not defined $value;
		main::logger "DEBUG: Substitute ($version): '$key' => '$value'\n" if $opt->{debug};
		# Remove/replace all non-nice-filename chars if required
		# Keep '/' (and '\' on Windows) if $sanitize_mode == 1
		if ($sanitize_mode == 0 || $sanitize_mode == 1) {
			$replace = StringUtils::sanitize_path( $value, $sanitize_mode );
		# html entity encode
		} elsif ($sanitize_mode == 3) {
			$replace = encode_entities( $value, '&<>"\'' );
		# escape these chars: ! ` \ "
		} elsif ($sanitize_mode == 4) {
			$replace = $value;
			# Don't escape file paths
			if ( $key !~ /(filename|filepart|thumbfile)/ ) {
				$replace =~ s/([\!"\\`])/\\$1/g;
			}
		} else {
			$replace = $value;
		}
		# special handling for <episode*>
		$replace = '' if $replace eq '-' && $key =~ /episode/i;
		# look for prefix in tag
		my $pfx_key = $tag_begin.'([^A-Za-z1-9'.$tag_end.']*?)(0*?)'.$key.$tag_end;
		my ($prefix, $pad) = $string =~ m/$pfx_key/;
		if ( $replace =~ m/^\d+$/ && length($pad) > length($replace) ) {
			$replace = substr($pad.$replace, -length($pad))
		}
		$pfx_key = $tag_begin."\Q$prefix$pad\E".$key.$tag_end;
		$prefix = '' if ! $replace;
		$string =~ s|$pfx_key|$prefix$replace|gi;
	}

	if ( $sanitize_mode == 0 || $sanitize_mode == 1 ) {
		# Remove unused tags
		my $key = $tag_begin.'.*?'.$tag_end;
		$string =~ s|$key||mg;
		# Replace whitespace with _ unless --whitespace
		$string =~ s/\s/_/g unless $opt->{whitespace};
	}
	return $string;
}

	

# Determine the correct filenames for a recording
# Sets the various filenames and creates appropriate directories
# Gets more programme metadata if the prog name does not exist
#
# Uses:
#	$opt->{fileprefix}
#	$opt->{subdir}
#	$opt->{whitespace}
#	$opt->{test}
# Requires: 
#	$prog->{dir}
# Sets: 
#	$prog->{fileprefix}
#	$prog->{filename}
#	$prog->{filepart}
#	$prog->{symlink}
# Returns 0 on success, 1 on failure (i.e. if the <filename> already exists)
#
sub generate_filenames {
	my ($prog, $ua, $format, $multipart) = (@_);

	# Get and set more meta data - Set the %prog values from metadata if they aren't already set (i.e. with --pid option)
	if ( ! $prog->{name} ) {
		if ( $prog->get_metadata( $ua ) ) {
			main::logger "ERROR: Could not get programme metadata\n" if $opt->{verbose};
			return 1;
		}
		$prog->get_metadata_general();
	}

	# Create symlink filename if required
	# do first before <dir> or <fileprefix> are encoded
	if ( $opt->{symlink} ) {
		# Substitute the fields for the pid
		$prog->{symlink} = $prog->substitute( $opt->{symlink}, 1 );
		$prog->{symlink} = main::encode_fs($prog->{symlink});
		main::logger("INFO: Symlink file name will be '$prog->{symlink}'\n") if $opt->{verbose};
		# remove old symlink
		unlink $prog->{symlink} if -l $prog->{symlink} && ! $opt->{test};
	}

	# Determine directory and find its absolute path
	$prog->{dir} = File::Spec->rel2abs( $opt->{ 'output'.$prog->{type} } || $opt->{output} || $ENV{IPLAYER_OUTDIR} || '.' );
	$prog->{dir} = main::encode_fs($prog->{dir});
	
	# Add modename to default format string if multimode option is used
	$format .= ' <mode>' if $opt->{multimode};

	$prog->{fileprefix} = $opt->{fileprefix} || $format;

	# get $name, $episode from title
	my ( $name, $episode ) = Programme::bbciplayer::split_title( $prog->{title} ) if $prog->{title};
	$prog->{name} = $name if $name && ! $prog->{name};
	$prog->{episode} = $episode if $episode && ! $prog->{episode};

	# store the name extracted from the title metadata in <longname> else just use the <name> field
	$prog->{longname} = $prog->{name} || $name;

	# Set some common metadata fallbacks
	$prog->{nameshort} = $prog->{name} if ! $prog->{nameshort};
	$prog->{episodeshort} = $prog->{episode} if ! $prog->{episodeshort};

	# Create descmedium, descshort by truncation of desc if they don't already exist
	$prog->{descmedium} = substr( $prog->{desc}, 0, 1024 ) if ! $prog->{descmedium};
	$prog->{descshort} = substr( $prog->{desc}, 0, 255 ) if ! $prog->{descshort};

	# substitute fields and sanitize $prog->{fileprefix}
	main::logger "DEBUG: Substituted '$prog->{fileprefix}' as " if $opt->{debug};
	# Don't allow <mode> in fileprefix as it can break when resumes fallback on differently numbered modes of the same type change for <modeshort>
	$prog->{fileprefix} =~ s/<mode>/<modeshort>/g;
	$prog->{fileprefix} = $prog->substitute( $prog->{fileprefix} );
	$prog->{fileprefix} = main::encode_fs($prog->{fileprefix});

	# Truncate filename to 240 chars (allows for extra stuff to keep it under system 256 limit)
	$prog->{fileprefix} = substr( $prog->{fileprefix}, 0, 240 );

	# Change the date in the filename to ISO8601 format if required
	$prog->{fileprefix} =~ s|(\d\d)[/_](\d\d)[/_](20\d\d)|$3-$2-$1|g if $opt->{isodate};
	main::logger "'$prog->{fileprefix}'\n" if $opt->{debug};

	# Special case for history mode, parse the fileprefix and dir from filename if it is already defined
	if ( $opt->{history} && defined $prog->{filename} && $prog->{filename} ne '' ) {
		( $prog->{fileprefix}, $prog->{dir}, $prog->{ext} ) = fileparse($prog->{filename}, qr/\.[^.]*/);
		# Fix up file path components
		$prog->{ext} =~ s/\.//;
		$prog->{dir} = File::Spec->canonpath($prog->{dir});
		$prog->{filename} = File::Spec->catfile($prog->{dir}, "$prog->{fileprefix}.$prog->{ext}");
	}

	# Don't create subdir if we are only testing recordings
	# Create a subdir for programme sorting option
	if ( $opt->{subdir} ) {
		my $subdir = $prog->substitute( $opt->{subdirformat} || '<longname>', 1 );
		if ( $opt->{isodate} ) {
			$subdir =~ s|(\d\d)[/_](\d\d)[/_](20\d\d)|$3-$2-$1|g;
		} else {
			$subdir =~ s|(\d\d)[/](\d\d)[/](20\d\d)|$1_$2_$3|g;
		}
		$prog->{dir} = File::Spec->catdir($prog->{dir}, $subdir);
		$prog->{dir} = main::encode_fs($prog->{dir});
		main::logger("INFO: Creating subdirectory $prog->{dir} for programme\n") if $opt->{verbose};
	}

	# Create a subdir if there are multiple parts
	if ( $multipart ) {
		$prog->{dir} = File::Spec->catdir($prog->{dir}, $prog->{fileprefix});
		$prog->{dir} = main::encode_fs($prog->{dir});
		main::logger("INFO: Creating multi-part subdirectory $prog->{dir} for programme\n") if $opt->{verbose};
	}

	main::logger("\rINFO: File name prefix = $prog->{fileprefix}                 \n");

	# Use a dummy file ext if one isn't set - helps with readability of metadata
	$prog->{ext} = 'EXT' if ! $prog->{ext};
	
	# check if file extension has changed as a result of failed attempt with different mode
	my $ext_changed = 0;
	if ( ! $opt->{history} && ! $opt->{multimode} && defined $prog->{filename} && $prog->{filename} ne '' ) {
		( my $fileprefix, my $dir, my $ext ) = fileparse($prog->{filename}, qr/\.[^.]*/);
		$ext =~ s/\.//;
		$ext_changed = ( defined $ext && $ext ne '' && $ext ne $prog->{ext} );
		main::logger "DEBUG: File ext changed:   $ext -> $prog->{ext}\n" if $ext_changed && $opt->{debug};
	}

	# Don't override the {filename} if it is already set (i.e. for history info) or unless multimode option is specified
	$prog->{filename} = File::Spec->catfile($prog->{dir}, "$prog->{fileprefix}.$prog->{ext}") if ( defined $prog->{filename} && $prog->{filename} =~ /\.EXT$/ ) || $opt->{multimode} || ! $prog->{filename} || $ext_changed;
	$prog->{filepart} = File::Spec->catfile($prog->{dir}, "$prog->{fileprefix}.partial.$prog->{ext}");
	$prog->{filename} = main::encode_fs($prog->{filename});
	$prog->{filepart} = main::encode_fs($prog->{filepart});

	# overwrite/error if the file already exists and is going to be written to
	if (
		( ! $opt->{nowrite} )
		&& ( ! $opt->{metadataonly} )
		&& ( ! $opt->{thumbonly} )
		&& ( ! $opt->{subsonly} )
		&& ( ! $opt->{tagonly} )
		&& -f $prog->{filename} 
		&& stat($prog->{filename})->size > $prog->min_download_size()
	) {
		if ( $opt->{overwrite} ) {
			main::logger("INFO: Overwriting file $prog->{filename}\n\n");
			unlink $prog->{filename} unless $opt->{test};
		} else {
			main::logger("WARNING: File $prog->{filename} already exists\n\n");
			return 1;
		}
	}

	# Determine thumbnail filename
	if ( $prog->{thumbnail} =~ /^http/i ) {
		my $ext;
		$ext = $1 if $prog->{thumbnail} =~ m{\.(\w+)$};
		$ext = $opt->{thumbext} || $ext;
		$prog->{thumbfile} = File::Spec->catfile($prog->{dir}, "$prog->{fileprefix}.${ext}");
		$prog->{thumbfile} = main::encode_fs($prog->{thumbfile});
	}

	main::logger "DEBUG: File prefix:        $prog->{fileprefix}\n" if $opt->{debug};
	main::logger "DEBUG: File ext:           $prog->{ext}\n" if $opt->{debug};
	main::logger "DEBUG: Directory:          $prog->{dir}\n" if $opt->{debug};
	main::logger "DEBUG: Partial Filename:   $prog->{filepart}\n" if $opt->{debug};
	main::logger "DEBUG: Final Filename:     $prog->{filename}\n" if $opt->{debug};
	main::logger "DEBUG: Thumbnail Filename: $prog->{thumbfile}\n" if $opt->{debug};
	main::logger "DEBUG: Raw Mode: $opt->{raw}\n" if $opt->{debug};

	# Check path length is < 256 chars (Windows only)
	if ( length( $prog->{filepart} ) > 255 && $^O eq "MSWin32" ) {
		main::logger("ERROR: Generated file path is too long, please use --fileprefix, --subdir and --output options to shorten it to below 256 characters ('$prog->{filepart}')\n\n");
		return 1;
	}
	return 0;
}



# Run a user specified command
# e.g. --command 'echo "<pid> <name> recorded"'
# run_user_command($pid, 'echo "<pid> <name> recorded"');
sub run_user_command {
	my $prog = shift;
	my $command = shift;

	# Substitute the fields for the pid (and sanitize for double-quoted shell use)
	$command = $prog->substitute( $command, 4 );
	$command = main::encode_fs($command);

	# run command
	main::logger "INFO: Running command '$command'\n" if $opt->{verbose};
	my $exit_value = main::run_cmd( 'normal', $command );
	
	main::logger "ERROR: Command Exit Code: $exit_value\n" if $exit_value;
	main::logger "INFO: Command succeeded\n" if $opt->{verbose} && ! $exit_value;
        return 0;
}



# %type
# Display a line containing programme info (using long, terse, and type options)
sub list_entry {
	my ( $prog, $prefix, $tree, $number_of_types, $episode_count, $episode_width ) = ( @_ );

	my $prog_type = '';
	# Show the type field if >1 type has been specified
	$prog_type = "$prog->{type}, " if $number_of_types > 1;
	my $name;
	# If tree view
	if ( $opt->{tree} ) {
		$prefix = '  '.$prefix;
		$name = '';
	} else {
		$name = "$prog->{name} - ";
	}

	main::logger "\n${prog_type}$prog->{name}\n" if $opt->{tree} && ! $tree;
	# Display based on output options
	if ( $opt->{listformat} ) {
		# Slow. Needs to be faster e.g:
		#main::logger 'ENTRY'."$prog->{index}|$prog->{thumbnail}|$prog->{pid}|$prog->{available}|$prog->{type}|$prog->{name}|$prog->{episode}|$prog->{versions}|$prog->{duration}|$prog->{desc}|$prog->{channel}|$prog->{categories}|$prog->{timeadded}|$prog->{guidance}|$prog->{web}|$prog->{filename}|$prog->{mode}\n";
		main::logger $prefix.$prog->substitute( $opt->{listformat}, 2 )."\n";
	} elsif ( $opt->{series} && $episode_width && $episode_count && ! $opt->{tree} ) {
		main::logger sprintf( "%s%-${episode_width}s %5s %s\n", $prefix, $prog->{name}, "($episode_count)", $prog->{categories} );
	} elsif ( $opt->{long} ) {
		my @time = gmtime( time() - $prog->{timeadded} );
		main::logger "${prefix}$prog->{index}:\t${prog_type}${name}$prog->{episode}".$prog->optional_list_entry_format.", $time[7] days $time[2] hours ago - $prog->{desc}\n";
	} elsif ( $opt->{terse} ) {
		main::logger "${prefix}$prog->{index}:\t${prog_type}${name}$prog->{episode}\n";
	} else {
		main::logger "${prefix}$prog->{index}:\t${prog_type}${name}$prog->{episode}".$prog->optional_list_entry_format."\n";
	}
	return 0;
}



sub list_entry_html {
	my ($prog, $tree) = (@_);
	my $html;
	# If tree view
	my $name = encode_entities( $prog->{name} );
	my $episode = encode_entities( $prog->{episode} );
	my $desc = encode_entities( $prog->{desc} );
	my $channel = encode_entities( $prog->{channel} );
	my $type = encode_entities( $prog->{type} );
	my $categories = encode_entities( $prog->{categories} );

	# Header
	if ( not $tree ) {
		# Assume all thumbnails for a prog name are the same
		$html = "<tr bgcolor='#cccccc'>
			<td rowspan=1 width=150><a href=\"$prog->{web}\"><img height=84 width=150 src=\"$prog->{thumbnail}\"></a></td>
				<td><a href=\"$prog->{web}\">${name}</a></td>
				<td>${channel}</td>
				<td>${type}</td>
				<td>${categories}</td>
			</tr>
		\n";
	# Follow-on episodes
	}
		$html .= "<tr>
				<td>$_</td>
				<td><a href=\"$prog->{web}\">${episode}</a></td>
				<td colspan=3>${desc}</td>
			</tr>
		\n";
	return $html;
}


# Creates symlink
# Usage: $prog->create_symlink( <symlink>, <target> );
sub create_symlink {
	my $prog = shift;
	my $symlink = shift;
	my $target = shift;

	if ( ( ! ( $opt->{stdout} && $opt->{nowrite} ) ) && ( ! $opt->{test} ) ) {
		# remove old symlink
		unlink $symlink if -l $symlink;
		# Create symlink
		symlink $target, $symlink;
		main::logger "INFO: Created symlink from '$symlink' -> '$target'\n" if $opt->{verbose};
	}
}



# Get time ago made available (x days y hours ago) from '2008-06-22T05:01:49Z' and specified epoch time
# Or, Get time in epoch from '2008-06-22T05:01:49Z' or '2008-06-22T05:01:49[+-]NN:NN' if no specified epoch time
sub get_time_string {
	$_ = shift;
	my $diff = shift;

	# suppress warnings for > 32-bit dates in obsolete Perl versions
	local $SIG{__WARN__} = sub {
			warn @_ unless $_[0] =~ m(^.* too (?:big|small));
	};
	# extract $year $mon $mday $hour $min $sec $tzhour $tzmin
	my ($year, $mon, $mday, $hour, $min, $sec, $tzhour, $tzmin);
	if ( m{(\d\d\d\d)\-(\d\d)\-(\d\d)T(\d\d):(\d\d):(\d\d)} ) {
		($year, $mon, $mday, $hour, $min, $sec) = ($1, $2, $3, $4, $5, $6);
	} else {
		return '';
	}

	# positive TZ offset
	($tzhour, $tzmin) = ($1, $2) if m{\d\d\d\d\-\d\d\-\d\dT\d\d:\d\d:\d\d\+(\d\d):(\d\d)};
	# negative TZ offset
	($tzhour, $tzmin) = ($1*-1, $2*-1) if m{\d\d\d\d\-\d\d\-\d\dT\d\d:\d\d:\d\d\-(\d\d):(\d\d)};
	# ending in 'Z'
	($tzhour, $tzmin) = (0, 0) if m{\d\d\d\d\-\d\d\-\d\dT\d\d:\d\d:\d\dZ};

	main::logger "DEBUG: $_ = $year, $mon, $mday, $hour, $min, $sec, $tzhour, $tzmin\n" if $opt->{debug};
	# Sanity check date data
	return '' if $year < 1970 || $mon < 1 || $mon > 12 || $mday < 1 || $mday > 31 || $hour < 0 || $hour > 24 || $min < 0 || $min > 59 || $sec < 0 || $sec > 59 || $tzhour < -13 || $tzhour > 13 || $tzmin < -59 || $tzmin > 59;
	# Calculate the seconds difference between epoch_now and epoch_datestring and convert back into array_time
	my $epoch = eval { timegm($sec, $min, $hour, $mday, ($mon-1), ($year-1900), undef, undef, 0) - $tzhour*60*60 - $tzmin*60; };
	# ensure safe 32-bit date if timegm croaks
	if ( $@ ) { $epoch = timegm(0, 0, 0, 1, 0, 138, undef, undef, 0) - $tzhour*60*60 - $tzmin*60; };
	my $rtn;
	if ( $diff ) {
		# Return time ago
		if ( $epoch < $diff ) {
			my @time = gmtime( $diff - $epoch );
			# The time() func gives secs since 1970, gmtime is since 1900
			my $years = $time[5] - 70;
			$rtn = "$years years " if $years;
			$rtn .= "$time[7] days $time[2] hours ago";
			return $rtn;
		# Return time to go
		} elsif ( $epoch > $diff ) {
			my @time = gmtime( $epoch - $diff );
			my $years = $time[5] - 70;
			$rtn = 'in ';
			$rtn .= "$years years " if $years;
			$rtn .= "$time[7] days $time[2] hours";
			return $rtn;
		# Return 'Now'
		} else {
			return "now";
		}
	# Return time in epoch
	} else {
		# Calculate the seconds difference between epoch_now and epoch_datestring and convert back into array_time
		return $epoch;
	}
}



sub download_thumbnail {
	my $prog = shift;
	my $file;
	my $ext;
	my $image;
		
	if ( $prog->{thumbnail} =~ /^http/i && $prog->{thumbfile} ) {
		main::logger "INFO: Getting thumbnail from $prog->{thumbnail}\n" if $opt->{verbose};
		$file = $prog->{thumbfile};

		# Download thumb
		$image = main::request_url_retry( main::create_ua( 'desktop', 1 ), $prog->{thumbnail}, 1);
		if (! $image ) {
			main::logger "ERROR: Thumbnail Download failed\n";
			return 1;
		} else {
			main::logger "INFO: Downloaded Thumbnail to '$file'\n" if $opt->{verbose} || $opt->{thumb};
		}

	} else {
		# Return if we have no url
		main::logger "INFO: Thumbnail not available\n" if $opt->{verbose};
		return 2;
	}

	# Write to file
	unlink($file);
	open( my $fh, ">:raw", $file );
	print $fh $image;
	close $fh;

	return 0;
}


sub check_duration {
	my $prog = shift;
	my $filename = shift || $prog->{filename};
	return unless $prog->{duration} && $filename;
	my $cmd = "\"$bin->{ffmpeg}\" -i \"$filename\" 2>&1";
	$cmd = main::encode_fs($cmd);
	my $ffout = `$cmd`;
	if ( $ffout =~ /duration:\s+((\d+):(\d\d):(\d\d))/i ) {
		my $expected_s = $prog->{duration};
		if ( $opt->{start} && ! $opt->{stop} ) {
			$expected_s -= $opt->{start};
		} elsif ( $opt->{stop} ) {
			$expected_s = $opt->{stop} - $opt->{start};
		}		
		my $expected = sprintf("%02d:%02d:%02d", $expected_s / 3600, ($expected_s % 3600) / 60, $expected_s % 60);
		my $recorded_s = ($2 * 3600) + ($3 * 60) + $4;
		my $recorded = $1;
		my $diff_s = abs($recorded_s - $expected_s);
		my $diff_sign = $recorded_s < $expected_s ? "-" : "";
		my $diff = sprintf("$diff_sign%02d:%02d:%02d", $diff_s / 3600, ($diff_s % 3600) / 60, $diff_s % 60);
		main::logger "\nINFO: Duration check: recorded: $recorded expected: $expected difference: $diff file: $filename\n\n";
	} else {
		main::logger "WARNING: Could not determine recorded duration of file: $filename\n";
	}
}


################### iPlayer Parent class #################
package Programme::bbciplayer;

use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::stat;
use HTML::Entities;
use HTTP::Cookies;
use HTTP::Headers;
use IO::Seekable;
use IO::Socket;
use LWP::ConnCache;
use LWP::UserAgent;
use POSIX qw(mkfifo);
use Storable qw(dclone);
use strict;
use Time::Local;
use URI;

# Inherit from Programme class
use base 'Programme';


# Return hash of version => verpid given a pid
sub get_verpids {
	my ( $prog, $ua ) = @_;
	my $url;

	# If this is already a live or streaming verpid just pass it through	
	# e.g. http://www.bbc.co.uk/mediaselector/4/gtis/?server=cp52115.live.edgefcs.net&identifier=sport1a@s2388&kind=akamai&application=live&cb=28022
	if ( $prog->{pid} =~ m{^http.+/mediaselector/4/[gm]tis}i ) {
		# bypass all the xml parsing and return
		$prog->{verpids}->{default} = $1 if $prog->{pid} =~ m{^.+(\?.+)$};

		# Name
		my $title;
		$title = $1 if $prog->{pid} =~ m{identifier=(.+?)&};
		$title =~ s/\@/_/g;

		# Add to prog hash
		$prog->{versions} = join ',', keys %{ $prog->{verpids} };
		$prog->{title} = decode_entities($title);
		return 0;
	
	# Determine if the is a standard pid, Live TV or EMP TV URL
	# EMP URL
	} elsif ( $prog->{pid} =~ /^http/i ) {
		$url = $prog->{pid};
		if ( $HTML::Parser::VERSION < 3.71 ) {
			main::logger "WARNING: Page parsing may fail with HTML::Parser versions before 3.71. You have version $HTML::Parser::VERSION.\n";
		}
		# May aswell set the web page metadata here if not set
		$prog->{web} = $prog->{pid} if ! $prog->{web};
		# Scrape the EMP web page and get playlist URL
		my $xml = main::request_url_retry( $ua, $url, 3 );
		if ( ! $xml ) {
			main::logger "\rERROR: Failed to get EMP page from BBC site\n\n";
			return 1;
		}
		# flatten
		$xml =~ s/\n/ /g;
		# Find playlist URL in various guises
 		# JSON config block
		if ( $xml =~ m{["\s]pid["\s]:\s?["']([bp]0[a-z0-9]{6})["']} ) {
			$prog->{pid} = $1;
			$url = 'http://www.bbc.co.uk/iplayer/playlist/'.$prog->{pid};
		} elsif ( $xml =~ m{<param\s+name="playlist"\s+value="(http.+?)"}i ) {
			$url = $1;
		# setPlaylist("http://www.bbc.co.uk/mundo/meta/dps/2009/06/emp/090625_video_festival_ms.emp.xml")
		# emp.setPlaylist("http://www.bbc.co.uk/learningzone/clips/clips/p_chin/bb/p_chin_ch_05303_16x9_bb.xml")
		} elsif ( $xml =~ m{setPlaylist\("(http.+?)"\)}i ) {
			$url = $1;
			$url =~ s/["']\+location\.host\+["']/www.bbc.co.uk/;
		# playlist = "http://www.bbc.co.uk/worldservice/meta/tx/flash/live/eneuk.xml";
		} elsif ( $xml =~ m{\splaylist\s+=\s+"(http.+?)";}i ) {
			$url = $1;
		# iplayer Programmes page format (also rewrite the pid)
		# href="http://www.bbc.co.uk/iplayer/episode/b00ldhj2"
		} elsif ( $xml =~ m{href="http://www.bbc.co.uk/iplayer/episode/([bp]0[a-z0-9]{6})"} ) {
			$prog->{pid} = $1;
			$url = 'http://www.bbc.co.uk/iplayer/playlist/'.$1;
		# live streams (e.g., olympics)
		} elsif ( $xml =~ m{"href":\s*"(http:\\/\\/playlists.bbc.co.uk\\/.+?\\/playlist.sxml)"[^\}]+?"live":\s*true} ) {
			($url = $1) =~ s/\\//g;
			$prog->{pid} = $url;
		} elsif ( $xml =~ m{live-experience\/services.+?pid=([bp]0[a-z0-9]{6})} ) {
			$url = 'http://www.bbc.co.uk/iplayer/playlist/'.$1;
			$prog->{pid} = $url;
		# playlist embedded in JSON
		} elsif ( $xml =~ m{"href":"(http:\\/\\/playlists.bbc.co.uk\\/.+?\\/playlist.sxml)"} ) {
 			($url = $1) =~ s/\\//g;
 		# embedded player
		} elsif ( $xml =~ m{emp\.load\("(http://www.bbc.co.uk/iplayer/playlist/([bp]0[a-z0-9]{6}))"\)} ) {
 			$url = $1;
 			$prog->{pid} = $2;
		} elsif ( $url =~ m{^http.+.xml$} ) {
			# Just keep the url as it is probably already an xml playlist
		## playlist: "http://www.bbc.co.uk/iplayer/playlist/bbc_radio_one",
		#} elsif ( $xml =~ m{playlist: "http.+?playlist\/(\w+?)"}i ) {
		#	$prog->{pid} = $1;
		#	$url = 'http://www.bbc.co.uk/iplayer/playlist/'.$prog->{pid};
		}
		# URL decode url
		$url = main::url_decode( $url );
	# iPlayer LiveTV
	} elsif ( $prog->{type} =~ 'live' && $prog->{pid} =~ /^(bbc_|cb)/i) {
		my ($verpid, $version);
		my $hls_pid_map;
		if ( $prog->{type} eq 'livetv' ) {
			$hls_pid_map = Programme::livetv->hls_pid_map();
		} else {
			$hls_pid_map = Programme::liveradio->hls_pid_map();
		}
		my $hls_pid = $hls_pid_map->{$prog->{pid}};
		$verpid = $hls_pid || $prog->{pid};
		main::logger "INFO: Using $prog->{type}: $verpid\n" if $opt->{verbose} && $verpid;
		$version = 'default';
		$prog->{verpids}->{$version} = $verpid;
		$prog->{versions} = join ',', keys %{ $prog->{verpids} };
		return 0;
	# iPlayer PID
	} else {
		$url = 'http://www.bbc.co.uk/iplayer/playlist/'.$prog->{pid};
		# use the audiodescribed playlist url if non-default versions are specified
		$url .= '/ad' if defined $opt->{versionlist} && $opt->{versionlist} =~ /(audiodescribed|signed)/;
	}
	
	main::logger "INFO: iPlayer metadata URL = $url\n" if $opt->{verbose};
	#main::logger "INFO: Getting version pids for programme $prog->{pid}        \n" if ! $opt->{verbose};

	# send request
	my $xml = main::request_url_retry( $ua, $url, 3 );
	if ( ! $xml ) {
		main::logger "\rERROR: Failed to get version pid metadata from iplayer site\n\n";
		return 1;
	}
	# The URL http://www.bbc.co.uk/iplayer/playlist/<PID> contains for example:
	#<?xml version="1.0" encoding="UTF-8"?>
	#<playlist xmlns="http://bbc.co.uk/2008/emp/playlist" revision="1">
	#  <id>tag:bbc.co.uk,2008:pips:b00dlrc8:playlist</id>
	#  <link rel="self" href="http://www.bbc.co.uk/iplayer/playlist/b00dlrc8"/>
	#  <link rel="alternate" href="http://www.bbc.co.uk/iplayer/episode/b00dlrc8"/>
	#  <link rel="holding" href="http://www.bbc.co.uk/iplayer/images/episode/b00dlrc8_640_360.jpg" height="360" width="640" type="image/jpeg" />
	#  <title>Amazon with Bruce Parry: Episode 1</title>
	#  <summary>Bruce Parry begins an epic adventure in the Amazon following the river from source to sea, beginning  in the High Andes and visiting the Ashaninka tribe.</summary>                                                                                                        
	#  <updated>2008-09-18T14:03:35Z</updated>
	#  <item kind="ident">
	#    <id>tag:bbc.co.uk,2008:pips:bbc_two</id>
	#    <mediator identifier="bbc_two" name="pips"/>
	#  </item>
	#  <item kind="programme" duration="3600" identifier="b00dlr9p" group="b00dlrc8" publisher="pips">
	#    <tempav>1</tempav>
	#    <id>tag:bbc.co.uk,2008:pips:b00dlr9p</id>
	#    <service id="bbc_two" href="http://www.bbc.co.uk/iplayer/bbc_two">BBC Two</service>
	#    <masterbrand id="bbc_two" href="http://www.bbc.co.uk/iplayer/bbc_two">BBC Two</masterbrand>
	#
	#    <alternate id="default" />
	#    <guidance>Contains some strong language.</guidance>
	#    <mediator identifier="b00dlr9p" name="pips"/>
	#  </item>
	#  <item kind="programme" duration="3600" identifier="b00dp4xn" group="b00dlrc8" publisher="pips">
	#    <tempav>1</tempav>
	#    <id>tag:bbc.co.uk,2008:pips:b00dp4xn</id>
	#    <service id="bbc_one" href="http://www.bbc.co.uk/iplayer/bbc_one">BBC One</service>
	#    <masterbrand id="bbc_two" href="http://www.bbc.co.uk/iplayer/bbc_two">BBC Two</masterbrand>
	#
	#    <alternate id="signed" />
	#    <guidance>Contains some strong language.</guidance>
	#    <mediator identifier="b00dp4xn" name="pips"/>
	#  </item>

	# If a prog is totally unavailable you get 
	# ...
	# <updated>2009-01-15T23:13:33Z</updated>
	# <noItems reason="noMedia" />
	#
	#                <relatedLink>
	                
	# flatten
	$xml =~ s/\n/ /g;

	# set title here - broken in JSON playlists
	$prog->{title} = decode_entities($1) if $xml =~ m{<title>\s*(.+?)\s*<\/title>};
	$prog->{thumbnail} ||= $1 if $xml =~ m{<link rel="holding" href="(.*?)"};
	$prog->{guidance} ||= $1 if $xml =~ m{<guidance.*?>(.*?)</guidance>};
	$prog->{descshort} = $1 if $xml =~ m{<summary>(.*?)</summary>};
	$prog->{type} ||= 'tv' if grep /kind="programme"/, $xml;
	$prog->{type} ||= 'radio' if grep /kind="radioProgramme"/, $xml;

	# Detect noItems or no programmes
	if ( $xml =~ m{<noItems\s+reason="(\w+)"} || $xml !~ m{kind="(programme|radioProgramme)"} ) {
		my $rc_json = $prog->get_verpids_json( $ua );
		my $rc_html = 1;
		if ( ( ! $prog->{type} || $prog->{type} eq 'tv' ) && ! $opt->{noscrapeversions} ) {
			$rc_html = $prog->get_verpids_html( $ua );
		}
		return 0 if ! $rc_json || ! $rc_html;
		main::logger "\nWARNING: No programmes are available for this pid with version(s): ".($opt->{versionlist} ? $opt->{versionlist} : 'default').($prog->{versions} ? " (available versions: $prog->{versions})\n" : "\n");
		main::logger "WARNING: You may receive this message if you are using get_iplayer outside the UK\n";
		return 1;
	}

	# Split into <item kind="programme"> sections
	my $prev_version = '';
	for ( split /<item\s+kind="(radioProgramme|programme)"/, $xml ) {
		main::logger "DEBUG: Block: $_\n" if $opt->{debug};
		my ($verpid, $version);

		# Treat live streams accordingly
		# Live TV
		if ( m{\s+simulcast="true"} ) {
			$version = 'default';
			# <item kind="programme" live="true" liverewind="true" identifier="bbc_two_england" group="bbc_two_england" simulcast="true" availability_class="liverewind">
			# $verpid = "http://www.bbc.co.uk/emp/simulcast/".$2.".xml" if m{\s+live="true"\s+(liverewind="true"\s+)?identifier="(.+?)"};
			$verpid = $2 if m{\s+live="true"\s+(liverewind="true"\s+)?identifier="(.+?)"};
			my $hls_pid_map = Programme::livetv->hls_pid_map();
			my $hls_pid = $hls_pid_map->{$prog->{pid}};
			$verpid = $hls_pid || $verpid;
			main::logger "INFO: Using Live TV: $verpid\n" if $opt->{verbose} && $verpid;
		# Live/Non-live EMP tv/radio XML URL
		} elsif ( $prog->{pid} =~ /^http/i && $url =~ /^http.+xml$/ ) {
			$version = 'default';
			$verpid = $url;
			main::logger "INFO: Using Live/Non-live EMP tv/radio XML URL: $verpid\n" if $opt->{verbose} && $verpid;

		# Live/Non-live EMP tv/radio URL
		} elsif ( $prog->{pid} =~ /^http/i && $url =~ /^http/ ) {
			$version = 'default';
			$verpid = $url;
			main::logger "INFO: Using Live/Non-live EMP tv/radio URL: $verpid\n" if $opt->{verbose} && $verpid;

		# Live/Non-live EMP tv/radio
		} elsif ( $prog->{pid} =~ /^http/i ) {
			$version = 'default';
			# <connection kind="akamai" identifier="48502/mundo/flash/2009/06/glastonbury_16x9_16x9_bb" server="cp48502.edgefcs.net"/>
			# <connection kind="akamai" identifier="intl/abercrombie" server="cp57856.edgefcs.net" />
			# <connection kind="akamai" application="live" identifier="sport2a@s2405" server="cp52115.live.edgefcs.net" tokenIssuer="akamaiUk" />
			# <connection kind="akamai" identifier="secure/p_chin/p_chin_ch_05303_16x9_bb" server="cp54782.edgefcs.net" tokenIssuer="akamaiUk"/>
			# <connection kind="akamai" application="live" identifier="eneuk_live@6512" server="wsliveflash.bbc.co.uk" />
			# verpid = ?server=cp52115.live.edgefcs.net&identifier=sport2a@s2405&kind=akamai&application=live
			$verpid = "?server=$4&identifier=$3&kind=$1&application=$2" if $xml =~ m{<connection\s+kind="(.+?)"\s+application="(.+?)"\s+identifier="(.+?)"\s+server="(.+?)"};
			# Or try this if application is not defined (i.e. like in learning zone)
			if ( ! $verpid ) {
				$verpid = "?server=$3&identifier=$2&kind=$1&application=ondemand" if $xml =~ m{<connection\s+kind="(.+?)"\s+identifier="(.+?)"\s+server="(.+?)"};
			}
			main::logger "INFO: Using Live/Non-live EMP tv/radio: $verpid\n" if $opt->{verbose} && $verpid;

		# Live radio
		} elsif ( m{\s+live="true"\s} ) {
			# Try to get live stream version and verpid
			# <item kind="radioProgramme" live="true" identifier="bbc_radio_one" group="bbc_radio_one">
			$verpid = $1 if m{\s+live="true"\s+identifier="(.+?)"};
			my $hls_pid_map = Programme::liveradio->hls_pid_map();
			my $hls_pid = $hls_pid_map->{$prog->{pid}};
			$verpid = $hls_pid || $verpid;
			$version = 'default';
			main::logger "INFO: Using Live radio: $verpid\n" if $opt->{verbose} && $verpid;

		# Not Live standard TV and Radio
		} else {
			#  duration="3600" identifier="b00dp4xn" group="b00dlrc8" publisher="pips">
			$verpid = $1 if m{\s+duration=".*?"\s+identifier="(.+?)"};
			# assume default version
			my $curr_version = "default";
			# <alternate id="default" />
			if ( m{<alternate\s+id="(.+?)"} ) {
				$curr_version = lc($1);
				# Remap version name from 'default' => 'audiodescribed' if we are using the /ad playlist URL:
				if ( defined $opt->{versionlist} && $opt->{versionlist} =~ /(audiodescribed|signed)/ ) {
					$curr_version = 'audiodescribed' if $curr_version eq 'default';
				}
			}
			$version = $curr_version;
			# check version collisions
			if ( $prog->{verpids}->{$curr_version} ) {
				my $vercount = 1;
				# Search for the next free suffix
				while ( $prog->{verpids}->{$curr_version} ) {
					$vercount++;
					$curr_version = $version.$vercount;
				}
				$version = $curr_version;
			}
			main::logger "INFO: Using Not Live standard TV and Radio: $verpid\n" if $opt->{verbose} && $verpid;
		}

		next if ! ($verpid && $version);
		$prog->{verpids}->{$version} = $verpid;
		$prog->{durations}->{$version} = $1 if m{duration="(\d+?)"};
		main::logger "INFO: Version: $version, VersionPid: $verpid, Duration: $prog->{durations}->{$version}\n" if $opt->{verbose};  
	}

	# try json playlist for channel and any missing fields
	if ( $prog->{type} eq 'tv' || $prog->{type} eq 'radio' ) {
		$prog->get_verpids_json( $ua );
	}

	# Add to prog hash
	$prog->{versions} = join ',', keys %{ $prog->{verpids} };
	return 0;
}


# Return hash of version => verpid given a pid
# Uses JSON playlist: http://www.bbc.co.uk/programmes/<pid>/playlist.json
sub get_verpids_json {
	my ( $prog, $ua ) = @_;
	my $pid;
	if ( $prog->{pid} =~ /^http/i ) {
		$pid = $1 if $prog->{pid} =~ /\/([bp]0[a-z0-9]{6})/ 
	}
	$pid ||= $prog->{pid};
	if ( $prog->{pid} ne $pid ) {
		main::logger "INFO: pid changed from $prog->{pid} to $pid (JSON)\n" if $opt->{verbose};
		$prog->{pid} = $pid;
	}
	if ( $pid !~ /^[bp]0[a-z0-9]{6}$/ ) {
		main::logger "INFO: skipping playlist for non-PID $pid (JSON)\n" if $opt->{verbose};
		return;
	}
	my $url = 'http://www.bbc.co.uk/programmes/'.$pid.'/playlist.json';
	main::logger "INFO: iPlayer metadata URL (JSON) = $url\n" if $opt->{verbose};
	my $json = main::request_url_retry( $ua, $url, 3 );
	if ( ! $json ) {
		main::logger "ERROR: Failed to get version pid metadata from iplayer site (JSON)\n";
		return 1;
	}
	my ( $default, $versions ) = split /"allAvailableVersions"/, $json;
	unless ( $prog->{channel} ) {
		$prog->{channel} = $1 if $default =~ /"masterBrandName":"(.*?)"/;
	}
	unless ( $prog->{descshort} ) {
		$prog->{descshort} = $1 if $default =~ /"summary":"(.*?)"/;
	}
	unless ( $prog->{guidance} ) {
		my $guidance = $2 if $default =~ /"guidance":(null|"(.*?)")/;
		$prog->{guidance} = "Yes" if $guidance;
	}
	unless ( $prog->{thumbnail} ) {
		my $thumbnail = $1 if $default =~ /"holdingImageURL":"(.*?)"/;
		$thumbnail =~ s/\\\//\//g;
		my $thumbsize = $opt->{thumbsize} || $opt->{thumbsizecache} || 150;
		my $recipe = Programme::bbciplayer->thumb_url_recipes->{ $thumbsize };
		if ( ! $recipe ) {
			main::logger "WARNING: Invalid thumbnail size: $thumbsize - using default (JSON)\n";
			$recipe = Programme::bbciplayer->thumb_url_recipes->{ 150 };
		}
		$thumbnail =~ s/\$recipe/$recipe/;
		$prog->{thumbnail} = $thumbnail if $thumbnail;
	}
	unless ( $prog->{title} ) {
		my $title = $1 if $default =~ /"title":"(.*?)"/;
		$title =~ s/\\\//\//g;
		$prog->{title} = decode_entities($title) if $title;
	}
	unless ( $prog->{type} ) {
		$prog->{type} = 'tv' if $default =~ /"kind":"video"/;
		$prog->{type} = 'radio' if $default =~ /"kind":"audio"/;
	}
	my @versions = split /"markers"/, $versions;
	pop @versions;
	for ( @versions ) {
		main::logger "DEBUG: Block (JSON): $_\n" if $opt->{debug};
		my ($verpid, $version);
		my $type = $1 if /"types":\["(.*?)"/;
		if ( $type =~ /describe/i ) {
			$version = "audiodescribed";
		} elsif ($type =~ /sign/i ) {
			$version = "signed";
		} else {
			$version = "default";
		}
		next if $prog->{verpids}->{$version};
		$verpid = $1 if /{"vpid":"(\w+)","kind":"(programme|radioProgramme)"/i;
		next if ! ($verpid && $version);
		$prog->{verpids}->{$version} = $verpid;
		$prog->{durations}->{$version} = $1 if /"duration":(\d+)/;
	}
	$prog->{versions} = join ',', keys %{ $prog->{verpids} };
	my $version_map = { "default" => "", "audiodescribed" => "ad", "signed" => "sign"};
	my $version_list = $opt->{versionlist} || 'default';
	for ( split /,/, $version_list ) {
		if ( $prog->{verpids}->{$_} ) {
			my $episode_url;
			if ( $prog->{type} eq 'tv' ) {
				$episode_url = 'http://www.bbc.co.uk/iplayer/episode/'.$pid."/$version_map->{$_}";
			} elsif ( $prog->{type} eq 'radio' ) {
				$episode_url = 'http://www.bbc.co.uk/programmes/'.$pid;
			}
			unless ( $prog->{player} ) {
				$prog->{player} = $episode_url if $episode_url;
				last;
			}
		}
	}
	my $found;
	for ( keys %{ $prog->{verpids} } ) {
		$found = 1 if $version_list =~ /$_/ && $prog->{verpids}->{$_};
		last if $found;
	}
	return 1 if ! $found;
	return 0;
}


# Return hash of version => verpid given a pid
# Scrapes HTML from episode page: http://www.bbc.co.uk/iplayer/episode/<pid>
# Only works for TV programmes
sub get_verpids_html {
	my ( $prog, $ua ) = @_;
	my $pid;
	if ( $prog->{pid} =~ /^http/i ) {
		$pid = $1 if $prog->{pid} =~ /\/([bp]0[a-z0-9]{6})/
	}
	$pid ||= $prog->{pid};
	if ( $prog->{pid} ne $pid ) {
		main::logger "INFO: pid changed from $prog->{pid} to $pid (HTML)\n" if $opt->{verbose};
		$prog->{pid} = $pid;
	}
	if ( $pid !~ /^[bp]0[a-z0-9]{6}$/ ) {
		main::logger "INFO: skipping playlist for non-PID $pid (HTML)\n" if $opt->{verbose};
		return;
	}
	my $version_list = $opt->{versionlist} || 'default';
	my $version_map = { "default" => "", "audiodescribed" => "ad", "signed" => "sign"};
	for my $version ( "default", "audiodescribed", "signed" ) {
		next if $version_list !~ /$version/ || $prog->{verpids}->{$version};
		my $url = 'http://www.bbc.co.uk/iplayer/episode/'.$pid."/$version_map->{$version}";
		main::logger "INFO: iPlayer metadata URL (HTML) [$version] = $url\n" if $opt->{verbose};
		my $html = main::request_url_retry( $ua, $url, 3 );
		if ( ! $html ) {
			main::logger "\rERROR: Failed to get version pid metadata from iplayer site (HTML)\n\n";
			return 1;
		}
		my $config = $1 if $html =~ /require\(\{\s*config:(.*?)\<\/script\>/s;
		main::logger "DEBUG: Block (HTML): $config\n" if $opt->{debug};
		my $verpid = $1 if $config =~ /"vpid":"(.*?)"/;
		if ( ! $verpid ) {
			main::logger "INFO: $version version not found in metadata retrieved from iplayer site (HTML)\n" if $opt->{verbose};
			next;
		}
		unless ( $prog->{channel} ) {
			$prog->{channel} = $1 if $config =~ /"masterBrandTitle":"(.*?)"/;
		}
		unless ( $prog->{descshort} ) {
			$prog->{descshort} = $1 if $config =~ /"summary":"(.*?)"/;
		}
		unless ( $prog->{guidance} ) {
			my $guidance = $2 if $config =~ /"guidance":(null|"(.*?)")/;
			$prog->{guidance} = "Yes" if $guidance;
		}
		unless ( $prog->{thumbnail} ) {
			my $thumbnail = $1 if $config =~ /"image":"(.*?)"/;
			$thumbnail =~ s/\\\//\//g;
			my $thumbsize = $opt->{thumbsize} || $opt->{thumbsizecache} || 150;
			my $recipe = Programme::bbciplayer->thumb_url_recipes->{ $thumbsize };
			if ( ! $recipe ) {
				main::logger "WARNING: Invalid thumbnail size: $thumbsize - using default (HTML)\n";
				$recipe = Programme::bbciplayer->thumb_url_recipes->{ 150 };
			}
			$thumbnail =~ s/{recipe}/$recipe/;
			$prog->{thumbnail} = $thumbnail if $thumbnail;
		}
		unless ( $prog->{title} ) {
			my $title = $1 if $config =~ /"title":"(.*?)"/;
			$title =~ s/\\\//\//g;
			my $subtitle = $1 if $config =~ /"subtitle":"(.*?)"/;
			$subtitle =~ s/\\\//\//g;
			$title .= ": $subtitle" if $subtitle;
			$prog->{title} = decode_entities($title) if $title;
		}
		unless ( $prog->{type} ) {
			$prog->{type} = "tv";
		}
		$prog->{verpids}->{$version} = $verpid;
		$prog->{durations}->{$version} = $1 if $config =~ /"duration":(\d+)/;
	}
	$prog->{versions} = join ',', keys %{ $prog->{verpids} };
	for ( split /,/, $version_list ) {
		if ( $prog->{verpids}->{$_} ) {
			my $episode_url;
			if ( $prog->{type} eq 'tv' ) {
				$episode_url = 'http://www.bbc.co.uk/iplayer/episode/'.$pid."/$version_map->{$_}";
			} elsif ( $prog->{type} eq 'radio' ) {
				$episode_url = 'http://www.bbc.co.uk/programmes/'.$pid;
			}
			unless ( $prog->{player} ) {
				$prog->{player} = $episode_url if $episode_url;
				last;
			}
		}
	}
	my $found;
	for ( keys %{ $prog->{verpids} } ) {
		$found = 1 if $version_list =~ /$_/ && $prog->{verpids}->{$_};
		last if $found;
	}
	return 1 if ! $found;
	return 0;
}


# get full episode metadata given pid and ua. Uses two different urls to get data
sub get_metadata {
	my $prog = shift;
	my $ua = shift;
	my $prog_data_url = 'http://www.bbc.co.uk/programmes/'; # $pid
	my @ignore_categories = ("Films", "Sign Zone", "Audio Described", "Northern Ireland", "Scotland", "Wales", "England");
	
	my ($title, $name, $brand, $series, $episode, $longname, $available, $channel, $expiry, $meddesc, $longdesc, $summary, $versions, $guidance, $prog_type, $categories, $category, $web, $player, $thumbnail, $seriesnum, $episodenum, $episodepart );

	# This URL works for tv/radio prog types:
	# http://www.bbc.co.uk/programmes/{pid}.xml

	# This URL works for tv/radio prog types (has long synopsis and categories):
	# http://www.bbc.co.uk/programmes/{pid}.rdf

	# Works for all Verison PIDs to get the last/first broadcast dates
	# http://www.bbc.co.uk/programmes/<verpid>.rdf

	main::logger "DEBUG: Getting Metadata for $prog->{pid}:\n" if $opt->{debug};

	my $got_metadata;
	eval "use XML::Simple";
	if ( $@ ) {
		main::logger "WARNING: Please download and run latest installer or install the XML::Simple Perl module for more accurate programme metadata.\n";
	} elsif ( $prog->{pid} =~ /^[bp]0[a-z0-9]{6}$/ ) {
		my $url = $prog_data_url.$prog->{pid}.".xml";
		main::logger "INFO: Programme metadata URL = $url\n" if $opt->{verbose};
		my $xml = main::request_url_retry($ua, $url, 3, '', '');
		if ( $xml ) {
			my $doc = eval { XMLin($xml, KeyAttr => [], ForceArray => 1, SuppressEmpty => 1) };
			if ( ! $@ ) {
				if ( $doc->{type} eq "episode" || $doc->{type} eq "clip" ) {
					my $parent = $doc->{parent}->[0]->{programme}->[0];
					my $grandparent = $parent->{parent}->[0]->{programme}->[0];
					my $greatgrandparent = $grandparent->{parent}->[0]->{programme}->[0];
					my $pid = $doc->{pid}->[0];
					my $parentpid = $parent->{pid}->[0];
					$prog_type = $doc->{media_type}->[0];
					$prog_type = 'tv' if $prog_type =~ m{video}s;
					$prog_type = 'radio' if $prog_type eq 'audio';
					$longdesc = $doc->{long_synopsis}->[0];
					$meddesc = $doc->{medium_synopsis}->[0];
					$summary = $doc->{short_synopsis}->[0];
					$channel = $doc->{ownership}->[0]->{service}->[0]->{title}->[0];
					my $image_pid = $doc->{image}->[0]->{pid}->[0];
					my $thumbsize = $opt->{thumbsize} || $opt->{thumbsizecache} || 150;
					my $recipe = Programme::bbciplayer->thumb_url_recipes->{ $thumbsize };
					$recipe = Programme::bbciplayer->thumb_url_recipes->{ 150 } if ! $recipe;
					$thumbnail = "http://ichef.bbci.co.uk/images/ic/${recipe}/${image_pid}.jpg";
					$web = "http://www.bbc.co.uk/programmes/$parentpid" if $parentpid;
					if ( $prog_type eq "tv" && $doc->{type} eq "episode" ) {
						$player = "http://www.bbc.co.uk/iplayer/episode/$pid";
					} else {
						$player = "http://www.bbc.co.uk/programmes/$pid";
					}
					# title strings
					my ($series_position, $subseries_position);
					$episode = $doc->{title}->[0];
					for my $ancestor ($parent, $grandparent, $greatgrandparent) {
						if ( $ancestor->{type} && $ancestor->{title}->[0] ) {
							if ( $ancestor->{type} eq "brand" ) {
								$brand = $ancestor->{title}->[0];
							} elsif ( $ancestor->{type} eq "series" ) {
								# handle rare subseries
								if ( $series ) {
									$episode = "$series $episode";
									$subseries_position = $series_position;
								}
								$series = $ancestor->{title}->[0];
								$series_position = $ancestor->{position}->[0];
							}
						}
					}
					if ( $brand ) {
						if ( $series && $series ne $brand ) {
							$name = "$brand: $series";
						} else {
							$name = $brand;
						}
					} else {
							$name = $series;
					}
					unless ( $name ) {
						$name = $brand = $episode;
						$episode = "-";
						$title = $name;
					} else {
						$title = "$name: $episode";
					}
					# categories
					my (@cats1, @cats2, @cats3);
					for my $cat1 ( @{$doc->{categories}->[0]->{category}} ) {
						unshift @cats1, $cat1->{title}->[0];
						for my $cat2 ( @{$cat1->{broader}->[0]->{category}} ) {
							unshift @cats2, $cat2->{title}->[0];
							for my $cat3 ( @{$cat2->{broader}->[0]->{category}} ) {
								unshift @cats3, $cat3->{title}->[0];
							}
						}
					}
					my %seen;
					my @categories = grep { ! $seen{$_}++ } ( @cats3, @cats2, @cats1 );
					$categories = join(',', @categories);
					foreach my $cat ( @categories ) {
						if ( ! grep(/$cat/i, @ignore_categories) ) {
							$category = $cat;
							last;
						}
					}
					$categories ||= "get_iplayer";
					$category ||= $categories[0] || "get_iplayer";
					# series/episode numbers
					if ( $subseries_position ) {
						my @parts = ("a".."z");
						$episodepart = $parts[$doc->{position}->[0] - 1];
					}
					$episodenum = $subseries_position || $doc->{position}->[0];
					$seriesnum = $series_position || $parent->{position}->[0];
					# the Doctor Who fudge
					my ($seriesnum2, $episodenum2);
					# Extract the seriesnum
					my $regex = 'Series\s+'.main::regex_numbers();
					if ( "$name $episode" =~ m{$regex}i ) {
						$seriesnum2 = main::convert_words_to_number( $1 );
					}
					# Extract the episode num
					my $regex_1 = 'Episode\s+'.main::regex_numbers();
					my $regex_2 = '^'.main::regex_numbers().'\.\s+';
					if ( "$name $episode" =~ m{$regex_1}i ) {
						$episodenum2 = main::convert_words_to_number( $1 );
					} elsif ( $episode =~ m{$regex_2}i ) {
						$episodenum2 = main::convert_words_to_number( $1 );
					}
					# override series/episode numbers if mismatch
					$seriesnum = $seriesnum2 if $seriesnum2;
					$episodenum = $episodenum2 if $episodenum2;
					# insert episode number in $episode
					$episode = Programme::bbciplayer::insert_episode_number($episode, $episodenum, $episodepart);
					# minimum episode number = 1 if not a film and series number == 0
					$episodenum = 1 if ( $seriesnum == 0 && $episodenum == 0 && $prog_type eq 'tv' && $categories !~ "Films" );
					# minimum series number = 1 if episode number != 0
					$seriesnum = 1 if ( $seriesnum == 0 && $episodenum != 0 );
					# programme versions
					my %found;
					for my $ver ( @{$doc->{versions}->[0]->{version}} ) {
						my $type;
						# check for audiodescribed and signed first
						if ( grep /describe/i, @{$ver->{types}->[0]->{type}} ) {
							$type = "audiodescribed";
						} elsif ( grep /sign/i, @{$ver->{types}->[0]->{type}} ) {
							$type = "signed";
						} elsif ( grep /open subtitles/i, @{$ver->{types}->[0]->{type}} ) {
							$type = "opensubtitles";
						} else {
							($type = lc($ver->{types}->[0]->{type}->[0])) =~ s/\s+.*$//;
						}
						if ( $type ) {
							my $version = $type;
							$version .= $found{$type} if ++$found{$type} > 1;
							$prog->{verpids}->{$version} = $ver->{pid}->[0];
							$prog->{durations}->{$version} = $ver->{duration}->[0];
						}
					}
					$got_metadata = 1;
				} else {
					main::logger "WARNING: PID $prog->{pid} does not refer to an iPlayer programme episode. Download may fail and metadata may be inaccurate.\n";
				}
			} else {
				main::logger "WARNING: Could not parse programme metadata from $url\n";
			}
		} else {
			main::logger "WARNING: Could not download programme metadata from $url\n";
		}
	}

	# Get list of available modes for each version available
	# populate version pid metadata if we don't have it already
	if ( keys %{ $prog->{verpids} } == 0 ) {
		if ( $prog->get_verpids( $ua ) ) {
			main::logger "ERROR: Could not get version pid metadata\n" if $opt->{verbose};
			# Return at this stage unless we want metadata/tags only for various reasons
			return 1 if ! ( $opt->{info} || $opt->{metadataonly} || $opt->{thumbonly} || $opt->{tagonly} )
		}
	}

	# use fallback metadata if necessary
	unless ( $got_metadata ) {
		$prog->get_metadata_fallback( $ua );
	}

	my $modes;
	my $mode_sizes;
	my $first_broadcast;
	my $last_broadcast;
	# Do this for each version tried in this order (if they appeared in the content)
	for my $version ( sort keys %{ $prog->{verpids} } ) {
		# Try to get stream data for this version if it isn't already populated
		if ( not defined $prog->{streams}->{$version} ) {
			# Add streamdata to object
			$prog->{streams}->{$version} = get_stream_data($prog, $prog->{verpids}->{$version} );
		}
		if ( keys %{ $prog->{streams}->{$version} } == 0 ) {
			main::logger "INFO: No streams available for '$version' version ($prog->{verpids}->{$version}) - skipping RDF\n" if $opt->{verbose};
			next;
		}
		$modes->{$version} = join ',', sort keys %{ $prog->{streams}->{$version} };
		# Estimate the file sizes for each mode
		my @sizes;
		for my $mode ( sort keys %{ $prog->{streams}->{$version} } ) {
			# get expiry from stream data
			if ( ! $expiry && $prog->{streams}->{$version}->{$mode}->{expires} ) {
				$expiry = $prog->{streams}->{$version}->{$mode}->{expires};
				$prog->{expiryrel} = Programme::get_time_string( $expiry, time() );
			}
			my $size;
			if ( $prog->{streams}->{$version}->{$mode}->{size} ) {
				$size = $prog->{streams}->{$version}->{$mode}->{size};
			} else {
				next if ( ! $prog->{durations}->{$version} ) || (! $prog->{streams}->{$version}->{$mode}->{bitrate} );
				$size = $prog->{streams}->{$version}->{$mode}->{bitrate} * $prog->{durations}->{$version} / 8.0 * 1024.0;
			}
			if ( $size < 1048576 ) {
				push @sizes, sprintf( "%s=%.0fKB", $mode, $size / 1024.0 );
			} else {
				push @sizes, sprintf( "%s=%.0fMB", $mode, $size / 1048576.0 );
			}
		}
		$mode_sizes->{$version} = join ',', @sizes;
		# Set duration for this version if it is not defined
		$prog->{durations}->{$version} = $prog->{duration} if $prog->{duration} =~ /\d+/ && ! $prog->{durations}->{$version};
		next unless $prog->{verpids}->{$version} =~ /^[bp]0[a-z0-9]{6}$/;
		# get the last/first broadcast dates from the RDF for this verpid
		# rdf url: http://www.bbc.co.uk/programmes/<verpid>.rdf
		# Date in this format 'CCYY-MM-DDTHH:MM:SS+01:00'
		# Don't get this feed if the verpid starts with '?'
		my $rdf_url = 'http://www.bbc.co.uk/programmes/'.$prog->{verpids}->{$version}.'.rdf';
		my $rdf;
		$rdf = main::request_url_retry($ua, $rdf_url, 3, '', '') if $prog->{verpids}->{$version} !~ m{^\?};
		decode_entities($rdf);
		main::logger "DEBUG: $rdf_url:\n$rdf\n\n" if $opt->{debug};
		# Flatten
		$rdf =~ s|\n| |g;
		# Get min/max bcast dates from rdf
		my ( $now, $first, $last, $first_string, $last_string ) = ( time(), 9999999999, 0, 'Never', 'Never' );
		# <po:(First|Repeat)Broadcast>
		#  <po:schedule_date rdf:datatype="http://www.w3.org/2001/XMLSchema#date">2009-06-06</po:schedule_date>
		#    <event:time>
		#        <timeline:Interval>
		#              <timeline:start rdf:datatype="http://www.w3.org/2001/XMLSchema#dateTime">2009-06-06T21:30:00+01:00</timeline:start>
		for ( split /<po:(First|Repeat)?Broadcast/, $rdf ) {
			my $timestring;
			my $epoch;
			$timestring = $1 if m{<timeline:start\s+rdf:datatype=".+?">(20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d([+-]\d\d:\d\d|Z))<};
			next if ! $timestring;
			$epoch = Programme::get_time_string( $timestring );
			main::logger "DEBUG: $version: $timestring -> $epoch\n" if $opt->{debug};
			if ( $epoch < $first ) {
				$first = $epoch;
				$first_string = $timestring;
			}
			if ( $now > $epoch && $epoch > $last ) {
				$last = $epoch;
				$last_string = $timestring;
			}
		}
		# Only set these attribs if required
		if ( $first < 9999999999 && $last > 0 ) {
			$prog->{firstbcast}->{$version} = $first_string;
			$prog->{lastbcast}->{$version} = $last_string;
			$prog->{firstbcastrel}->{$version} = Programme::get_time_string( $first_string, time() );
			$prog->{lastbcastrel}->{$version} = Programme::get_time_string( $last_string, time() );
			($prog->{firstbcastdate}->{$version} = $first_string) =~ s/T.*$//;
			($prog->{lastbcastdate}->{$version} = $last_string) =~ s/T.*$//;
		}
	}

	my @fields1 = qw(verpids streams durations);
	my @fields2 = qw(firstbcast lastbcast firstbcastrel lastbcastrel firstbcastdate lastbcastdate);
	
	# remove versions with no streams
	for my $version ( sort keys %{ $prog->{verpids} } ) {
		if ( ! $modes->{$version} || $modes->{$version} =~ /^subtitles\d+$/ ) {
			main::logger "INFO: No streams available for '$version' version ($prog->{verpids}->{$version}) - deleting\n" if $opt->{verbose};
			delete $modes->{$version};
			delete $mode_sizes->{$version};
			for my $key ( @fields1, @fields2 ) {
	 			delete $prog->{$key}->{$version};
			}
		}
	}

	# collapse alternate versions with same base name
	for my $version ( sort keys %{ $prog->{verpids} } ) {
		next if $version !~ /\d+$/;
		next if ! $modes->{$version};
		(my $base_version = $version) =~ s/\d+$//;
		if ( ! $modes->{$base_version} || $prog->{durations}->{$base_version} < $prog->{durations}->{$version} ) {
			main::logger "INFO: Using '$version' version ($prog->{verpids}->{$version}) as '$base_version'\n" if $opt->{verbose};
			$modes->{$base_version} = $modes->{$version};
			$mode_sizes->{$base_version} = $mode_sizes->{$version};
			for my $key ( @fields1 ) {
				$prog->{$key}->{$base_version} = $prog->{$key}->{$version};
			}
			if ( $prog->{firstbcast}->{$version} ) {
				for my $key ( @fields2 ) {
					$prog->{$key}->{$base_version} = $prog->{$key}->{$version};
				}
			}
			delete $modes->{$version};
			delete $mode_sizes->{$version};
			for my $key ( @fields1, @fields2 ) {
	 			delete $prog->{$key}->{$version};
			}
		}
	}

	my @default_versions = $prog->default_version_list();
	# incorporate unknown versions
	for my $version ( sort keys %{ $prog->{verpids} } ) {
		if ( ! grep /^${version}$/, @default_versions ) {
			push @default_versions, $version;
		}
	}
	
	# use first/longest available variants, ensure default version if possible
	for my $version ( @default_versions ) {
		next if $version =~ /(audiodescribed|signed)/;
		next if ! $modes->{$version};
		my $base_version = "default";
		if ( ! $modes->{$base_version} || $prog->{durations}->{$base_version} < $prog->{durations}->{$version} ) {
			main::logger "INFO: Using '$version' version ($prog->{verpids}->{$version}) as '$base_version'\n" if $version ne "default" && $opt->{verbose};
			$modes->{$base_version} = $modes->{$version};
			$mode_sizes->{$base_version} = $mode_sizes->{$version};
			for my $key ( @fields1 ) {
				$prog->{$key}->{$base_version} = $prog->{$key}->{$version};
			}
			if ( $prog->{firstbcast}->{$version} ) {
				for my $key ( @fields2 ) {
					$prog->{$key}->{$base_version} = $prog->{$key}->{$version};
				}
			}
			# delete $modes->{$version};
			# delete $mode_sizes->{$version};
			# for my $key ( @fields1, @fields2 ) {
			# 	delete $prog->{$key}->{$version};
			# }
		}
	}
	if ( ! $modes->{default} ) {
		main::logger "WARNING: The 'default' programme version could not be determined\n";
	}

	# check at least one version available
	if ( keys %{ $prog->{verpids} } == 0 ) {
		main::logger "WARNING: No programme versions found\n";
		main::logger "WARNING: You may receive this message if you are using get_iplayer outside the UK\n";
		# Return at this stage unless we want metadata/tags only for various reasons
		return 1 if ! ( $opt->{info} || $opt->{metadataonly} || $opt->{thumbonly} || $opt->{tagonly} )
	}

	$versions = join ',', sort keys %{ $prog->{verpids} };

	$prog->{title} 		= $title || $prog->{title};
	$prog->{name} 		= $name || $prog->{name};
	$prog->{episode} 	= $episode || $prog->{episode} || $prog->{name};
	$prog->{brand} 	= $brand || $prog->{name};
	$prog->{series} 	= $series;
	$prog->{type}		= $prog_type || $prog->{type};
	$prog->{channel}	= $channel || $prog->{channel};
	$prog->{expiry}		= $expiry;
	$prog->{versions}	= $versions;
	$prog->{guidance}	= $guidance || $prog->{guidance};
	$prog->{categories}	= $categories || $prog->{categories};
	$prog->{category}	= $category || $prog->{category};
	$prog->{desc}		= $summary || $prog->{desc} || $prog->{descshort};
	$prog->{desclong}	= $longdesc || $meddesc || $summary || $prog->{desclong};
	$prog->{descmedium}	= $meddesc || $summary || $prog->{descmedium};
	$prog->{descshort}	= $summary || $prog->{descshort};
	$prog->{player}		= $player || $prog->{player};
	$prog->{web}		= $web || $prog->{web};
	$prog->{thumbnail}	= $thumbnail || $prog->{thumbnail};
	$prog->{modes}		= $modes;
	$prog->{modesizes}	= $mode_sizes;
	$prog->{episodenum}	= $episodenum || $prog->{episodenum};
	$prog->{episodepart}	= $episodepart || $prog->{episodepart};
	$prog->{seriesnum}	= $seriesnum || $prog->{seriesnum};
	# Conditionally set the senum
	$prog->{senum} = sprintf "s%02se%02s%s", $prog->{seriesnum}, $prog->{episodenum}, $prog->{episodepart} if $prog->{seriesnum} != 0 || $prog->{episodenum} != 0;
	# Create a stripped episode and series with numbers removed + senum s##e## element.
	$prog->{episodeshort} = $prog->{episode};
	$prog->{episodeshort} =~ s/(^|:(\s+))\d+[a-z]?\.\s+/$1/i;
	my $no_number = $prog->{episodeshort};
	$prog->{episodeshort} =~ s/:?\s*Episode\s+.+?(:\s*|$)//i;
	$prog->{episodeshort} =~ s/:?\s*Series\s+.+?(:\s*|$)//i;
	$prog->{episodeshort} = $no_number if $prog->{episodeshort} eq '';
	$prog->{nameshort} = $prog->{brand};
	$prog->{nameshort} =~ s/:?\s*Series\s+\d.*?(:\s*|$)//i;
	return 0;
}

sub get_metadata_fallback {
	my $prog = shift;
	my $ua = shift;
	my $prog_data_url = 'http://www.bbc.co.uk/programmes/'; # $pid
	my @ignore_categories = ("Films", "Sign Zone", "Audio Described", "Northern Ireland", "Scotland", "Wales", "England");
	my ($name, $episode, $seriesnum, $episodenum, @categories, $categories );
	# Even more info...
	#<?xml version="1.0" encoding="utf-8"?>
	#<rdf:RDF xmlns:rdf      = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
	#         xmlns:rdfs     = "http://www.w3.org/2000/01/rdf-schema#"
	#         xmlns:foaf     = "http://xmlns.com/foaf/0.1/"
	#         xmlns:po       = "http://purl.org/ontology/po/"
	#         xmlns:mo       = "http://purl.org/ontology/mo/"
	#         xmlns:skos     = "http://www.w3.org/2008/05/skos#"
	#         xmlns:time     = "http://www.w3.org/2006/time#"
	#         xmlns:dc       = "http://purl.org/dc/elements/1.1/"
	#         xmlns:dcterms  = "http://purl.org/dc/terms/"
	#         xmlns:wgs84_pos= "http://www.w3.org/2003/01/geo/wgs84_pos#"
	#         xmlns:timeline = "http://purl.org/NET/c4dm/timeline.owl#"
	#         xmlns:event    = "http://purl.org/NET/c4dm/event.owl#">
	#
	#<rdf:Description rdf:about="/programmes/b00mbvmz.rdf">
	#  <rdfs:label>Description of the episode Episode 5</rdfs:label>
	#  <dcterms:created rdf:datatype="http://www.w3.org/2001/XMLSchema#dateTime">2009-08-17T00:16:16+01:00</dcterms:created>
	#  <dcterms:modified rdf:datatype="http://www.w3.org/2001/XMLSchema#dateTime">2009-08-21T16:09:30+01:00</dcterms:modified>
	#  <foaf:primaryTopic rdf:resource="/programmes/b00mbvmz#programme"/>
	#</rdf:Description>
	#
	#<po:Episode rdf:about="/programmes/b00mbvmz#programme">
	#
	#  <dc:title>Episode 5</dc:title>
	#  <po:short_synopsis>Jem Stansfield tries to defeat the US Navy&#39;s latest weapon with foam and a crash helmet.</po:short_synopsis>
	#  <po:medium_synopsis>Jem Stansfield attempts to defeat the US Navy&#39;s latest weapon with no more than some foam and a crash helmet, while zoologist Liz Bonnin gets in contact with her frog brain.</po:medium_synopsis>
	#  <po:long_synopsis>Jem Stansfield attempts to defeat the US Navy&#39;s latest weapon with no more than some foam and a crash helmet.
	#
	#Zoologist Liz Bonnin gets in contact with her frog brain, Dallas Campbell re-programmes his caveman brain to become a thrill-seeker, and Dr Yan Wong gets his thrills from inhaling sulphur hexafluoride.
	#The programme is co-produced with The Open University.
	#For more ways to put science to the test, go to the Hands-on Science area at www.bbc.co.uk/bang for details of our free roadshow touring the UK and activities that you can try at home.</po:long_synopsis>
	#  <po:microsite rdf:resource="http://www.bbc.co.uk/bang"/>
	#  <po:masterbrand rdf:resource="/bbcone#service"/>
	#  <po:position rdf:datatype="http://www.w3.org/2001/XMLSchema#int">5</po:position>
	#  <po:genre rdf:resource="/programmes/genres/factual/scienceandnature/scienceandtechnology#genre" />
	#  <po:version rdf:resource="/programmes/b00mbvhc#programme" />
	#
	#</po:Episode>
	#
	#<po:Series rdf:about="/programmes/b00lywwy#programme">
	#  <po:episode rdf:resource="/programmes/b00mbvmz#programme"/>
	#</po:Series>
	#
	#<po:Brand rdf:about="/programmes/b00lwxj1#programme">
	#  <po:episode rdf:resource="/programmes/b00mbvmz#programme"/>
	#</po:Brand>
	#</rdf:RDF>
	# Get metadata from this URL only if the pid contains a standard BBC iPlayer PID)

	if ( $prog->{pid} =~ /^[bp]0[a-z0-9]{6}$/ ) {
		my $rdf_url = $prog_data_url.$prog->{pid}.'.rdf';
		my $entry = main::request_url_retry($ua, $rdf_url, 3, '', '');
		decode_entities($entry);
		main::logger "DEBUG: $rdf_url:\n$entry\n\n" if $opt->{debug};
		$prog->{desclong} = $1 if $entry =~ m{<po:long_synopsis>\s*(.+?)\s*</po:long_synopsis>}s;
		# Flatten
		$entry =~ s|[\n\r]| |g;
		$prog->{descmedium} = $1 if $entry =~ m{<po:medium_synopsis>\s*(.+?)\s*</po:medium_synopsis>};
		$prog->{descshort} = $1 if $entry =~ m{<po:short_synopsis>\s*(.+?)\s*</po:short_synopsis>};
		# extract categories from RDF
		if ( ! $prog->{categories} ) {
			my $genres = genres();
			my $subgenres = subgenres();
			my $subsubgenres = subsubgenres();
			my $formats = formats();
			my @cats;
			for my $po_genre (split /<po:genre/, $entry) {
				my ($genre, $subgenre, $subsubgenre) = ($1, $3, $5) if $po_genre =~ m{/programmes/genres/(\w+)(/(\w+)(/(\w+))?)?};
				next unless $genre;
				my $format = $1 if $po_genre =~ m{/programmes/formats/(\w+)};
				my $genre_title = $genres->{$genre};
				push @cats, $genre_title if $genre_title;
				if ( $subgenre ) {
					my $subgenre_title = $subgenres->{$genre}->{$subgenre};
					push @cats, $subgenre_title if $subgenre_title;
				}
				if ( $subsubgenre ) {
					my $subsubgenre_title = $subsubgenres->{$genre}->{$subgenre}->{$subsubgenre};
					push @cats, $subsubgenre_title if $subsubgenre_title;
				}
				if ( $format ) {
					my $format_title = $formats->{$format};
					push @cats, $format_title if $format_title;
				}
			}
			my %seen;
			@categories = grep { ! $seen{$_}++ } @cats;
		}
	}
	if ( $#categories >= 0 ) {
		$prog->{categories} = join(',', @categories);
	}
	# capture first category, skip generic values
	foreach my $cat ( split(/,/, $prog->{categories}) ) {
		if ( ! grep(/$cat/i,  @ignore_categories) ) {
			$prog->{category} = $cat;
			last;
		}
	}
	$prog->{categories} ||= "get_iplayer";
	$prog->{category} ||= "get_iplayer";

	unless ( $prog->{name} && $prog->{episode} ) {
		# $prog->{title} should be set in get_verpids()
		( $name, $episode ) = Programme::bbciplayer::split_title( $prog->{title} );
		$prog->{name} ||= $name;
		$prog->{episode} ||= $episode;
	}
	
	unless ( $prog->{seriesnum} && $prog->{episodenum} ) {

		unless ( $prog->{seriesnum} ) {
			# Extract the seriesnum
			my $regex = 'Series\s+'.main::regex_numbers();
			# Extract the seriesnum
			if ( "$prog->{name} $prog->{episode}" =~ m{$regex}i ) {
				$seriesnum = main::convert_words_to_number( $1 );
			} elsif ( "$name $episode" =~ m{$regex}i ) {
				$seriesnum = main::convert_words_to_number( $1 );
			}
		}

		unless ( $prog->{episodenum} ) {
			# Extract the episode num
			my $regex_1 = 'Episode\s+'.main::regex_numbers();
			my $regex_2 = '^'.main::regex_numbers().'\.\s+';
			if ( "$prog->{name} $prog->{episode}" =~ m{$regex_1}i ) {
				$episodenum = main::convert_words_to_number( $1 );
			} elsif ( "$name $episode" =~ m{$regex_1}i ) {
				$episodenum = main::convert_words_to_number( $1 );
			} elsif ( $prog->{episode} =~ m{$regex_2}i ) {
				$episodenum = main::convert_words_to_number( $1 );
			} elsif ( $episode =~ m{$regex_2}i ) {
				$episodenum = main::convert_words_to_number( $1 );
			}
		}

		$prog->{seriesnum} ||= $seriesnum;
		$prog->{episodenum} ||= $episodenum;
		# insert episode number in $episode
		$prog->{episode} = Programme::bbciplayer::insert_episode_number($prog->{episode}, $prog->{episodenum});
		# minimum episode number = 1 if not a film and series number == 0
		$prog->{episodenum} = 1 if ( $prog->{seriesnum} == 0 && $prog->{episodenum} == 0 && $prog->{type} eq 'tv' && $prog->{categories} !~ "Films" );
		# minimum series number = 1 if episode number != 0
		$prog->{seriesnum} = 1 if ( $prog->{seriesnum} == 0 && $prog->{episodenum} != 0 );
	}

	unless ( $prog->{player} ) {
		if ( $prog->{pid} =~ /^[bp]0[a-z0-9]{6}$/ ) {
			if ( $prog->{type} eq "tv" ) {
				$prog->{player} = "http://www.bbc.co.uk/iplayer/episode/$prog->{pid}";
			} else {
				$prog->{player} = "http://www.bbc.co.uk/programmes/$prog->{pid}";
			}
		}
	}

}

sub genres {
	return {
		childrens => "Children's", 
		comedy => "Comedy", 
		drama => "Drama", 
		entertainment => "Entertainment", 
		factual => "Factual", 
		learning => "Learning", 
		weather => "Weather",
		music => "Music", 
		news => "News",
		religionandethics => "Religion & Ethics",
		sport => "Sport", 
		weather => "Weather",
	};
}

sub subgenres {
	return {
		childrens => {
			activities => "Activities",
			drama => "Drama",
			entertainmentandcomedy => "Entertainment & Comedy",
			factual => "Factual",
			music => "Music",
			news => "News",
			sport => "Sport",
		},
		comedy => {
			character => "Character",
			impressionists => "Impressionists",
			music => "Music",
			satire => "Satire",
			sitcoms => "Sitcoms",
			sketch => "Sketch",
			spoof => "Spoof",
			standup => "Standup",
			stunt => "Stunt",
		},
		drama => {
			actionandadventure => "Action & Adventure",
			biographical => "Biographical",
			classicandperiod => "Classic & Period",
			crime => "Crime",
			historical => "Historical",
			horrorandsupernatural => "Horror & Supernatural",
			legalandcourtroom => "Legal & Courtroom",
			medical => "Medical",
			musical => "Musical",
			political => "Political",
			psychological => "Psychological",
			relationshipsandromance => "Relationships & Romance",
			scifiandfantasy => "SciFi & Fantasy",
			soaps => "Soaps",
			spiritual => "Spiritual",
			thriller => "Thriller",
			waranddisaster => "War & Disaster",
			western => "Western",
		},
		entertainment => {
			varietyshows => "Variety Shows",
		},
		factual => {
			antiques => "Antiques",
			artscultureandthemedia => "Arts Culture & the Media",
			beautyandstyle => "Beauty & Style",
			carsandmotors => "Cars & Motors",
			consumer => "Consumer",
			crimeandjustice => "Crime & Justice",
			disability => "Disability",
			familiesandrelationships => "Families & Relationships",
			foodanddrink => "Food & Drink",
			healthandwellbeing => "Health & Wellbeing",
			history => "History",
			homesandgardens => "Homes & Gardens",
			lifestories => "Life Stories",
			money => "Money",
			petsandanimals => "Pets & Animals",
			politics => "Politics",
			scienceandnature => "Science & Nature",
			travel => "Travel",
		},
		learning => {
			adults => "Adults",
			preschool => "Pre-School",
			primary => "Primary",
			secondary => "Secondary",
		},
		music => {
			classicpopandrock => "Classic Pop & Rock",
			classical => "Classical",
			country => "Country",
			danceandelectronica => "Dance & Electronica",
			desi => "Desi",
			easylisteningsoundtracksandmusicals => "Easy Listening Soundtracks & Musicals",
			folk => "Folk",
			hiphoprnbanddancehall => "Hip Hop RnB & Dancehall",
			jazzandblues => "Jazz & Blues",
			popandchart => "Pop & Chart",
			rockandindie => "Rock & Indie",
			soulandreggae => "Soul & Reggae",
			world => "World",
		},
		news => {
		},
		religionandethics => {
		},
		sport => {
			alpineskiing => "Alpine Skiing",
			americanfootball => "American Football",
			archery => "Archery",
			athletics => "Athletics",
			badminton => "Badminton",
			baseball => "Baseball",
			basketball => "Basketball",
			beachvolleyball => "Beach Volleyball",
			biathlon => "Biathlon",
			bobsleigh => "Bobsleigh",
			bowls => "Bowls",
			boxing => "Boxing",
			canoeing => "Canoeing",
			commonwealthgames => "Commonwealth Games",
			cricket => "Cricket",
			crosscountryskiing => "Cross Country Skiing",
			curling => "Curling",
			cycling => "Cycling",
			darts => "Darts",
			disabilitysport => "Disability Sport",
			diving => "Diving",
			equestrian => "Equestrian",
			fencing => "Fencing",
			figureskating => "Figure Skating",
			football => "Football",
			formulaone => "Formula One",
			freestyleskiing => "Freestyle Skiing",
			gaelicgames => "Gaelic Games",
			golf => "Golf",
			gymnastics => "Gymnastics",
			handball => "Handball",
			hockey => "Hockey",
			horseracing => "Horse Racing",
			icehockey => "Ice Hockey",
			judo => "Judo",
			luge => "Luge",
			modernpentathlon => "Modern Pentathlon",
			motorsport => "Motorsport",
			netball => "Netball",
			nordiccombined => "Nordic Combined",
			olympics => "Olympics",
			rowing => "Rowing",
			rugbyleague => "Rugby League",
			rugbyunion => "Rugby Union",
			sailing => "Sailing",
			shinty => "Shinty",
			shooting => "Shooting",
			shorttrackskating => "Short Track Skating",
			skeleton => "Skeleton",
			skijumping => "Ski Jumping",
			snooker => "Snooker",
			snowboarding => "Snowboarding",
			softball => "Softball",
			speedskating => "Speed Skating",
			squash => "Squash",
			swimming => "Swimming",
			synchronisedswimming => "Synchronised Swimming",
			tabletennis => "Table Tennis",
			taekwondo => "Taekwondo",
			tennis => "Tennis",
			triathlon => "Triathlon",
			volleyball => "Volleyball",
			waterpolo => "Water Polo",
			weightlifting => "Weightlifting",
			winterolympics => "Winter Olympics",
			wintersports => "Winter Sports",
			wrestling => "Wrestling",
		},
		weather => {
		}
	};
}

sub subsubgenres {
	return {
		factual => {
			artscultureandthemedia => {
				arts => "Arts"
			},
			scienceandnature => {
				natureandenvironment => "Nature & Environment",
				scienceandtechnology => "Science & Technology"
			},
		},
		music => {
			classicpopandrock => {
				experimentalandnew => "Experimental & New",
			},
			classical => {
				chamberandrecital => "Chamber & Recital",
				choral => "Choral",
				earlymusic => "Early Music",
				experimentalandnew => "Experimental & New",
				opera => "Opera",
				orchestral => "Orchestral"
			},
			country => {
				experimentalandnew => "Experimental & New",
			},
			folk => {
				experimentalandnew => "Experimental & New",
			},			
			hiphoprnbanddancehall => {
				hiphop => " Hip Hop",
				rnb => " RnB",
			},
			jazzandblues => {
				blues => "Blues",
				experimentalandnew => "Experimental & New",
				jazz => "Jazz",
			},
			soulandreggae => {
				gospel => "Gospel",
				reggae => "Reggae",
				soul => "Soul",
			},
			world => {
				africa => "Arrica",
				americas => "Americas",
				asiapacific => "Asia Pacific",
				europe => "Europe",
			},
		},
		sport => {
			rugbyunion => {
				rugbyworldcup => "Rugby World Cup",
			},
		}
	}
}

sub formats {
	return {
		animation => "Animation",
		appeals => "Appeals",
		bulletins => "Bulletins",
		discussionandtalk => "Discussion & Talk",
		docudramas => "Docudramas",
		documentaries => "Documentaries",
		films => "Films",
		gamesandquizzes => "Games & Quizzes",
		magazinesandreviews => "Magazines & Reviews",
		makeovers => "Makeovers",
		performancesandevents => "Performances & Events",
		phoneins => "Phone-ins",
		readings => "Readings",
		reality => "Reality",
		talentshows => "Talent Shows",
	};
}

sub get_pids_recursive {
	my $prog = shift;
	my $ua = main::create_ua( 'desktop' );
	my @pids = ();

	# Clean up the pid
	main::logger "Cleaning pid Old: '$prog->{pid}', " if $opt->{verbose};
	$prog->clean_pid();
	main::logger " New: '$prog->{pid}'\n" if $opt->{verbose};

	# Skip RDF retrieval if a web URL
	return $prog->{pid} if $prog->{pid} =~ '^http';

	eval "use XML::Simple";
	if ($@) {
		main::logger "WARNING: Please download and run latest installer or install the XML::Simple Perl module to use the Series and Brand parsing functionality\n";
		push @pids, $prog->{pid};
	} else {
		#use Data::Dumper qw(Dumper);
		my $rdf = get_rdf_data( $ua, $prog->{pid} );
		if ( ! $rdf ) {
			main::logger "WARNING: PID URL contained no RDF data. Trying to record PID directly.\n";
			return $prog->{pid};
		}
		# an episode-only pid page
		if ( $rdf->{'po:Episode'} ) {
			main::logger "INFO: Episode-only pid detected\n";
			# No need to lookup - we already are an episode pid
			push @pids, $prog->{pid};
		} elsif ( $rdf->{'po:Clip'} ) {
			main::logger "INFO: Clip-only pid detected\n";
			# No need to lookup - we already are a clip pid
			push @pids, $prog->{pid};
		# a series pid page
		} elsif ( $rdf->{'po:Series'} ) {
			main::logger "INFO: Series pid detected\n";
			push @pids, parse_rdf_series( $ua, $prog->{pid} );
			if ( ! $opt->{pidrecursive} ) {
				main::logger "INFO: Please run the command again using one of the above episode PIDs or to get all programmes add the --pid-recursive option\n";
				return ();
			}
		# a brand pid page
		} elsif ( $rdf->{'po:Brand'} ) {
			main::logger "INFO: Brand pid detected\n";
			push @pids, parse_rdf_brand( $ua, $prog->{pid} );
			if ( ! $opt->{pidrecursive} ) {
				main::logger "INFO: Please run the command again using one of the above episode PIDs or to get all programmes add the --pid-recursive option\n";
				return ();
			}
		}
	}
	# now make list unique
	@pids = main::make_array_unique_ordered( @pids );
	return @pids;
}

sub ensure_array {
	my ($in) = @_;
	return ref $in eq 'ARRAY' ? @$in : $in;
}

# Gets the episode data from a given episode pid
sub parse_rdf_episode {
	my $ua = shift;
	my $uri = shift;
	my $rdf = get_rdf_data( $ua, $uri );
	if ( ! $rdf ) {
		main::logger "WARNING: Episode PID rdf URL contained no RDF data.\n";
		return '';
	}
	my $pid = extract_pid( $uri );
	main::logger "INFO:      Episode '".$rdf->{'po:Episode'}->{'dc:title'}."' ($pid)\n";
	# We don't really need the ver pids from here
	if ( ref$rdf->{'po:Episode'}->{'po:version'} eq 'ARRAY' ) {
		for my $verpid_element ( @{ $rdf->{'po:Episode'}->{'po:version'} } ) {
			main::logger "INFO:        With Version PID '".extract_pid( $verpid_element->{'rdf:resource'} )."'\n" if $opt->{debug};
		}
	} else {
		main::logger "INFO:        With Version PID '".extract_pid( $rdf->{'po:Episode'}->{'po:version'}->{'rdf:resource'} )."'\n" if $opt->{debug};
	}
	main::logger "INFO:        From Series PID '".extract_pid( $rdf->{'po:Series'}->{'rdf:about'} )."'\n" if $opt->{debug};
	main::logger "INFO:        From Brand PID '".extract_pid( $rdf->{'po:Brand'}->{'rdf:about'} )."'\n" if $opt->{debug};
}



# Gets the clip data from a given clip pid
sub parse_rdf_clip {
	my $ua = shift;
	my $uri = shift;
	my $rdf = get_rdf_data( $ua, $uri );
	if ( ! $rdf ) {
		main::logger "WARNING: Clip PID rdf URL contained no RDF data.\n";
		return '';
	}
	my $pid = extract_pid( $uri );
	main::logger "INFO:      Clip '".$rdf->{'po:Clip'}->{'dc:title'}."' ($pid)\n";
	# We don't really need the ver pids from here
	if ( ref$rdf->{'po:Clip'}->{'po:version'} eq 'ARRAY' ) {
		for my $verpid_element ( @{ $rdf->{'po:Clip'}->{'po:version'} } ) {
			main::logger "INFO:        With Version PID '".extract_pid( $verpid_element->{'rdf:resource'} )."'\n" if $opt->{debug};
		}
	} else {
		main::logger "INFO:        With Version PID '".extract_pid( $rdf->{'po:Clip'}->{'po:version'}->{'rdf:resource'} )."'\n" if $opt->{debug};
	}
	#main::logger "INFO:        From Series PID '".extract_pid( $rdf->{'po:Series'}->{'rdf:about'} )."'\n" if $opt->{debug};
	main::logger "INFO:        From Brand PID '".extract_pid( $rdf->{'po:Brand'}->{'rdf:about'} )."'\n" if $opt->{debug};
}



sub parse_rdf_series {
	my $ua = shift;
	my $uri = shift;
	my $rdf = get_rdf_data( $ua, $uri );
	if ( ! $rdf ) {
		main::logger "WARNING: Series PID rdf URL contained no RDF data.\n";
		return '';
	}
	my @pids = ();
	my $spid = extract_pid( $rdf->{'po:Series'}->{'rdf:about'} );
	main::logger "INFO:    Series: '".$rdf->{'po:Series'}->{'dc:title'}."' ($spid)\n";
	main::logger "INFO:      From Brand PID '".$rdf->{'po:Brand'}->{'rdf:about'}."'\n" if $opt->{debug};
	for my $episode_element (ensure_array($rdf->{'po:Series'}->{'po:episode'})) {
		my $pid = extract_pid( $episode_element->{'po:Episode'}->{'rdf:about'} );
		main::logger "INFO:      Episode '".$episode_element->{'po:Episode'}->{'dc:title'}."' ($pid)\n";
		push @pids, $pid;
		#parse_rdf_episode( $ua, $pid );
	}
	return @pids;
}



sub parse_rdf_brand {
	my $ua = shift;
	my $uri = shift;
	my $rdf = get_rdf_data( $ua, $uri );
	if ( ! $rdf ) {
		main::logger "WARNING: Brand PID rdf URL contained no RDF data.\n";
		return '';
	}
	my @pids = ();
	my $bpid = extract_pid( $uri );
	main::logger "INFO:  Brand: '".$rdf->{'po:Brand'}->{'dc:title'}."' ($bpid)\n";
	for my $series_element ( ensure_array($rdf->{'po:Brand'}->{'po:series'}) ) {
		main::logger "INFO: With Series pid '".$series_element->{'rdf:resource'}."'\n" if $opt->{debug};
		push @pids, parse_rdf_series( $ua, $series_element->{'rdf:resource'} );
	}
	my @episodes = ensure_array($rdf->{'po:Brand'}->{'po:episode'});
	main::logger "INFO:    Series: <None>\n" if @episodes;
	for my $episode_element ( @episodes ) {
		main::logger "INFO:      Episode pid: ".$episode_element->{'rdf:resource'}."\n" if $opt->{debug};
		push @pids, extract_pid( $episode_element->{'rdf:resource'} );
		parse_rdf_episode( $ua, $episode_element->{'rdf:resource'} );
	}
	my @clips = ensure_array($rdf->{'po:Brand'}->{'po:clip'});
	for my $clip_element ( @clips ) {
		main::logger "INFO:      Clip pid: ".$clip_element->{'rdf:resource'}."\n" if $opt->{debug};
		push @pids, extract_pid( $clip_element->{'rdf:resource'} );
		parse_rdf_clip( $ua, $clip_element->{'rdf:resource'} );
	}
	return @pids;
}



# Extracts and returns a pid from a URI/URL
sub extract_pid {
	return $1 if $_[0] =~ m{/?([wpb]0[a-z0-9]{6})};
	return '';
}



# Given a pid, gets the rdf URL and returns an XML::Simple object
sub get_rdf_data {
	eval "use XML::Simple";
	if ($@) {
		main::logger "WARNING: Please download and run latest installer or install the XML::Simple Perl module to use the Series and Brand parsing functionality\n";
		return;
	}
	#use Data::Dumper qw(Dumper);
	my $ua = shift;
	my $uri = shift;
	my $pid = extract_pid( $uri );
	my $entry = main::request_url_retry($ua, 'http://www.bbc.co.uk/programmes/'.$pid.'.rdf', 3, '', '');
	if ( ! $entry ) {
		main::logger "WARNING: rdf URL contained no data\n";
		return '';
	}
	# Flatten
	$entry =~ s|[\n\r]| |g;
	my $simple = new XML::Simple();
	my $rdf = $simple->XMLin( $entry );
	#main::logger Dumper ( $rdf )."\n" if $opt->{debug};
	return $rdf;
}



# Intelligently split name and episode from title string for BBC iPlayer metadata
sub split_title {
	my $title = shift;
	my ( $name, $episode );
	# <title type="text">The Sarah Jane Adventures: Series 1: Revenge of the Slitheen: Part 2</title>
	# <title type="text">The Story of Tracy Beaker: Series 4 Compilation: Independence Day/Beaker Witch Project</title>
	# <title type="text">The Sarah Jane Adventures: Series 1: The Lost Boy: Part 2</title>
	if ( $title =~ m{^(.+?Series.*?):\s+(.+?)$} ) {
		( $name, $episode ) = ( $1, $2 );
	} elsif ( $title =~ m{^(.+?):\s+(.+)$} ) {
		( $name, $episode ) = ( $1, $2 );
	# Catch all - i.e. no ':' separators
	} else {
		( $name, $episode ) = ( $title, '-' );
	}
	return ( $name, $episode );
}


sub insert_episode_number {
	my $episode = shift;
	my $episodenum = shift;
	my $episodepart = shift;
	#my $episode_regex = 'Episode\s+'.main::regex_numbers();
	#my $date_regex = '^(\d{2}\/\d{2}\/\d{4}|\d{4}\-\d{2}\-\d{2})';
	if ( $episodenum && $episode !~ /^\d+[a-z]?\./ ) { #&& $episode !~ /$episode_regex/ && $episode !~ /$date_regex/ ) {
		$episode =~ s/^(.*)$/$episodenum$episodepart. $1/;
	}
	return $episode;
}


# Returns hash
sub thumb_url_suffixes {
	return {
		86	=> '_86_48.jpg',
		150	=> '_150_84.jpg',
		178	=> '_178_100.jpg',
		512	=> '_512_288.jpg',
		528	=> '_528_297.jpg',
		640	=> '_640_360.jpg',
		832	=> '_832_468.jpg',
		1024	=> '_1024_576.jpg',
		1280	=> '_1280_720.jpg',
		1600	=> '_1600_900.jpg',
		1920	=> '_1920_1080.jpg',
		1	=> '_86_48.jpg',
		2	=> '_150_84.jpg',
		3	=> '_178_100.jpg',
		4	=> '_512_288.jpg',
		5	=> '_528_297.jpg',
		6	=> '_640_360.jpg',
		7	=> '_832_468.jpg',
		8	=> '_1024_576.jpg',
		9	=> '_1280_720.jpg',
		10	=> '_1600_900.jpg',
		11	=> '_1920_1080.jpg',
	}
}


sub thumb_url_recipes {
	return {
		86	=> '86x48',
		150	=> '150x84',
		178	=> '178x100',
		512	=> '512x288',
		528	=> '528x297',
		640	=> '640x360',
		832	=> '832x468',
		1024	=> '1024x576',
		1280	=> '1280x720',
		1600	=> '1600x900',
		1920	=> '1920x1080',
		1	=> '86x48',
		2	=> '150x84',
		3	=> '178x100',
		4	=> '512x288',
		5	=> '528x297',
		6	=> '640x360',
		7	=> '832x468',
		8	=> '1024x576',
		9	=> '1280x720',
		10	=> '1600x900',
		11	=> '1920x1080',
	}
}


#new_stream_report($mattribs, $cattribs)
sub new_stream_report {
	my $mattribs = shift;
	my $cattribs = shift;
	
	main::logger "New BBC iPlayer Stream Found:\n";
	main::logger "MEDIA-ELEMENT:\n";
		
	# list media attribs
	main::logger "MEDIA-ATTRIBS:\n";
	for (keys %{ $mattribs }) {
		main::logger "\t$_ => $mattribs->{$_}\n";
	}
	
	my @conn;
	if ( defined $cattribs ) {
		@conn = ( $cattribs );
	} else {
		@conn = @{ $mattribs->{connections} };
	}
	for my $cattribs ( @conn ) {
		main::logger "\tCONNECTION-ELEMENT:\n";
			
		# Print attribs
		for (keys %{ $cattribs }) {
			main::logger "\t\t$_ => $cattribs->{$_}\n";
		}	
	}
	return 0;
}



sub parse_metadata {
	my @medias;
	my $xml = shift;
	my %elements;

	# Parse all 'media' elements
	my $element = 'media';
	while ( $xml =~ /<$element\s+(.+?)>(.+?)<\/$element>/sg ) {
		my $xml = $2;
		my $mattribs = parse_attributes( $1 );

		# Parse all 'connection' elements
		my $element = 'connection';
		while ( $xml =~ /<$element\s+(.+?)\/>/sg ) {
			# push to data structure
			push @{ $mattribs->{connections} }, parse_attributes( $1 );
		}
		# mediaselector 5 -> 4 compatibility
		for my $cattribs ( @{ $mattribs->{connections} } ) {
			if ( ! $cattribs->{kind} && $cattribs->{supplier} ) {
				$cattribs->{kind} = $cattribs->{supplier};
			}
		}
		push @medias, $mattribs;
	}


	# Parse and dump structure
	if ( $opt->{debug} ) {
		for my $mattribs ( @medias ) {
			main::logger "MEDIA-ELEMENT:\n";
		
			# list media attribs
			main::logger "MEDIA-ATTRIBS:\n";
			for (keys %{ $mattribs }) {
				main::logger "\t$_ => $mattribs->{$_}\n";
			}

			for my $cattribs ( @{ $mattribs->{connections} } ) {
				main::logger "\tCONNECTION-ELEMENT:\n";
			
				# Print attribs
				for (keys %{ $cattribs }) {
					main::logger "\t\t$_ => $cattribs->{$_}\n";
				}	
			}
		}	
	}
	
	return @medias;
}



sub parse_attributes {
	$_ = shift;
	my $attribs;
	# Parse all attributes
	while ( /([\w]+?)="(.*?)"/sg ) {
		$attribs->{$1} = $2;
	}
	return $attribs;
}


sub parse_hds_connection {
	my $media = shift;
	my $conn = shift;
	my $min_bitrate = shift;
	my @hds_medias;
	eval "use XML::Simple";
	if ( $@ ) {
		main::logger "WARNING: Please download and run latest installer or install the XML::Simple Perl module to parse f4m manifests.\n";
	} else {
		my $ua = main::create_ua( 'desktop' );
		my $xml = main::request_url_retry( $ua, $conn->{href}, 3, undef, undef, 1 );
		my $doc = eval { XMLin($xml, KeyAttr => [], ForceArray => 1, SuppressEmpty => 1) };
		if ( ! $@ ) {
			for my $hds_media ( @{$doc->{media} }) {
				next if $min_bitrate && $hds_media->{bitrate} < $min_bitrate;
				my $xml2 = main::request_url_retry( $ua, $hds_media->{href}, 3, undef, undef, 1 );
				my $doc2 = eval { XMLin($xml2, KeyAttr => [], ForceArray => 0, SuppressEmpty => 1) };
				if ( ! $@ ) {
					$hds_media->{type} = $media->{type};
					$hds_media->{kind} = $media->{kind};
					$hds_media->{encoding} = $media->{encoding};
					$hds_media->{width} = $doc2->{media}->{width};
					$hds_media->{height} = $doc2->{media}->{height};
					my ($ab, $vb) = ($1, $2) if $doc2->{media}->{url} =~ m{audio.*?=(\d+)-(video=(\d+))?};
					$hds_media->{audio_bitrate} = int($ab/1000);
					$hds_media->{video_bitrate} = int($vb/1000);
					if ( $doc2->{streamType} eq 'live' ) {
						$hds_media->{service} = "gip_hls_simulcast_$hds_media->{bitrate}";
					} else {
						$hds_media->{service} = "gip_hls_iplayer_$hds_media->{bitrate}";
					}
					my $href = $hds_media->{href};
					delete $hds_media->{href};
					$href =~ s/\.f4m/.m3u8/;
					@{$hds_media->{connections}} = ({
 						href => $href, 
 						kind => $conn->{supplier},
 						supplier => $conn->{supplier},
 						protocol => 'http',
 						transferFormat => 'hls',
						priority => $conn->{priority},
 					});
					push @hds_medias, $hds_media;
				} else {
					main::logger "WARNING: Could not parse f4m chunklist: $hds_media->{href}: $@.\n";
				}
			}
		} else {
			main::logger "WARNING: Could not parse f4m playlist: $@.\n";
		}
		return @hds_medias;
	}
}

# from https://github.com/osklil/hls-fetch
sub parse_hls_connection {
	my $media = shift;
	my $conn = shift;
	my $min_bitrate = shift;
	my $pc_medias = shift;
	my $conn_href;
	for my $pc_media ( @{$pc_medias} ) {
		if ( $pc_media->{bitrate} > 2000 ) {
			for my $pc_conn ( @{$pc_media->{connections}} ) {
				(my $hd_id = $pc_conn->{identifier}) =~ s/(^mp4:(secure\/)?|\.mp4$)//g;
				if ( $hd_id ) {
					($conn_href = $conn->{href}) =~ s/(\*\~hmac|\,\.mp4\.csmil)/,${hd_id}$1/g;
					last;
				}
			}
		}
		last if $conn_href;
	}
	$conn_href ||= $conn->{href};
	my @hls_medias;
	my $data = main::request_url_retry( main::create_ua( 'desktop' ), $conn_href, 3, undef, undef, 1 );
	if ( ! $data ) {
		main::logger "WARNING: No HLS playlist returned ($conn->{href})\n" if $opt->{verbose};
		return;
	}
	my @lines = split(/\r*\n|\r\n*/, $data);
	if ( @lines < 1 || $lines[0] !~ '^#EXTM3U' ) {
		main::logger "WARNING: Invalid HLS playlist, no header ($conn->{href})\n" if $opt->{verbose};
		return;
	}

	if (!grep { /^#EXTINF:/ } @lines) {
		my (@streams, $last_stream);
		foreach my $line (@lines) {
			next if ($line =~ /^#/ && $line !~ /^#EXT/) || $line =~ /^\s*$/;
			if ($line =~ /^#EXT-X-STREAM-INF:(.*)$/) {
				$last_stream = { parse_m3u_attribs($conn->{href}, $1) };
				push @streams, $last_stream;
			} elsif ($line !~ /^#EXT/) {
				if ( ! defined $last_stream ) {
					main::logger "WARNING: Missing #EXT-X-STREAM-INF for URL: $line ($conn->{href})\n" if $opt->{verbose};
					return;
				}
				$last_stream->{'URL'} = $line;
				$last_stream = undef;
			}
		}
		if ( ! @streams ) {
			main::logger "WARNING: No streams found in HLS playlist ($conn->{href})\n";
			return,
		};

		main::logger "WARNING: non-numeric bandwidth in HLS playlist\n" if grep { $_->{'BANDWIDTH'} =~ /\D/ } @streams;
		for my $stream ( @streams ) {
			my $hls_media = dclone($media);
			delete $hls_media->{width};
			delete $hls_media->{height};
			delete $hls_media->{bitrate};
			delete $hls_media->{media_file_size};
			delete $hls_media->{service};
			delete $hls_media->{connections};
			$hls_media->{bitrate} = int($stream->{BANDWIDTH}/1000);
			next if $min_bitrate && $hls_media->{bitrate} < $min_bitrate;
			if ( $stream->{RESOLUTION} ) {
				($hls_media->{width}, $hls_media->{height}) = split(/x/, $stream->{RESOLUTION});
			} 
			if ( $stream->{URL} =~ /live/ ) {
				$hls_media->{service} = "gip_hls_simulcast_$hls_media->{bitrate}";
			} else {
				$hls_media->{service} = "gip_hls_iplayer_$hls_media->{bitrate}";
			}
			my $hls_conn = dclone($conn);
			my $uri1 = URI->new($hls_conn->{href});
			my $qs1 = $uri1->query;
			my $uri2 = URI->new($stream->{URL});
			my $qs2 = $uri2->query;
			$qs2 .= "&" if $qs2 && $qs1;
			$uri2->query($qs2.$qs1);
			delete $hls_conn->{href};
			$hls_conn->{href} = $uri2->as_string;
			$hls_media->{connections} = [ $hls_conn ];
			push @hls_medias, $hls_media;
		}
	}
	return @hls_medias;
}

sub parse_pls_connection {
	my $media = shift;
	my $conn = shift;
	my @pls_medias;
	my $data = main::request_url_retry( main::create_ua( 'desktop' ), $conn->{href}, 3, undef, undef, 1 );
	my @lines = split(/\r*\n|\r\n*/, $data);
	if ( @lines < 1 || $lines[0] ne '[playlist]' ) {
		main::logger "WARNING: Invalid PLS playlist, no header ($conn->{href})\n";
		return;
	}
	foreach my $line (@lines) {
		my ($idx, $href)  = ( $1, $2 ) if $line =~ /File(\d+)=(.*)$/i;
		if ( $href ) {
			my $pls_media = dclone($media);
			$pls_media->{service} .= "_$idx";
			my $pls_conn = dclone($conn);
			$pls_conn->{priority} = $idx;
			$pls_conn->{href} = $href;
			$pls_media->{connections} = [ $pls_conn ];
			push @pls_medias, $pls_media;
		}
	}
	return @pls_medias;
}

# from https://github.com/osklil/hls-fetch
sub parse_m3u_attribs {
  my ($url, $attr_str) = @_;
  my %attr;
  for (my $as = $attr_str; $as ne ''; ) {
    $as =~ s/^?([^=]*)=([^,"]*|"[^"]*")\s*(,\s*|$)// or main::logger "WARNING: Invalid attributes in HLS playlist: $attr_str ($url)\n";
    my ($key, $val) = ($1, $2);
    $val =~ s/^"(.*)"$/$1/;
    $attr{$key} = $val;
  }
  return %attr;
}


sub get_stream_data_cdn {
	my ( $data, $mattribs, $mode, $streamer, $ext ) = ( @_ );
	my $data_pri = {};

	# Public Non-Live EMP Video without auth
	#if ( $cattribs->{kind} eq 'akamai' && $cattribs->{identifier} =~ /^public\// ) {
	#	$data->{$mode}->{bitrate} = 480; # ??
	#	$data->{$mode}->{swfurl} = "http://news.bbc.co.uk/player/emp/2.11.7978_8433/9player.swf";
	# Live TV, Live EMP Video or Non-public EMP video
	#} elsif ( $cattribs->{kind} eq 'akamai' ) {
	#	$data->{$mode}->{bitrate} = 480; # ??

	my $count = 1;
	for my $cattribs ( @{ $mattribs->{connections} } ) {

		# Get authstring from more specific mediaselector if this mode is specified - fails sometimes otherwise
		if ( $opt->{mediaselector} eq '4' && $cattribs->{authString} && $cattribs->{kind} =~ /^(limelight|akamai|level3|sis|iplayertok)$/ && (grep /^$mode$/, (split /,/, $mattribs->{modelist})) ) {
			# Build URL
			my $media_stream_data_prefix = 'http://www.bbc.co.uk/mediaselector/4/mtis/stream/';
			my $url = $media_stream_data_prefix."$mattribs->{verpid}/$mattribs->{service}/$cattribs->{kind}?cb=".( sprintf "%05.0f", 99999*rand(0) );
			my $xml = main::request_url_retry( main::create_ua( 'desktop' ), $url, 3, undef, undef, 1 );
			main::logger "\n$xml\n" if $opt->{debug};
			# get new set of connection attributes from the new xml data
			my $new_mattribs = (parse_metadata( $xml ))[0];
			my $new_cattribs = $new_mattribs->{connections}[0];
			# Override elemnts from more specific connection attribs if present
			for my $element ( keys %{ $new_cattribs } ) {
				$cattribs->{$element} = $new_cattribs->{$element} if $new_cattribs->{$element};
			}
		}
		decode_entities($cattribs->{authString});

		# Common attributes
		# swfurl = Default iPlayer swf version
		my $conn = {
			swfurl		=> $opt->{swfurl} || "http://emp.bbci.co.uk/emp/SMPf/1.11.16/StandardMediaPlayerChromelessFlash.swf",
			ext		=> $ext,
			streamer	=> $streamer,
			bitrate		=> $mattribs->{bitrate},
			server		=> $cattribs->{server},
			identifier	=> $cattribs->{identifier},
			authstring	=> $cattribs->{authString},
			priority	=> $cattribs->{priority},
			expires		=> $mattribs->{expires},
			size			=>  $mattribs->{media_file_size},
		};

		# Akamai CDN
		if ( $cattribs->{kind} eq 'akamai' ) {
			# Set the live flag if this is not an ondemand stream
			$conn->{live} = 1 if defined $cattribs->{application} && $cattribs->{application} =~ /^live/;
			# Default appication is 'ondemand'
			$cattribs->{application} = 'ondemand' if ! $cattribs->{application};

			# if the authString is not set and this is a live (i.e. simulcast) then try to get an authstring
			# Maybe should this be general for all CDNs?
			if ( $opt->{mediaselector} eq '4' && ! $cattribs->{authString} ) {
				# Build URL
				my $media_stream_live_prefix = 'http://www.bbc.co.uk/mediaselector/4/gtis/stream/';
				my $url = ${media_stream_live_prefix}."?server=$cattribs->{server}&identifier=$cattribs->{identifier}&kind=$cattribs->{kind}&application=$cattribs->{application}";
				my $xml = main::request_url_retry( main::create_ua( 'desktop' ), $url, 3, undef, undef, 1 );
				main::logger "\n$xml\n" if $opt->{debug};
				$cattribs->{authString} = 'auth='.$1 if $xml =~ m{<token>auth=(.+?)</token>};
				if ( ! $cattribs->{authString} ) {
					$cattribs->{authString} = 'auth='.$1 if $xml =~ m{<token>(.+?)</token>};
				}
				$conn->{authstring} = $cattribs->{authString};
			}

			$conn->{playpath} = $cattribs->{identifier};
			$conn->{streamurl} = "rtmp://$cattribs->{server}:1935/$cattribs->{application}?_fcs_vhost=$cattribs->{server}&undefined";
			$conn->{application} = "$cattribs->{application}?_fcs_vhost=$cattribs->{server}&undefined";

			if ( $cattribs->{authString} ) {
				if ( $cattribs->{authString} !~ /&aifp=/ ) {
					$cattribs->{authString} .= '&aifp=v001';
				}

				if ( $cattribs->{authString} !~ /&slist=/ ) {
					$cattribs->{identifier} =~ s/^mp[34]://;
					$cattribs->{authString} .= "&slist=$cattribs->{identifier}";
				}

				### ??? live and Live TV, Live EMP Video or Non-public EMP video:
				$conn->{playpath} .= "?$cattribs->{authString}";
				$conn->{streamurl} .= "&$cattribs->{authString}";
				$conn->{application} .= "&$cattribs->{authString}";
			} else {
				$conn->{streamurl} .= "&undefined";
				$conn->{application} .= "&undefined";
			}

			# Port 1935? for live?
			$conn->{tcurl} = "rtmp://$cattribs->{server}:80/$conn->{application}";

		# Limelight CDN
		} elsif ( $cattribs->{kind} eq 'limelight' ) {
			# Set the live flag if this has 'live' in the service name
			$conn->{live} = 1 if defined $mattribs->{service} && $mattribs->{service} =~ /live/;
			decode_entities( $cattribs->{authString} );
			$conn->{playpath} = $cattribs->{identifier};
			# Remove offending mp3/mp4: at the start of the identifier (don't remove in stream url)
			### Not entirely sure if this is even required for video modes either??? - not reqd for aac and low
			# $conn->{playpath} =~ s/^mp[34]://g;
			$conn->{streamurl} = "rtmp://$cattribs->{server}:1935/ondemand?_fcs_vhost=$cattribs->{server}&auth=$cattribs->{authString}&aifp=v001&slist=$cattribs->{identifier}";
			$conn->{application} = "$cattribs->{application}?$cattribs->{authString}";
			$conn->{tcurl} = "rtmp://$cattribs->{server}:1935/$conn->{application}";
			
		# Level3 CDN	
		} elsif ( $cattribs->{kind} eq 'level3' ) {
			$conn->{playpath} = $cattribs->{identifier};
			$conn->{application} = "$cattribs->{application}?$cattribs->{authString}";
			$conn->{tcurl} = "rtmp://$cattribs->{server}:1935/$conn->{application}";
			$conn->{streamurl} = "rtmp://$cattribs->{server}:1935/ondemand?_fcs_vhost=$cattribs->{server}&auth=$cattribs->{authString}&aifp=v001&slist=$cattribs->{identifier}";

		# iplayertok CDN
		} elsif ( $cattribs->{kind} eq 'iplayertok' ) {
			$conn->{application} = $cattribs->{application};
			decode_entities($cattribs->{authString});
			$conn->{playpath} = "$cattribs->{identifier}?$cattribs->{authString}";
			$conn->{playpath} =~ s/^mp[34]://g;
			$conn->{streamurl} = "rtmp://$cattribs->{server}:1935/ondemand?_fcs_vhost=$cattribs->{server}&auth=$cattribs->{authString}&aifp=v001&slist=$cattribs->{identifier}";
			$conn->{tcurl} = "rtmp://$cattribs->{server}:1935/$conn->{application}";

		# sis/edgesuite/sislive streams
		} elsif ( $cattribs->{kind} eq 'sis' || $cattribs->{kind} eq 'edgesuite' || $cattribs->{kind} eq 'sislive' ) {
			$conn->{streamurl} = $cattribs->{href};

		# http stream
		} elsif ( $cattribs->{kind} eq 'http' ) {
			$conn->{streamurl} = $cattribs->{href};

		# drm license - ignore
		} elsif ( $cattribs->{kind} eq 'licence' ) {

		# iphone new
		} elsif ( $cattribs->{kind} eq 'securesis' ) {
			$conn->{streamurl} = $cattribs->{href};

		# asx playlist
		} elsif ( $cattribs->{kind} eq 'asx' ) {
			$conn->{streamurl} = $cattribs->{href};

		# hls stream
		} elsif ( $cattribs->{transferFormat} =~ /hls/ ) {
			$conn->{streamurl} = $cattribs->{href};
			$conn->{kind} = $mattribs->{kind};
			$conn->{live} = 1 if $mattribs->{service} =~ /simulcast/i;
			if ( $conn->{kind} eq 'video' ) {
				$conn->{audio_bitrate} = $mattribs->{audio_bitrate};
				if ( $mattribs->{bitrate} > 2000 ) {
					$conn->{audio_bitrate} ||= 128;
				} elsif ( $mattribs->{bitrate} > 700 ) {
					$conn->{audio_bitrate} ||= 96;
				} else {
					$conn->{audio_bitrate} ||= 64;
				}
				$conn->{video_bitrate} = $mattribs->{video_bitrate};
				$conn->{video_bitrate} ||= $mattribs->{bitrate} - $conn->{audio_bitrate};
			}

		# shoutcast stream
		} elsif ( $cattribs->{kind} =~ /icy/ ) {
			$conn->{streamurl} = decode_entities($cattribs->{href});
			$conn->{kind} = $mattribs->{kind};
			$conn->{live} = 1 if $mattribs->{service} =~ /simulcast/i;

		# ddlaac stream
		} elsif ( $cattribs->{kind} eq 'sis_http_open' ) {
			$conn->{streamurl} = $cattribs->{href};

		# Unknown CDN
		} else {
			new_stream_report($mattribs, $cattribs) if $opt->{verbose};
			next;
		}

		get_stream_set_type( $conn, $mattribs, $cattribs );

		# Find the next free mode name
		while ( defined $data->{$mode.$count} ) {
			$count++;
		}
		# Add to data structure
		$data->{$mode.$count} = $conn;
		$count++;

	}

	# Add to data structure hased by priority
	$count = 1;
	while ( defined $data->{$mode.$count} ) {
		$data_pri->{ $data->{$mode.$count}->{priority} } = $data->{$mode.$count};
		$count++;
	}
	# Sort mode number according to priority
	$count = 1;
	for my $priority ( reverse sort {$a <=> $b} keys %{ $data_pri } ) {
		# Add to data structure hashed by priority
		$data->{$mode.$count} = $data_pri->{ $priority };
		main::logger "DEBUG: Mode $mode$count = priority $priority\n" if $opt->{debug};
		$count++;
	}
}



# Builds connection type string
sub get_stream_set_type {
		my ( $conn, $mattribs, $cattribs ) = ( @_ );
		my @type;
		push @type, "($mattribs->{service})" if $mattribs->{service};
		push @type, "$conn->{streamer}";
		push @type, "$mattribs->{encoding}" if $mattribs->{encoding};
		push @type, "$mattribs->{width}x$mattribs->{height}" if $mattribs->{width} && $mattribs->{height};
		push @type, "$mattribs->{bitrate}kbps" if $mattribs->{bitrate};
		push @type, "stream";
		push @type, "(CDN: $cattribs->{kind}/$cattribs->{priority})" if $cattribs->{kind} && $cattribs->{priority};
		push @type, "(CDN: $cattribs->{kind})" if $cattribs->{kind} && not defined $cattribs->{priority};
		$conn->{type} = join ' ', @type;
}



# Generic
# Gets media streams data for this version pid
# $media = undef|<modename>
sub get_stream_data {
	my ( $prog, $verpid, $media ) = @_;
	my $data = {};
	my $media_stream_data_prefix;
	my $media_stream_live_prefix;
	my @media_stream_pc_prefixes;
	my @media_stream_mobile_prefixes;
	my @media_stream_shoutcast_prefixes;
	my ( @pc_mediasets, @mobile_mediasets, @shoutcast_mediasets );
	# use mediaselector/4 for obvious archive programmes
	my $mediaselector = $opt->{mediaselector};
	$opt->{mediaselector} = '4' if $verpid =~ /http:.+?\/archive\/xml\//;
	if ( $opt->{mediaselector} eq '4' ) {
		$media_stream_data_prefix = 'http://www.bbc.co.uk/mediaselector/4/mtis/stream/'; # $verpid 
		$media_stream_live_prefix = 'http://www.bbc.co.uk/mediaselector/4/gtis/stream/'; # $verpid
	} else {
		# assume URL in $verpid is XML playlist from news site
		if ( $verpid =~ /http:/ ) {
			@pc_mediasets = ( 'journalism-pc' ); 
			@mobile_mediasets = ('journalism-http-tablet');
		} else {
			@pc_mediasets = ( 'pc' );
			if ( $prog->{type} =~ /tv/ ) {
				push @pc_mediasets, 'apple-ipad-hls'; 
			}
			@mobile_mediasets = ( 'apple-ipad-hls' ); 
			if ( $prog->{type} =~ /radio/ ) {
				push @mobile_mediasets, 'apple-iphone4-ipad-hls-3g'; 
			}
			if ( $prog->{type} eq "liveradio" ) {
				push @shoutcast_mediasets, 'http-icy-mp3-a';
				# R3 320k AAC stream (temporary)
				if ( $verpid eq 'bbc_radio_three' ) {
					push @shoutcast_mediasets, 'http-icy-aac-lc-a';
				}
			}
		}
		$media_stream_data_prefix = "http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/$pc_mediasets[0]/vpid/"; # $verpid
		$media_stream_live_prefix = $media_stream_data_prefix;
		for my $mediaset ( @pc_mediasets ) {
			push @media_stream_pc_prefixes, "http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/$mediaset/vpid/"; # $verpid
		}
		for my $mediaset ( @mobile_mediasets ) {
			push @media_stream_mobile_prefixes, "http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/$mediaset/vpid/"; # $verpid
		}
		for my $mediaset ( @shoutcast_mediasets ) {
			push @media_stream_shoutcast_prefixes, "http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/$mediaset/vpid/"; # $verpid
		}
	}
	
  my @exclude_supplier = split(/,/, $opt->{excludesupplier});
  if ( grep /akamai/, @exclude_supplier ) {
		push @exclude_supplier, 'ak';
  }
  if ( grep /limelight/, @exclude_supplier ) {
		push @exclude_supplier, 'll';
  }
  if ( ! grep /bidi/, @exclude_supplier ) {
		push @exclude_supplier, 'bidi';
  }
  my $exclude_regex = '('.(join('|', @exclude_supplier)).')';

	# Setup user agent with redirection enabled
	my $ua = main::create_ua( 'desktop' );

	# BBC streams
	my $xml;
	my @medias;

	# If this is an EMP stream verpid
	if ( $verpid =~ /^\?/ ) {
		$xml = main::request_url_retry( $ua, $media_stream_live_prefix.$verpid, 3, undef, undef, 1 );
		main::logger "\n$xml\n" if $opt->{debug};
		my $mattribs;
		my $cattribs;
		# Parse connection attribs
		$cattribs->{server} = $1 if $xml =~ m{<server>(.+?)</server>};
		$cattribs->{kind} = $1 if $xml =~ m{<kind>(.+?)</kind>};
		$cattribs->{identifier} = $1 if $xml =~ m{<identifier>(.+?)</identifier>};
		$cattribs->{authString} = $1 if $xml =~ m{<token>(.+?)</token>};
		$cattribs->{application} = $1 if $xml =~ m{<application>(.+?)</application>};
		# TV / EMP video (flashnormal mode)
		if ( $prog->{type} eq 'tv' || $prog->{type} eq 'livetv' ) {
			# Parse XML
			#<server>cp56493.live.edgefcs.net</server>
			#<identifier>bbc1_simcast@s3173</identifier>
			#<token>dbEb_c0abaHbWcxaYbRcHcQbfcMczaocvaB-bklOc_-c0-d0i_-EpnDBnzoNDqEnxF</token>
			#<kind>akamai</kind>
			#<application>live</application>
			#width="512" height="288" type="video/x-flv" encoding="vp6"
			$mattribs = { kind => 'video', type => 'video/x-flv', encoding => 'vp6', width => 512, height => 288 };
		# AAC Live Radio / EMP Audio
		} elsif ( $prog->{type} eq 'radio' || $prog->{type} eq 'liveradio' ) {
			# MP3 (flashaudio mode)
			if ( $cattribs->{identifier} =~ m{mp3:} ) {
				$mattribs = { kind => 'audio', type => 'audio/mpeg', encoding => 'mp3' };
			# AAC (flashaac mode)
			} else {
				$mattribs = { kind => 'audio', type => 'audio/mp4', encoding => 'aac' };
			}
		}
		# Push into media data structure
		push @{ $mattribs->{connections} }, $cattribs;
		push @medias, $mattribs;
	} else {
		my (%seen, $stream_key);
		if ( $verpid =~ /http:/ ) {
			$xml = main::request_url_retry( $ua, $verpid, 3, undef, undef, 1 );
			main::logger "\n$xml\n" if $opt->{debug};
			if  ( $xml =~ m{<mediator identifier=\"(.+?)\"} ) {
				$verpid = $1;
				main::logger "new verpid $verpid" if $opt->{debug};
			}
		}
		if ( $verpid =~ /http:/ ) {
			@medias = parse_metadata( $xml );
		} else { 
			# get Flash streams for on-demand
			if ( $prog->{type} !~ /live/ ) {
				for my $media_stream_pc_prefix ( @media_stream_pc_prefixes ) {
					$xml = main::request_url_retry( $ua, $media_stream_pc_prefix.$verpid.'/proto/rtmp?cb='.( sprintf "%05.0f", 99999*rand(0) ), 3, undef, undef, 1 );
					main::logger "\n$xml\n" if $opt->{debug};
					my @pc_medias = parse_metadata( $xml );
					for my $pc_media ( @pc_medias ) {
						my @pc_conns;
						for my $pc_conn ( @{$pc_media->{connections}} ) {
							next if ( $pc_conn->{supplier} =~ /$exclude_regex/ );
							$stream_key = "$pc_conn->{identifier}-$pc_conn->{protocol}-$pc_conn->{supplier}";
							next if $seen{$stream_key};
							$seen{$stream_key}++;
							push @pc_conns, $pc_conn;
						}
						@{$pc_media->{connections}} = @pc_conns;
						push @medias, $pc_media;
					}
				}
			}
			# get HLS streams from mobile data
			for my $media_stream_mobile_prefix ( @media_stream_mobile_prefixes ) {
				$xml = main::request_url_retry( $ua, $media_stream_mobile_prefix.$verpid.'/proto/http?cb='.( sprintf "%05.0f", 99999*rand(0) ), 3, undef, undef, 1 );
				main::logger "\n$xml\n" if $opt->{debug};
				my @mobile_medias = parse_metadata( $xml );
				for my $mobile_media ( @mobile_medias ) {
					for my $mobile_conn ( @{$mobile_media->{connections}} ) {
						# direct download files
						if ( $mobile_conn->{supplier} eq "sis_http_open" ) {
							my $ddl_conn = dclone($mobile_conn);
							my $ddl_media = dclone($mobile_media);
							$ddl_media->{service} .= '_ddl';
							$ddl_media->{connections} = [ $ddl_conn ];
							push @medias, $ddl_media;
							next;
						}
						next if $mobile_conn->{transferFormat} ne 'hls';
						next if $mobile_conn->{supplier} =~ /$exclude_regex/;
						$stream_key = "$mobile_media->{service}-$mobile_conn->{protocol}-$mobile_conn->{supplier}";
						next if $seen{$stream_key};
						$seen{$stream_key}++;
						($stream_key = $mobile_conn->{href}) =~ s/\?.*//;
						next if $seen{$stream_key};
						$seen{$stream_key}++;
						my @hls_medias = parse_hls_connection( $mobile_media, $mobile_conn, 0, \@medias );
						for my $hls_media ( @hls_medias ) {
							for my $hls_conn ( @{$hls_media->{connections}} ) {
								$stream_key = "$hls_media->{service}-$hls_conn->{protocol}-$hls_conn->{supplier}";
								next if $seen{$stream_key};
								$seen{$stream_key}++;
								($stream_key = $hls_conn->{href}) =~ s/\?.*//;
								next if $seen{$stream_key};
								$seen{$stream_key}++;
								# ensure higher priority for UK live streams
								$hls_conn->{priority} += 100 if $prog->{type} =~ /live/;
								push @medias, $hls_media;
								last;
							}
						}
					}
				}
			}
			# generate additional live streams
			if ( $prog->{type} =~ /live/ ) {
				my ( $media, $href_prefix, $href_prefix_nonuk, $href_ext, $min_bitrate, $uk );
				# override other HLS streams if requested
				if ( ( $prog->{type} =~ /tv/ && $opt->{livetvuk} ) || ( $prog->{type} =~ /radio/ && ( $opt->{liveradiouk} || $opt->{liveradiointl} ) ) ) {
					@medias = ();
					%seen = ();
				}
				if ( $prog->{type} =~ /tv/ ) {
					$uk = @medias;
					$uk = 1 if $opt->{livetvuk};
					$media = { encoding => "h264", kind => "video", type => "video/mp4" };
					$href_prefix = "http://a.files.bbci.co.uk/media/live/manifests/hds/pc";
					$href_ext = ".f4m";
					$min_bitrate = $opt->{livetvuk} ? 0 : 2000; 
				} else {
					$uk = grep { $_->{bitrate} >= 120 } @medias;
					$uk = 0 if $opt->{liveradiointl};
					$uk = 1 if $opt->{liveradiouk};
					$media = { encoding => "aac", kind => "audio", type => "audio/mp4" };
					$href_prefix = "http://a.files.bbci.co.uk/media/live/manifesto/audio/simulcast/hls";
					$href_ext = ".m3u8";
					$min_bitrate = 0; 
				} 
				my @hls_medias;
				my $priority = 0;
				my @cdns = ( "ak", "llnw" );
				my @rand_cdns = $cdns[rand @cdns];
				push @rand_cdns, $rand_cdns[0] eq "ak" ? "llnw" : "ak";
				for my $cdn ( @rand_cdns ) {
					my $conn_priority = ( $priority % ($#rand_cdns + 1) ) + 1;
					$priority++;
					my $conn = { supplier => "gip_${cdn}_hls_live", priority => $conn_priority, transferFormat => 'hls', protocol => 'http' };
					$conn->{kind} = $conn->{supplier};
					if ( $prog->{type} =~ /tv/ ) {
						if ( $uk ) {
							$conn->{href} = "${href_prefix}/${cdn}/${verpid}${href_ext}";
							push @hls_medias, parse_hds_connection( $media, $conn, $min_bitrate );
						}
					} elsif ( $verpid eq 'bbc_world_service' ) {
							$conn->{href} = 'http://bbcwsen-lh.akamaihd.net/i/WSEIEUK_1@189911/master.m3u8';
							push @hls_medias, parse_hls_connection( $media, $conn, $min_bitrate );
					} else {
						my $loc;
						my @sbr;
						if ( $uk ) {
							$loc = 'uk';
							@sbr = ( 'sbr_high', 'sbr_med', 'sbr_low', 'sbr_vlow' );
						} else {
							$loc = 'nonuk';
							@sbr = ( 'sbr_low', 'sbr_vlow' );
						}
						for my $sbr ( @sbr ) {
							$conn->{href} = "${href_prefix}/${loc}/${sbr}/${cdn}/${verpid}${href_ext}";
							push @hls_medias, parse_hls_connection( $media, $conn, $min_bitrate);
						}
					}
				}
				for my $hls_media ( @hls_medias ) {
					for my $hls_conn ( @{$hls_media->{connections}} ) {
						$stream_key = "$hls_media->{service}-$hls_conn->{protocol}-$hls_conn->{supplier}";
						next if $seen{$stream_key};
						$seen{$stream_key}++;
						($stream_key = $hls_conn->{href}) =~ s/\?.*//;
						next if $seen{$stream_key};
						$seen{$stream_key}++;
						push @medias, $hls_media;
						last;
					}
				}
			}
			# generate shoutcast streams
			if ( $prog->{type} eq 'liveradio' ) {
				for my $media_stream_shoutcast_prefix ( @media_stream_shoutcast_prefixes ) {
					$xml = main::request_url_retry( $ua, $media_stream_shoutcast_prefix.$verpid.'?cb='.( sprintf "%05.0f", 99999*rand(0) ), 3, undef, undef, 1 );
					main::logger "\n$xml\n" if $opt->{debug};
					my @shoutcast_medias = parse_metadata( $xml );
					for my $shoutcast_media ( @shoutcast_medias ) {
						for my $shoutcast_conn ( @{$shoutcast_media->{connections}} ) {
							next if $shoutcast_conn->{supplier} =~ /$exclude_regex/;
							$stream_key = "$shoutcast_media->{service}-$shoutcast_conn->{protocol}-$shoutcast_conn->{supplier}";
							next if $seen{$stream_key};
							$seen{$stream_key}++;
							($stream_key = $shoutcast_conn->{href}) =~ s/\?.*//;
							next if $seen{$stream_key};
							$seen{$stream_key}++;
							# world service returns playlist instead of streams
							if ( $shoutcast_conn->{href} =~ /\.pls/ ) {
								my @pls_medias = parse_pls_connection( $shoutcast_media, $shoutcast_conn );
								for my $pls_media ( @pls_medias ) {
									for my $pls_conn ( @{$pls_media->{connections}} ) {
										$stream_key = "$pls_media->{service}-$pls_conn->{protocol}-$pls_conn->{supplier}";
										next if $seen{$stream_key};
										$seen{$stream_key}++;
										($stream_key = $pls_conn->{href}) =~ s/\?.*//;
										next if $seen{$stream_key};
										$seen{$stream_key}++;
										push @medias, $pls_media;
										last;
									}
								}
							} else {
								my $sc_media = dclone($shoutcast_media);
								my $sc_conn = dclone($shoutcast_conn);
								$sc_media->{connections} = [ $sc_conn ];
								push @medias, $sc_media;
							}
						}
					}
				}
			}
		}
 	}

	# Parse and dump structure
	my $mode;
	for my $mattribs ( @medias ) {
		
		# Put verpid into mattribs
		$mattribs->{verpid} = $verpid;
		$mattribs->{modelist} = $prog->modelist;

		# New iphone stream
		if ( $mattribs->{service} eq 'iplayer_streaming_http_mp4' ) {
			# Fix/remove some audio stream attribs
			if ( $prog->{type} eq 'radio' ) {
				$mattribs->{bitrate} = 128;
				delete $mattribs->{width};
				delete $mattribs->{height};
			}
			get_stream_data_cdn( $data, $mattribs, 'iphone', 'iphone', 'mov' );
		
		} elsif (	$mattribs->{service} =~ /hls/ ) {

			if ( $mattribs->{kind} =~ 'video' ) {
				my $ext = "mp4";
				if ( $mattribs->{bitrate} > 3000 or $mattribs->{width} > 1200 ) {
					get_stream_data_cdn( $data, $mattribs, 'hlshd', 'hls', $ext );
				} elsif ( $mattribs->{bitrate} > 2000 or $mattribs->{width} > 1000 ) {
					get_stream_data_cdn( $data, $mattribs, 'hlssd', 'hls', $ext );
				} elsif ( $mattribs->{bitrate} > 1200 ) {
					get_stream_data_cdn( $data, $mattribs, 'hlsvhigh', 'hls', $ext );
				} elsif ( $mattribs->{bitrate} > 700 ) {
					get_stream_data_cdn( $data, $mattribs, 'hlshigh', 'hls', $ext );
				} elsif ( $mattribs->{bitrate} > 400  ) {
					get_stream_data_cdn( $data, $mattribs, 'hlsstd', 'hls', $ext );
				} elsif ( $mattribs->{bitrate} > 300 ) {
					get_stream_data_cdn( $data, $mattribs, 'hlslow', 'hls', $ext );
				#} elsif ( $mattribs->{bitrate} > 200 ) {
				#	get_stream_data_cdn( $data, $mattribs, 'hlsvlow', 'hls', $ext );
				#} elsif ( $mattribs->{bitrate} > 100 ) {
				#	get_stream_data_cdn( $data, $mattribs, 'hlsvvlow', 'hls', $ext );
				#} else {
				#	get_stream_data_cdn( $data, $mattribs, 'hlsvvvlow', 'hls', $ext );
				}
			} elsif ( $mattribs->{kind} =~ 'audio' ) {
				my $ext = "m4a";
				if (  $mattribs->{bitrate} >= 192 ) {
					get_stream_data_cdn( $data, $mattribs, 'hlsaachigh', 'hls', $ext );
				} elsif ( $mattribs->{bitrate} >= 120 ) {
					get_stream_data_cdn( $data, $mattribs, 'hlsaacstd', 'hls', $ext );
				} elsif ( $mattribs->{bitrate} >= 80 ) {
					get_stream_data_cdn( $data, $mattribs, 'hlsaacmed', 'hls', $ext );
				} else {
					get_stream_data_cdn( $data, $mattribs, 'hlsaaclow', 'hls', $ext );
				}
			}

		} elsif ( $mattribs->{type} =~ /x-scpls/ ) {
			my $enc = $mattribs->{encoding};
			my $ext = $enc eq 'aac' ? 'm4a' : 'mp3';
			if (  $mattribs->{bitrate} >= 192 ) {
				get_stream_data_cdn( $data, $mattribs, "shoutcast${enc}high", 'shoutcast', $ext );
			} elsif ( $mattribs->{bitrate} >= 96 ) {
				# R3 320k AAC mislabelled
				if ( $verpid eq 'bbc_radio_three' && $enc eq 'aac' ) {
					get_stream_data_cdn( $data, $mattribs, "shoutcast${enc}high", 'shoutcast', $ext );
				} else {
					get_stream_data_cdn( $data, $mattribs, "shoutcast${enc}std", 'shoutcast', $ext );
				}
			} else {
				get_stream_data_cdn( $data, $mattribs, "shoutcast${enc}low", 'shoutcast', $ext );
			}

		} elsif ( $mattribs->{service} =~ /ddl/ ) {
			if ( $mattribs->{kind} =~ 'audio' ) {
				my $ext = "m4a";
				if (  $mattribs->{bitrate} >= 192 ) {
					get_stream_data_cdn( $data, $mattribs, 'ddlaachigh', 'ddl', $ext );
				} elsif ( $mattribs->{bitrate} >= 96 ) {
					get_stream_data_cdn( $data, $mattribs, 'ddlaacstd', 'ddl', $ext );
				} else {
					get_stream_data_cdn( $data, $mattribs, 'ddlaaclow', 'ddl', $ext );
				}
			}

		# flashhd modes
		} elsif (	$mattribs->{kind} eq 'video' &&
				$mattribs->{type} eq 'video/mp4' &&
				$mattribs->{encoding} eq 'h264'
		) {
			# Determine classifications of modes based mainly on bitrate

			# flashhd modes
			if ( $mattribs->{bitrate} > 2000 ) {
				get_stream_data_cdn( $data, $mattribs, 'flashhd', 'rtmp', 'mp4' );

			# flashvhigh modes
			} elsif ( $mattribs->{bitrate} > 1200 ) {
				get_stream_data_cdn( $data, $mattribs, 'flashvhigh', 'rtmp', 'mp4' );

			# flashhigh modes
			} elsif ( $mattribs->{bitrate} > 700 ) {
				get_stream_data_cdn( $data, $mattribs, 'flashhigh', 'rtmp', 'mp4' );

			# flashstd modes
			} elsif ( $mattribs->{bitrate} > 400 && $mattribs->{width} >= 500 ) {
				get_stream_data_cdn( $data, $mattribs, 'flashstd', 'rtmp', 'mp4' );

			# flashlow modes
			} elsif ( $mattribs->{bitrate} > 300 && $mattribs->{width} >= 380 ) {
				get_stream_data_cdn( $data, $mattribs, 'flashlow', 'rtmp', 'mp4' );
			}
			
		# flashnormal modes (also live and EMP modes)
		} elsif (	$mattribs->{kind} eq 'video' &&
				$mattribs->{type} eq 'video/x-flv' &&
				$mattribs->{encoding} eq 'vp6'
		) {
			get_stream_data_cdn( $data, $mattribs, 'flashnormal', 'rtmp', 'avi' );

		# flashlow modes
		} elsif (	$mattribs->{kind} eq 'video' &&
				$mattribs->{type} eq 'video/x-flv' &&
				$mattribs->{encoding} eq 'spark'
		) {
			get_stream_data_cdn( $data, $mattribs, 'flashlow', 'rtmp', 'avi' );

		# flashnormal modes without encoding specifed - assume vp6
		} elsif (	$mattribs->{kind} eq 'video' &&
				$mattribs->{type} eq 'video/x-flv'
		) {
			$mattribs->{encoding} = 'vp6';
			get_stream_data_cdn( $data, $mattribs, 'flashnormal', 'rtmp', 'avi' );

		# n95 modes
		} elsif (	$mattribs->{kind} eq 'video' &&
				$mattribs->{type} eq 'video/mpeg' &&
				$mattribs->{encoding} eq 'h264'
		) {
			# n95_wifi modes
			if ( $mattribs->{bitrate} > 140 ) {
				$mattribs->{width} = $mattribs->{width} || 320;
				$mattribs->{height} = $mattribs->{height} || 176;
				get_stream_data_cdn( $data, $mattribs, 'n95_wifi', '3gp', '3gp' );

			# n95_3g modes
			} else {
				$mattribs->{width} = $mattribs->{width} || 176;
				$mattribs->{height} = $mattribs->{height} || 96;
				get_stream_data_cdn( $data, $mattribs, 'n95_3g', '3gp', '3gp' );
			}

		# WMV drm modes - still used?
		} elsif (	$mattribs->{kind} eq 'video' &&
				$mattribs->{type} eq 'video/wmv'
		) {
			$mattribs->{width} = $mattribs->{width} || 320;
			$mattribs->{height} = $mattribs->{height} || 176;
			get_stream_data_cdn( $data, $mattribs, 'mobile_wmvdrm', 'http', 'wmv' );
			# Also DRM (same data - just remove _mobile from href and identfier)
			$mattribs->{width} = 672;
			$mattribs->{height} = 544;
			get_stream_data_cdn( $data, $mattribs, 'wmvdrm', 'http', 'wmv' );
			$data->{wmvdrm}->{identifier} =~ s/_mobile//g;
			$data->{wmvdrm}->{streamurl} =~ s/_mobile//g;

		# flashaac modes
		} elsif (	$mattribs->{kind} eq 'audio' &&
				$mattribs->{type} eq 'audio/mp4'
				# This also catches worldservice who happen not to set the encoding type
				# && $mattribs->{encoding} eq 'aac'
		) {
			# flashaachigh
			if (  $mattribs->{bitrate} >= 192 ) {
				get_stream_data_cdn( $data, $mattribs, 'flashaachigh', 'rtmp', 'aac' );

			# flashaacstd
			} elsif ( $mattribs->{bitrate} >= 96 ) {
				get_stream_data_cdn( $data, $mattribs, 'flashaacstd', 'rtmp', 'aac' );

			# flashaaclow
			} elsif ( $mattribs->{service} !~ /3gp/ ) {
				get_stream_data_cdn( $data, $mattribs, 'flashaaclow', 'rtmp', 'aac' );
			}

		# flashaudio modes
		} elsif (	$mattribs->{kind} eq 'audio' &&
				( $mattribs->{type} eq 'audio/mpeg' || $mattribs->{type} eq 'audio/mp3' )
				#&& $mattribs->{encoding} eq 'mp3'
		) {
			get_stream_data_cdn( $data, $mattribs, 'flashaudio', 'rtmp', 'mp3' );

		# RealAudio modes
		} elsif (	$mattribs->{type} eq 'audio/real' &&
				$mattribs->{encoding} eq 'real'
		) {
			get_stream_data_cdn( $data, $mattribs, 'realaudio', 'rtsp', 'mp3' );

		# wma modes
		} elsif (	( $mattribs->{type} eq 'audio/wma' || $mattribs->{type} eq "audio/x-ms-asf" ) &&
				$mattribs->{encoding} =~ /wma/
		) {
			get_stream_data_cdn( $data, $mattribs, 'wma', 'mms', 'wma' );

		# aac3gp modes
		} elsif (	$mattribs->{kind} eq '' &&
				$mattribs->{type} eq 'audio/mp4' &&
				$mattribs->{encoding} eq 'aac'
		) {
			# Not sure how to stream these yet
			#$mattribs->{kind} = 'sis';
			#get_stream_data_cdn( $data, $mattribs, 'aac3gp', 'http', 'aac' );

		# Subtitles modes
		} elsif (	$mattribs->{kind} eq 'captions' &&
				$mattribs->{type} eq 'application/ttaf+xml'
		) {
			get_stream_data_cdn( $data, $mattribs, 'subtitles', 'http', 'srt' );

		# Catch unknown
		} else {
			new_stream_report($mattribs, undef) if $opt->{verbose};
		}	
	}

	$opt->{mediaselector} = $mediaselector;
	
	# Do iphone redirect check regardless of an xml entry for iphone (except for EMP/Live) - sometimes the iphone streams exist regardless
	# Skip check if the modelist selected excludes iphone
	if ( $prog->{pid} !~ /^http/i && $verpid !~ /^\?/ && $verpid !~ /^http:/ && grep /^iphone/, split ',', $prog->modelist() ) {
		if ( my $streamurl = Streamer::iphone->get_url($ua, $prog->{pid}) ) {
			my $mode = 'iphone1';
			if ( $prog->{type} eq 'radio' ) {
				$data->{$mode}->{bitrate} = 128;
				$data->{$mode}->{type} = "(iplayer_streaming_http_mp3) http mp3 128kbps stream";
			} else {
				$data->{$mode}->{bitrate} = 480;
				$data->{$mode}->{type} = "(iplayer_streaming_http_mp4) http h264 480x272 480kbps stream";
			}
			$data->{$mode}->{streamurl} = $streamurl;
			$data->{$mode}->{streamer} = 'iphone';
			$data->{$mode}->{ext} = 'mov';
			get_stream_set_type( $data->{$mode} ) if ! $data->{$mode}->{type};
		} else {
			main::logger "DEBUG: No iphone redirect stream\n" if $opt->{verbose};
		}
	}

	# Report modes found
	if ( $opt->{verbose} ) {
		main::logger "INFO: Found mode $_: $data->{$_}->{type}\n" for sort keys %{ $data };
	}

	# Return a hash with media => url if '' is specified - otherwise just the specified url
	if ( ! $media ) {
		return $data;
	} else {
		# Make sure this hash exists before we pass it back...
		$data->{$media}->{exists} = 0 if not defined $data->{$media};
		return $data->{$media};
	}
}

# map pid to HLS pid
sub hls_pid_map {
	return {}
}


################### TV class #################
package Programme::tv;

use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::stat;
use HTML::Entities;
use HTTP::Cookies;
use HTTP::Headers;
use IO::Seekable;
use IO::Socket;
use LWP::ConnCache;
use LWP::UserAgent;
use POSIX qw(mkfifo strftime);
use strict;
use Time::Local;
use URI;

# Inherit from Programme class
use base 'Programme::bbciplayer';

# Class vars
sub index_min { return 1 }
sub index_max { return 9999 }
sub channels {
	return {
		'national' => {
			'bbc_one'			=> 'BBC One',
			'bbc_two'			=> 'BBC Two',
			'bbc_three'			=> 'BBC Three',
			'bbc_four'			=> 'BBC Four',
			'bbc_sport'		=> 'BBC Sport',
			'cbbc'				=> 'CBBC',
			'cbeebies'			=> 'CBeebies',
			'bbc_news'		=> 'BBC News',
			'bbc_news24'		=> 'BBC News',
			'bbc_parliament'	=> 'BBC Parliament',
			'bbc_webonly'		=> 'BBC Web Only',
		},
		'regional' => {
			'bbc_alba'			=> 'BBC Alba',
			's4cpbs'			=> 'S4C'
		}
	};
}


# channel ids be found on http://www.bbc.co.uk/bbcone/programmes/schedules/today
sub channels_schedule {
	return {
		'national' => {
			'bbcone/programmes/schedules/hd'	=> 'BBC One',
			'bbctwo/programmes/schedules/hd'	=> 'BBC Two',
			'bbcfour/programmes/schedules'		=> 'BBC Four',
			'bbcnews/programmes/schedules'		=> 'BBC News',
			'bbcthree/programmes/schedules'		=> 'BBC Three',
			'cbbc/programmes/schedules'		=> 'CBBC',
			'cbeebies/programmes/schedules'		=> 'CBeebies',
			'bbcparliament/programmes/schedules'	=> 'BBC Parliament',
		},
		'regional' => {
			#'bbcone/programmes/schedules/ni'	=> 'BBC One Northern Ireland',
			'bbcone/programmes/schedules/ni_hd'	=> 'BBC One Northern Ireland',
			#'bbcone/programmes/schedules/scotland'	=> 'BBC One Scotland',
			'bbcone/programmes/schedules/scotland_hd'	=> 'BBC One Scotland',
			#'bbcone/programmes/schedules/wales'	=> 'BBC One Wales',
			'bbcone/programmes/schedules/wales_hd'	=> 'BBC One Wales',
			'bbctwo/programmes/schedules/england'	=> 'BBC Two England',
			'bbctwo/programmes/schedules/ni'	=> 'BBC Two Northern Ireland',
			'bbctwo/programmes/schedules/scotland'	=> 'BBC Two Scotland',
			'bbctwo/programmes/schedules/wales'	=> 'BBC Two Wales',
			'bbcalba/programmes/schedules'		=> 'BBC Alba',
			's4c/programmes/schedules'		=> 'S4C',
		},
		'local' => {
			'bbcone/programmes/schedules/cambridge'	=> 'BBC One Cambridgeshire',
			'bbcone/programmes/schedules/channel_islands'	=> 'BBC One Channel Islands',
			'bbcone/programmes/schedules/east'	=> 'BBC One East',
			'bbcone/programmes/schedules/east_midlands'	=> 'BBC One East Midlands',
			'bbcone/programmes/schedules/london'	=> 'BBC One London',
			'bbcone/programmes/schedules/north_east'	=> 'BBC One North East & Cumbria',
			'bbcone/programmes/schedules/north_west'	=> 'BBC One North West',
			'bbcone/programmes/schedules/oxford'	=> 'BBC One Oxfordshire',
			'bbcone/programmes/schedules/south'	=> 'BBC One South',
			'bbcone/programmes/schedules/south_east'	=> 'BBC One South East',
			'bbcone/programmes/schedules/south_west'	=> 'BBC One South West',
			'bbcone/programmes/schedules/west'	=> 'BBC One West',
			'bbcone/programmes/schedules/west_midlands'	=> 'BBC One West Midlands',
			'bbcone/programmes/schedules/east_yorkshire'	=> 'BBC One Yorks & Lincs',
			'bbcone/programmes/schedules/yorkshire'	=> 'BBC One Yorkshire',
		}
	};
}


# Class cmdline Options
sub opt_format {
	return {
		tvmode		=> [ 1, "tvmode|vmode=s", 'Recording', '--tvmode <mode>,<mode>,...', "TV recording modes: flashhd,flashvhigh,flashhigh,flashstd,flashnormal,flashlow. Shortcuts: default,good,better(=default),best,rtmp,flash. (Use 'best' for HD TV. 'default'=flashvhigh,flashhigh,flashstd,flashnormal,flashlow)"],
		outputtv	=> [ 1, "outputtv=s", 'Output', '--outputtv <dir>', "Output directory for tv recordings (overrides --output)"],
		vlc		=> [ 1, "vlc=s", 'External Program', '--vlc <path>', "Location of vlc or cvlc binary"],
		rtmptvopts	=> [ 1, "rtmp-tv-opts|rtmptvopts=s", 'Recording', '--rtmp-tv-opts <options>', "Add custom options to rtmpdump for tv"],
		hlstvopts	=> [ 1, "hls-tv-opts|hlstvopts=s", 'Recording', '--hls-tv-opts <options>', "Add custom options to ffmpeg HLS download re-muxing for tv"],
		ffmpegtvopts	=> [ 1, "ffmpeg-tv-opts|ffmpegtvopts=s", 'Recording', '--ffmpeg-tv-opts <options>', "Add custom options to ffmpeg re-muxing for tv"],
	};
}



# Method to return optional list_entry format
sub optional_list_entry_format {
	my $prog = shift;
	my @format;
	for ( qw/ channel categories versions / ) {
		push @format, $prog->{$_} if defined $prog->{$_};
	}
	return ', '.join ', ', @format;
}



# Returns the modes to try for this prog type
sub modelist {
	my $prog = shift;
	my $mlist = $opt->{tvmode} || $opt->{modes};
	
	# Defaults
	if ( ! $mlist ) {
		if ( ! main::exists_in_path('rtmpdump') ) {
			main::logger "WARNING: Not using flash modes since rtmpdump is not found\n" if $opt->{verbose};
		} elsif ( ! main::exists_in_path('ffmpeg') ) {
			main::logger "WARNING: Not using HLS modes since ffmpeg is not found\n" if $opt->{verbose};
		} else {
			$mlist = 'default';
		}
	}
	# Deal with BBC TV fallback modes and expansions
	$mlist = main::expand_list($mlist, 'rtmp', 'flash');
	$mlist = main::expand_list($mlist, 'flash', 'default');
	$mlist = main::expand_list($mlist, 'default', 'better');
	$mlist = main::expand_list($mlist, 'best', 'flashhd,better');
	$mlist = main::expand_list($mlist, 'vbetter', 'better');
	$mlist = main::expand_list($mlist, 'better', 'flashvhigh,good');
	$mlist = main::expand_list($mlist, 'good', 'flashhigh,flashstd,flashnormal,flashlow');
	$mlist = main::expand_list($mlist, 'hls', 'hlsdefault');
	$mlist = main::expand_list($mlist, 'hlsdefault', 'hlsbetter');
	$mlist = main::expand_list($mlist, 'hlsbest', 'hlshd,hlsbetter');
	$mlist = main::expand_list($mlist, 'hlsvbetter', 'hlsbetter');
	$mlist = main::expand_list($mlist, 'hlsbetter', 'hlsvhigh,hlsgood');
	$mlist = main::expand_list($mlist, 'hlsgood', 'hlshigh,hlsstd,hlslow');

	return $mlist;
}



# Cleans up a pid and removes url parts that might be specified
sub clean_pid {
	my $prog = shift;

	# Extract the appended start timestamp if it exists and set options accordingly e.g. '?t=16m51s'
	if ( $prog->{pid} =~ m{\?t=(\d+)m(\d+)s$} ) {
		# calculate the start offset
		$opt->{start} = $1*60.0 + $2;
	}
	
	# Expand Short iplayer URL redirects
	# e.g. http://bbc.co.uk/i/lnc8s/
	if ( $prog->{pid} =~ m{bbc\.co\.uk\/i\/[a-z0-9]{5}\/.*$}i ) {
		# Do a recursive redirect lookup to get the final URL
		my $ua = main::create_ua( 'desktop' );
		main::proxy_disable($ua) if $opt->{partialproxy};
		my $res;
		do {
			# send request (use simple_request here because that will not allow redirects)
			$res = $ua->simple_request( HTTP::Request->new( 'GET', $prog->{pid} ) );
			if ( $res->is_redirect ) {
				$prog->{pid} = $res->header("location");
				$prog->{pid} = 'http://bbc.co.uk'.$prog->{pid} if $prog->{pid} !~ /^http/;
				main::logger "DEBUG: got short url redirect to '$prog->{pid}' from iplayer site\n" if $opt->{debug};
			}
		} while ( $res->is_redirect );
		main::proxy_enable($ua) if $opt->{partialproxy};
		main::logger "DEBUG: Final expanded short URL is '$prog->{pid}'\n" if $opt->{debug};
	}
		
	# If this is an iPlayer pid
	if ( $prog->{pid} =~ m{^([pb]0[a-z0-9]{6})$} ) {
		# extract b??????? format from any URL containing it
		$prog->{pid} = $1;

	# If this an URL containing a PID (except for BBC programmes URLs)
	} elsif ( $prog->{pid} =~ m{^http.+\/([pb]0[a-z0-9]{6})\/?.*$} ) { #&& $prog->{pid} !~ m{/programmes/} ) {
		# extract b??????? format from any URL containing it
		$prog->{pid} = $1;

	# If this is a BBC *iPlayer* Live channel
	# e.g. http://www.bbc.co.uk/iplayer/playlive/bbc_radio_fourfm/
	} elsif ( $prog->{pid} =~ m{http.+bbc\.co\.uk/iplayer}i ) {
		# Remove trailing path for URLs like 'http://www.bbc.co.uk/iplayer/radio/bbc_radio_fourfm/listenlive'
		$prog->{pid} =~ s/\/\w+live\/?$//;
		# Remove extra URL path for URLs like 'http://www.bbc.co.uk/iplayer/playlive/bbc_one_london/' or 'http://www.bbc.co.uk/iplayer/tv/bbc_one'
		$prog->{pid} =~ s/^http.+\/(.+?)\/?$/$1/g;
	# Else this is an embedded media player URL (live or otherwise)
	} elsif ($prog->{pid} =~ m{^http}i ) {
		# Just leave the URL as the pid
	}
}

sub get_links_aod {
	my $self = shift;
	my $prog = shift;
	my $prog_type = shift;
	my %channel_map = (
		'1xtra'			=> 'bbc_1xtra',
		'radio1'		=> 'bbc_radio_one',
		'radio2'		=> 'bbc_radio_two',
		'radio3'		=> 'bbc_radio_three',
		'radio4'		=> 'bbc_radio_four',
		'radio4extra'	=> 'bbc_radio_four_extra',
		'fivelive'		=> 'bbc_radio_five_live',
		'sportsextra'	=> 'bbc_radio_five_live_sports_extra',
		'6music'		=> 'bbc_6music',
		'asiannetwork'	=> 'bbc_asian_network',
		'radiofoyle'	=> 'bbc_radio_foyle',
		'radioscotland'	=> 'bbc_radio_scotland',
		'alba'			=> 'bbc_radio_nan_gaidheal',
		'radioulster'	=> 'bbc_radio_ulster',
		'radiowales'	=> 'bbc_radio_wales',
		'radiocymru'	=> 'bbc_radio_cymru',
		'worldservice'	=> 'bbc_world_service'
	);
	# Hack to get correct 'channels' method because this methods is being shared with Programme::radio
	my %channels = %{ main::progclass($prog_type)->channels_filtered( main::progclass($prog_type)->channels_aod() ) };
	my $bbc_prog_page_prefix = 'http://www.bbc.co.uk/programmes'; # /$pid
	# Setup User agent
	my $ua = main::create_ua( 'desktop', 1 );
	# Download index feed
	my @channel_list = keys %channels;
 	for my $channel_id ( @channel_list ) {
		my $url = "http://www.bbc.co.uk/radio/aod/availability/${channel_id}.xml";
		main::logger "\nDEBUG: Getting feed $url\n" if $opt->{verbose};
		my $xml = main::request_url_retry($ua, $url, 3, '.', "\nWARNING: Failed to get programme index feed for $channels{$channel_id}\n");
		if ( ! $xml ) {
			return 1 if $opt->{refreshabortonerror};
			next;
		}
		decode_entities($xml);
		# Parse XML
		# get list of entries within <entry> </entry> tags
		my @entries = split /<entry/, $xml;
		# Discard first element == header
		shift @entries;
		main::logger "\nINFO: Got ".($#entries + 1)." programmes for $channels{$channel_id}\n" if $opt->{verbose};
		my $now = time();
		foreach my $entry (@entries) {
			my ( $title, $name, $brand_pid, $series_pid, $brand, $series, $episode, $episodenum, $seriesnum, $desc, $pid, $available, $channel, $duration, $thumbnail, $version, $guidance );
			my ($start, $available) = ($1, $2) if $entry =~ m{<availability\s+start="(.*?)"\s+end="(.*?)"};
			next if ! ( $start || $available );
			if ( $start ) {
				my $xstart = Programme::get_time_string( $start );
				next if $xstart > $now;
			}
			if ( $available ) {
				my $xavailable = Programme::get_time_string( $available );
				next if $xavailable < $now;
			}
			my $vpid = $1 if $entry =~ m{pid="(.+?)">};
			$pid = $1 if $entry =~ m{<pid>(.+?)</pid>};
			$duration = $1 if $entry =~ m{duration="(.*?)"};
			$desc = $1 if $entry =~ m{<synopsis>(.*?)</synopsis>};
			$episode = $1 if $entry =~ m{<title>(.*?)</title>};
			($brand_pid, $brand) = ($1, $2) if $entry =~ m{<parent.*?pid="(.*?)".*?type="Brand">(.*?)</parent>};
			($series_pid, $series) = ($1, $2) if $entry =~ m{<parent.*?pid="(.*?)".*?type="Series">(.*?)</parent>};
			$episode =~ s/^\Q$brand\E:\s+// if $brand;
			$episode =~ s/^\Q$series\E:\s+// if $series;
			if ( $brand ) {
				if ( $series && $series ne $brand ) {
					$name = "$brand: $series";
				} else {
					$name = $brand;
				}
			} else {
					$name = $series;
			}
			unless ( $name ) {
				# determine name and episode from title
				#( $name, $episode ) = Programme::bbciplayer::split_title( $title );
				$name = $brand = $episode;
				$episode = "-";
			}
			# Extract the seriesnum
			my $regex = 'Series\s+'.main::regex_numbers();
			$seriesnum = main::convert_words_to_number( $1 ) if "$name $episode" =~ m{$regex}i;
			# Extract the episode num
			my $regex_1 = 'Episode\s+'.main::regex_numbers();
			my $regex_2 = '^'.main::regex_numbers().'\.\s+';
			if ( "$name $episode" =~ m{$regex_1}i ) { 
				$episodenum = main::convert_words_to_number( $1 );
			} elsif ( $episode =~ m{$regex_2}i ) {
				$episodenum = main::convert_words_to_number( $1 );
			}
			# insert episode number in $episode
			#$episode = Programme::bbciplayer::insert_episode_number($episode, $episodenum);
			# Extract channel
			$channel = $channels{$channel_id};
			main::logger "DEBUG: '$pid, $name - $episode, $channel'\n" if $opt->{debug};
			# Merge and Skip if this pid is a duplicate
			if ( defined $prog->{$pid} ) {
				next;
			}
			# only default for radio
			$version = 'default';
			# no categories in AOD
			my @category;
			my $thumbsize = $opt->{thumbsizecache} || 150;
			my ($thumb_pid, $thumb_type, $thumbnail);
			($thumb_pid, $thumb_type) = ( $brand_pid , "brand" ) if $brand_pid;
			if ( ! ( $thumb_pid && $thumb_type ) ) {
				($thumb_pid, $thumb_type) = ( $series_pid , "series" ) if $series_pid;
			}
			if ( $thumb_pid && $thumb_type) {
				my $recipe = Programme::bbciplayer->thumb_url_recipes->{ $thumbsize };
				$recipe = Programme::bbciplayer->thumb_url_recipes->{ 150 } unless $recipe;
				$thumbnail = "http://ichef.bbci.co.uk/images/ic/${recipe}/legacy/${thumb_type}/${thumb_pid}.jpg";
			} else {
				$thumb_pid = $channel_map{$channel_id} || $channel_id;
				$thumbnail = "http://www.bbc.co.uk/iplayer/images/radio/${thumb_pid}_640_360.jpg";
			}
			# build data structure
			$prog->{$pid} = main::progclass($prog_type)->new(
				'pid'		=> $pid,
				'name'		=> $name,
				'versions'	=> $version,
				'episode'	=> $episode,
				'seriesnum'	=> $seriesnum,
				'episodenum'	=> $episodenum,
				'desc'		=> $desc,
				'guidance'	=> $guidance,
				'available'	=> 'Unknown',
				'duration'	=> $duration || 'Unknown',
				'thumbnail'	=> $thumbnail,
				'channel'	=> $channel,
				'categories'	=> join(',', sort @category),
				'type'		=> $prog_type,
				'web'		=> "${bbc_prog_page_prefix}/${pid}",
			);
		}
	}
}


sub get_links_ion {
	my $self = shift;
	my $prog = shift;
	my $prog_type = shift;
	my $atoz = shift;
	# Hack to get correct 'channels' method because this methods is being shared with Programme::radio
	my %channels = %{ main::progclass($prog_type)->channels_filtered( main::progclass($prog_type)->channels() ) };
	my $bbc_prog_page_prefix = 'http://www.bbc.co.uk/programmes'; # /$pid
	my $ua = main::create_ua( 'desktop', 1 );
	my $feed = 'listview';
	my @biguns = ( 'bbc_radio_four', 'bbc_radio_three', 'bbc_world_service' );
	my @dobs;
	my $now = time();
	for (my $i = 0; $i < 8; $i++) {
		my $then = $now - $i * 86400;
		my ($day, $mon, $year) = (gmtime($then))[3,4,5];
		push @dobs, sprintf("/date/%04d-%02d-%02d", $year+1900, ++$mon, $day);
	}
	my @filters;
	if ( $atoz ) {
		$feed = 'atoz';
		@filters = ( '/letters/a-z', '/letters/0-9' );
		if ( $prog_type eq 'tv' ) {
			push @filters, ( '/letters/a-z/category/signed', '/letters/0-9/category/signed' );
		}
	} else {
			@filters = ('');
			if ( $prog_type eq 'tv' ) {
				push @filters, '/category/signed';
				push @filters, '/category/dubbedaudiodescribed';
			}
	}
	my @channel_list = sort keys %channels;
	for my $channel_id ( @channel_list ) {
		my @channel_filters;
		if ( grep(/^$channel_id$/, @biguns) ) {
			for my $dob ( @dobs ) {
				for my $filter ( @filters ) {
					push @channel_filters, "$filter$dob";
				}
			}
		} else {
			@channel_filters = @filters;
		}
		for my $filter ( @channel_filters ) {
			my $url = "http://www.bbc.co.uk/iplayer/ion/$feed/format/xml/block_type/episode/service_type/${prog_type}/masterbrand/$channel_id$filter";
			main::logger "\nDEBUG: Getting feed $url\n" if $opt->{verbose};
			my $xml = main::request_url_retry($ua, $url, 3, '.', "\nWARNING: Failed to get programme index feed for $channels{$channel_id} - $filter\n");
			if ( ! $xml ) {
				return 1 if $opt->{refreshabortonerror};
				next;
			}
			decode_entities($xml);
			# Parse XML
			# get list of entries within <entry> </entry> tags
			my @entries = split /<episode>/, $xml;
			# Discard first element == header
			shift @entries;
			main::logger "\nINFO: Got ".($#entries + 1)." programmes for $channels{$channel_id} - $filter\n" if $opt->{verbose};
			foreach my $entry (@entries) {
				my ( $brand, $series, $subseries, $title, $name, $episode, $episodetitle, $nametitle, $episodenum, $seriesnum, $desc, $pid, $available, $channel, $duration, $thumbnail, $version, $guidance );
				$pid = $1 if $entry =~ m{<passionsite_title.*?<id>(.+?)</id>}s;
				$duration = $1 if $entry =~ m{<duration>(.*?)</duration>};
				$desc = $1 if $entry =~ m{<short_synopsis>(.*?)</short_synopsis>};
				$brand = $1 if $entry =~ m{<brand_title>(.*?)</brand_title>};
				$series = $1 if $entry =~ m{<series_title>(.*?)</series_title>};
				$subseries = $1 if $entry =~ m{<subseries_title>(.*?)</subseries_title>};
				$episode = $1 if $entry =~ m{<tag_schemes.*?<title>(.*?)</title>}s;
				if ( $subseries ) {
					$episode = "$subseries $episode";
				}
				$title = $1 if $entry =~ m{<complete_title>(.*?)</complete_title>};
				if ( $brand ) {
					if ( $series && $series ne $brand ) {
						$name = "$brand: $series";
					} else {
						$name = $brand;
					}
				} else {
						$name = $series;
				}
				unless ( $name ) {
					$name = $brand = $episode;
					$episode = "-";
				}
				# Extract the seriesnum
				my $regex = 'Series\s+'.main::regex_numbers();
				$seriesnum = main::convert_words_to_number( $1 ) if "$name $episode" =~ m{$regex}i;
				# Extract the episode num
				my $regex_1 = 'Episode\s+'.main::regex_numbers();
				my $regex_2 = '^'.main::regex_numbers().'\.\s+';
				if ( "$name $episode" =~ m{$regex_1}i ) { 
					$episodenum = main::convert_words_to_number( $1 );
				} elsif ( $episode =~ m{$regex_2}i ) {
					$episodenum = main::convert_words_to_number( $1 );
				}
				# insert episode number in $episode
				#$episode = Programme::bbciplayer::insert_episode_number($episode, $episodenum);
				# Extract channel
				$channel = $1 if $entry =~ m{<masterbrand_title>(.*?)</masterbrand_title>};
				main::logger "DEBUG: '$pid, $name - $episode, $channel'\n" if $opt->{debug};
				# categories
				my @category;
				my @lines = split /<category>/, $entry;
				shift @lines;
				for my $line ( @lines ) {
					push @category, $1 if $line =~ m{<title>(.*?)</title>};
				}
				# strip commas - they confuse sorting and spliting later
				s/,//g for @category;
				# Merge and Skip if this pid is a duplicate
				if ( defined $prog->{$pid} ) {
					main::logger "WARNING: '$pid, $prog->{$pid}->{name} - $prog->{$pid}->{episode}, $prog->{$pid}->{channel}' already exists (this channel = $channel)\n" if $opt->{verbose};
					# Since we use the 'Signed' (or 'Audio Described') channel to get sign zone/audio described data, merge the categories from this entry to the existing entry
					if ( $prog->{$pid}->{categories} ne join(',', sort @category) ) {
						my %cats;
						$cats{$_} = 1 for ( @category, split /,/, $prog->{$pid}->{categories} );
						main::logger "INFO: Merged categories for $pid from $prog->{$pid}->{categories} to ".join(',', sort keys %cats)."\n" if $opt->{verbose};
						$prog->{$pid}->{categories} = join(',', sort keys %cats);
					}
					# If this is a duplicate pid and the channel is now Signed then both versions are available
					$version = 'signed' if grep /Sign Zone/, @category;
					$version = 'audiodescribed' if grep /Audio Described/, @category;
					# Add version to versions for existing prog
					$prog->{$pid}->{versions} = join ',', main::make_array_unique_ordered( (split /,/, $prog->{$pid}->{versions}), $version );
					next;
				}
				# Check for signed-only or audiodescribed-only version from category
				if ( grep /Sign Zone/, @category ) {
					$version = 'signed';
				} elsif ( grep /Audio Described/, @category ) {
					$version = 'audiodescribed';
				} else {
					$version = 'default';
				}
				$guidance = $1 if $entry =~ m{<has_guidance>(.*?)</has_guidance>};
				if ( $guidance ) {
					$guidance = "Yes";
				} else {
					undef $guidance;
				}
				# Default to 150px width thumbnail;
				my $thumbsize = $opt->{thumbsizecache} || 150;
				my $image_template_url = $1 if $entry =~ m{<image_template_url>(.*?)</image_template_url>};
				my $recipe = Programme::bbciplayer->thumb_url_recipes->{ $thumbsize };
				$recipe = Programme::bbciplayer->thumb_url_recipes->{ 150 } if ! $recipe;
				my $thumbnail = $image_template_url;
				$thumbnail =~ s/\$recipe/$recipe/;
				# build data structure
				$prog->{$pid} = main::progclass($prog_type)->new(
					'pid'		=> $pid,
					'name'		=> $name,
					'versions'	=> $version,
					'episode'	=> $episode,
					'seriesnum'	=> $seriesnum,
					'episodenum'	=> $episodenum,
					'desc'		=> $desc,
					'guidance'	=> $guidance,
					'available'	=> 'Unknown',
					'duration'	=> $duration || 'Unknown',
					'thumbnail'	=> $thumbnail,
					'channel'	=> $channel,
					'categories'	=> join(',', sort @category),
					'type'		=> $prog_type,
					'web'		=> "${bbc_prog_page_prefix}/${pid}",
				);
			}
		}
	}
}


# Usage: Programme::tv->get_links( \%prog, 'tv' );
# Uses: %{ channels() }, \%prog
sub get_links {
	my $self = shift; # ignore obj ref
	my $prog = shift;
	my $prog_type = shift;
	main::logger "\nINFO: Getting $prog_type Index Feeds (this may take a few minutes)\n";
	my $rc = 0;
	if ( $prog_type eq 'radio' ) {
		$rc = $self->get_links_aod($prog, $prog_type);
	}
	elsif ( $prog_type eq 'tv' ) {
		$rc = $self->get_links_schedule($prog, $prog_type, 0);
	}
	return 1 if $rc && $opt->{refreshabortonerror};
	if ( $opt->{refreshfuture} ) {
		$rc = $self->get_links_schedule($prog, $prog_type, 1);
		return 1 if $rc && $opt->{refreshabortonerror};
	}
	main::logger "\n";
	return 0;
}


# get cache info for programmes from schedule
sub get_links_schedule {
	my $self = shift;
	my $prog = shift;
	my $prog_type = shift;
	my $future = shift;
	my %channels = %{ main::progclass($prog_type)->channels_filtered( main::progclass($prog_type)->channels_schedule() ) };
	my @channel_list = sort keys %channels;
	my @schedule_dates;
	my $limit = 0;
	my $limit_days = $opt->{"refreshlimit".${prog_type}} || $opt->{"refreshlimit"};
	$limit_days = 30 if $limit_days > 30;
	if ( $limit_days ) {
		my $now = time();
		$limit = $now - $limit_days * 86400;
		my ($limit_weeks, $rem) = (int $limit_days / 7, $limit_days % 7);
		$limit_weeks++ if $rem && $limit_weeks;
		for (my $i = $limit_weeks; $i >= 0; $i -= 1) {
			my $then = $now - ($i * 7) * 86400;
			my $year = (gmtime($then))[5];
			my $week = strftime( "%W", gmtime($then) );
			push @schedule_dates, sprintf("%04d/w%02d", $year+1900, ++$week);
		}
	} else {
		if ( $future ) {
			@schedule_dates = ( "this_week", "next_week" );
		} else {
			@schedule_dates = ( "last_week", "this_week" );
		}
	}
	for my $channel_id ( @channel_list ) {
		for my $schedule_date ( @schedule_dates ) {
			my $url = "http://www.bbc.co.uk/${channel_id}/${schedule_date}.xml";
			my $rc = $self->get_links_schedule_page($prog, $prog_type, $channels{$channel_id}, $future, $url, $limit);
			if ( $rc ) {
				return 1 if $opt->{refreshabortonerror};
				next;
			}
		}
	}
}

# get cache info from schedule page
sub get_links_schedule_page {
	my $self = shift;
	my $prog = shift;
	my $prog_type = shift;
	my $channel = shift;
	my $future = shift;
	my $url = shift;
	my $limit = shift;
	my $bbc_prog_page_prefix = 'http://www.bbc.co.uk/programmes'; # /$pid
	my $ua = main::create_ua( 'desktop', 1 );
	main::logger "DEBUG: Getting feed $url\n" if $opt->{debug};
	my $xml = main::request_url_retry($ua, $url, 3, '.', "\nWARNING: Failed to download programme schedule $url\n");
	return 1 if ! $xml;
	decode_entities($xml);
		
	# <broadcast is_repeat="0" is_blanked="0">
	# 	<pid>p0290kxs</pid>
	# 	<start>2014-10-31T11:00:00Z</start>
	# 	<end>2014-10-31T11:45:00Z</end>
	# 	<duration>2700</duration>
	# 	<programme type="episode">
	# 		<pid>b04n8rx0</pid>
	# 		<position>10</position>
	# 		<title>Episode 10</title>
	# 		<short_synopsis>Council officers deal with home owners living on top of deadly waste.</short_synopsis>
	# 		<media_type>audio_video</media_type>
	# 		<duration>2700</duration>
	# 		<image>
	# 			<pid>p028r5jx</pid>
	# 		</image>
	# 		<display_titles>
	# 			<title>Call the Council</title>
	# 			<subtitle>Series 2, Episode 10</subtitle>
	# 		</display_titles>
	# 		<first_broadcast_date>2014-10-31T11:00:00Z</first_broadcast_date>
	# 		<ownership>
	# 			<service type="tv" id="bbc_one" key="bbcone">
	# 				<title>BBC One</title>
	# 			</service>
	# 		</ownership>
	# 		<programme type="series">
	# 			<pid>b04mlq1k</pid>
	# 			<title>Series 2</title>
	# 			<position>2</position>
	# 			<image>
	# 				<pid>p028r5jx</pid>
	# 			</image>
	# 			<expected_child_count>10</expected_child_count>
	# 			<first_broadcast_date>2014-10-20T11:00:00+01:00</first_broadcast_date>
	# 			<ownership>
	# 				<service type="tv" id="bbc_one" key="bbcone">
	# 					<title>BBC One</title>
	# 				</service>
	# 			</ownership>
	# 			<programme type="brand">
	# 				<pid>b04mlpdd</pid>
	# 				<title>Call the Council</title>
	# 				<position/>
	# 				<image>
	# 					<pid>p028r5jx</pid>
	# 				</image>
	# 				<expected_child_count/>
	# 				<first_broadcast_date>2014-05-19T11:30:00+01:00</first_broadcast_date>
	# 				<ownership>
	# 					<service type="tv" id="bbc_one" key="bbcone">
	# 						<title>BBC One</title>
	# 					</service>
	# 				</ownership>
	# 			</programme>
	# 		</programme>
	# 		<available_until>2014-12-03T07:45:00Z</available_until>
	# 		<actual_start>2014-10-31T11:45:00Z</actual_start>
	# 		<is_available_mediaset_pc_sd>1</is_available_mediaset_pc_sd>
	# 		<is_legacy_media>0</is_legacy_media>
	# 		<media format="video">
	# 			<expires>2014-12-03T07:45:00Z</expires>
	# 			<availability>1 month left to watch</availability>
	# 		</media>
	# 	</programme>
	# </broadcast>	

	# get list of entries within <broadcast> </broadcast> tags
	my @entries = split /<broadcast[^s]/, $xml;
	# Discard first element == header
	shift @entries;
	main::logger "\nINFO: Got ".($#entries + 1)." programmes for $channel\n" if $opt->{verbose};
	my $now = time();
	foreach my $entry (@entries) {
		my ( $title, $name, $episode, $brand_pid, $series_pid, $brand, $series, $episodenum, $seriesnum, $desc, $pid, $available, $until, $duration, $thumbnail, $version, $guidance, $descshort );
		# Don't create this prog instance if the availability is in the past 
		# this prevents programmes which never appear in iPlayer from being indexed
		if ( $future ) {
			$available = $1 if $entry =~ m{<start>\s*(.+?)\s*</start>};
		} else {
			$available = $1 if $entry =~ m{<actual_start>\s*(.+?)\s*</actual_start>};
		}
		next if ! $available;
		if ( $future ) {
			next if Programme::get_time_string( $available ) < $now;
		} else {
			next if Programme::get_time_string( $available ) > $now;
			next if $limit && Programme::get_time_string( $available ) < $limit;
			$until = $1 if $entry =~ m{<available_until>\s*(.+?)\s*</available_until>};
			next if ! $until;
			next if Programme::get_time_string( $until ) < $now;
		}
		$pid = $1 if $entry =~ m{<programme\s+type="episode">.*?<pid>\s*(.+?)\s*</pid>};
		$desc = $1 if $entry =~ m{<short_synopsis>\s*(.+?)\s*</short_synopsis>};
		$duration = $1 if $entry =~ m{<duration>\s*(.+?)\s*</duration>};
		$episode = $1 if $entry =~ m{<programme\s+type="episode">.*?<title>\s*(.*?)\s*</title>};
		($brand_pid, $brand) = ($1, $2) if $entry =~ m{<programme\s+type="brand">.*?<pid>\s*(.*?)\s*</pid>.*?<title>\s*(.*?)\s*</title>.*?</programme>};
		($series_pid, $series) = ($1, $2) if $entry =~ m{<programme\s+type="series">.*?<pid>\s*(.*?)\s*</pid>.*?<title>\s*(.*?)\s*</title>.*?</programme>};
		if ( $brand ) {
			if ( $series && $series ne $brand ) {
				$name = "$brand: $series";
			} else {
				$name = $brand;
			}
		} else {
			$name = $series;
		}
		unless ( $name ) {
			$name = $brand = $episode;
			$episode = "-";
		}
		# Extract the seriesnum
		my $regex = 'Series\s+'.main::regex_numbers();
		$seriesnum = main::convert_words_to_number( $1 ) if "$name $episode" =~ m{$regex}i;
		my $series_position = $1 if $entry =~ m{<programme\s+type="series">.*?<position>\s*(.+?)\s*</position>};
		$seriesnum ||= $series_position;
		# Extract the episode num
		my $regex_1 = 'Episode\s+'.main::regex_numbers();
		my $regex_2 = '^'.main::regex_numbers().'\.\s+';
		if ( $episode =~ m{$regex_1}i ) { 
			$episodenum = main::convert_words_to_number( $1 );
		} elsif ( $episode =~ m{$regex_2}i ) {
			$episodenum = main::convert_words_to_number( $1 );
		}
		my $episode_position = $1 if $entry =~ m{<programme\s+type="episode">.*?<position>\s*(.+?)\s*</position>};
		$episodenum ||= $episode_position;
		# insert episode number in $episode
		#$episode = Programme::bbciplayer::insert_episode_number($episode, $episodenum);
		main::logger "DEBUG: '$pid, $name - $episode, $channel'\n" if $opt->{debug};
		# Merge and Skip if this pid is a duplicate
		if ( defined $prog->{$pid} ) {
			main::logger "WARNING: '$pid, $prog->{$pid}->{name} - $prog->{$pid}->{episode}, $prog->{$pid}->{channel}' already exists (this channel = $channel)\n" if $opt->{verbose};
			# Update this info from schedule (not available in the usual iplayer channels feeds)
			$prog->{$pid}->{duration} = $duration;
			$prog->{$pid}->{episodenum} = $episodenum if ! $prog->{$pid}->{episodenum};
			$prog->{$pid}->{seriesnum} = $seriesnum if ! $prog->{$pid}->{seriesnum};
			# use listing with earliest availability
			if ( $available && $prog->{$pid}->{available} && $prog->{$pid}->{available} ne "Unknown" && $available lt $prog->{$pid}->{available} ) {
				$prog->{$pid}->{available} = $available;
				$prog->{$pid}->{channel} = $channel;
			}
			next;
		}
		# only default version in schedules
		$version = 'default';
		# thumbnail options
		# http://ichef.bbci.co.uk/programmeimages/p01m1x5p/b04l8sml_640_360.jpg
		# http://ichef.bbci.co.uk/images/ic/640x360/p01m1x5p.jpg
		# Default to 150px width thumbnail;
		my $thumbsize = $opt->{thumbsizecache} || 150;
		my $image_pid = $1 if $entry =~ m{<image><pid>(.*?)</pid>}s;
		my $suffix = Programme::bbciplayer->thumb_url_suffixes->{ $thumbsize };
		$suffix = Programme::bbciplayer->thumb_url_suffixes->{ 150 } unless $suffix;
		my $thumbnail = "http://ichef.bbci.co.uk/programmeimages/${image_pid}/${pid}${suffix}";
		# build data structure
		$prog->{$pid} = main::progclass($prog_type)->new(
			'pid'		=> $pid,
			'name'		=> $name,
			'versions'	=> $version,
			'episode'	=> $episode,
			'seriesnum'	=> $seriesnum,
			'episodenum'	=> $episodenum,
			'desc'		=> $desc,
			'available'	=> $available,
			'duration'	=> $duration,
			'thumbnail'	=> $thumbnail,
			'channel'	=> $channel,
			'type'		=> $prog_type,
			'web'		=> "${bbc_prog_page_prefix}/${pid}",
		);
	}
}


# Usage: download (<prog>, <ua>, <mode>, <version>, <version_pid>)
sub download {
	my ( $prog, $ua, $mode, $version, $version_pid ) = ( @_ );

	# Check if we need 'tee'
	if ( $mode =~ /^real/ && (! main::exists_in_path('tee')) && $opt->{stdout} && (! $opt->{nowrite}) ) {
		main::logger "\nERROR: tee does not exist in path, skipping\n";
		return 'next';
	}
	if ( $mode =~ /^(real|wma)/ && (! main::exists_in_path('mplayer')) ) {
		main::logger "\nWARNING: Required mplayer does not exist\n";
		return 'next';
	}
	# Check if we have mplayer and lame
	if ( $mode =~ /^real/ && (! $opt->{wav}) && (! $opt->{raw}) && (! main::exists_in_path('lame')) ) {
		main::logger "\nWARNING: Required lame does not exist, will save file in wav format\n";
		$opt->{wav} = 1;
	}
	# Check if we have vlc
	if ( $mode =~ /^n95/ && (! main::exists_in_path('vlc')) ) {
		main::logger "\nWARNING: Required vlc does not exist\n";
		return 'next';
	}
	# if rtmpdump does not exist
	if ( $mode =~ /^(rtmp|flash)/ && ! main::exists_in_path('rtmpdump')) {
		main::logger "WARNING: Required rtmpdump does not exist - cannot download Flash audio/video\n";
		return 'next';
	}
	# Force raw mode if ffmpeg is not installed
	if ( $mode =~ /^(rtmp|flash)/ && ! main::exists_in_path('ffmpeg')) {
		main::logger "\nWARNING: Required ffmpeg/avconv does not exist - not converting flv file\n";
		$opt->{raw} = 1;
	}
	# require ffmpeg for HLS
	if ( $mode =~ /^hls/ && (! main::exists_in_path('ffmpeg')) ) {
		main::logger "\nWARNING: Required ffmpeg does not exist - cannot download HLS audio/video\n";
		return 'next';
	}

	if ( $mode =~ /^shoutcast/ && (! main::exists_in_path('ffmpeg')) ) {
		main::logger "\nWARNING: Required ffmpeg does not exist - cannot download Shoutcast audio\n";
		return 'next';
	}

	# Get extension from streamdata if defined and raw not specified
	$prog->{ext} = $prog->{streams}->{$version}->{$mode}->{ext};

	# Nasty hacky filename ext overrides based on non-default fallback modes
	# Override iphone ext from metadata which is wrong for radio
	$prog->{ext} = 'mp3' if $mode =~ /^iphone/ && $prog->{type} eq 'radio';
	# Override realaudio ext based on raw / wav
	$prog->{ext} = 'ra'  if $opt->{raw} &&  $mode =~ /^real/;
	$prog->{ext} = 'wav' if $opt->{wav} &&  $mode =~ /^real/;
	# Override flash ext based on raw
	$prog->{ext} = 'flv' if $opt->{raw} && $mode =~ /^flash/;
	# Override flashaac ext
	if ( ! $opt->{raw} && $mode =~ /^(flash|hls|ddl)aac/ ) {
		if ( $opt->{aactomp3} ) {
			$prog->{ext} = 'mp3';
		} else {
			$prog->{ext} = 'm4a';
		}
	}
	# Override ext based on  avi option
	$prog->{ext} = 'avi' if ! $opt->{raw} && $opt->{avi} && $prog->{type} eq 'tv';
	# Override ext based on mkv option
	$prog->{ext} = 'mkv' if ! $opt->{raw} && $opt->{mkv} && $prog->{type} eq 'tv';
	$prog->{ext} = 'ts' if $opt->{raw} && $mode =~ /^hls/;
	$prog->{ext} = 'aac' if $opt->{raw} && $mode =~ /^shoutcastaac/;
	$prog->{ext} = 'mp3' if $opt->{raw} && $mode =~ /^shoutcastmp3/;
	$prog->{ext} = 'm4a' if $opt->{raw} && $mode =~ /^ddlaac/;

	# Determine the correct filenames for this recording
	if ( $prog->generate_filenames( $ua, $prog->file_prefix_format() ) ) {
		return 'skip';
	}

	# Create symlink if required
	$prog->create_symlink( $prog->{symlink}, $prog->{filename}) if $opt->{symlink};

	# Create dir for prog if not streaming-only
	if ( ( ! ( $opt->{stdout} && $opt->{nowrite} ) ) && ( ! $opt->{test} ) ) {
		$prog->create_dir();
	}

	# Skip from here if we are only testing recordings
	return 'skip' if $opt->{test};

	# Get subtitles if they exist and are required 
	# best to do this before streaming file so that the subtitles can be enjoyed while recording progresses
	my $subfile_done;
	my $subfile;
	if ( $opt->{subtitles} ) {
		$subfile_done = "$prog->{dir}/$prog->{fileprefix}.srt";
		$subfile = "$prog->{dir}/$prog->{fileprefix}.partial.srt";
		main::logger "\n";
		if ( $prog->download_subtitles( $ua, $subfile ) && $opt->{subsrequired} && $prog->{type} eq 'tv') {
			main::logger "WARNING: Subtitles not available and --subsrequired specified.\n";
			return 'skip';
		}
	}

	my $return = 0;
	# Only get the stream if we are writing a file or streaming
	if ( $opt->{stdout} || ! $opt->{nowrite} ) {
		# set mode
		$prog->{mode} = $mode;

		# Disable proxy here if required
		main::proxy_disable($ua) if $opt->{partialproxy};

		# Instantiate new streamer based on streamdata
		my $class = "Streamer::$prog->{streams}->{$version}->{$mode}->{streamer}";
		my $stream = $class->new;

		# Do recording
		$return = $stream->get( $ua, $prog->{streams}->{$version}->{$mode}->{streamurl}, $prog, %{ $prog->{streams}->{$version}->{$mode} } );

		# Re-enable proxy here if required
		main::proxy_enable($ua) if $opt->{partialproxy};
	}

	# Rename the subtitle file accordingly if the stream get was successful
	move($subfile, $subfile_done) if $opt->{subtitles} && -f $subfile && ! $return;

	return $return;
}



# BBC iPlayer TV
# Download Subtitles, convert to srt(SubRip) format and apply time offset
# Todo: get the subtitle streamurl before this...
sub download_subtitles {
	my $prog = shift;
	my ( $ua, $file ) = @_;
	my $suburl;
	my $subs;
	
	# Don't redownload subs if the file already exists
	if ( ( -f $file || -f "$prog->{dir}/$prog->{fileprefix}.partial.srt" ) && ! $opt->{overwrite} ) {
		main::logger "INFO: Skipping subtitles download - file already exists: $file\n" if $opt->{verbose};
		return 0;
	}

	# Find subtitles stream
	for ( keys %{$prog->{streams}} ) {
		$suburl = $prog->{streams}->{$_}->{subtitles1}->{streamurl};
		last if $suburl;
	}
	# Return if we have no url
	if (! $suburl) {
		main::logger "INFO: Subtitles not available\n";
		return 2;
	}

	main::logger "INFO: Getting Subtitles from $suburl\n" if $opt->{verbose};

	# Open subs file
	unlink($file);
	open( my $fh, "> $file" );

	# Download subs
	$subs = main::request_url_retry($ua, $suburl, 2);
	if (! $subs ) {
		main::logger "ERROR: Subtitle Download failed\n";
		close $fh;
		unlink($file) if -f $file;
		return 1;
	} else {
		# Dump raw subs into a file if required
		if ( $opt->{subsraw} ) {
			unlink("$prog->{dir}/$prog->{fileprefix}.ttxt");
			main::logger "INFO: 'Downloading Raw Subtitles to $prog->{dir}/$prog->{fileprefix}.ttxt'\n";
			open( my $fhraw, "> $prog->{dir}/$prog->{fileprefix}.ttxt");
			print $fhraw $subs;
			close $fhraw;
		}
		main::logger "INFO: Downloading Subtitles to '$prog->{dir}/$prog->{fileprefix}.srt'\n";
	}

	# Convert the format to srt
	# SRT:
	#1
	#00:01:22,490 --> 00:01:26,494
	#Next round!
	#
	#2
	#00:01:33,710 --> 00:01:37,714
	#Now that we've moved to paradise, there's nothing to eat.
	#
	
	# TT:
	#<p begin="0:01:12.400" end="0:01:13.880">Thinking.</p>
	#<p begin="00:01:01.88" id="p15" end="00:01:04.80"><span tts:color="cyan">You're thinking of Hamburger Hill...<br /></span>Since we left...</p>
	#<p begin="00:00:18.48" id="p0" end="00:00:20.52">APPLAUSE AND CHEERING</p>
	# There is also a multiline form:
	#<p region="speaker" begin="00:00:01.840" end="00:00:08.800"><span style="textStyle">  This programme contains  <br/>
	#                  some strong language</span></p>
	# And a form with explicit namespace:
	#<tt:p xml:id="C80" begin="00:08:45.440" end="00:08:49.240" style="s2">It was in 2000. At the beginning,<tt:br />it was different.</tt:p>

	my @subsfmts = qw/compact default/;
	if ( $opt->{subsfmt} && ! grep /^$opt->{subsfmt}$/i, @subsfmts ) {
		main::logger "WARNING: Invalid value specified for --subsfmt: $opt->{subsfmt}. Must be one of: @subsfmts. Using default subtitles format.\n";
		$opt->{subsfmt} = "default";
	}
	my ($ns) = $subs =~ m{<(\w+:)p\b};
	my $p = $ns.'p';
	my $span = $ns.'span';
	my $br = $ns.'br';
	my $count = 0;
	for ( $subs =~ m{<$p\b.+?</$p>}gis ) {
		my ( $begin, $end, $sub ) = ( m{\bbegin="(.+?)".*?\bend="(.+?)".*?>(.+?)</$p>}is );
		if ( $begin && $end && $sub ) {
			($begin = sprintf( '%02d:%02d:%06.3f', split /:/, $begin )) =~ s/\./,/;
			($end = sprintf( '%02d:%02d:%06.3f', split /:/, $end )) =~ s/\./,/;
			if ($opt->{suboffset}) {
				$begin = main::subtitle_offset( $begin, $opt->{suboffset} );
				$end = main::subtitle_offset( $end, $opt->{suboffset} );
			}
			# remove line breaks, squeeze whitespace, fix up <br> and <span>
			$sub =~ s|\n+||g;
			$sub =~ s/(^\s+|\s+$)//g;
			$sub =~ s|\s+| |g;
			$sub =~ s|(\s?<$br.*?>\s?)+|<br/>|gi;
			$sub =~ s!(^<br/>|<br/>$)!!g;
			$sub =~ s|<br/>(</$span>)$|$1|i;
			$sub =~ s|(<$span.*?>)\s|$1|i;
			# separate individual lines based on <span>s
			$sub =~ s|<$span.*?>(.*?)</$span>|\n$1\n|gi;
			if ($sub =~ m{\n}) {
				# fix up line breaks
				$sub =~ s/(^\n|\n$)//g;
				# add leading hyphens
				$sub =~ s|\n+|\n- |g;
				if ( $sub =~ m{\n-} ) {
					$sub =~ s|^|- |;
				}
			}
			if ( $opt->{subsfmt} eq 'compact' ) {
				$sub =~ s|\n+||g;
				# embed line breaks
				$sub =~ s|<br/>|\n|g;
			} else {
				# remove <br/> elements
				$sub =~ s|\n- <br/>\n|\n|g;
				$sub =~ s|\n- <br/>|\n- |g;
				$sub =~ s|<br/>| |g;
			}
			decode_entities($sub);
			# Write to file
			print $fh ++$count, "\n";
			print $fh "$begin --> $end\n";
			print $fh "$sub\n\n";
		}
	}	
	close $fh;

	if ( ! $count ) {
		main::logger "WARNING: Subtitles empty\n";
		return 3;
	}

	return 0;
}



################### Radio class #################
package Programme::radio;

use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::stat;
use HTML::Entities;
use HTTP::Cookies;
use HTTP::Headers;
use IO::Seekable;
use IO::Socket;
use LWP::ConnCache;
use LWP::UserAgent;
use POSIX qw(mkfifo);
use strict;
use Time::Local;
use URI;

# Inherit from Programme class
use base 'Programme::bbciplayer';

# Class vars
sub index_min { return 10001 }
sub index_max { return 39999 };
sub channels_aod {
	return {
		'national' => {
			'radio1'		=> 'BBC Radio 1',
			'radio2'		=> 'BBC Radio 2',
			'radio3'		=> 'BBC Radio 3',
			'radio4'		=> 'BBC Radio 4',
			'fivelive'		=> 'BBC Radio 5 live',
			'worldservice'	=> 'BBC World Service',
			'1xtra'			=> 'BBC Radio 1Xtra',
			'radio4extra'	=> 'BBC Radio 4 Extra',
			'sportsextra'	=> 'BBC 5 live sports extra',
			'6music'		=> 'BBC 6 Music',
			'asiannetwork'	=> 'BBC Asian Network',
		},
		'regional' => {
			'radiofoyle'	=> 'BBC Radio Foyle',
			'radioscotland'	=> 'BBC Radio Scotland',
			'alba'			=> 'BBC Radio Nan Gaidheal',
			'radioulster'	=> 'BBC Radio Ulster',
			'radiowales'	=> 'BBC Radio Wales',
			'radiocymru'	=> 'BBC Radio Cymru',
		},
		'local' => {
			'bbc_radio_cumbria'			=> 'BBC Radio Cumbria',
			'bbc_radio_newcastle'			=> 'BBC Newcastle',
			'bbc_tees'				=> 'BBC Tees',
			'bbc_radio_lancashire'			=> 'BBC Radio Lancashire',
			'bbc_radio_merseyside'			=> 'BBC Radio Merseyside',
			'bbc_radio_manchester'			=> 'BBC Radio Manchester',
			'bbc_radio_leeds'			=> 'BBC Radio Leeds',
			'bbc_radio_sheffield'			=> 'BBC Radio Sheffield',
			'bbc_radio_york'			=> 'BBC Radio York',
			'bbc_radio_humberside'			=> 'BBC Radio Humberside',
			'bbc_radio_lincolnshire'		=> 'BBC Radio Lincolnshire',
			'bbc_radio_nottingham'			=> 'BBC Radio Nottingham',
			'bbc_radio_leicester'			=> 'BBC Radio Leicester',
			'bbc_radio_derby'			=> 'BBC Radio Derby',
			'bbc_radio_stoke'			=> 'BBC Radio Stoke',
			'bbc_radio_shropshire'			=> 'BBC Radio Shropshire',
			'bbc_wm'				=> 'BBC WM 95.6',
			'bbc_radio_coventry_warwickshire'	=> 'BBC Coventry & Warwickshire',
			'bbc_radio_hereford_worcester'		=> 'BBC Hereford & Worcester',
			'bbc_radio_northampton'			=> 'BBC Radio Northampton',
			'bbc_three_counties_radio'		=> 'BBC Three Counties Radio',
			'bbc_radio_cambridge'			=> 'BBC Radio Cambridgeshire',
			'bbc_radio_norfolk'			=> 'BBC Radio Norfolk',
			'bbc_radio_suffolk'			=> 'BBC Radio Suffolk',
			'bbc_radio_essex'			=> 'BBC Essex',
			'bbc_london'				=> 'BBC London 94.9',
			'bbc_radio_kent'			=> 'BBC Radio Kent',
			'bbc_radio_surrey'			=> 'BBC Surrey',
			'bbc_radio_sussex'			=> 'BBC Sussex',
			'bbc_radio_oxford'			=> 'BBC Radio Oxford',
			'bbc_radio_berkshire'			=> 'BBC Radio Berkshire',
			'bbc_radio_solent'			=> 'BBC Radio Solent',
			'bbc_radio_gloucestershire'		=> 'BBC Radio Gloucestershire',
			'bbc_radio_wiltshire'			=> 'BBC Wiltshire',
			'bbc_radio_bristol'			=> 'BBC Radio Bristol',
			'bbc_radio_somerset_sound'		=> 'BBC Somerset',
			'bbc_radio_devon'			=> 'BBC Radio Devon',
			'bbc_radio_cornwall'			=> 'BBC Radio Cornwall',
			'bbc_radio_guernsey'			=> 'BBC Radio Guernsey',
			'bbc_radio_jersey'			=> 'BBC Radio Jersey',
		}
	};
}

sub channels {
	return {
		'national' => {
			'bbc_radio_one'				=> 'BBC Radio 1',
			'bbc_radio_two'				=> 'BBC Radio 2',
			'bbc_radio_three'			=> 'BBC Radio 3',
			'bbc_radio_four'			=> 'BBC Radio 4',
			'bbc_radio_five_live'			=> 'BBC Radio 5 live',
			'bbc_world_service'			=> 'BBC World Service',
			'bbc_1xtra'				=> 'BBC Radio 1Xtra',
			'bbc_radio_four_extra'			=> 'BBC Radio 4 Extra',
			'bbc_radio_five_live_sports_extra'	=> 'BBC 5 live sports extra',
			'bbc_6music'				=> 'BBC 6 Music',
			#'bbc_7'					=> 'BBC 7',
			'bbc_asian_network'			=> 'BBC Asian Network',
		},
		'regional' => {
			'bbc_radio_foyle'			=> 'BBC Radio Foyle',
			'bbc_radio_scotland'			=> 'BBC Radio Scotland',
			'bbc_radio_nan_gaidheal'		=> 'BBC Radio Nan Gaidheal',
			'bbc_radio_ulster'			=> 'BBC Radio Ulster',
			'bbc_radio_wales'			=> 'BBC Radio Wales',
			'bbc_radio_cymru'			=> 'BBC Radio Cymru',
		},
		'local' => {
			'bbc_radio_cumbria'			=> 'BBC Radio Cumbria',
			'bbc_radio_newcastle'			=> 'BBC Newcastle',
			'bbc_tees'				=> 'BBC Tees',
			'bbc_radio_lancashire'			=> 'BBC Radio Lancashire',
			'bbc_radio_merseyside'			=> 'BBC Radio Merseyside',
			'bbc_radio_manchester'			=> 'BBC Radio Manchester',
			'bbc_radio_leeds'			=> 'BBC Radio Leeds',
			'bbc_radio_sheffield'			=> 'BBC Radio Sheffield',
			'bbc_radio_york'			=> 'BBC Radio York',
			'bbc_radio_humberside'			=> 'BBC Radio Humberside',
			'bbc_radio_lincolnshire'		=> 'BBC Radio Lincolnshire',
			'bbc_radio_nottingham'			=> 'BBC Radio Nottingham',
			'bbc_radio_leicester'			=> 'BBC Radio Leicester',
			'bbc_radio_derby'			=> 'BBC Radio Derby',
			'bbc_radio_stoke'			=> 'BBC Radio Stoke',
			'bbc_radio_shropshire'			=> 'BBC Radio Shropshire',
			'bbc_wm'				=> 'BBC WM 95.6',
			'bbc_radio_coventry_warwickshire'	=> 'BBC Coventry & Warwickshire',
			'bbc_radio_hereford_worcester'		=> 'BBC Hereford & Worcester',
			'bbc_radio_northampton'			=> 'BBC Radio Northampton',
			'bbc_three_counties_radio'		=> 'BBC Three Counties Radio',
			'bbc_radio_cambridge'			=> 'BBC Radio Cambridgeshire',
			'bbc_radio_norfolk'			=> 'BBC Radio Norfolk',
			'bbc_radio_suffolk'			=> 'BBC Radio Suffolk',
			'bbc_radio_essex'			=> 'BBC Essex',
			'bbc_london'				=> 'BBC London 94.9',
			'bbc_radio_kent'			=> 'BBC Radio Kent',
			'bbc_radio_surrey'			=> 'BBC Surrey',
			'bbc_radio_sussex'			=> 'BBC Sussex',
			'bbc_radio_oxford'			=> 'BBC Radio Oxford',
			'bbc_radio_berkshire'			=> 'BBC Radio Berkshire',
			'bbc_radio_solent'			=> 'BBC Radio Solent',
			'bbc_radio_gloucestershire'		=> 'BBC Radio Gloucestershire',
			'bbc_radio_wiltshire'			=> 'BBC Wiltshire',
			'bbc_radio_bristol'			=> 'BBC Radio Bristol',
			'bbc_radio_somerset_sound'		=> 'BBC Somerset',
			'bbc_radio_devon'			=> 'BBC Radio Devon',
			'bbc_radio_cornwall'			=> 'BBC Radio Cornwall',
			'bbc_radio_guernsey'			=> 'BBC Radio Guernsey',
			'bbc_radio_jersey'			=> 'BBC Radio Jersey',
		}
	};
}


# channel ids be found on http://www.bbc.co.uk/radio/stations
sub channels_schedule {
	return {
		'national' => {
			'radio1/programmes/schedules/england'	=> 'BBC Radio 1',
			'radio2/programmes/schedules'		=> 'BBC Radio 2',
			'radio3/programmes/schedules'		=> 'BBC Radio 3',
			'radio4/programmes/schedules/fm'	=> 'BBC Radio 4',
			'radio4/programmes/schedules/lw'	=> 'BBC Radio 4',
			'5live/programmes/schedules'		=> 'BBC Radio 5 live',
			'worldserviceradio/programmes/schedules'	=> 'BBC World Service',
			'1xtra/programmes/schedules'		=> 'BBC Radio 1Xtra',
			'radio4extra/programmes/schedules'	=> 'BBC Radio 4 Extra',
			'5livesportsextra/programmes/schedules'	=> 'BBC 5 live sports extra',
			'6music/programmes/schedules'		=> 'BBC 6 Music',
			'asiannetwork/programmes/schedules'	=> 'BBC Asian Network',
		},
		'regional' => {
			'radioscotland/programmes/schedules/fm'	=> 'BBC Radio Scotland',
			'radioscotland/programmes/schedules/orkney'	=> 'BBC Radio Scotland',
			'radioscotland/programmes/schedules/shetland'	=> 'BBC Radio Scotland',
			'radioscotland/programmes/schedules/highlandsandislands'	=> 'BBC Radio Scotland',
			'radioscotland/programmes/schedules/mw'	=> 'BBC Radio Scotland',
			'radionangaidheal/programmes/schedules'	=> 'BBC Radio Nan Gaidheal',
			'radioulster/programmes/schedules'		=> 'BBC Radio Ulster',
			'radiofoyle/programmes/schedules'		=> 'BBC Radio Foyle',
			'radiowales/programmes/schedules/fm'	=> 'BBC Radio Wales',
			'radiowales/programmes/schedules/mw'	=> 'BBC Radio Wales',
			'radiocymru/programmes/schedules'		=> 'BBC Radio Cymru',
		},
		'local' => {
			'radioberkshire/programmes/schedules'	=> 'BBC Radio Berkshire',
			'radiobristol/programmes/schedules'		=> 'BBC Radio Bristol',
			'radiocambridgeshire/programmes/schedules'	=> 'BBC Radio Cambridgeshire',
			'radiocornwall/programmes/schedules'	=> 'BBC Radio Cornwall',
			'bbccoventryandwarwickshire/programmes/schedules'	=> 'BBC Coventry & Warwickshire',
			'radiocumbria/programmes/schedules'		=> 'BBC Radio Cumbria',
			'radioderby/programmes/schedules'		=> 'BBC Radio Derby',
			'radiodevon/programmes/schedules'		=> 'BBC Radio Devon',
			'bbcessex/programmes/schedules'			=> 'BBC Essex',
			'radiogloucestershire/programmes/schedules'	=> 'BBC Radio Gloucestershire',
			'radioguernsey/programmes/schedules'		=> 'BBC Radio Guernsey',
			'bbcherefordandworcester/programmes/schedules'	=> 'BBC Hereford & Worcester',
			'radiohumberside/programmes/schedules'	=> 'BBC Radio Humberside',
			'radiojersey/programmes/schedules'		=> 'BBC Radio Jersey',
			'radiokent/programmes/schedules'		=> 'BBC Radio Kent',
			'radiolancashire/programmes/schedules'	=> 'BBC Radio Lancashire',
			'radioleeds/programmes/schedules'		=> 'BBC Radio Leeds',
			'radioleicester/programmes/schedules'	=> 'BBC Radio Leicester',
			'radiolincolnshire/programmes/schedules'	=> 'BBC Radio Lincolnshire',
			'bbclondon/programmes/schedules'		=> 'BBC London 94.9',
			'radiomanchester/programmes/schedules'	=> 'BBC Radio Manchester',
			'radiomerseyside/programmes/schedules'	=> 'BBC Radio Merseyside',
			'bbcnewcastle/programmes/schedules'		=> 'BBC Newcastle',
			'radionorfolk/programmes/schedules'		=> 'BBC Radio Norfolk',
			'radionorthampton/programmes/schedules'	=> 'BBC Radio Northampton',
			'radionottingham/programmes/schedules'	=> 'BBC Radio Nottingham',
			'radiooxford/programmes/schedules'		=> 'BBC Radio Oxford',
			'radiosheffield/programmes/schedules'	=> 'BBC Radio Sheffield',
			'radioshropshire/programmes/schedules'	=> 'BBC Radio Shropshire',
			'radiosolent/programmes/schedules'		=> 'BBC Radio Solent',
			'bbcsomerset/programmes/schedules'		=> 'BBC Somerset',
			'radiostoke/programmes/schedules'		=> 'BBC Radio Stoke',
			'radiosuffolk/programmes/schedules'		=> 'BBC Radio Suffolk',
			'bbcsurrey/programmes/schedules'		=> 'BBC Surrey',
			'bbcsussex/programmes/schedules'		=> 'BBC Sussex',
			'bbctees/programmes/schedules'			=> 'BBC Tees',
			'threecountiesradio/programmes/schedules'	=> 'BBC Three Counties Radio',
			'bbcwiltshire/programmes/schedules'		=> 'BBC Wiltshire',
			'wm/programmes/schedules'				=> 'BBC WM 95.6',
			'radioyork/programmes/schedules'		=> 'BBC Radio York',
		}
	};
}


# Class cmdline Options
sub opt_format {
	return {
		radiomode	=> [ 1, "radiomode|amode=s", 'Recording', '--radiomode <mode>,<mode>,...', "Radio recording modes: flashaachigh,flashaacstd,flashaudio,flashaaclow,wma. Shortcuts: default,good,better(=default),best,rtmp,flash,flashaac. ('default'=flashaachigh,flashaacstd,flashaudio,flashaaclow)"],
		bandwidth 	=> [ 1, "bandwidth=n", 'Recording', '--bandwidth', "In radio realaudio mode specify the link bandwidth in bps for rtsp streaming (default 512000)"],
		lame		=> [ 0, "lame=s", 'External Program', '--lame <path>', "Location of lame binary"],
		outputradio	=> [ 1, "outputradio=s", 'Output', '--outputradio <dir>', "Output directory for radio recordings (overrides --output)"],
		wav		=> [ 1, "wav!", 'Recording', '--wav', "In radio realaudio mode output as wav and don't transcode to mp3"],
		rtmpradioopts	=> [ 1, "rtmp-radio-opts|rtmpradioopts=s", 'Recording', '--rtmp-radio-opts <options>', "Add custom options to rtmpdump for radio"],
		hlsradioopts	=> [ 1, "hls-radio-opts|hlsradioopts=s", 'Recording', '--hls-radio-opts <options>', "Add custom options to ffmpeg HLS download re-muxing for radio"],
		ddlradioopts	=> [ 1, "ddl-radio-opts|ddlradioopts=s", 'Recording', '--ddl-radio-opts <options>', "Add custom options to ffmpeg DDL download re-muxing for radio"],
		ffmpegradioopts	=> [ 1, "ffmpeg-radio-opts|ffmpegradioopts=s", 'Recording', '--ffmpeg-radio-opts <options>', "Add custom options to ffmpeg re-muxing for radio"],
	};
}



# This gets run before the download retry loop if this class type is selected
sub init {
	# Force certain options for radio
	# Force --raw otherwise realaudio stdout streaming fails
	# (this would normally be a bad thing but since its a stdout stream we 
	# won't be downloading other types of progs afterwards)
	$opt->{raw} = 1 if $opt->{stdout} && $opt->{nowrite};
}



# Method to return optional list_entry format
sub optional_list_entry_format {
	my $prog = shift;
	my @format;
	for ( qw/ channel categories / ) {
		push @format, $prog->{$_} if defined $prog->{$_};
	}
	return ', '.join ', ', @format;
}



# Default minimum expected download size for a programme type
sub min_download_size {
	return 102400;
}



# Returns the modes to try for this prog type
sub modelist {
	my $prog = shift;
	my $mlist = $opt->{radiomode} || $opt->{modes};
	
	# Defaults
	if ( ! $mlist ) {
		if ( ! main::exists_in_path('rtmpdump') ) {
			main::logger "WARNING: Not using flash modes since rtmpdump is not found\n" if $opt->{verbose};
		} elsif ( ! main::exists_in_path('ffmpeg') ) {
			main::logger "WARNING: Not using HLS modes since ffmpeg is not found\n" if $opt->{verbose};
		} else {
			$mlist = 'default';
		}
	}
	# Deal with BBC Radio fallback modes and expansions
	$mlist = main::expand_list($mlist, 'best', 'default');
	$mlist = main::expand_list($mlist, 'vbetter', 'default');
	$mlist = main::expand_list($mlist, 'better', 'default');
	$mlist = main::expand_list($mlist, 'good', 'default');
	$mlist = main::expand_list($mlist, 'default', 'flash');
	$mlist = main::expand_list($mlist, 'rtmp', 'flash');
	$mlist = main::expand_list($mlist, 'flash', 'flashaachigh,flashaacstd,flashaaclow');
	$mlist = main::expand_list($mlist, 'flashaac', 'flashaachigh,flashaacstd,flashaaclow');
	$mlist = main::expand_list($mlist, 'hlsbest', 'hlsdefault');
	$mlist = main::expand_list($mlist, 'hlsvbetter', 'hlsdefault');
	$mlist = main::expand_list($mlist, 'hlsbetter', 'hlsdefault');
	$mlist = main::expand_list($mlist, 'hlsgood', 'hlsdefault');
	$mlist = main::expand_list($mlist, 'hlsdefault', 'hls');
	$mlist = main::expand_list($mlist, 'hls', 'hlsaac');
	$mlist = main::expand_list($mlist, 'hlsaac', 'hlsaachigh,hlsaacstd,hlsaaclow');
	$mlist = main::expand_list($mlist, 'ddl', 'ddlaac');
	$mlist = main::expand_list($mlist, 'ddlaac', 'ddlaachigh,ddlaacstd,ddlaaclow');

	return $mlist;
}



sub clean_pid {
	my $prog = shift;

	## extract [bpw]??????? format - remove surrounding url
	#$prog->{pid} =~ s/^.+\/([bpw]\w{7})(\..+)?$/$1/g;
	## Remove extra URL path for URLs like 'http://www.bbc.co.uk/iplayer/radio/bbc_radio_one'
	#$prog->{pid} =~ s/^.+\/(.+?)\/?$/$1/g;

	# If this is an iPlayer pid
	if ( $prog->{pid} =~ m{^([bpw]0[a-z0-9]{6})$} ) {
		# extract b??????? format from any URL containing it
		$prog->{pid} = $1;

	# If this is an iPlayer programme pid URL (and not on BBC programmes site)
	} elsif ( $prog->{pid} =~ m{^http.+\/([bpw]0[a-z0-9]{6})\/?.*$} ) { #&& $prog->{pid} !~ m{/programmes/} ) {
		# extract b??????? format from any URL containing it
		$prog->{pid} = $1;

	# If this is a BBC *iPlayer* Live channel
	#} elsif ( $prog->{pid} =~ m{http.+bbc\.co\.uk/iplayer/console/}i ) {
	#	# Just leave the URL as the pid

	# e.g. http://www.bbc.co.uk/iplayer/playlive/bbc_radio_fourfm/
	} elsif ( $prog->{pid} =~ m{http.+bbc\.co\.uk/iplayer}i ) {
		# Remove trailing path for URLs like 'http://www.bbc.co.uk/iplayer/radio/bbc_radio_fourfm/listenlive'
		$prog->{pid} =~ s/\/\w+live\/?$//;
		# Remove extra URL path for URLs like 'http://www.bbc.co.uk/iplayer/playlive/bbc_radio_one/'
		$prog->{pid} =~ s/^http.+\/(.+?)\/?$/$1/g;

	# Else this is an embedded media player URL (live or otherwise)
	} elsif ($prog->{pid} =~ m{^http}i ) {
		# Just leave the URL as the pid
	}
}



sub get_links {
	shift;
	# Delegate to Programme::tv (same function is used)
	return Programme::tv->get_links(@_);
}



sub download {
	# Delegate to Programme::tv (same function is used)
	return Programme::tv::download(@_);
}



################### BBC Live Parent class #################
package Programme::bbclive;

use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::stat;
use HTML::Entities;
use HTTP::Cookies;
use HTTP::Headers;
use IO::Seekable;
use IO::Socket;
use LWP::ConnCache;
use LWP::UserAgent;
use POSIX qw(mkfifo);
use strict;
use Time::Local;
use URI;

# Inherit from Programme class
use base 'Programme::bbciplayer';

# Class vars
sub file_prefix_format { '<name> <episode> <dldate> <dltime>' }

# Class cmdline Options
sub opt_format {
	return {};
}



# Method to return optional list_entry format
sub optional_list_entry_format {
	return '';
}


sub clean_pid {
	my $prog = shift;

	# If this is a BBC *iPlayer* Live channel
	#if ( $prog->{pid} =~ m{http.+bbc\.co\.uk/iplayer/console/}i ) {
	#	# Just leave the URL as the pid
	# e.g. http://www.bbc.co.uk/iplayer/playlive/bbc_radio_fourfm/
	if ( $prog->{pid} =~ m{http.+bbc\.co\.uk/iplayer}i ) {
		# Remove trailing path for URLs like 'http://www.bbc.co.uk/iplayer/radio/bbc_radio_fourfm/listenlive'
		$prog->{pid} =~ s/\/\w+live\/?$//;
		# Remove extra URL path for URLs like 'http://www.bbc.co.uk/iplayer/playlive/bbc_radio_one/'
		$prog->{pid} =~ s/^http.+\/(.+?)\/?$/$1/g;

	# Else this is an embedded media player URL (live or otherwise)
	} elsif ($prog->{pid} =~ m{^http}i ) {
		# Just leave the URL as the pid
	}
}



# Usage: Programme::liveradio->get_links( \%prog, 'liveradio' );
# Uses: %{ channels() }, \%prog
sub get_links {
	shift; # ignore obj ref
	my $prog = shift;
	my $prog_type = shift;
	# Hack to get correct 'channels' method because this methods is being shared with Programme::radio
	my %channels = %{ main::progclass($prog_type)->channels_filtered( main::progclass($prog_type)->channels() ) };

	for ( sort keys %channels ) {

			# Extract channel
			my $channel = $channels{$_};
			my $pid = $_;
			my $name = $channels{$_};
			my $episode = 'live';
			main::logger "DEBUG: '$pid, $name - $episode, $channel'\n" if $opt->{debug};

			(my $thumb_prog_type = $prog_type) =~ s/live//i;
			my $thumb_pid = $pid;
			$thumb_pid =~ s/^(bbc_one).*$/${1}_london/;
			$thumb_pid =~ s/^(bbc_two).*$/${1}_england/;
			$thumb_pid =~ s/scotland_mw/scotland_fm/g;
			my $thumbnail = "http://www.bbc.co.uk/iplayer/images/${thumb_prog_type}/${thumb_pid}_640_360.jpg";
			if ( $channel =~ /s4c/i ) {
				$thumbnail = "http://www.s4c.co.uk/static/img/s4c.png";
			}
			my $web_pid = $pid;
			if ( $prog_type eq 'livetv' ) {
				($web_pid = lc($channel)) =~ s/ //g;
				$web_pid =~ s/(northernireland|scotland|wales)/?area=$1/;
				$web_pid =~ s/northernireland/northern_ireland/;
			}
			if ( $prog_type eq 'liveradio' ) {
				($web_pid = lc($channel)) =~ s/ //g;
				$web_pid =~ s/scotland(fm|mw)/scotland/;
				$web_pid =~ s/bbc//;
			}
			# build data structure
			$prog->{$pid} = main::progclass($prog_type)->new(
				'pid'		=> $pid,
				'name'		=> $name,
				'versions'	=> 'default',
				'episode'	=> $episode,
				'desc'		=> "Live stream of $name",
				'guidance'	=> '',
				#'thumbnail'	=> "http://static.bbc.co.uk/mobile/iplayer_widget/img/ident_${pid}.png",
				#'thumbnail'	=> "http://www.bbc.co.uk/iplayer/img/station_logos/${pid}.png",
				'thumbnail'	=> $thumbnail,
				'channel'	=> $channel,
				#'categories'	=> join(',', @category),
				'type'		=> $prog_type,
				#'web'		=> "http://www.bbc.co.uk/iplayer/live/${web_pid}",
				'web'		=> "http://www.bbc.co.uk/${web_pid}",
			);
	}
	main::logger "\n";
	return 0;
}



sub download {
	# Delegate to Programme::tv (same function is used)
	return Programme::tv::download(@_);
}



################### Live TV class #################
package Programme::livetv;

use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::stat;
use HTML::Entities;
use HTTP::Cookies;
use HTTP::Headers;
use IO::Seekable;
use IO::Socket;
use LWP::ConnCache;
use LWP::UserAgent;
use POSIX qw(mkfifo);
use strict;
use Time::Local;
use URI;

# Inherit from Programme class
use base 'Programme::bbclive';

# Class vars
sub index_min { return 80000 }
sub index_max { return 80099 }
sub channels {
	return {
		'national' => {
			'bbc_one_hd'	=> 'BBC One',
			'bbc_two_hd'	=> 'BBC Two',
			'bbc_three'		=> 'BBC Three',
			'bbc_four'		=> 'BBC Four',
			'cbbc'				=> 'CBBC',
			'cbeebies'		=> 'CBeebies',
			'bbc_news24'	=> 'BBC News',
			'bbc_parliament'	=> 'BBC Parliament',
			'bbc_alba'		=> 'BBC Alba',
			's4cpbs'		=> 'S4C',
			'bbc_one_northern_ireland_hd'	=> 'BBC One Northern Ireland',
			'bbc_one_scotland_hd'	=> 'BBC One Scotland',
			'bbc_one_wales_hd'	=> 'BBC One Wales',
			'bbc_two_northern_ireland_digital'	=> 'BBC Two Northern Ireland',
			'bbc_two_scotland'	=> 'BBC Two Scotland',
			'bbc_two_wales_digital'	=> 'BBC Two Wales',
		}
	};
}

sub hls_pid_map {
	return {
		'bbc_three'		=> 'bbc_three_hd',
		'bbc_four'		=> 'bbc_four_hd',
		'cbbc'				=> 'cbbc_hd',
		'cbeebies'		=> 'cbeebies_hd',
		'bbc_news24'	=> 'bbc_news_channel_hd',
	}
}

# Class cmdline Options
sub opt_format {
	return {
		livetvmode	=> [ 1, "livetvmode=s", 'Recording', '--livetvmode <mode>,<mode>,...', "Live TV recording modes: hlshd,hlssd,hlsvhigh,hlshigh,hlsstd,hlslow. Shortcuts: default,good,better(=default),vbetter,best,hls. ('default'=hlsvhigh,hlshigh,hlsstd,hlslow)"],
		outputlivetv	=> [ 1, "outputlivetv=s", 'Output', '--outputlivetv <dir>', "Output directory for live tv recordings (overrides --output)"],
		rtmplivetvopts	=> [ 1, "rtmp-livetv-opts|rtmplivetvopts=s", 'Recording', '--rtmp-livetv-opts <options>', "Add custom options to rtmpdump for livetv"],
		hlslivetvopts	=> [ 1, "hls-livetv-opts|hlslivetvopts=s", 'Recording', '--hls-livetv-opts <options>', "Add custom options to ffmpeg HLS download encoding for livetv"],
		ffmpeglivetvopts	=> [ 1, "ffmpeg-livetv-opts|ffmpeglivetvopts=s", 'Recording', '--ffmpeg-livetv-opts <options>', "Add custom options to ffmpeg re-muxing for livetv"],
		livetvuk	=> [ 1, "livetv-uk|livetvuk!", 'Recording', '--livetv-uk', "Force use of hard-coded UK streams for HLS live tv"],
	};
}



# This gets run before the download retry loop if this class type is selected
sub init {
	# Force certain options for Live 
	# Force only one try if live and recording to file
	$opt->{attempts} = 1 if ( ! $opt->{attempts} ) && ( ! $opt->{nowrite} );
	# Force to skip checking history if live
	$opt->{force} = 1;
}



# Returns the modes to try for this prog type
sub modelist {
	my $prog = shift;
	my $mlist = $opt->{livetvmode} || $opt->{modes};
	
	# Defaults
	if ( ! $mlist ) {
		if ( ! main::exists_in_path('ffmpeg') ) {
			main::logger "WARNING: Not using HLS modes since ffmpeg is not found\n" if $opt->{verbose};
		} else {
			$mlist = 'default';
		}
	}
	# deal with obsolete values
	$mlist =~ s/(flash|rtmp)/hls/g;
	$mlist =~ s/normal/std/g;
	# Deal with BBC TV fallback modes and expansions
	$mlist = main::expand_list($mlist, 'default', 'hlsdefault');
	$mlist = main::expand_list($mlist, 'best', 'hlsbest');
	$mlist = main::expand_list($mlist, 'vbetter', 'hlsvbetter');
	$mlist = main::expand_list($mlist, 'better', 'hlsbetter');
	$mlist = main::expand_list($mlist, 'good', 'hlsgood');
	$mlist = main::expand_list($mlist, 'hls', 'hlsdefault');
	$mlist = main::expand_list($mlist, 'hlsdefault', 'hlsbetter');
	$mlist = main::expand_list($mlist, 'hlsbest', 'hlshd,hlsvbetter');
	$mlist = main::expand_list($mlist, 'hlsvbetter', 'hlssd,hlsbetter');
	$mlist = main::expand_list($mlist, 'hlsbetter', 'hlsvhigh,hlsgood');
	$mlist = main::expand_list($mlist, 'hlsgood', 'hlshigh,hlsstd,hlslow');

	return $mlist;
}



# Default minimum expected download size for a programme type
sub min_download_size {
	return 102400;
}



################### Live Radio class #################
package Programme::liveradio;

use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::stat;
use HTML::Entities;
use HTTP::Cookies;
use HTTP::Headers;
use IO::Seekable;
use IO::Socket;
use LWP::ConnCache;
use LWP::UserAgent;
use POSIX qw(mkfifo);
use strict;
use Time::Local;
use URI;

# Inherit from Programme class
use base 'Programme::bbclive';

# Class vars
sub index_min { return 80100 }
sub index_max { return 80199 }
sub channels {
	return {
		'national' => {
			'bbc_radio_one'				=> 'BBC Radio 1',
			'bbc_radio_two'				=> 'BBC Radio 2',
			'bbc_radio_three'			=> 'BBC Radio 3',
			'bbc_radio_fourfm'			=> 'BBC Radio 4 FM',
			'bbc_radio_fourlw'			=> 'BBC Radio 4 LW',
			'bbc_radio_five_live'			=> 'BBC Radio 5 live',
			'bbc_world_service' 			=> 'BBC World Service',
			'bbc_1xtra'				=> 'BBC 1Xtra',
			'bbc_radio_four_extra'			=> 'BBC Radio 4 Extra',
			'bbc_radio_five_live_sports_extra'	=> 'BBC 5 live Sports Extra',
			'bbc_6music'				=> 'BBC 6 Music',
			'bbc_asian_network'			=> 'BBC Asian Network',
		},
		'regional' => {
			'bbc_radio_foyle'			=> 'BBC Radio Foyle',
			'bbc_radio_scotland_fm'			=> 'BBC Radio Scotland FM',
			'bbc_radio_scotland_mw'			=> 'BBC Radio Scotland MW',
			'bbc_radio_nan_gaidheal'		=> 'BBC Radio Nan Gaidheal',
			'bbc_radio_ulster'			=> 'BBC Radio Ulster',
			'bbc_radio_wales'			=> 'BBC Radio Wales',
			'bbc_radio_cymru'			=> 'BBC Radio Cymru',
		},
		'local' => {
			'bbc_radio_cumbria'			=> 'BBC Cumbria',
			'bbc_radio_newcastle'			=> 'BBC Newcastle',
			'bbc_tees'				=> 'BBC Tees',
			'bbc_radio_lancashire'			=> 'BBC Lancashire',
			'bbc_radio_merseyside'			=> 'BBC Merseyside',
			'bbc_radio_manchester'			=> 'BBC Manchester',
			'bbc_radio_leeds'			=> 'BBC Leeds',
			'bbc_radio_sheffield'			=> 'BBC Sheffield',
			'bbc_radio_york'			=> 'BBC York',
			'bbc_radio_humberside'			=> 'BBC Humberside',
			'bbc_radio_lincolnshire'		=> 'BBC Lincolnshire',
			'bbc_radio_nottingham'			=> 'BBC Nottingham',
			'bbc_radio_leicester'			=> 'BBC Leicester',
			'bbc_radio_derby'			=> 'BBC Derby',
			'bbc_radio_stoke'			=> 'BBC Stoke',
			'bbc_radio_shropshire'			=> 'BBC Shropshire',
			'bbc_wm'				=> 'BBC WM',
			'bbc_radio_coventry_warwickshire'	=> 'BBC Coventry & Warwickshire',
			'bbc_radio_hereford_worcester'		=> 'BBC Hereford & Worcester',
			'bbc_radio_northampton'			=> 'BBC Northampton',
			'bbc_three_counties_radio'		=> 'BBC Three Counties',
			'bbc_radio_cambridge'			=> 'BBC Cambridgeshire',
			'bbc_radio_norfolk'			=> 'BBC Norfolk',
			'bbc_radio_suffolk'			=> 'BBC Suffolk',
			'bbc_radio_sussex'			=> 'BBC Sussex',
			'bbc_radio_essex'			=> 'BBC Essex',
			'bbc_london'				=> 'BBC London',
			'bbc_radio_kent'			=> 'BBC Kent',
			'bbc_southern_counties_radio'		=> 'BBC Southern Counties',
			'bbc_radio_oxford'			=> 'BBC Oxford',
			'bbc_radio_berkshire'			=> 'BBC Berkshire',
			'bbc_radio_solent'			=> 'BBC Solent',
			'bbc_radio_gloucestershire'		=> 'BBC Gloucestershire',
			'bbc_radio_swindon'			=> 'BBC Swindon',
			'bbc_radio_wiltshire'			=> 'BBC Wiltshire',
			'bbc_radio_bristol'			=> 'BBC Bristol',
			'bbc_radio_somerset_sound'		=> 'BBC Somerset',
			'bbc_radio_devon'			=> 'BBC Devon',
			'bbc_radio_cornwall'			=> 'BBC Cornwall',
			'bbc_radio_guernsey'			=> 'BBC Guernsey',
			'bbc_radio_jersey'			=> 'BBC Jersey',
		}
	};
}


# Class cmdline Options
sub opt_format {
	return {
		liveradiomode	=> [ 1, "liveradiomode=s", 'Recording', '--liveradiomode <mode>,<mode>,..', "Live Radio recording modes: hlsaachigh,hlsaacstd,hlsaacmed,hlsaaclow,shoutcastmp3std,shoutcastaachigh(R3 only, UK only). Shortcuts: default,good,better(=default),best,hls. ('default'=hlsaachigh,hlsaacstd,hlsaacmed,hlsaaclow)"],
		outputliveradio	=> [ 1, "outputliveradio=s", 'Output', '--outputliveradio <dir>', "Output directory for live radio recordings (overrides --output)"],
		rtmpliveradioopts => [ 1, "rtmp-liveradio-opts|rtmpliveradioopts=s", 'Recording', '--rtmp-liveradio-opts <options>', "Add custom options to rtmpdump for liveradio"],
		hlsliveradioopts	=> [ 1, "hls-liveradio-opts|hlsliveradioopts=s", 'Recording', '--hls-liveradio-opts <options>', "Add custom options to ffmpeg HLS download re-muxing for liveradio"],
		ffmpegliveradioopts => [ 1, "ffmpeg-liveradio-opts|ffmpegliveradioopts=s", 'Recording', '--ffmpeg-liveradio-opts <options>', "Add custom options to ffmpeg re-muxing for liveradio"],
		shoutcastliveradioopts	=> [ 1, "shoutcast-liveradio-opts|shoutcastliveradioopts=s", 'Recording', '--shoutcast-liveradio-opts <options>', "Add custom options to ffmpeg Shoutcast download re-muxing for liveradio"],
		liveradiouk	=> [ 1, "liveradio-uk|liveradiouk!", 'Recording', '--liveradio-uk', "Force use of hard-coded UK streams for HLS live radio (overrides --liveradio-intl). Ignored for World Service"],
		liveradiointl	=> [ 1, "liveradio-intl|liveradiointl!", 'Recording', '--liveradio-intl', "Force use of hard-coded international streams for HLS live radio.  Ignored for World Service"],
	};
}



# This gets run before the download retry loop if this class type is selected
sub init {
	# Force certain options for Live 
	# Force --raw otherwise realaudio stdout streaming fails
	# (this would normally be a bad thing but since its a live stream we 
	# won't be downloading other types of progs afterwards)
	$opt->{raw} = 1 if $opt->{stdout} && $opt->{nowrite};
	# Force only one try if live and recording to file
	$opt->{attempts} = 1 if ( ! $opt->{attempts} ) && ( ! $opt->{nowrite} );
	# Force to skip checking history if live
	$opt->{force} = 1;
}



# Returns the modes to try for this prog type
sub modelist {
	my $prog = shift;
	my $mlist = $opt->{liveradiomode} || $opt->{modes};
	
	# Defaults
	if ( ! $mlist ) {
		if ( ! main::exists_in_path('ffmpeg') ) {
			main::logger "WARNING: Not using HLS and Shoutcast modes since ffmpeg is not found\n" if $opt->{verbose};
		} else {
			$mlist = 'default';
		}
	}
	# deal with obsolete values
	$mlist =~ s/(flash|rtmp)/hls/g;
	# Deal with BBC Radio fallback modes and expansions
	$mlist = main::expand_list($mlist, 'default', 'hlsdefault');
	$mlist = main::expand_list($mlist, 'best', 'hlsbest');
	$mlist = main::expand_list($mlist, 'vbetter', 'hlsvbetter');
	$mlist = main::expand_list($mlist, 'better', 'hlsbetter');
	$mlist = main::expand_list($mlist, 'good', 'hlsgood');
	$mlist = main::expand_list($mlist, 'hlsbest', 'hlsdefault');
	$mlist = main::expand_list($mlist, 'hlsvbetter', 'hlsdefault');
	$mlist = main::expand_list($mlist, 'hlsbetter', 'hlsdefault');
	$mlist = main::expand_list($mlist, 'hlsgood', 'hlsdefault');
	$mlist = main::expand_list($mlist, 'hlsdefault', 'hls');
	$mlist = main::expand_list($mlist, 'hls', 'hlsaac');
	$mlist = main::expand_list($mlist, 'hlsaac', 'hlsaachigh,hlsaacstd,hlsaacmed,hlsaaclow');
	$mlist = main::expand_list($mlist, 'shoutcast', 'shoutcastaac,shoutcastmp3');
	$mlist = main::expand_list($mlist, 'shoutcastmp3', 'shoutcastmp3high,shoutcastmp3std,shoutcastmp3low');
	$mlist = main::expand_list($mlist, 'shoutcastaac', 'shoutcastaachigh,shoutcastaacstd,shoutcastaaclow');

	return $mlist;
}



# Default minimum expected download size for a programme type
sub min_download_size {
	return 102400;
}


################### Streamer class #################
package Streamer;

# Class vars
# Global options
my $optref;
my $opt;


# Constructor
# Usage: $streamer = Streamer->new();
sub new {
	my $type = shift;
	my %params = @_;
	my $self = {};
	for (keys %params) {
		$self->{$_} = $params{$_};
	}
	# Ensure the subclass $opt var is pointing to the Superclass global optref
	$opt = $Streamer::optref;
	bless $self, $type;
}


# Use to bind a new options ref to the class global $optref var
sub add_opt_object {
	my $self = shift;
	$Streamer::optref = shift;
}


# $opt->{<option>} access method
sub opt {
	my $self = shift;
	my $optname = shift;
	return $opt->{$optname};
}



################### Streamer::iphone class #################
package Streamer::iphone;

# Inherit from Streamer class
use base 'Streamer';

use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::stat;
use HTML::Entities;
use HTTP::Cookies;
use HTTP::Headers;
use IO::Seekable;
use IO::Socket;
use LWP::ConnCache;
use LWP::UserAgent;
use POSIX qw(mkfifo);
use strict;
use Time::Local;
use URI;



# Generic
# Get streaming iphone URL
# More iphone stream data http://www.bbc.co.uk/json/stream/b0067vmx/iplayer_streaming_http_mp4?r=585330738351 HTTP/1.1
# Capabilities based on IP address: http://www.bbc.co.uk/mobile/iplayer-mgw/damp/proxytodemi?ip=111.222.333.444
# Category codes list: http://www.bbc.co.uk/mobile/iwiplayer/category_codes.php
sub get_url {
	shift;
	my $ua = shift;
	my $pid = shift;

	# Look for href="http://download.iplayer.bbc.co.uk/iplayer_streaming_http_mp4/5439950172312621205.mp4?token=iVX.lots.of.text.x9Z%2F2GNBdQKl0%3D%0A&amp;pid=b00qhs36"
	my $url;
	my $iphone_download_prefix = 'http://www.bbc.co.uk/mobile/iplayer/episode';
	my $url_0 = ${iphone_download_prefix}.'/'.${pid};
	main::logger "INFO: iphone stream URL = $url_0\n" if $opt->{verbose};
	my $safari_ua = main::create_ua( 'safari' );
	my $html = main::request_url_retry( $safari_ua, $url_0, 3, undef, undef, 1 );
	$html =~ s/\n/ /g;
	# Check for guidance warning
	my $guidance_post;
	$guidance_post = $1 if $html =~ m{(isOver\d+)};
	if ( $guidance_post ) {
		my $h = new HTTP::Headers(
			'User-Agent'		=> main::user_agent( 'coremedia' ),
			'Accept'		=> '*/*',
			'Accept-Language'	=> 'en',
			'Connection'		=> 'keep-alive',
 			'Pragma'		=> 'no-cache',
		);
		main::logger "INFO: Guidance '$guidance_post' Warning Detected\n" if $opt->{verbose};
		# Now post this var and get html again
		my $req = HTTP::Request->new('POST', $url_0, $h);
		$req->content_type('application/x-www-form-urlencoded');
		$req->content('form=guidanceprompt&'.$guidance_post.'=1');
		my $res = $ua->request($req);
		$html = $res->as_string;
	}
	$url = decode_entities($1) if $html =~ m{href="(http.//download\.iplayer\.bbc\.co\.uk/iplayer_streaming_http_mp4.+?)"};
	main::logger "DEBUG: Got iphone mediaselector URL: $url\n" if $opt->{verbose};
	
	if ( ! $url ) {
		main::logger "ERROR: Failed to get iphone URL from iplayer site\n\n";
	}
	return $url;
}



# %prog (only for %prog for mode and tagging)
# Get the h.264/mp3 stream
# ( $stream, $ua, $url_2, $prog )
sub get {
	my ( $stream, $ua, $url_2, $prog ) = @_;
	my $childpid;
	my $iphone_block_size	= 0x2000000; # 32MB

	# Stage 3a: Download 1st byte to get exact file length
	main::logger "INFO: Stage 3 URL = $url_2\n" if $opt->{verbose};

	# Use url prepend if required
	if ( defined $opt->{proxy} && $opt->{proxy} =~ /^prepend:/ ) {
		$url_2 = $opt->{proxy}.main::url_encode( $url_2 );
		$url_2 =~ s/^prepend://g;
	}

	# Setup request header
	my $h = new HTTP::Headers(
		'User-Agent'	=> main::user_agent( 'coremedia' ),
		'Accept'	=> '*/*',
		'Range'		=> 'bytes=0-1',
	);
	# detect bad url => not available
	if ( $url_2 !~ /^http:\/\// ) {
		main::logger "WARNING: iphone version not available\n";
		return 'next';
	}
	my $req = HTTP::Request->new ('GET', $url_2, $h);
	my $res = $ua->request($req);
	# e.g. Content-Range: bytes 0-1/181338136 (return if no content length returned)
	my $download_len = $res->header("Content-Range");
	if ( ! $download_len ) {
		main::logger "WARNING: iphone version not available\n";
		return 'retry';
	}
	$download_len =~ s|^bytes 0-1/(\d+).*$|$1|;
	main::logger "INFO: Download File Length $download_len\n" if $opt->{verbose};

	# Only do this if we're rearranging QT streams
	my $mdat_start = 0;
	# default (tells the download chunk loop where to stop - i.e. EOF instead of end of mdat atom)
	my $moov_start = $download_len + 1;
	my $header;

	# If we have partial content and wish to stream, resume the recording & spawn off STDOUT from existing file start 
	# Sanity check - we cannot support resuming of partial content if we're streaming also. 
	if ( $opt->{stdout} && (! $opt->{nowrite}) && -f $prog->{filepart} ) {
		main::logger "WARNING: Partially recorded file exists, streaming will start from the beginning of the programme\n";
		# Don't do usual streaming code - also force all messages to go to stderr
		delete $opt->{stdout};
		$opt->{stderr} = 1;
		$childpid = fork();
		if (! $childpid) {
			# Child starts here
			main::logger "INFO: Streaming directly for partially recorded file $prog->{filepart}\n";
			if ( ! open( STREAMIN, "< $prog->{filepart}" ) ) {
				main::logger "INFO: Cannot Read partially recorded file to stream\n";
				exit 4;
			}
			my $outbuf;
			# Write out until we run out of bytes
			my $bytes_read = 65536;
			while ( $bytes_read == 65536 ) {
				$bytes_read = read(STREAMIN, $outbuf, 65536 );
				#main::logger "INFO: Read $bytes_read bytes\n";
				print STDOUT $outbuf;
			}
			close STREAMIN;
			main::logger "INFO: Stream thread has completed\n";
			exit 0;
		}
	}

	# Open file if required
	my $fh = main::open_file_append($prog->{filepart});

	# If the partial file already exists, then resume from the correct mdat/download offset
	my $restart_offset = 0;
	my $moovdata;
	my $moov_length = 0;

	# If we have a too-small-sized file (greater than moov_length+mdat_start) and not stdout and not no-write then this is a partial recording
	if (-f $prog->{filepart} && (! $opt->{stdout}) && (! $opt->{nowrite}) && stat($prog->{filepart})->size > ($moov_length+$mdat_start) ) {
		# Calculate new start offset (considering that we've put moov first in file)
		$restart_offset = stat($prog->{filepart})->size - $moov_length;
		main::logger "INFO: Resuming recording from $restart_offset                        \n";
	}

	# Not sure if this is already done in download method???
	# Create symlink if required
	$prog->create_symlink( $prog->{symlink}, $prog->{filepart} ) if $opt->{symlink};

	# Start marker
	my $start_time = time();

	# Download mdat in blocks
	my $chunk_size = $iphone_block_size;
	for ( my $s = $restart_offset; $s < ${moov_start}-1; $s+= $chunk_size ) {
		# get mdat chunk into file
		my $retcode;
		my $e;
		# Get block end offset
		if ( ($s + $chunk_size - 1) > (${moov_start}-1) ) {
			$e = $moov_start - 1;
		} else {
			$e = $s + $chunk_size - 1;
		}
		# Get block from URL and append to $prog->{filepart}
		if ( main::download_block($prog->{filepart}, $url_2, $ua, $s, $e, $download_len, $fh ) ) {
			main::logger "\rERROR: Could not download block $s - $e from $prog->{filepart}\n\n";
			return 'retry';
		}
	}

	# Close fh
	close $fh;

	# end marker
	my $end_time = time() + 0.0001;

	# Calculate average speed, duration and total bytes recorded
	main::logger sprintf("\rINFO: Recorded %.2fMB in %s at %5.0fkbps to %s\n", 
		($moov_start - 1 - $restart_offset) / (1024.0 * 1024.0),
		sprintf("%02d:%02d:%02d", ( gmtime($end_time - $start_time))[2,1,0] ), 
		( $moov_start - 1 - $restart_offset ) / ($end_time - $start_time) / 1024.0 * 8.0, 
		$prog->{filename} );

	# Moving file into place as complete (if not stdout)
	move($prog->{filepart}, $prog->{filename}) if $prog->{filepart} ne $prog->{filename} && ! $opt->{stdout};

	# Re-symlink file
	$prog->create_symlink( $prog->{symlink}, $prog->{filename} ) if $opt->{symlink};

	return 0;
}



################### Streamer::rtmp class #################
package Streamer::rtmp;

# Inherit from Streamer class
use base 'Streamer';

use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::Spec;
use File::stat;
use HTML::Entities;
use HTTP::Cookies;
use HTTP::Headers;
use IO::Seekable;
use IO::Socket;
use LWP::ConnCache;
use LWP::UserAgent;
use POSIX qw(mkfifo);
use strict;
use Time::Local;
use URI;


sub opt_format {
	return {
		ffmpeg		=> [ 0, "ffmpeg|avconv=s", 'External Program', '--ffmpeg <path>', "Location of ffmpeg or avconv binary. Synonyms: --avconv"],
		ffmpegobsolete		=> [ 1, "ffmpeg-obsolete|ffmpegobsolete|avconv-obsolete|avconvobsolete!", 'External Program', '--ffmpeg-obsolete', "Indicates you are using an obsolete version of ffmpeg (<0.7) that does not support the -loglevel option, so  --quiet, --verbose and --debug will not be applied to ffmpeg. Synonym: --avconv-obsolete"],
		rtmpport	=> [ 1, "rtmpport=n", 'Recording', '--rtmpport <port>', "Override the RTMP port (e.g. 443)"],
		rtmpdump	=> [ 0, "rtmpdump|flvstreamer=s", 'External Program', '--rtmpdump <path>', "Location of rtmpdump binary. Synonyms: --flvstreamer"],
		swfurl	=> [ 0, "swfurl=s", 'Recording', '--swfurl <URL>', "URL of Flash player used by rtmpdump for verification.  Only use if default Flash player URL is not working."],
	};
}


# %prog (only for {ext} and {mode})
# Actually do the RTMP streaming
sub get {
	my ( $stream, undef, undef, $prog, %streamdata ) = @_;
	my @cmdopts;

	my $url_2 	= $streamdata{streamurl};
	my $server	= $streamdata{server};
	my $application = $streamdata{application};
	my $tcurl 	= $streamdata{tcurl};
	my $authstring 	= $streamdata{authstring};
	my $swfurl 	= $streamdata{swfurl};
	my $playpath 	= $streamdata{playpath};
	my $port 	= $streamdata{port} || $opt->{rtmpport} || 1935;
	my $protocol	= $streamdata{protocol} || 0;
	my $pageurl	= $prog->{player};
	my $mode	= $prog->{mode};
	push @cmdopts, ( split /\s+/, $streamdata{extraopts} ) if $streamdata{extraopts};

	my $file_tmp;
	my @cmd;
	my $swfarg = "--swfUrl";

	if ( $opt->{raw} ) {
		$file_tmp = $prog->{filepart};
	} else {
		$file_tmp = $prog->{filepart}.'.flv'
	}

	# Remove failed file recording (below a certain size) - hack to get around rtmpdump not returning correct exit code
	if ( -f $file_tmp && stat($file_tmp)->size < $prog->min_download_size() ) {
		unlink( $file_tmp );
	}
		
	# rtmpdump version detection e.g. 'RTMPDump v2.4'
	my $rtmpver = `"$bin->{rtmpdump}" --help 2>&1`;
	if ( $opt->{verbose} ) {
		(my $rtmpver2 = $rtmpver) =~ s/^/INFO: /gm;
		main::logger "INFO: rtmpver: \n$rtmpver2";
	}
	if ( $rtmpver =~ /swfVfy/ ) {
		$swfarg = "--swfVfy";
	} else {
		main::logger "WARNING: Your version of rtmpdump/flvstreamer does not support SWF Verification\n";
		main::logger "WARNING: You may see this warning if rtmpdump has malfunctioned\n";
		main::logger "WARNING: Use --verbose to print the output from rtmpdump\n" unless $opt->{verbose};
	}
	$rtmpver =~ s/^\w+\s+v?([\.\d]+)(.*\n)*$/$1/g;
	main::logger "INFO: $bin->{rtmpdump} version $rtmpver\n" if $opt->{verbose};
	main::logger "INFO: RTMP_URL: $url_2, tcUrl: $tcurl, application: $application, authString: $authstring, swfUrl: $swfurl, file: $prog->{filepart}, file_done: $prog->{filename}\n" if $opt->{verbose};

	# Save the effort and don't support < v1.8
	if ( $rtmpver < 1.8 ) {
		main::logger "WARNING: rtmpdump/flvstreamer 1.8 or later is required - please upgrade\n";
		main::logger "WARNING: You may see this warning if rtmpdump has malfunctioned\n";
		main::logger "WARNING: Use --verbose to print the output from rtmpdump\n" unless $opt->{verbose};
		return 'next';
	}

	# Add --live option if required
	push @cmdopts, '--live' if $streamdata{live};

	# Add start stop options if defined
	if ( $opt->{start} || $opt->{stop} ) {
		push @cmdopts, ( '--start', $opt->{start} ) if $opt->{start};
		push @cmdopts, ( '--stop', $opt->{stop} ) if $opt->{stop};
	}
	
	# Add hashes option if required
	push @cmdopts, '--hashes' if $opt->{hash};
	
	# Create symlink if required
	$prog->create_symlink( $prog->{symlink}, $file_tmp ) if $opt->{symlink};

	# Deal with stdout streaming
	if ( $opt->{stdout} && not $opt->{nowrite} ) {
		main::logger "ERROR: Cannot stream RTMP to STDOUT and file simultaneously\n";
		exit 4;
	}
	push @cmdopts, ( '--resume', '-o', $file_tmp ) if ! ( $opt->{stdout} && $opt->{nowrite} );
	push @cmdopts, @{ $binopts->{rtmpdump} } if $binopts->{rtmpdump};
	
	# Add custom options to rtmpdump for this type if specified with --rtmp-<type>-opts
	if ( defined $opt->{'rtmp'.$prog->{type}.'opts'} ) {
		push @cmdopts, ( split /\s+/, $opt->{'rtmp'.$prog->{type}.'opts'} );
	}

	my $return;
	# Different invocation depending on version
	# if playpath is defined
	if ( $playpath ) {
		@cmd = (
			$bin->{rtmpdump},
			'--port', $port,
			'--protocol', $protocol,
			'--playpath', $playpath,
			'--host', $server,
			$swfarg, $swfurl,
			'--tcUrl', $tcurl,
			'--app', $application,
			'--pageUrl', $pageurl,
			@cmdopts,
		);
	# Using just streamurl (i.e. no playpath defined)
	} else {
		@cmd = (
			$bin->{rtmpdump},
			'--port', $port,
			'--protocol', $protocol,
			'--rtmp', $streamdata{streamurl},
			@cmdopts,
		);
	}

	$return = main::run_cmd( 'normal', @cmd );

	# exit behaviour when streaming
	if ( $opt->{nowrite} && $opt->{stdout} ) {
		if ( $return == 0 ) {
			main::logger "\nINFO: Streaming completed successfully\n";
			return 0;
		} else {
			main::logger "\nINFO: Streaming failed with exit code $return\n";
			return 'abort';
		}
	}

	# if we fail during the rtmp streaming, try to resume (this gets new streamdata again so that it isn't stale)
	unless ( $return == 2 && $opt->{stop} ) {
		return 'retry' if $return && -f $file_tmp && stat($file_tmp)->size > $prog->min_download_size();
	}

	# If file is too small or non-existent then delete and try next mode
	if ( (! -f $file_tmp) || ( -f $file_tmp && stat($file_tmp)->size < $prog->min_download_size()) ) {
		main::logger "WARNING: Failed to stream file $file_tmp via RTMP\n";
		unlink $file_tmp;
		return 'next';
	}
	
	# Add custom options to ffmpeg for this type if specified with -ffmpeg-<type>-opts
	my @ffmpeg_opts = ();
	if ( defined $opt->{'ffmpeg'.$prog->{type}.'opts'} ) {
		push @ffmpeg_opts, ( split /\s+/, $opt->{'ffmpeg'.$prog->{type}.'opts'} );
	}

	# Retain raw flv format if required
	if ( $opt->{raw} ) {
		if ( $file_tmp ne $prog->{filename} && ! $opt->{stdout} ) {
			move($file_tmp, $prog->{filename});
			$prog->check_duration() if $opt->{checkduration} && !$streamdata{live};
		}
		return 0;

	# Convert flv to mp3/aac
	} elsif ( $mode =~ /^flashaudio/ ) {
		# We could do id3 tagging here with ffmpeg but id3v2 does this later anyway
		# This fails
		# $cmd = "$bin->{ffmpeg} -i \"$file_tmp\" -vn -acodec copy -y \"$prog->{filepart}\" 1>&2";
		# This works but it's really bad bacause it re-transcodes mp3 and takes forever :-(
		# $cmd = "$bin->{ffmpeg} -i \"$file_tmp\" -acodec libmp3lame -ac 2 -ab 128k -vn -y \"$prog->{filepart}\" 1>&2";
		# At last this removes the flv container and dumps the mp3 stream! - mplayer dumps core but apparently succeeds
		@cmd = (
			$bin->{mplayer},
			@{ $binopts->{mplayer} },
			'-dumpaudio',
			$file_tmp,
			'-dumpfile', $prog->{filepart},
		);
	# Convert flv to aac/mp4a/mp3
	} elsif ( $mode =~ /flashaac/ ) {
		# transcode to MP3 if directed. If mp3vbr is not set then perform CBR.
		if ( $opt->{aactomp3} ) {
			my @br_opts = ('-ab', '128k');
			if ( $opt->{mp3vbr} =~ /^\d$/ ) {
				@br_opts = ('-aq', $opt->{mp3vbr});
			}
			@cmd = (
				$bin->{ffmpeg},
				@{ $binopts->{ffmpeg} },
				'-i', $file_tmp,
				'-vn',
				'-acodec', 'libmp3lame', '-ac', '2', @br_opts,
				@ffmpeg_opts,
				'-y', $prog->{filepart},
			);
		} else {
			@cmd = (
				$bin->{ffmpeg},
				@{ $binopts->{ffmpeg} },
				'-i', $file_tmp,
				'-vn',
				'-acodec', 'copy',
				@ffmpeg_opts,
				'-y', $prog->{filepart},
			);
		}
	# Convert video flv to mp4/mkv/avi if required
	} else {
		@cmd = (
			$bin->{ffmpeg},
			@{ $binopts->{ffmpeg} },
			'-i', $file_tmp,
			'-vcodec', 'copy',
			'-acodec', 'copy',
			@ffmpeg_opts,
			'-y', $prog->{filepart},
		);
	}

	# Run flv conversion and delete source file on success
	my $return = main::run_cmd( 'STDERR', @cmd );
	if ( (! $return) && -f $prog->{filepart} && stat($prog->{filepart})->size > $prog->min_download_size() ) {
			unlink( $file_tmp );
	# If the ffmpeg conversion failed, remove the failed-converted file attempt - move the file as done anyway
	} else {
		main::logger "WARNING: flv conversion failed - retaining flv file\n";
		unlink $prog->{filepart};
		$prog->{filepart} = $file_tmp;
		$prog->{filename} = $file_tmp;
	}
	# Moving file into place as complete (if not stdout)
	if ( $prog->{filepart} ne $prog->{filename} && ! $opt->{stdout} ) {
		move($prog->{filepart}, $prog->{filename}); 
		$prog->check_duration() if $opt->{checkduration} && !$streamdata{live};
	}
	
	# Re-symlink file
	$prog->create_symlink( $prog->{symlink}, $prog->{filename} ) if $opt->{symlink};

	main::logger "INFO: Recorded $prog->{filename}\n";
	return 0;
}


################### Streamer::hls class #################
package Streamer::hls;

# Inherit from Streamer class
use base 'Streamer';
use File::Copy;
use File::Path;
use File::stat;
use strict;

sub opt_format {
	return {
		ffmpeg		=> [ 0, "ffmpeg|avconv=s", 'External Program', '--ffmpeg <path>', "Location of ffmpeg or avconv binary. Synonyms: --avconv"],
		ffmpegobsolete		=> [ 1, "ffmpeg-obsolete|ffmpegobsolete|avconv-obsolete|avconvobsolete!", 'External Program', '--ffmpeg-obsolete', "Indicates you are using an obsolete version of ffmpeg (<0.7) that does not support the -loglevel option, so  --quiet, --verbose and --debug will not be applied to ffmpeg. Synonym: --avconv-obsolete"],
	};
}


# %prog (only for {ext} and {mode})
# Actually do the HLS streaming
sub get {
	my ( $stream, undef, undef, $prog, %streamdata ) = @_;
	my $file_tmp;
	my @cmd;
	my @cmdopts;
	my $return;
	my $url = $streamdata{streamurl};
	my $ab = $streamdata{audio_bitrate};
	my $vb = $streamdata{video_bitrate};
	my $kind = $streamdata{kind};
	my $live = $streamdata{live};
	my $mode = $prog->{mode};

	if ( $opt->{raw} ) {
		$file_tmp = $prog->{filepart};
	} else {
		$file_tmp = $prog->{filepart}.".ts"
	}

	# Remove failed file recording (below a certain size) - hack to get around rtmpdump not returning correct exit code
	if ( -f $file_tmp && stat($file_tmp)->size < $prog->min_download_size() ) {
		unlink( $file_tmp );
	}
	
	# Create symlink if required
	$prog->create_symlink( $prog->{symlink}, $file_tmp ) if $opt->{symlink};

	# Deal with stdout streaming
	#if ( $opt->{stdout} && not $opt->{nowrite} ) {
	#	main::logger "ERROR: Cannot stream HLS to STDOUT and file simultaneously\n";
	#	exit 4;
	#}
	
	# Add start stop options if defined
	push @cmdopts, ( '-ss', $opt->{start} ) if $opt->{start};
	push @cmdopts, ( '-t', $opt->{stop} - $opt->{start} ) if $opt->{stop};
	# requires ffmpeg 1.2
	# push @cmdopts, ( '-to', $opt->{stop} ) if $opt->{stop};
	if ( $live ) {
		if ( $kind eq 'video' ) {
			push @cmdopts, ( '-vb', "${vb}k" ) if $vb;
 			#push @cmdopts, ( '-vcodec', 'h264' );
			push @cmdopts, ( '-ab', "${ab}k" ) if $ab;
			push @cmdopts, ( '-acodec', 'aac', '-strict', 'experimental' );
		} else {
			push @cmdopts, ( '-vn' );
	 		push @cmdopts, ( '-acodec', 'copy' );
		}
	} else {
		if ( $kind eq 'video' ) {
			push @cmdopts, ( '-vcodec', 'copy' );
		} else {
			push @cmdopts, ( '-vn' );
		}
 		push @cmdopts, ( '-acodec', 'copy' );
 	}

	# Add custom options to ffmpeg for this type if specified with --hls-<type>-opts
	if ( defined $opt->{'hls'.$prog->{type}.'opts'} ) {
		push @cmdopts, ( split /\s+/, $opt->{'hls'.$prog->{type}.'opts'} );
	}

	my @globals = ( '-y' );
	if ( ! grep( /-loglevel/i, @{$binopts->{ffmpeg}} ) ) {
		if ( $live && $kind eq 'video') {
			push @globals, ( '-loglevel', 'error', '-stats' );
		} else {
			push @globals, ( '-loglevel', 'info', '-stats' );
		}
	}
	@cmd = (
		$bin->{ffmpeg},
		@{$binopts->{ffmpeg}},
		@globals,
		'-i', $url,
	);
	if ( ! $opt->{nowrite} ) {
		if ( $live ) {
 			push @cmd, ( '-vcodec', 'h264' ) if $kind eq 'video';
 		}
		push @cmd, @cmdopts;
		push @cmd, ( $file_tmp );
	}
	if ( $opt->{stdout} ) {
		push @cmd, @cmdopts;
		push @cmd, ( '-f', 'mpegts', 'pipe:1' );
	}
	
	$return = main::run_cmd( 'normal', @cmd );

	# exit behaviour when streaming
	if ( $opt->{nowrite} && $opt->{stdout} ) {
		if ( $return == 0 ) {
			main::logger "\nINFO: Streaming completed successfully\n";
			return 0;
		} else {
			main::logger "\nINFO: Streaming failed with exit code $return\n";
			return 'abort';
		}
	}

	# if we fail during the hls streaming, try to resume (this gets new streamdata again so that it isn't stale)
	return 'retry' if $return && -f $file_tmp && stat($file_tmp)->size > $prog->min_download_size();

	# If file is too small or non-existent then delete and try next mode
	if ( (! -f $file_tmp) || ( -f $file_tmp && stat($file_tmp)->size < $prog->min_download_size()) ) {
		main::logger "WARNING: Failed to stream file $file_tmp via HLS\n";
		unlink $file_tmp;
		return 'next';
	}

	# Add custom options to ffmpeg for this type if specified with --ffmpeg-<type>-opts
	my @ffmpeg_opts = ();
	if ( defined $opt->{'ffmpeg'.$prog->{type}.'opts'} ) {
		push @ffmpeg_opts, ( split /\s+/, $opt->{'ffmpeg'.$prog->{type}.'opts'} );
	}

	# use backwards-compatible option for ffmpeg
	my @filter_opts;
	if ( $bin->{ffmpeg} =~ /avconv/ ) {
		push @filter_opts, '-bsf:a';
	} else {
		push @filter_opts, '-absf';
	}
	push @filter_opts, 'aac_adtstoasc';

	# Retain raw ts format if required
	if ( $opt->{raw} ) {
		if ( $file_tmp ne $prog->{filename} && ! $opt->{stdout} ) {
			move($file_tmp, $prog->{filename});
			$prog->check_duration() if $opt->{checkduration} && ! $live;
		}
		return 0;

	# Convert ts to aac/mp4a/mp3
	} elsif ( $mode =~ /hlsaac/ ) {
		# transcode to MP3 if directed. If mp3vbr is not set then perform CBR.
		if ( $opt->{aactomp3} ) {
			my @br_opts = ('-ab', '128k');
			if ( $opt->{mp3vbr} =~ /^\d$/ ) {
				@br_opts = ('-aq', $opt->{mp3vbr});
			}
			@cmd = (
				$bin->{ffmpeg},
				@{ $binopts->{ffmpeg} },
				@globals,
				'-i', $file_tmp,
				'-vn',
				'-acodec', 'libmp3lame', '-ac', '2', @br_opts,
				@ffmpeg_opts,
				$prog->{filepart},
			);
		} else {
			@cmd = (
				$bin->{ffmpeg},
				@{ $binopts->{ffmpeg} },
				@globals,
				'-i', $file_tmp,
				'-vn',
				'-acodec', 'copy',
				@filter_opts,
				@ffmpeg_opts,
				$prog->{filepart},
			);
		}
	} else {
		@cmd = (
			$bin->{ffmpeg},
			@{ $binopts->{ffmpeg} },
			@globals,
			'-i', $file_tmp,
			'-vcodec', 'copy',
			'-acodec', 'copy',
			@filter_opts,
			@ffmpeg_opts,
			$prog->{filepart},
		);
	}

	# Run ts conversion and delete source file on success
	$return = main::run_cmd( 'STDERR', @cmd );
	
	if ( (! $return) && -f $prog->{filepart} && stat($prog->{filepart})->size > $prog->min_download_size() ) {
			unlink( $file_tmp );
	# If the ffmpeg conversion failed, remove the failed-converted file attempt - move the file as done anyway
	} else {
		main::logger "WARNING: ts conversion failed - retaining ts file\n";
		unlink $prog->{filepart};
		$prog->{filepart} = $file_tmp;
		$prog->{filename} = $file_tmp;
	}
	# Moving file into place as complete
	if ( $prog->{filepart} ne $prog->{filename} ) {
		move($prog->{filepart}, $prog->{filename}); 
		$prog->check_duration() if $opt->{checkduration} && ! $live;
	}
	
	# Re-symlink file
	$prog->create_symlink( $prog->{symlink}, $prog->{filename} ) if $opt->{symlink};

	main::logger "INFO: Recorded $prog->{filename}\n";
	return 0;
}


################### Streamer::ddl class #################
package Streamer::ddl;

# Inherit from Streamer class
use base 'Streamer';
use File::Copy;
use File::Path;
use File::stat;
use strict;

sub opt_format {
	return {
		ffmpeg		=> [ 0, "ffmpeg|avconv=s", 'External Program', '--ffmpeg <path>', "Location of ffmpeg or avconv binary. Synonyms: --avconv"],
		ffmpegobsolete		=> [ 1, "ffmpeg-obsolete|ffmpegobsolete|avconv-obsolete|avconvobsolete!", 'External Program', '--ffmpeg-obsolete', "Indicates you are using an obsolete version of ffmpeg (<0.7) that does not support the -loglevel option, so  --quiet, --verbose and --debug will not be applied to ffmpeg. Synonym: --avconv-obsolete"],
	};
}


# %prog (only for {ext} and {mode})
# Actually do the DDL streaming
sub get {
	my ( $stream, undef, undef, $prog, %streamdata ) = @_;
	my $file_tmp;
	my @cmd;
	my @cmdopts;
	my $return;
	my $url = $streamdata{streamurl};
	my $kind = $streamdata{kind};
	my $mode = $prog->{mode};

	$file_tmp = $prog->{filepart};

	# Remove failed file recording (below a certain size) - hack to get around rtmpdump not returning correct exit code
	if ( -f $file_tmp && stat($file_tmp)->size < $prog->min_download_size() ) {
		unlink( $file_tmp );
	}
	
	# Create symlink if required
	$prog->create_symlink( $prog->{symlink}, $file_tmp ) if $opt->{symlink};

	# Deal with stdout streaming
	#if ( $opt->{stdout} && not $opt->{nowrite} ) {
	#	main::logger "ERROR: Cannot stream DDL to STDOUT and file simultaneously\n";
	#	exit 4;
	#}
	
	push @cmdopts, ( '-vn' );
	push @cmdopts, ( '-acodec', 'copy' );

	# Add custom options to ffmpeg for this type if specified with --ddl-<type>-opts
	if ( defined $opt->{'ddl'.$prog->{type}.'opts'} ) {
		push @cmdopts, ( split /\s+/, $opt->{'ddl'.$prog->{type}.'opts'} );
	}

	my @globals = ( '-y' );
	if ( ! grep( /-loglevel/i, @{$binopts->{ffmpeg}} ) ) {
		push @globals, ( '-loglevel', 'error', '-stats' );
	}
	@cmd = (
		$bin->{ffmpeg},
		@{$binopts->{ffmpeg}},
		@globals,
		'-i', $url,
	);
	if ( ! $opt->{nowrite} ) {
		push @cmd, @cmdopts;
		push @cmd, ( $file_tmp );
	}
	if ( $opt->{stdout} ) {
		push @cmd, @cmdopts;
		push @cmd, ( '-f', 'adts', 'pipe:1' );
	}
	
	$return = main::run_cmd( 'normal', @cmd );

	# exit behaviour when streaming
	if ( $opt->{nowrite} && $opt->{stdout} ) {
		if ( $return == 0 ) {
			main::logger "\nINFO: Streaming completed successfully\n";
			return 0;
		} else {
			main::logger "\nINFO: Streaming failed with exit code $return\n";
			return 'abort';
		}
	}

	# if we fail during the hls streaming, try to resume (this gets new streamdata again so that it isn't stale)
	return 'retry' if $return && -f $file_tmp && stat($file_tmp)->size > $prog->min_download_size();

	# If file is too small or non-existent then delete and try next mode
	if ( (! -f $file_tmp) || ( -f $file_tmp && stat($file_tmp)->size < $prog->min_download_size()) ) {
		main::logger "WARNING: Failed to stream file $file_tmp via 3gpaac\n";
		unlink $file_tmp;
		return 'next';
	}

	# Add custom options to ffmpeg for this type if specified with --ffmpeg-<type>-opts
	my @ffmpeg_opts = ();
	if ( defined $opt->{'ffmpeg'.$prog->{type}.'opts'} ) {
		push @ffmpeg_opts, ( split /\s+/, $opt->{'ffmpeg'.$prog->{type}.'opts'} );
	}

	if ( $opt->{raw} ) {
		if ( $file_tmp ne $prog->{filename} && ! $opt->{stdout} ) {
			move($file_tmp, $prog->{filename});
			$prog->check_duration() if $opt->{checkduration};
		}
		return 0;

	} elsif ( $mode =~ /ddlaac/ ) {
		# transcode to MP3 if directed. If mp3vbr is not set then perform CBR.
		if ( $opt->{aactomp3} ) {
			my @br_opts = ('-ab', '128k');
			if ( $opt->{mp3vbr} =~ /^\d$/ ) {
				@br_opts = ('-aq', $opt->{mp3vbr});
			}
			@cmd = (
				$bin->{ffmpeg},
				@{ $binopts->{ffmpeg} },
				@globals,
				'-i', $file_tmp,
				'-vn',
				'-acodec', 'libmp3lame', '-ac', '2', @br_opts,
				@ffmpeg_opts,
				$prog->{filepart},
			);
			# Run conversion and delete source file on success
			$return = main::run_cmd( 'STDERR', @cmd );
			if ( (! $return) && -f $prog->{filepart} && stat($prog->{filepart})->size > $prog->min_download_size() ) {
					unlink( $file_tmp );
			# If the ffmpeg conversion failed, remove the failed-converted file attempt - move the file as done anyway
			} else {
				main::logger "WARNING: m4a conversion failed - retaining m4a file\n";
				unlink $prog->{filepart};
				$prog->{filepart} = $file_tmp;
				$prog->{filename} = $file_tmp;
			}
		}
	}

	# Moving file into place as complete
	if ( $prog->{filepart} ne $prog->{filename} ) {
		move($prog->{filepart}, $prog->{filename}); 
		$prog->check_duration() if $opt->{checkduration};
	}
	
	# Re-symlink file
	$prog->create_symlink( $prog->{symlink}, $prog->{filename} ) if $opt->{symlink};

	main::logger "INFO: Recorded $prog->{filename}  $prog->{filepart}\n";
	return 0;
}


package Streamer::rtsp;

# Inherit from Streamer class
use base 'Streamer';

use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::stat;
use HTML::Entities;
use HTTP::Cookies;
use HTTP::Headers;
use IO::Seekable;
use IO::Socket;
use LWP::ConnCache;
use LWP::UserAgent;
use POSIX qw(mkfifo);
use strict;
use Time::Local;
use URI;


# %prog (only for lame id3 tagging and {mode})
# Actually do the rtsp streaming
sub get {
	my ( $stream, $ua, $url, $prog ) = @_;
	my $childpid;

	# get bandwidth options value
	# Download bandwidth bps used for rtsp streams
	my $bandwidth = $opt->{bandwidth} || 512000;

	# Parse/recurse playlist if required to get mms url
	$url = main::get_playlist_url( $ua, $url, 'rtsp' );

	# Add stop and start if defined
	# append: ?start=5400&end=7400 or &start=5400&end=7400
	if ( $opt->{start} || $opt->{stop} ) {
		# Make sure we add the correct separator for adding to the rtsp url
		my $prefix_char = '?';
		$prefix_char = '&' if $url =~ m/\?.+/;
		if ( $opt->{start} && $opt->{stop} ) {
			$url .= "${prefix_char}start=$opt->{start}&end=$opt->{stop}";
		} elsif ( $opt->{start} && not $opt->{stop} ) {
			$url .= "${prefix_char}start=$opt->{start}";
		} elsif ( $opt->{stop} && not $opt->{start} ) {
			$url .= "${prefix_char}end=$opt->{stop}";
		}
	}
	
	# Create named pipe
	if ( $^O !~ /^MSWin32$/ ) {
		mkfifo($namedpipe, 0700);
	} else {
		main::logger "WARNING: fifos/named pipes are not supported - only limited output modes will be supported\n";
	}
	
	main::logger "INFO: RTSP URL = $url\n" if $opt->{verbose};

	# Create ID3 tagging options for lame (escape " for shell)
	my ( $id3_name, $id3_episode, $id3_desc, $id3_channel ) = ( $prog->{name}, $prog->{episode}, $prog->{desc}, $prog->{channel} );
	s|"|\\"|g for ($id3_name, $id3_episode, $id3_desc, $id3_channel);
	$binopts->{lame} .= " --ignore-tag-errors --ty ".( (localtime())[5] + 1900 )." --tl \"$id3_name\" --tt \"$id3_episode\" --ta \"$id3_channel\" --tc \"$id3_desc\" ";

	# Use post-streaming transcoding using lame if namedpipes are not supported (i.e. ActivePerl/Windows)
	# (Fallback if no namedpipe support and raw/wav not specified)
	if ( ( ! -p $namedpipe ) && ! ( $opt->{raw} || $opt->{wav} ) ) {
			my @cmd;
			# Remove filename extension
			$prog->{filepart} =~ s/\.mp3$//gi;
			# Remove named pipe
			unlink $namedpipe;
			main::logger "INFO: Recording wav format (followed by transcoding)\n";
			my $wavfile = "$prog->{filepart}.wav";
			# Strip off any leading drivename in win32 - mplayer doesn't like this for pcm output files
			$wavfile =~ s|^[a-zA-Z]:||g;
			@cmd = (
				$bin->{mplayer},
				@{ $binopts->{mplayer} },
				'-cache', 128,
				'-bandwidth', $bandwidth,
				'-vc', 'null',
				'-vo', 'null',
				'-ao', "pcm:waveheader:fast:file=\"$wavfile\"",
				$url,
			);
			# Create symlink if required
			$prog->create_symlink( $prog->{symlink}, "$prog->{filepart}.wav" ) if $opt->{symlink};
			if ( main::run_cmd( 'STDERR', @cmd ) ) {
				unlink $prog->{symlink};
				return 'next';
			}
			# Transcode
			main::logger "INFO: Transcoding $prog->{filepart}.wav\n";
			my $cmd = "$bin->{lame} $binopts->{lame} \"$prog->{filepart}.wav\" \"$prog->{filepart}.mp3\" 1>&2";
			main::logger "DEGUG: Running $cmd\n" if $opt->{debug};
			# Create symlink if required
			$prog->create_symlink( $prog->{symlink}, "$prog->{filepart}.mp3" ) if $opt->{symlink};		
			if ( system($cmd) || (-f "$prog->{filepart}.wav" && stat("$prog->{filepart}.wav")->size < $prog->min_download_size()) ) {
				unlink $prog->{symlink};
				return 'next';
			}
			unlink "$prog->{filepart}.wav";
			move "$prog->{filepart}.mp3", $prog->{filename};
			$prog->{ext} = 'mp3';
		
	} elsif ( $opt->{wav} && ! $opt->{stdout} ) {
		main::logger "INFO: Writing wav format\n";
		my $wavfile = $prog->{filepart};
		# Strip off any leading drivename in win32 - mplayer doesn't like this for pcm output files
		$wavfile =~ s|^[a-zA-Z]:||g;
		# Start the mplayer process and write to wav file
		my @cmd = (
			$bin->{mplayer},
			@{ $binopts->{mplayer} },
			'-cache', 128,
			'-bandwidth', $bandwidth,
			'-vc', 'null',
			'-vo', 'null',
			'-ao', "pcm:waveheader:fast:file=\"$wavfile\"",
			$url,
		);
		# Create symlink if required
		$prog->create_symlink( $prog->{symlink}, $prog->{filepart} ) if $opt->{symlink};		
		if ( main::run_cmd( 'STDERR', @cmd ) ) {
			unlink $prog->{symlink};
			return 'next';
		}
		# Move file to done state
		move $prog->{filepart}, $prog->{filename} if $prog->{filepart} ne $prog->{filename} && ! $opt->{nowrite};

	# No transcoding if --raw was specified
	} elsif ( $opt->{raw} && ! $opt->{stdout} ) {
		# Write out to .ra ext instead (used on fallback if no fifo support)
		main::logger "INFO: Writing raw realaudio stream\n";
		# Start the mplayer process and write to raw file
		my @cmd = (
			$bin->{mplayer},
			@{ $binopts->{mplayer} },
			'-cache', 128,
			'-bandwidth', $bandwidth,
			'-dumpstream',
			'-dumpfile', $prog->{filepart},
			$url,
		);
		# Create symlink if required
		$prog->create_symlink( $prog->{symlink}, $prog->{filepart} ) if $opt->{symlink};		
		if ( main::run_cmd( 'STDERR', @cmd ) ) {
			unlink $prog->{symlink};
			return 'next';
		}
		# Move file to done state
		move $prog->{filepart}, $prog->{filename} if $prog->{filepart} ne $prog->{filename} && ! $opt->{nowrite};

	# Fork a child to do transcoding on the fly using a named pipe written to by mplayer
	# Use transcoding via named pipes
	} elsif ( -p $namedpipe )  {
		$childpid = fork();
		if (! $childpid) {
			# Child starts here
			$| = 1;
			main::logger "INFO: Transcoding $prog->{filepart}\n";

			# Stream mp3 to file and stdout simultaneously
			if ( $opt->{stdout} && ! $opt->{nowrite} ) {
				# Create symlink if required
				$prog->create_symlink( $prog->{symlink}, $prog->{filepart} ) if $opt->{symlink};
				if ( $opt->{wav} || $opt->{raw} ) {
					# Race condition - closes named pipe immediately unless we wait
					sleep 5;
					# Create symlink if required
					$prog->create_symlink( $prog->{symlink}, $prog->{filepart} ) if $opt->{symlink};
					main::tee($namedpipe, $prog->{filepart});
					#system( "cat $namedpipe 2>/dev/null| $bin->{tee} $prog->{filepart}");
				} else {
					my $cmd = "$bin->{lame} $binopts->{lame} \"$namedpipe\" - 2>/dev/null| $bin->{tee} \"$prog->{filepart}\"";
					main::logger "DEGUG: Running $cmd\n" if $opt->{debug};
					# Create symlink if required
					$prog->create_symlink( $prog->{symlink}, $prog->{filepart} ) if $opt->{symlink};
					system($cmd);
				}

			# Stream mp3 stdout only
			} elsif ( $opt->{stdout} && $opt->{nowrite} ) {
				if ( $opt->{wav} || $opt->{raw} ) {
					sleep 5;
					main::tee($namedpipe);
					#system( "cat $namedpipe 2>/dev/null");
				} else {
					my $cmd = "$bin->{lame} $binopts->{lame} \"$namedpipe\" - 2>/dev/null";
					main::logger "DEGUG: Running $cmd\n" if $opt->{debug};
					system( "$bin->{lame} $binopts->{lame} \"$namedpipe\" - 2>/dev/null");
				}

			# Stream mp3 to file directly
			} elsif ( ! $opt->{stdout} ) {
				my $cmd = "$bin->{lame} $binopts->{lame} \"$namedpipe\" \"$prog->{filepart}\" >/dev/null 2>/dev/null";
				main::logger "DEGUG: Running $cmd\n" if $opt->{debug};
				# Create symlink if required
				$prog->create_symlink( $prog->{symlink}, $prog->{filepart} ) if $opt->{symlink};
				system($cmd);
			}
			# Remove named pipe
			unlink $namedpipe;

			# Move file to done state
			move $prog->{filepart}, $prog->{filename} if $prog->{filepart} ne $prog->{filename} && ! $opt->{nowrite};
			main::logger "INFO: Transcoding thread has completed\n";
			# Re-symlink if required
			$prog->create_symlink( $prog->{symlink}, $prog->{filename} ) if $opt->{symlink};
			exit 0;
		}
		# Start the mplayer process and write to named pipe
		# Raw mode
		if ( $opt->{raw} ) {
			my @cmd = (
				$bin->{mplayer},
				@{ $binopts->{mplayer} },
				'-cache', 32,
				'-bandwidth', $bandwidth,
				'-dumpstream',
				'-dumpfile', $namedpipe,
				$url,
			);
			if ( main::run_cmd( 'STDERR', @cmd ) ) {
				# If we fail then kill off child processes
				kill 9, $childpid;
				unlink $prog->{symlink};
				return 'next';
			}
		# WAV / mp3 mode - seems to fail....
		} else {
			my @cmd = (
				$bin->{mplayer},
				@{ $binopts->{mplayer} },
				'-cache', 128,
				'-bandwidth', $bandwidth,
				'-vc', 'null',
				'-vo', 'null',
				'-ao', "pcm:waveheader:fast:file=$namedpipe",
				$url,
			);
			if ( main::run_cmd( 'STDERR', @cmd ) ) {
				# If we fail then kill off child processes
				kill 9, $childpid;
				unlink $prog->{symlink};
				return 'next';
			}
		}
		# Wait for child processes to prevent zombies
		wait;

		unlink $namedpipe;
	} else {
		main::logger "ERROR: Unsupported method of download on this platform\n";
		return 'next';
	}

	main::logger "INFO: Recorded $prog->{filename}\n";
	# Re-symlink if required
	$prog->create_symlink( $prog->{symlink}, $prog->{filename} ) if $opt->{symlink};

	return 0;
}




package Streamer::mms;

# Inherit from Streamer class
use base 'Streamer';

use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::stat;
use HTML::Entities;
use HTTP::Cookies;
use HTTP::Headers;
use IO::Seekable;
use IO::Socket;
use LWP::ConnCache;
use LWP::UserAgent;
use POSIX qw(mkfifo);
use strict;
use Time::Local;
use URI;



# %prog (only used for {mode} and generating multi-part file prefixes)
# Actually do the MMS video streaming
sub get {
	my ( $stream, $ua, $urls, $prog ) = @_;
	my $file_tmp;
	my $cmd;
	my @url_list = split /\|/, $urls;
	my @file_tmp_list;
	my %threadpid;
	my $retries = $opt->{attempts} || 3;

	main::logger "INFO: MMS_URLs: ".(join ', ', @url_list).", file: $prog->{filepart}, file_done: $prog->{filename}\n" if $opt->{verbose};

	if ( $opt->{stdout} ) {
		main::logger "ERROR: stdout streaming isn't supported for mms streams\n";
		return 'next';
	}

	# Start marker
	my $start_time = time();
	# Download each mms url (multi-threaded to stream in parallel)
	my $file_part_prefix = "$prog->{dir}/$prog->{fileprefix}_part";
	for ( my $count = 0; $count <= $#url_list; $count++ ) {
		
		# Parse/recurse playlist if required to get mms url
		$url_list[$count] = main::get_playlist_url( $ua, $url_list[$count], 'mms' );

		# Create temp recording filename
		$file_tmp = sprintf( "%s%02d.".$prog->{ext}, $file_part_prefix, $count+1);
		$file_tmp_list[$count] = $file_tmp;
		#my $null;
		#$null = '-really-quiet' if ! $opt->{quiet};
		# Can also use 'mencoder mms://url/ -oac copy -ovc copy -o out.asf' - still gives zero exit code on failed stream...
		# Can also use $bin->{vlc} --sout file/asf:\"$file_tmp\" \"$url_list[$count]\" vlc://quit
		# The vlc cmd does not quit of there is an error - it just hangs
		# $cmd = "$bin->{mplayer} $binopts->{mplayer} -dumpstream \"$url_list[$count]\" -dumpfile \"$file_tmp\" $null 1>&2";
		# Use backticks to invoke mplayer and grab all output then grep for 'read error'
		# problem is that the following output is given by mplayer at the end of liong streams:
		#read error:: Operation now in progress
		#pre-header read failed
		#Core dumped ;)
		#vo: x11 uninit called but X11 not initialized..
		#
		#Exiting... (End of file)
		$cmd = "\"$bin->{mplayer}\" ".(join ' ', @{ $binopts->{mplayer} } )." -dumpstream \"$url_list[$count]\" -dumpfile \"$file_tmp\" 2>&1";
		$cmd = main::encode_fs($cmd);
		main::logger "INFO: Command: $cmd\n" if $opt->{verbose};

		# fork streaming threads
		if ( not $opt->{mmsnothread} ) {
			my $childpid = fork();
			if (! $childpid) {
				# Child starts here
				main::logger "INFO: Streaming to file $file_tmp\n";
				# Remove old file
				unlink $file_tmp;
				# Retry loop
				my $retry = $retries;
				while ($retry) {
					my $cmdoutput = `$cmd`;
					my $exitcode = $?;
					main::logger "DEBUG: Command '$cmd', Output:\n$cmdoutput\n\n" if $opt->{debug};
					# Assume file is fully downloaded if > 10MB and we get an error reported !!!
					if ( ( -f $prog->{filename} && stat($prog->{filename})->size < $prog->min_download_size()*10.0 && grep /(read error|connect error|Failed, exiting)/i, $cmdoutput ) || $exitcode ) {
						# Failed, retry
						main::logger "WARNING: Failed, retrying to stream $file_tmp, exit code: $exitcode\n";
						$retry--;
					} else {
						# Successfully streamed
						main::logger "INFO: Streaming thread has completed for file $file_tmp\n";
						exit 0;
					}
				}
				main::logger "ERROR: Record thread failed after $retries retries for $file_tmp (renamed to ${file_tmp}.failed)\n";
				move $file_tmp, "${file_tmp}.failed";
				exit 1;
			}
			# Create a hash of process_id => 'count'
			$threadpid{$childpid} = $count;

		# else stream each part in turn
		} else {
			# Child starts here
			main::logger "INFO: Recording file $file_tmp\n";
			# Remove old file
			unlink $file_tmp;
			# Retry loop
			my $retry = $retries;
			my $done = 0;
			while ( $retry && not $done ) {
				my $cmdoutput = `$cmd`;
				my $exitcode = $?;
				main::logger "DEBUG: Command '$cmd', Output:\n$cmdoutput\n\n" if $opt->{debug};
				# Assume file is fully downloaded if > 10MB and we get an error reported !!!
				if ( ( -f $prog->{filename} && stat($prog->{filename})->size < $prog->min_download_size()*10.0 && grep /(read error|connect error|Failed, exiting)/i, $cmdoutput ) || $exitcode ) {
				#if ( grep /(read error|connect error|Failed, exiting)/i, $cmdoutput || $exitcode ) {
					# Failed, retry
					main::logger "DEBUG: Trace of failed command:\n####################\n${cmdoutput}\n####################\n" if $opt->{debug};
					main::logger "WARNING: Failed, retrying to stream $file_tmp, exit code: $exitcode\n";
					$retry--;
				} else {
					# Successfully downloaded
					main::logger "INFO: Streaming has completed to file $file_tmp\n";
					$done = 1;
				}
			} 
			# if the programme part failed after a few retries...
			if (not $done) {
				main::logger "ERROR: Recording failed after $retries retries for $file_tmp (renamed to ${file_tmp}.failed)\n";
				move $file_tmp, "${file_tmp}.failed";
				return 'next';
			}
		} 
	}

	# If doing a threaded streaming, monitor the progress and thread completion
	if ( not $opt->{mmsnothread} ) {
		# Wait for all threads to complete
		$| = 1;
		# Autoreap zombies
		$SIG{CHLD}='IGNORE';
		my $done = 0;
		my $done_symlink;
		while (keys %threadpid) {
			my @sizes;
			my $total_size = 0;
			my $total_size_new = 0;
			my $format = "Threads: ";
			sleep 1;
			#main::logger "DEBUG: ProcessIDs: ".(join ',', keys %threadpid)."\n";
			for my $procid (sort keys %threadpid) {
				my $size = 0;
				# Is this child still alive?
				if ( kill 0 => $procid ) {
					main::logger "DEBUG Thread $threadpid{$procid} still alive ($file_tmp_list[$threadpid{$procid}])\n" if $opt->{debug};
					# Build the status string
					$format .= "%d) %.3fMB   ";
					$size = stat($file_tmp_list[$threadpid{$procid}])->size if -f $file_tmp_list[$threadpid{$procid}];
					push @sizes, $threadpid{$procid}+1, $size/(1024.0*1024.0);
					$total_size_new += $size;
					# Now create a symlink if this is the first part and size > $prog->min_download_size()
					if ( $threadpid{$procid} == 0 && $done_symlink != 1 && $opt->{symlink} && $size > $prog->min_download_size() ) {
						# Symlink to file if only one part or to dir if multi-part
						if ( $#url_list ) {
							$prog->create_symlink( $prog->{symlink}, $prog->{dir} );
						} else {
							$prog->create_symlink( $prog->{symlink}, $file_tmp_list[$threadpid{$procid}] );
						}
						$done_symlink = 1;
					}
				# Thread has completed/failed
				} else {
					$size = stat($file_tmp_list[$threadpid{$procid}])->size if -f $file_tmp_list[$threadpid{$procid}];
					# end marker
					my $end_time = time() + 0.0001;
					# Calculate average speed, duration and total bytes downloaded
					main::logger sprintf("INFO: Thread #%d Recorded %.2fMB in %s at %5.0fkbps to %s\n", 
						($threadpid{$procid}+1),
						$size / (1024.0 * 1024.0),
						sprintf("%02d:%02d:%02d", ( gmtime($end_time - $start_time))[2,1,0] ), 
						$size / ($end_time - $start_time) / 1024.0 * 8.0,
						$file_tmp_list[$threadpid{$procid}] );
					# Remove from thread test list
					delete $threadpid{$procid};
				}
			}
			$format .= " recorded (%.0fkbps)        \r";
			main::logger sprintf $format, @sizes, ($total_size_new - $total_size) / (time() - $start_time) / 1024.0 * 8.0 unless $opt->{quiet};
		}
		main::logger "INFO: All streaming threads completed\n";	
		# Unset autoreap
		delete $SIG{CHLD};
	}
	# If not all files > min_size then assume streaming failed
	for (@file_tmp_list) {
		# If file doesnt exist or too small then skip
		if ( (! -f $_) || ( -f $_ && stat($_)->size < $prog->min_download_size() ) ) {
			main::logger "ERROR: Recording of programme failed, skipping\n" if $opt->{verbose};
			return 'next';
		}
	}
	if ( $#file_tmp_list == 0 ) {
		$prog->check_duration($file_tmp_list[0]) if $opt->{checkduration} && $prog->{type} !~ /live/;
	}

#	# Retain raw format if required
#	if ( $opt->{raw} ) {
#		# Create symlink to first part file
#		$prog->create_symlink( $prog->{symlink}, $file_tmp_list[0] ) if $opt->{symlink};
#		return 0;
#	}
#
#	# Convert video asf to mp4 if required - need to find a suitable converter...
#	} else {
#		# Create part of cmd that specifies each partial file
#		my $filestring;
#		$filestring .= " -i \"$_\" " for (@file_tmp_list);
#		$cmd = "$bin->{ffmpeg} $binopts->{ffmpeg} $filestring -vcodec copy -acodec copy -f $prog->{ext} -y \"$prog->{filepart}\" 1>&2";
#	}
#
#	main::logger "INFO: Command: $cmd\n\n" if $opt->{verbose};
#	# Run asf conversion and delete source file on success
#	if ( ! system($cmd) ) {
#		unlink( @file_tmp_list );
#	} else {
#		main::logger "ERROR: asf conversion failed - retaining files ".(join ', ', @file_tmp_list)."\n";
#		return 2;
#	}
#	# Moving file into place as complete (if not stdout)
#	move($prog->{filepart}, $prog->{filename}) if ! $opt->{stdout};
#	# Create symlink if required
#	$prog->create_symlink( $prog->{symlink}, $prog->{filename} ) if $opt->{symlink};
	return 0;
}



package Streamer::3gp;

# Inherit from Streamer class
use base 'Streamer';

use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::stat;
use HTML::Entities;
use HTTP::Cookies;
use HTTP::Headers;
use IO::Seekable;
use IO::Socket;
use LWP::ConnCache;
use LWP::UserAgent;
use POSIX qw(mkfifo);
use strict;
use Time::Local;
use URI;


# Generic
# Actually do the 3gp / N95 h.264 streaming
sub get {
	my ( $stream, $ua, $url, $prog ) = @_;

	# Resolve URL if required
	if ( $url =~ /^http/ ) {
		my $url1 = main::request_url_retry($ua, $url, 2, '', '');
		chomp($url1);
		$url = $url1;
	}

	my @opts;
	@opts = @{ $binopts->{vlc} } if $binopts->{vlc};

	main::logger "INFO: URL = $url\n" if $opt->{verbose};
	if ( ! $opt->{stdout} ) {
		main::logger "INFO: Recording Low Quality H.264 stream\n";
		my @cmd = (
			$bin->{vlc},
			@opts,
			'--sout', 'file/ts:'.$prog->{filepart},
			$url,
			'vlc://quit',
		);
		if ( main::run_cmd( 'STDERR', @cmd ) ) {
			return 'next';
		}

	# to STDOUT
	} else {
		main::logger "INFO: Streaming Low Quality H.264 stream to stdout\n";
		my @cmd = (
			$bin->{vlc},
			@opts,
			'--sout', 'file/ts:-',
			$url,
			'vlc://quit',
		);
		if ( main::run_cmd( 'STDERR', @cmd ) ) {
			return 'next';
		}
	}
	main::logger "INFO: Recorded $prog->{filename}\n";
	# Moving file into place as complete (if not stdout)
	move($prog->{filepart}, $prog->{filename}) if $prog->{filepart} ne $prog->{filename} && ! $opt->{stdout};

	$prog->create_symlink( $prog->{symlink}, $prog->{filename} ) if $opt->{symlink};

	return 0;
}


package Streamer::http;

# Inherit from Streamer class
use base 'Streamer';

use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::stat;
use HTML::Entities;
use HTTP::Cookies;
use HTTP::Headers;
use IO::Seekable;
use IO::Socket;
use LWP::ConnCache;
use LWP::UserAgent;
use POSIX qw(mkfifo);
use strict;
use Time::Local;
use URI;

# Generic
# Actually do the http streaming
sub get {
	my ( $stream, $ua, $url, $prog ) = @_;
	my $start_time = time();

	# Set user agent
	$ua->agent('get_iplayer');

	main::logger "INFO: URL = $url\n" if $opt->{verbose};

	# Resume partial recording?
	my $start = 0;
	if ( -f $prog->{filepart} ) {
		$start = stat($prog->{filepart})->size;
		main::logger "INFO: Resuming recording from $start\n";
	}

	my $fh = main::open_file_append($prog->{filepart});

	if ( main::download_block($prog->{filepart}, $url, $ua, $start, undef, undef, $fh) != 0 ) {
		main::logger "\rERROR: Recording failed\n";
		close $fh;
		return 'next';
	} else {
		close $fh;
		# end marker
		my $end_time = time() + 0.0001;
		# Final file size
		my $size = stat($prog->{filepart})->size;
		# Calculate average speed, duration and total bytes downloaded
		main::logger sprintf("\rINFO: Recorded %.2fMB in %s at %5.0fkbps to %s\n", 
			($size - $start) / (1024.0 * 1024.0),
			sprintf("%02d:%02d:%02d", ( gmtime($end_time - $start_time))[2,1,0] ), 
			( $size - $start ) / ($end_time - $start_time) / 1024.0 * 8.0, 
			$prog->{filename} );
		move $prog->{filepart}, $prog->{filename} if $prog->{filepart} ne $prog->{filename};
		# re-symlink file
		$prog->create_symlink( $prog->{symlink}, $prog->{filename} ) if $opt->{symlink};
	}

	return 0;
}


################### Streamer::shoutcast class #################
package Streamer::shoutcast;

# Inherit from Streamer class
use base 'Streamer';
use File::Copy;
use File::Path;
use File::stat;
use strict;

sub opt_format {
	return {
		ffmpeg		=> [ 0, "ffmpeg|avconv=s", 'External Program', '--ffmpeg <path>', "Location of ffmpeg or avconv binary. Synonyms: --avconv"],
		ffmpegobsolete		=> [ 1, "ffmpeg-obsolete|ffmpegobsolete|avconv-obsolete|avconvobsolete!", 'External Program', '--ffmpeg-obsolete', "Indicates you are using an obsolete version of ffmpeg (<0.7) that does not support the -loglevel option, so  --quiet, --verbose and --debug will not be applied to ffmpeg. Synonym: --avconv-obsolete"],
	};
}


# %prog (only for {ext} and {mode})
# Actually do the shoutcast streaming
sub get {
	my ( $stream, undef, undef, $prog, %streamdata ) = @_;
	my $file_tmp;
	my @cmd;
	my @cmdopts;
	my $return;
	my $url = $streamdata{streamurl};
	my $kind = $streamdata{kind};
	my $live = $streamdata{live};
	my $mode = $prog->{mode};
	my $mode_mp3 = $mode =~ /shoutcastmp3/;
	my $mode_aac = $mode =~ /shoutcastaac/;
	
	if ( $opt->{raw} ) {
		$file_tmp = $prog->{filepart};
	} else {
		if ( $mode_mp3 ) {
			$file_tmp = $prog->{filepart}.".mp3";
		} elsif ( $mode_aac ) {
			$file_tmp = $prog->{filepart}.".aac";
		}
	}

	# Remove failed file recording (below a certain size)
	if ( -f $file_tmp && stat($file_tmp)->size < $prog->min_download_size() ) {
		unlink( $file_tmp );
	}
	
	# Create symlink if required
	$prog->create_symlink( $prog->{symlink}, $file_tmp ) if $opt->{symlink};

	# Deal with stdout streaming
	#if ( $opt->{stdout} && not $opt->{nowrite} ) {
	#	main::logger "ERROR: Cannot stream Shoutcast to STDOUT and file simultaneously\n";
	#	exit 4;
	#}
	
	# Add start stop options if defined
	if ( $opt->{start} || $opt->{stop} ) {
		push @cmdopts, ( '-ss', $opt->{start} ) if $opt->{start};
		push @cmdopts, ( '-t', $opt->{stop} ) if $opt->{stop};
	}
	push @cmdopts, ( '-acodec', 'copy', '-vn' );

	# Add custom options to ffmpeg for this type if specified with --shoutcast-<type>-opts
	if ( defined $opt->{'shoutcast'.$prog->{type}.'opts'} ) {
		push @cmdopts, ( split /\s+/, $opt->{'shoutcast'.$prog->{type}.'opts'} );
	}

	my @globals = ( '-y' );
	if ( ! grep( /-loglevel/i, @{$binopts->{ffmpeg}} ) ) {
		push @globals, ( '-loglevel', 'error', '-stats' );
	}
	@cmd = (
		$bin->{ffmpeg},
		@{$binopts->{ffmpeg}},
		@globals,
		'-i', $url,
	);
	if ( ! $opt->{nowrite} ) {
		push @cmd, @cmdopts;
		push @cmd, ( $file_tmp );
	}
	if ( $opt->{stdout} ) {
		push @cmd, @cmdopts;
		if ( $mode_mp3 ) {
			push @cmd, ( '-f', 'mp3', 'pipe:1' );
		} elsif ( $mode_aac ) {
			push @cmd, ( '-f', 'adts', 'pipe:1' );
		}
	}

	$return = main::run_cmd( 'normal', @cmd );

	# exit behaviour when streaming
	if ( $opt->{nowrite} && $opt->{stdout} ) {
		if ( $return == 0 ) {
			main::logger "\nINFO: Streaming completed successfully\n";
			return 0;
		} else {
			main::logger "\nINFO: Streaming failed with exit code $return\n";
			return 'abort';
		}
	}

	# if we fail during the hls streaming, try to resume (this gets new streamdata again so that it isn't stale)
	return 'retry' if $return && -f $file_tmp && stat($file_tmp)->size > $prog->min_download_size();

	# If file is too small or non-existent then delete and try next mode
	if ( (! -f $file_tmp) || ( -f $file_tmp && stat($file_tmp)->size < $prog->min_download_size()) ) {
		main::logger "WARNING: Failed to stream file $file_tmp via Shoutcast\n";
		unlink $file_tmp;
		return 'next';
	}
	
	# Add custom options to ffmpeg for this type if specified with --ffmpeg-<type>-opts
	my @ffmpeg_opts = ();
	if ( defined $opt->{'ffmpeg'.$prog->{type}.'opts'} ) {
		push @ffmpeg_opts, ( split /\s+/, $opt->{'ffmpeg'.$prog->{type}.'opts'} );
	}

	# Retain raw aac format if required
	if ( $opt->{raw} ) {
		if ( $file_tmp ne $prog->{filename} && ! $opt->{stdout} ) {
			move($file_tmp, $prog->{filename});
			$prog->check_duration() if $opt->{checkduration} && ! $live;
		}
		return 0;

	} elsif ( $mode_mp3 ) {
			@cmd = (
				$bin->{ffmpeg},
				@{ $binopts->{ffmpeg} },
				@globals,
				'-i', $file_tmp,
				'-vn',
				'-acodec', 'copy',
				@ffmpeg_opts,
				$prog->{filepart},
			);
			
	# Convert aac to m4a/mp3
	} elsif ( $mode_aac ) {
		# transcode to MP3 if directed. If mp3vbr is not set then perform CBR.
		if ( $opt->{aactomp3} ) {
			my @br_opts = ('-ab', '128k');
			if ( $opt->{mp3vbr} =~ /^\d$/ ) {
				@br_opts = ('-aq', $opt->{mp3vbr});
			}
			@cmd = (
				$bin->{ffmpeg},
				@{ $binopts->{ffmpeg} },
				@globals,
				'-i', $file_tmp,
				'-vn',
				'-acodec', 'libmp3lame', '-ac', '2', @br_opts,
				@ffmpeg_opts,
				$prog->{filepart},
			);
		} else {
			@cmd = (
				$bin->{ffmpeg},
				@{ $binopts->{ffmpeg} },
				@globals,
				'-i', $file_tmp,
				'-vn',
				'-acodec', 'copy',
				'-absf', 'aac_adtstoasc',
				@ffmpeg_opts,
				$prog->{filepart},
			);
		}
	}

	# Run aac conversion and delete source file on success
	$return = main::run_cmd( 'STDERR', @cmd );

	if ( (! $return) && -f $prog->{filepart} && stat($prog->{filepart})->size > $prog->min_download_size() ) {
			unlink( $file_tmp );
	# If the ffmpeg conversion failed, remove the failed-converted file attempt - move the file as done anyway
	} else {
		main::logger "WARNING: aac conversion failed - retaining aac file\n";
		unlink $prog->{filepart};
		$prog->{filepart} = $file_tmp;
		$prog->{filename} = $file_tmp;
	}
	# Moving file into place as complete (if not stdout)
	if ( $prog->{filepart} ne $prog->{filename} && ! $opt->{stdout} ) {
		move($prog->{filepart}, $prog->{filename}); 
		$prog->check_duration() if $opt->{checkduration} && ! $live;
	}
	
	# Re-symlink file
	$prog->create_symlink( $prog->{symlink}, $prog->{filename} ) if $opt->{symlink};

	main::logger "INFO: Recorded $prog->{filename}\n";
	return 0;
}


package Streamer::filestreamonly;

# Inherit from Streamer class
use base 'Streamer';

use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::stat;
use strict;

# Generic
# Actually do the file streaming
sub get {
	my ( $stream, $ua, $url, $prog ) = @_;
	my $start_time = time();

	main::logger "INFO: URL = $url\n" if $opt->{verbose};

	# Just remove any existing file
	unlink $prog->{filepart};
	
	# Streaming
	if ( $opt->{stdout} && $opt->{nowrite} ) {
		main::logger "INFO: Streaming $url to STDOUT\n" if $opt->{verbose};
		if ( ! open(FH, "< $url") ) {
			main::logger "ERROR: Cannot open $url: $!\n";
			return 'next';
		}
		# Fix for binary - needed for Windows
		binmode STDOUT;

		# Read each char from command output and push to STDOUT
		my $char;
		my $bytes;
		my $size = 200000;
		while ( $bytes = read( FH, $char, $size ) ) {
			if ( $bytes <= 0 ) {
				close FH;
				last;
			} else {
				print STDOUT $char;
			}
			last if $bytes < $size;
		}
		close FH;
		main::logger "DEBUG: streaming $url completed\n" if $opt->{debug};

	# Recording - disabled
	} else {
		main::logger "\rERROR: Recording failed - this is a stream-only programme\n";
		return 'next';
	}

	return 0;
}



############# PVR Class ##############
package Pvr;

use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::stat;
use IO::Seekable;
use IO::Socket;
use strict;
use Time::Local;

# Class vars
my %vars = {};
# Global options
my $optref;
my $opt_fileref;
my $opt_cmdlineref;
my $opt;
my $opt_file;
my $opt_cmdline;

# Class cmdline Options
sub opt_format {
	return {
		pvr		=> [ 0, "pvr|pvrrun|pvr-run!", 'PVR', '--pvr [pvr search name]', "Runs the PVR using all saved PVR searches (intended to be run every hour from cron etc). The list can be limited by adding a regex to the command. Synonyms: --pvrrun, --pvr-run"],
		pvrexclude	=> [ 0, "pvrexclude|pvr-exclude=s", 'PVR', '--pvr-exclude <string>', "Exclude the PVR searches to run by search name (regex or comma separated values). Synonyms: --pvrexclude"],
		pvrsingle	=> [ 0, "pvrsingle|pvr-single=s", 'PVR', '--pvr-single <search name>', "Runs a named PVR search. Synonyms: --pvrsingle"],
		pvradd		=> [ 0, "pvradd|pvr-add=s", 'PVR', '--pvr-add <search name>', "Save the named PVR search with the specified search terms.  Search terms required. Use --search=.* to force download of all available programmes. Synonyms: --pvradd"],
		pvrdel		=> [ 0, "pvrdel|pvr-del=s", 'PVR', '--pvr-del <search name>', "Remove the named search from the PVR searches. Synonyms: --pvrdel"],
		pvrdisable	=> [ 1, "pvrdisable|pvr-disable=s", 'PVR', '--pvr-disable <search name>', "Disable (not delete) a named PVR search. Synonyms: --pvrdisable"],
		pvrenable	=> [ 1, "pvrenable|pvr-enable=s", 'PVR', '--pvr-enable <search name>', "Enable a previously disabled named PVR search. Synonyms: --pvrenable"],
		pvrlist		=> [ 0, "pvrlist|pvr-list!", 'PVR', '--pvr-list', "Show the PVR search list. Synonyms: --pvrlist"],
		pvrqueue	=> [ 0, "pvrqueue|pvr-queue!", 'PVR', '--pvr-queue', "Add currently matched programmes to queue for later one-off recording using the --pvr option. Search terms required unless --pid specified. Use --search=.* to force download of all available programmes. Synonyms: --pvrqueue"],
		pvrscheduler	=> [ 0, "pvrscheduler|pvr-scheduler=n", 'PVR', '--pvr-scheduler <seconds>', "Runs the PVR using all saved PVR searches every <seconds>. Synonyms: --pvrscheduler"],
		comment		=> [ 1, "comment=s", 'PVR', '--comment <string>', "Adds a comment to a PVR search"],
	};
}


# Constructor
# Usage: $pvr = Pvr->new();
sub new {
	my $type = shift;
	my %params = @_;
	my $self = {};
	for (keys %params) {
		$self->{$_} = $params{$_};
	}
	## Ensure the subclass $opt var is pointing to the Superclass global optref
	$opt = $Pvr::optref;
	$opt_file = $Pvr::opt_fileref;
	$opt_cmdline = $Pvr::opt_cmdlineref;
	bless $self, $type;
}


# Use to bind a new options ref to the class global $opt_ref var
sub add_opt_object {
	my $self = shift;
	$Pvr::optref = shift;
}
# Use to bind a new options ref to the class global $opt_fileref var
sub add_opt_file_object {
	my $self = shift;
	$Pvr::opt_fileref = shift;
}
# Use to bind a new options ref to the class global $opt_cmdlineref var
sub add_opt_cmdline_object {
	my $self = shift;
	$Pvr::opt_cmdlineref = shift;
}


# Use to bind a new options ref to the class global $optref var
sub setvar {
	my $self = shift;
	my $varname = shift;
	my $value = shift;
	$vars{$varname} = $value;
}
sub getvar {
	my $self = shift;
	my $varname = shift;
	return $vars{$varname};
}


# $opt->{<option>} access method
sub opt {
	my $self = shift;
	my $optname = shift;
	return $opt->{$optname};
}


# Load all PVR searches and run one-by-one
# Usage: $pvr->run( [pvr search name] )
sub run {
	my $pvr = shift;
	my $pvr_name_regex = shift || '.*';
	my $exclude_regex = '_ROUGE_VALUE_';

	# Don't attempt to record programmes with pids in history
	my $hist = History->new();

	# Load all PVR searches
	$pvr->load_list();

	if ( $opt->{pvrexclude} ) {
		$exclude_regex = '('.(join '|', ( split /,/, $opt->{pvrexclude} ) ).')';
	}

	# For each PVR search (or single one if specified)
	my @names = ( grep !/$exclude_regex/i, grep /$pvr_name_regex/i, sort {lc $a cmp lc $b} keys %{$pvr} );

	my $retcode = 0;
	main::logger "Running PVR Searches:\n";
	for my $name ( @names ) {
		# Ignore if this search is disabled
		if ( $pvr->{$name}->{disable} ) {
			main::logger "\nSkipping '$name' (disabled)\n" if $opt->{verbose};
			next;
		}
		main::logger "$name\n";
		# Clear then Load options for specified pvr search name
		my $opt_backup;
		foreach ( @encoding_opts ) {
			$opt_backup->{$_} = $opt->{$_} if $opt->{$_};
		}
		my @search_args = $pvr->load_options($name);
		foreach ( @encoding_opts ) {
			$opt->{$_} = $opt_backup->{$_} if $opt_backup->{$_};
		}

		## Display all options used for this pvr search
		#$opt->display('Default Options', '(help|debug|get|^pvr)');

		# Switch on --hide option
		$opt->{hide} = 1;
		# Switch off --future option (no point in checking future programmes)
		$opt->{future} = '';
		# Dont allow --refresh with --pvr
		$opt->{refresh} = '';
		# Don't allow --info with --pvr
		$opt->{info} = '';
		# Do the recording (force --get option)
		$opt->{get} = 1 if ! $opt->{test};

		my $failcount = 0;
		# If this is a one-off queue pid entry then delete the PVR entry upon successful recording(s)
		if ( $pvr->{$name}->{pid} && $name =~ /^ONCE_/ ) {
			my @pids = split( /,/, $pvr->{$name}->{pid}  );	
			for ( @pids ) {
				$opt->{pid} = $_;
				$failcount += main::find_pid_matches( $hist );
			}
			$pvr->del( $name ) if not $failcount;

		# Just make recordings of matching progs
		} else {
			$failcount = main::download_matches( $hist, main::find_matches( $hist, @search_args ) );
		}
		if ( $failcount ) {
			main::logger "WARNING: PVR Run: $name: $failcount download failure(s)\n";
		}
		$retcode += $failcount
	}
	return $retcode;
}



sub run_scheduler {
	my $pvr = shift;
	my $interval = $opt->{pvrscheduler};
	# Ensure the caches refresh every run (assume cache refreshes take at most 300 seconds)
	$opt_cmdline->{expiry} = $interval - 300;
	main::logger "INFO: Scheduling the PVR to run every $interval secs\n";
	while ( 1 ) {
		my $start_time = time();
		$opt_cmdline->{pvr} = 1;
		# empty mem cache before each run to force cache file refresh
		for ( keys %$memcache ) {
			delete $memcache->{$_};
		}
		my $retcode = $pvr->run();
		if ( $retcode ) {
			main::logger "WARNING: PVR Scheduler: ".localtime().": $retcode download failure(s) \n";
		}
		my $remaining = $interval - ( time() - $start_time );
		if ( $remaining > 0 ) {
			main::logger "INFO: Sleeping for $remaining secs\n";
			sleep $remaining;
		}
	}
}



# If queuing, only add pids because the index number might change by the time the pvr runs
# If --pid and --type <type> is specified then add this prog also
sub queue {
	my $pvr = shift;
	my @search_args = @_;

	# Switch on --hide option
	$opt->{hide} = 1;
	my $hist = History->new();

	# PID and TYPE specified
	if ( $opt_cmdline->{pid} ) {
		# ensure we only have one prog type defined
		if ( $opt->{type} && $opt->{type} !~ /,/ ) {
			# Add to PVR if not already in history (unless multimode specified)
			$pvr->add( "ONCE_$opt_cmdline->{pid}" ) if ( ! $hist->check( $opt_cmdline->{pid} ) ) || $opt->{multimode};
		} else {
			main::logger "ERROR: Cannot add a pid to the PVR queue without a single --type specified\n";
			return 1;
		}

	# Search specified
	} else {
		my @matches = main::find_matches( $hist, @search_args );
		# Add a PVR entry for each matching prog PID
		for my $this ( @matches ) {
			$opt_cmdline->{pid} = $this->{pid};
			$opt_cmdline->{type} = $this->{type};
			$pvr->add( $this->substitute('ONCE_<name> - <episode> <pid>') );
		}

	}
	return 0;
}



# Save the options on the cmdline as a PVR search with the specified name
sub add {
	my $pvr = shift;
	my $name = shift;
	my @search_args = @_;
	my @options;
	# validate name
	if ( $name !~ m{[\w\-\+]+} ) {
		main::logger "ERROR: Invalid PVR search name '$name'\n";
		return 1;
	}
	# Parse valid options and create array (ignore options from the options files that have not been overriden on the cmdline)
	for ( grep !/(encoding.*|silent|webrequest|future|nocopyright|^test|metadataonly|subsonly|thumbonly|tagonly|stdout|^get|refresh|^save|^prefs|help|expiry|nowrite|tree|terse|streaminfo|listformat|^list|showoptions|hide|info|pvr.*)$/, sort {lc $a cmp lc $b} keys %{$opt_cmdline} ) {
		if ( defined $opt_cmdline->{$_} ) {
				push @options, "$_ $opt_cmdline->{$_}";
				main::logger "DEBUG: Adding option $_ = $opt_cmdline->{$_}\n" if $opt->{debug};
		}
	}
	# Add search args to array
	for ( my $count = 0; $count <= $#search_args; $count++ ) {
		push @options, "search${count} $search_args[$count]";
		main::logger "DEBUG: Adding search${count} = $search_args[$count]\n" if $opt->{debug};
	}
	# Save search to file
	$pvr->save( $name, @options );
	return 0;
}



# Delete the named PVR search
sub del {
	my $pvr = shift;
	my $name = shift;
	# validate name
	if ( $name !~ m{[\w\-\+]+} ) {
		main::logger "ERROR: Invalid PVR search name '$name'\n";
		return 1;
	}
	# Delete pvr search file
	if ( -f $vars{pvr_dir}.$name ) {
		unlink $vars{pvr_dir}.$name;
		main::logger "INFO: Deleted PVR search '$name'\n";
	} else {
		main::logger "ERROR: PVR search '$name' does not exist\n";
		return 1;
	}
	return 0;
}



# Display all the PVR searches
sub display_list {
	my $pvr = shift;
	# Load all the PVR searches
	$pvr->load_list();
	# Print out list
	main::logger "All PVR Searches:\n\n";
	for my $name ( sort {lc $a cmp lc $b} keys %{$pvr} ) {
		# Report whether disabled
		if ( $pvr->{$name}->{disable} ) {
			main::logger "pvrsearch = $name (disabled)\n";
		} else {
			main::logger "pvrsearch = $name\n";
		}
		for ( sort keys %{ $pvr->{$name} } ) {
			main::logger "\t$_ = $pvr->{$name}->{$_}\n";
		}
		main::logger "\n";
	}
	return 0;
}



# Load all the PVR searches into %{$pvr}
sub load_list {
	my $pvr = shift;
	# Clear any previous data in $pvr
	$pvr->clear_list();
	# Make dir if not existing
	mkpath $vars{pvr_dir} if ! -d $vars{pvr_dir};
	# Get list of files in pvr_dir
	# open file with handle DIR
	opendir( DIR, $vars{pvr_dir} );
	if ( ! opendir( DIR, $vars{pvr_dir}) ) {
		main::logger "ERROR: Cannot open directory $vars{pvr_dir}\n";
		return 1;
	}
	# Get contents of directory (ignoring . .. and ~ files)
	my @files = grep ! /(^\.{1,2}$|^.*~$)/, readdir DIR;
	# Close the directory
	closedir DIR;
	# process each file
	for my $file (@files) {
		chomp($file);
		# Re-add the dir
		$file = "$vars{pvr_dir}/$file";
		next if ! -f $file;
		if ( ! open (PVR, "< $file") ) {
			main::logger "WARNING: Cannot read PVR search file $file\n";
			next;
		}
		my @options = <PVR>;
		close PVR;
		# Get search name from filename
		my $name = $file;
		$name =~ s/^.*\/([^\/]+?)$/$1/g;
		for (@options) {
			/^\s*([\w\-_]+?)\s+(.*)\s*$/;
			main::logger "DEBUG: PVR search '$name': option $1 = $2\n" if $opt->{debug};
			$pvr->{$name}->{$1} = $2;
		}
		main::logger "INFO: Loaded PVR search '$name'\n" if $opt->{verbose};
	}
	main::logger "INFO: Loaded PVR search list\n" if $opt->{verbose};
	return 0;
}



# Clear all the PVR searches in %{$pvr}
sub clear_list {
	my $pvr = shift;
	# There is probably a faster way
	delete $pvr->{$_} for keys %{ $pvr };
	return 0;
}



# Save the array options specified as a PVR search
sub save {
	my $pvr = shift;
	my $name = shift;
	my @options = @_;
	# Sanitize name
	$name = StringUtils::sanitize_path( $name, 0, 1 );
	# Make dir if not existing
	mkpath $vars{pvr_dir} if ! -d $vars{pvr_dir};
	main::logger "INFO: Saving PVR search '$name':\n";
	# Open file
	if ( ! open (PVR, "> $vars{pvr_dir}/${name}") ) { 
		main::logger "ERROR: Cannot save PVR search to $vars{pvr_dir}.$name\n";
		return 1;
	}
	# Write options array to file
	for (@options) {
		print PVR "$_\n";
		main::logger "\t$_\n";
	}
	close PVR;
	return 0;
}


# Uses globals: $profile_dir, $optfile_system, $optfile_default
# Uses class globals: %opt, %opt_file, %opt_cmdline
# Returns @search_args
# Clear all exisiting global args and opts then load the options specified in the default options and specified PVR search
sub load_options {
	my $pvr = shift;
	my $name = shift;

	my $optfile_preset;
	# reset proxy env var
	$ENV{http_proxy} = $ENV_HTTP_PROXY;
	# Clear out existing options and file options hashes
	%{$opt} = ();

	# If the preset option is used in the PVR search then use it.
	if ( $pvr->{$name}->{preset} ) {
		$optfile_preset = ${profile_dir}."/presets/".$pvr->{$name}->{preset};
		main::logger "DEBUG: Using preset file: $optfile_preset\n" if $opt_cmdline->{debug};
	}

	# Re-copy options read from files at start of whole run
	$opt->copy_set_options_from( $opt_file );

	# Load options from $optfile_preset into $opt (uses $opt_cmdline as readonly options for debug/verbose etc)
	$opt->load( $opt_cmdline, $optfile_preset );
	
	# Clear search args
	@search_args = ();
	# Set each option from the search
	for ( sort {$a cmp $b} keys %{ $pvr->{$name} } ) {
		# Add to list of search args if this is not an option
		if ( /^search\d+$/ ) {
			main::logger "INFO: $_ = $pvr->{$name}->{$_}\n" if $opt->{verbose};
			push @search_args, $pvr->{$name}->{$_};
		# Else populate options, ignore disable option
		} elsif ( $_ ne 'disable' ) {
			main::logger "INFO: Option: $_ = $pvr->{$name}->{$_}\n" if $opt->{verbose};
			$opt->{$_} = $pvr->{$name}->{$_};
		}
	}

	# Allow cmdline args to override those in the PVR search
	# Re-copy options from the cmdline
	$opt->copy_set_options_from( $opt_cmdline );
	return @search_args;
}



# Disable a PVR search by adding 'disable 1' option
sub disable {
	my $pvr = shift;
	my $name = shift;
	$pvr->load_list();
	my @options;
	for ( keys %{ $pvr->{$name} }) {
		push @options, "$_ $pvr->{$name}->{$_}";
	}
	# Add the disable option
	push @options, 'disable 1';
	$pvr->save( $name, @options );
	return 0;
}



# Re-enable a PVR search by removing 'disable 1' option
sub enable {
	my $pvr = shift;
	my $name = shift;
	$pvr->load_list();
	my @options;
	for ( keys %{ $pvr->{$name} }) {
		push @options, "$_ $pvr->{$name}->{$_}";
	}
	# Remove the disable option
	@options = grep !/^disable\s/, @options;
	$pvr->save( $name, @options );	
	return 0;
}


package Tagger;
use Encode;
use File::stat;
use constant FB_EMPTY => sub { '' };

# already in scope
# my ($opt, $bin);

# constructor
sub new {
	my $class = shift;
	my $self = {};
	bless($self, $class);
}

# map metadata values to tags
sub tags_from_metadata {
	my ($self, $meta) = @_;
	my $tags;
	my $name = $opt->{tag_shortname} ? $meta->{nameshort} : $meta->{name};
	my $episode = $opt->{tag_longepisode} ? $meta->{episode} : $meta->{episodeshort};
	# iTunes media kind
	$tags->{stik} = 'Normal';
	if ( $meta->{ext} =~ /(mp4|m4v)/i) {
		$tags->{stik} = $meta->{categories} =~ /(film|movie)/i ? 'Short Film' : 'TV Show';
	}
	$tags->{advisory} = $meta->{guidance} ? 'explicit' : 'remove';
	# copyright message from download date
	$tags->{copyright} = substr($meta->{dldate}, 0, 4)." British Broadcasting Corporation, all rights reserved";
	# select version of of episode title to use
	if ( $opt->{tag_fulltitle} ) {
		$tags->{title} = "$name: $episode";
	} else {
		# fix up episode if necessary
		(my $title = $episode) =~ s/[\s\-]+$//;
		$title = "$meta->{series}: $title" if $opt->{tag_longtitle} && $meta->{series};
		$tags->{title} = $title ? $title : $name;
	}
	$tags->{artist} = $meta->{channel};
	# album artist from programme type
	($tags->{albumArtist} = "BBC " . ucfirst($meta->{type})) =~ s/tv/TV/i;
	$tags->{album} = $name;
	$tags->{grouping} = $meta->{categories};
	# composer references iPlayer
	$tags->{composer} = "BBC iPlayer";
	# extract genre as first category, use second if first too generic
	$tags->{genre} = $meta->{category};
	$tags->{comment} = $meta->{descshort};
	# fix up firstbcast if necessary
	$tags->{year} = $meta->{firstbcast};
	if ( $tags->{year} !~ /\d{4}-\d{2}-\d{2}\D\d{2}:\d{2}:\d{2}/ ) {
		my @utc = gmtime();
		$utc[4] += 1;
		$utc[5] += 1900;
		$tags->{year} = sprintf("%4d-%02d-%02dT%02d:%02d:%02dZ", reverse @utc[0..5]);
	}
	# extract date components for ID3v2.3
	my @date = split(//, $tags->{year});
	$tags->{tyer} = join('', @date[0..3]);
	$tags->{tdat} = join('', @date[8,9,5,6]);
	$tags->{time} = join('', @date[11,12,14,15]);
	$tags->{tracknum} = $meta->{episodenum};
	$tags->{disk} = $meta->{seriesnum};
	# generate lyrics text with links if available
	$tags->{lyrics} = $meta->{desclong};
	$tags->{lyrics} .= "\n\nEPISODE\n$meta->{player}" if $meta->{player};
	$tags->{lyrics} .= "\n\nSERIES\n$meta->{web}" if $meta->{web};
	$tags->{description} = $meta->{descshort};
	$tags->{longDescription} = $meta->{desclong};
	$tags->{hdvideo} = $meta->{mode} =~ /hd/i ? 'true' : 'false';
	$tags->{TVShowName} = $name;
	$tags->{TVEpisode} = $meta->{senum} ? $meta->{senum} : $meta->{pid};
	$tags->{TVSeasonNum} = $tags->{disk};
	$tags->{TVEpisodeNum} = $tags->{tracknum};
	$tags->{TVNetwork} = $meta->{channel};
	$tags->{podcastFlag} = 'true';
	$tags->{category} = $tags->{genre};
	$tags->{keyword} = $meta->{categories};
	$tags->{podcastGUID} = $meta->{player};
	$tags->{artwork} = $meta->{thumbfile};
	# video flag
	$tags->{is_video} = $meta->{ext} =~ /(mp4|m4v)/i;
	# tvshow flag
	$tags->{is_tvshow} = $tags->{stik} eq 'TV Show';
	# podcast flag
	$tags->{is_podcast} = $meta->{type} =~ /podcast/i || $opt->{tag_podcast}
		|| ( $opt->{tag_podcast_radio} && ! $tags->{is_video} )
		|| ( $opt->{tag_podcast_tv} && $tags->{is_video} );
	$tags->{cnID} = $self->tag_cnid_from_pid($meta->{pid}) if $opt->{tag_cnid};
	if ( $opt->{tag_isodate} ) {
		for my $field ( 'title', 'album', 'TVShowName' ) {
			$tags->{$field} =~ s|(\d\d)[/_](\d\d)[/_](20\d\d)|$3-$2-$1|g;
		}
	}
	while ( my ($key, $val) = each %{$tags} ) {
		$tags->{$key} = StringUtils::convert_punctuation($val);
	}
	return $tags;
}

# convert PID into 32-bit fake cnID
sub tag_cnid_from_pid {
	use integer;
	my ($self, $pid) = @_;
	my $cnid = 0;
	foreach( split(//, $pid) ) {
		$cnid = (unpack("L", (pack("L", 33 * $cnid))));
		$cnid = (unpack("L", (pack "L", $cnid + ord($_))));
	}
	$cnid = (unpack("L", (pack "L", $cnid + ($cnid >> 5))));
	return $cnid;
}

# in-place escape/enclose embedded quotes in command line parameters
sub tags_escape_quotes {
	my ($tags) = @_;
	# only necessary for Windows
	if ( $^O =~ /^MSWin32$/ ) {
		while ( my ($key, $val) = each %$tags ) {
			if ($val =~ /"/) {
				$val =~ s/"/\\"/g;
				$tags->{$key} = '"'.$val.'"';
			}
		}
	}
}

# in-place encode metadata values to iso-8859-1
sub tags_encode {
	my ($tags) = @_;
	while ( my ($key, $val) = each %{$tags} ) {
		$tags->{$key} = encode("iso-8859-1", $val, FB_EMPTY);
	}
}

# add metadata tag to file
sub tag_file {
	my ($self, $meta) = @_;
	my $tags = $self->tags_from_metadata($meta);
	# dispatch to appropriate tagging function
	if ( $meta->{filename} =~ /\.(mp3)$/i ) {
		return $self->tag_file_id3($meta, $tags);
	} elsif ( $meta->{filename} =~ /\.(mp4|m4v|m4a)$/i ) {
		return $self->tag_file_mp4($meta, $tags);
	} else {
		main::logger "WARNING: Don't know how to tag \U$meta->{ext}\E file\n" if $opt->{verbose};
	}
}

# add full ID3 tag with MP3::Tag
sub tag_file_id3 {
	my ($self, $meta, $tags) = @_;
	# look for required module
	eval 'use MP3::Tag';
	if ( $@ ) {
		if ( $opt->{verbose} ) {
			main::logger "INFO: Install the MP3::Tag module for full taggging of \U$meta->{ext}\E files\n";
			main::logger "INFO: Falling back to ID3 BASIC taggging of \U$meta->{ext}\E files\n";
		}
		return $self->tag_file_id3_basic($meta, $tags);
	}
	eval {
		main::logger "INFO: ID3 tagging \U$meta->{ext}\E file\n";
		# translate podcast flag
		$tags->{podcastFlag} = "\x01";
		for ( keys %$tags ) {
			$tags->{$_} = '' if ! defined $tags->{$_};
		}
		# encode for MP3::Tag
		tags_encode($tags);
		# remove existing tag(s) to avoid decoding errors
		my $mp3 = MP3::Tag->new($meta->{filename});
		$mp3->get_tags();
		$mp3->{ID3v1}->remove_tag() if exists $mp3->{ID3v1};
		$mp3->{ID3v2}->remove_tag() if exists $mp3->{ID3v2};
		$mp3->close();
		# add metadata
		if ( $opt->{tag_id3sync} ) {
			MP3::Tag->config(id3v23_unsync => 0);
		}
		$mp3 = MP3::Tag->new($meta->{filename});
		$mp3->select_id3v2_frame_by_descr('TCOP', $tags->{copyright});
		$mp3->select_id3v2_frame_by_descr('TIT2', $tags->{title});
		$mp3->select_id3v2_frame_by_descr('TPE1', $tags->{artist});
		$mp3->select_id3v2_frame_by_descr('TPE2', $tags->{albumArtist});
		$mp3->select_id3v2_frame_by_descr('TALB', $tags->{album});
		$mp3->select_id3v2_frame_by_descr('TIT1', $tags->{grouping});
		$mp3->select_id3v2_frame_by_descr('TCOM', $tags->{composer});
		$mp3->select_id3v2_frame_by_descr('TCON', $tags->{genre});
		$mp3->select_id3v2_frame_by_descr('COMM(eng,#0)[]', $tags->{comment});
		$mp3->select_id3v2_frame_by_descr('TYER', $tags->{tyer});
		$mp3->select_id3v2_frame_by_descr('TDAT', $tags->{tdat});
		$mp3->select_id3v2_frame_by_descr('TIME', $tags->{time});
		$mp3->select_id3v2_frame_by_descr('TRCK', $tags->{tracknum});
		$mp3->select_id3v2_frame_by_descr('TPOS', $tags->{disk});
		$mp3->select_id3v2_frame_by_descr('USLT', $tags->{lyrics});
		# tag iTunes podcast
		if ( $tags->{is_podcast} ) {
			# ID3v2.4 only, but works in iTunes
			$mp3->select_id3v2_frame_by_descr('TDRL', $tags->{year});
			# ID3v2.3 and ID3v2.4
			$mp3->select_id3v2_frame_by_descr('TIT3', $tags->{description});
			# Neither ID3v2.3 nor ID3v2.4, but work in iTunes
			$mp3->select_id3v2_frame_by_descr('TDES', $tags->{longDescription});
			$mp3->{ID3v2}->add_raw_frame('PCST', $tags->{podcastFlag});
			$mp3->select_id3v2_frame_by_descr('TCAT', $tags->{category});
			$mp3->select_id3v2_frame_by_descr('TKWD', $tags->{keyword});
			$mp3->select_id3v2_frame_by_descr('TGID', $tags->{podcastGUID});
		}
		# add artwork if available
		if ( -f $meta->{thumbfile}  && ! $opt->{noartwork} ) {
			my $data;
			open(THUMB, "<:raw", $meta->{thumbfile});
			read(THUMB, $data, stat($meta->{thumbfile})->size());
			close(THUMB);
			$mp3->select_id3v2_frame_by_descr('APIC', $data);
		}
		# write metadata to file
		$mp3->update_tags();
		$mp3->close();
	};
	if ( $@ ) {
		main::logger "ERROR: Failed to tag \U$meta->{ext}\E file\n";
		main::logger "ERROR: $@" if $opt->{verbose};
		# clean up thumbnail if necessary
		unlink $meta->{thumbfile} if ! $opt->{thumb};
		return 4;
	}
}

# add basic ID3 tag with id3v2
sub tag_file_id3_basic {
	my ($self, $meta, $tags) = @_;
	if ( main::exists_in_path('id3v2') ) {
		main::logger "INFO: ID3 BASIC tagging \U$meta->{ext}\E file\n";
		# notify about limitations of basic tagging
		if ( $opt->{verbose} ) {
			main::logger "INFO: ID3 BASIC tagging cannot add artwork to \U$meta->{ext}\E files\n";
			main::logger "INFO: ID3 BASIC tagging cannot add podcast metadata to \U$meta->{ext}\E files\n" if $tags->{is_podcast};
		}
		# colons are parsed as frame field separators by id3v2
		# so replace them to make safe comment text
		$tags->{comment} =~ s/:/_/g;
		# make safe lyrics text as well
		# can't use $tags->{lyrics} because of colons in links
		$tags->{longDescription} =~ s/:/_/g;
		# handle embedded quotes
		tags_escape_quotes($tags);
		# encode for id3v2
		tags_encode($tags);
		# build id3v2 command
		my @cmd = (
			$bin->{id3v2},
			'--TCOP', $tags->{copyright},
			'--TIT2', $tags->{title},
			'--TPE1', $tags->{artist},
			'--TPE2', $tags->{albumArtist},
			'--TALB', $tags->{album},
			'--TIT1', $tags->{grouping},
			'--TCOM', $tags->{composer},
			'--TCON', $tags->{genre},
			'--COMM', $tags->{comment},
			'--TYER', $tags->{tyer},
			'--TDAT', $tags->{tdat},
			'--TIME', $tags->{time},
			'--TRCK', $tags->{tracknum},
			'--TPOS', $tags->{disk},
			'--USLT', $tags->{longDescription},
			$meta->{filename},
		);
		# run id3v2 command
		if ( main::run_cmd( 'STDERR', @cmd ) ) {
			main::logger "WARNING: Failed to tag \U$meta->{ext}\E file\n";
			return 2;
		}
	} else {
		main::logger "WARNING: Cannot tag \U$meta->{ext}\E file\n" if $opt->{verbose};
	}
}

# add MP4 tag with atomicparsley
sub tag_file_mp4 {
	my ($self, $meta, $tags) = @_;
	# Only tag if the required tool exists
	if ( main::exists_in_path( 'atomicparsley' ) ) {
		main::logger "INFO: MP4 tagging \U$meta->{ext}\E file\n";
		# handle embedded quotes
		tags_escape_quotes($tags);
		# encode metadata for atomicparsley
		tags_encode($tags) unless $opt->{tag_utf8};
		# build atomicparsley command
		my @cmd = (
			$bin->{atomicparsley},
			$meta->{filename},
			'--freefree',
			'--overWrite',
			'--stik', $tags->{stik},
			'--advisory', $tags->{advisory},
			'--copyright', $tags->{copyright},
			'--title', $tags->{title},
			'--artist', $tags->{artist},
			'--albumArtist', $tags->{albumArtist},
			'--album', $tags->{album},
			'--grouping', $tags->{grouping},
			'--composer', $tags->{composer},
			'--genre', $tags->{genre},
			'--comment', $tags->{comment},
			'--year', $tags->{year},
			'--tracknum', $tags->{tracknum},
			'--disk', $tags->{disk},
			'--lyrics', $tags->{lyrics},
		);
		# add descriptions to audio podcasts and video
		if ( $tags->{is_video} || $tags->{is_podcast}) {
			push @cmd, ('--description', $tags->{description} );
			if ( $opt->{tag_longdescription} ) {
				push @cmd, ( '--longDescription', $tags->{longDescription} );
			} elsif ( $opt->{tag_longdesc} ) {
				push @cmd, ( '--longdesc', $tags->{longDescription} );
			}
		}
		# video only
		if ( $tags->{is_video} ) {
			# all video
			push @cmd, ( '--cnID', $tags->{cnID} ) if $opt->{tag_cnid};
			push @cmd, ( '--hdvideo', $tags->{hdvideo} ) if $opt->{tag_hdvideo};
			# tv only
			if ( $tags->{is_tvshow} ) {
				push @cmd, (
					'--TVShowName', $tags->{TVShowName},
					'--TVEpisode', $tags->{TVEpisode},
					'--TVSeasonNum', $tags->{TVSeasonNum},
					'--TVEpisodeNum', $tags->{TVEpisodeNum},
					'--TVNetwork', $tags->{TVNetwork},
				);
			}
		}
		# tag iTunes podcast
		if ( $tags->{is_podcast} ) {
			push @cmd, (
				'--podcastFlag', $tags->{podcastFlag},
				'--category', $tags->{category},
				'--keyword', $tags->{keyword},
				'--podcastGUID', $tags->{podcastGUID},
			);
		}
		# add artwork if available
		push @cmd, ( '--artwork', $meta->{thumbfile} ) if ( -f $meta->{thumbfile} && ! $opt->{noartwork} );
		# run atomicparsley command
		if ( main::run_cmd( 'STDERR', @cmd ) ) {
			main::logger "WARNING: Failed to tag \U$meta->{ext}\E file\n";
			return 2;
		}
	} else {
		main::logger "WARNING: Cannot tag \U$meta->{ext}\E file\n" if $opt->{verbose};
	}
}

############## End OO ##############
