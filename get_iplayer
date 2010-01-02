#!/usr/bin/perl
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
# Web: http://linuxcentre.net/iplayer
# License: GPLv3 (see LICENSE.txt)
#
#
package main;
my $version = 2.55;
#
# Help:
#	./get_iplayer --help | --longhelp
#
# Changelog:
# 	http://linuxcentre.net/get_iplayer/CHANGELOG.txt
#
# Example Usage and Documentation:
# 	http://linuxcentre.net/getiplayer/documentation
#
# Todo:
# * Fix non-uk detection - iphone auth?
# * Index/Record live radio streams w/schedule feeds to assist timing
# * Remove all rtsp/mplayer/lame/tee dross when realaudio streams become obselete (not quite yet)
# ** all global vars into a class???
# ** Cut down 'use' clauses in each class
# ** Globalise %prog, %got_cache so that they aren't repopulated for every PVR run
# * Correctly handle connection priorities in mediaselector metadata for each mode for iplayer
# * stdout streaming with mms
#
# Known Issues:

use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::stat;
use Getopt::Long;
use HTML::Entities;
use HTTP::Cookies;
use HTTP::Headers;
use IO::Seekable;
use IO::Socket;
use LWP::ConnCache;
#use LWP::Debug qw(+);
use LWP::UserAgent;
use POSIX qw(mkfifo);
use strict;
#use warnings;
use Time::Local;
use URI;
use POSIX qw(:termios_h);
my %SIGORIG;
$SIGORIG{$_} = $SIG{$_} for keys %SIG; # Save default SIG actions
$|=1;

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

# User Agents
my %user_agent = (
	coremedia	=> 'Apple iPhone v1.1.1 CoreMedia v1.0.0.3A110a',
	safari		=> 'Mozilla/5.0 (iPhone; U; CPU like Mac OS X; en) AppleWebKit/420.1 (KHTML, like Gecko) Version/3.0 Mobile/3A110a Safari/419.3',
	update		=> "get_iplayer updater (v${version} - $^O - $^V)",
	get_iplayer	=> "get_iplayer/$version $^O/$^V",
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
my $opt_format = {
	# Recording
	attempts	=> [ 1, "attempts=n", 'Recording', '--attempts <number>', "Number of attempts to make or resume a failed connection"],
	force		=> [ 1, "force|force-download", 'Recording', '--force', "Ignore programme history (unsets --hide option also). Forces a script update if used wth -u"],
	get		=> [ 2, "get|record|g", 'Recording', '--get, -g', "Start recording matching programmes"],
	hash		=> [ 1, "hash", 'Recording', '--hash', "Show recording progress as hashes"],
	mmsnothread	=> [ 1, "mmsnothread|itvnothread", 'Recording', '--mmsnothread', "Disable parallel threaded recording for mms"],
	modes		=> [ 0, "modes=s", 'Recording', '--modes <mode>,<mode>,...', "Recoding modes: iphone,flashhd,flashvhigh,flashhigh,flashstd,flashnormal,flashlow,n95_wifi,flashaac,flashaachigh,flashaacstd,flashaaclow,flashaudio,realaudio,wma"],
	multimode	=> [ 1, "multimode", 'Recording', '--multimode', "Allow the recording of more than one mode for the same programme - WARNING: will record all specified/default modes!!"],
	overwrite	=> [ 1, "overwrite|over-write", 'Recording', '--overwrite', "Overwrite recordings if they already exist"],
	partialproxy	=> [ 1, "partial-proxy", 'Recording', '--partial-proxy', "Only uses web proxy where absolutely required (try this extra option if your proxy fails)"],
	pid		=> [ 2, "pid|url=s", 'Recording', '--pid, --url [<type>:]<pid|URL>', "Record an arbitrary pid that does not necessarily appear in the index. Also used to stream live programmes"],
	proxy		=> [ 0, "proxy|p=s", 'Recording', '--proxy, -p <url>', "Web proxy URL spec"],
	raw		=> [ 0, "raw", 'Recording', '--raw', "Don't transcode or change the recording/stream in any way (i.e. radio/realaudio, rtmp/flv, iphone/mov)"],
	start		=> [ 1, "start=s", 'Recording', '--start <secs>', "Recording/streaming start offset (rtmp and realaudio only)"],
	stop		=> [ 1, "stop=s", 'Recording', '--stop <secs>', "Recording/streaming stop offset (can be used to limit live rtmp recording length) rtmp and realaudio only"],
	suboffset	=> [ 1, "suboffset=n", 'Recording', '--suboffset <offset>', "Offset the subtitle timestamps by the specified number of milliseconds"],
	subtitles	=> [ 2, "subtitles", 'Recording', '--subtitles', "Download subtitles into srt/SubRip format if available and supported"],
	subsonly	=> [ 1, "subtitlessonly|subsonly", 'Recording', '--subtitles-only', "Only download the subtitles, not the programme"],
	subsraw		=> [ 1, "subsraw", 'Recording', '--subsraw', "Additionally save the raw subtitles file"],
	test		=> [ 1, "test|t", 'Recording', '--test, -t', "Test only - no recording (will show programme type)"],
	thumb		=> [ 1, "thumb|thumbnail", 'Recording', '--thumb', "Download Thumbnail image if available"],
	thumbonly	=> [ 1, "thumbonly|thumbnailonly|thumbnail-only|thumb-only", 'Recording', '--thumbnail-only', "Only Download Thumbnail image if available, not the programme"],

	# Search
	before		=> [ 1, "before=n", 'Search', '--before', "Limit search to programmes added to the cache before N hours ago"],
	category 	=> [ 2, "category=s", 'Search', '--category <string>', "Narrow search to matched categories (regex or comma separated values)"],
	channel		=> [ 2, "channel=s", 'Search', '--channel <string>', "Narrow search to matched channel(s) (regex or comma separated values)"],
	exclude		=> [ 1, "exclude=s", 'Search', '--exclude <string>', "Narrow search to exclude matched programme names (regex or comma separated values)"],
	excludecategory	=> [ 1, "xcat|exclude-category=s", 'Search', '--exclude-category <string>', "Narrow search to exclude matched catogories (regex or comma separated values)"],
	excludechannel	=> [ 1, "xchan|exclude-channel=s", 'Search', '--exclude-channel <string>', "Narrow search to exclude matched channel(s) (regex or comma separated values)"],
	fields		=> [ 1, "fields=s", 'Search', '--fields <field1>,<field2>,..', "Searches only in the specified comma separated fields"],
	long		=> [ 0, "long|l", 'Search', '--long, -l', "Additionally search & display long programme descriptions / episode names"],
	search		=> [ 1, "search=s", 'Search', '--search <search term>', "GetOpt compliant way of specifying search args"],
	history		=> [ 1, "history", 'Search', '--history', "Search/show recordings history"],
	since		=> [ 1, "since=n", 'Search', '--since', "Limit search to programmes added to the cache in the last N hours"],
	type		=> [ 2, "type=s", 'Search', '--type <type>', "Only search in these types of programmes: ".join(',', keys %prog_types).",all (tv is default)"],
	versionlist	=> [ 1, "versionlist|versions|version-list=s", 'Search', '--versions <versions>', "Version of programme to search or record (e.g. '--versions signed,audiodescribed,default')"],

	# Output
	command		=> [ 1, "c|command=s", 'Output', '--command, -c <command>', "Run user command after successful recording using args such as <pid>, <name> etc"],
	fatfilename	=> [ 1, "fatfilename", 'Output', '--fatfilename, -w', "Omit characters forbidden by FAT filesystems from filenames but keep whitespace"],
	fileprefix	=> [ 1, "file-prefix|fileprefix=s", 'Output', '--file-prefix <format>', "The filename prefix (excluding dir and extension) using formatting fields. e.g. '<name>-<episode>-<pid>'"],
	fxd		=> [ 1, "fxd=s", 'Output', '--fxd <file>', "Create Freevo FXD XML of matching programmes in specified file"],
	html		=> [ 1, "html=s", 'Output', '--html <file>', "Create basic HTML index of matching programmes in specified file"],
	isodate		=> [ 1, "isodate",  'Output', '--isodate', "Use ISO8601 dates (YYYY-MM-DD) in filenames"],
	metadata	=> [ 1, "metadata=s", 'Output', '--metadata <type>', "Create metadata info file after recording. Valid types are: xbmc, xbmc_movie, generic"],
	metadataonly	=> [ 1, "metadataonly", 'Output', '--metadataonly', "Create specified metadata info file without any recording or streaming (can also be used with thumbnail option)."],
	mythtv		=> [ 1, "mythtv=s", 'Output', '--mythtv <file>', "Create Mythtv streams XML of matching programmes in specified file"],
	nowrite		=> [ 1, "no-write|nowrite|n", 'Output', '--nowrite, -n', "No writing of file to disk (use with -x to prevent a copy being stored on disk)"],
	output		=> [ 2, "output|o=s", 'Output', '--output, -o <dir>', "Default Recording output directory"],
	player		=> [ 0, "player=s", 'Output', "--player \'<command> <options>\'", "Use specified command to directly play the stream"],
	stdout		=> [ 1, "stdout|x", 'Output', '--stdout, -x', "Additionally stream to STDOUT (so you can pipe output to a player)"],
	stream		=> [ 0, "stream", 'Output', '--stream', "Stream to STDOUT (so you can pipe output to a player)"],
	subdir		=> [ 1, "subdirs|subdir|s", 'Output', '--subdir, -s', "Put Recorded files into Programme name subdirectory"],
	symlink		=> [ 1, "symlink|freevo=s", 'Output', '--symlink <file>', "Create symlink to <file> once we have the header of the recording"],
	thumbext	=> [ 1, "thumbext=s", 'Output', '--thumb-ext <ext>', "Thumbnail filename extension to use"],
	thumbsizecache	=> [ 1, "thumbsizecache=n", 'Output', '--thumbsizecache <index|width>', "Default thumbnail size/index to use when building cache and index (see --info for thumbnailN: to get size/index)"],
	thumbsize	=> [ 1, "thumbsize|thumbsizemeta=n", 'Output', '--thumbsize <index|width>', "Default thumbnail size/index to use for the current recording and metadata (see --info for thumbnailN: to get size/index)"],
	whitespace	=> [ 1, "whitespace|ws|w", 'Output', '--whitespace, -w', "Keep whitespace (and escape chars) in filenames"],
	xmlchannels	=> [ 1, "xml-channels|fxd-channels", 'Output', '--xml-channels', "Create freevo/Mythtv menu of channels -> programme names -> episodes"],
	xmlnames	=> [ 1, "xml-names|fxd-names", 'Output', '--xml-names', "Create freevo/Mythtv menu of programme names -> episodes"],
	xmlalpha	=> [ 1, "xml-alpha|fxd-alpha", 'Output', '--xml-alpha', "Create freevo/Mythtv menu sorted alphabetically by programme name"],

	# Config
	expiry		=> [ 1, "expiry|e=n", 'Config', '--expiry, -e <secs>', "Cache expiry in seconds (default 4hrs)"],
	flush		=> [ 2, "flush|refresh|f", 'Config', '--flush, --refresh, -f', "Refresh cache"],
	ignorechannels	=> [ 1, "ignorechannels=s", 'Config', '--ignorechannels <string>', "Ignore matched channel(s) when refreshing cache (regex or comma separated values)"],
	nopurge		=> [ 0, "no-purge|nopurge", 'Config', '--nopurge', "Don't ask to delete programmes recorded over 30 days ago"],	
	packagemanager	=> [ 1, "packagemanager=s", 'Config', '--packagemanager <string>', "Tell the updater that we were installed using a package manager and don't update (use either: apt,rpm,deb,yum,disable)"],
	pluginsupdate	=> [ 0, "pluginsupdate|plugins-update", 'Config', '--plugins-update', "Update get_iplayer plugins to the latest"],
	prefsadd	=> [ 0, "addprefs|add-prefs|prefsadd|prefs-add", 'Config', '--prefs-add', "Add/Change specified saved user or preset options"],
	prefsdel	=> [ 0, "del-prefs|delprefs|prefsdel|prefs-del", 'Config', '--prefs-del', "Remove specified saved user or preset options"],
	prefsclear	=> [ 0, "clear-prefs|clearprefs|prefsclear|prefs-clear", 'Config', '--prefs-clear', "Remove *ALL* saved user or preset options"],
	prefsshow	=> [ 0, "showprefs|show-prefs|prefsshow|prefs-show", 'Config', '--prefs-show', "Show saved user or preset options"],
	preset		=> [ 1, "preset|z=s", 'Config', '--preset, -z <name>', "Use specified user options preset"],
	presetlist	=> [ 1, "listpresets|list-presets|presetlist|preset-list", 'Config', '--preset-list', "Show all valid presets"],
	profiledir	=> [ 1, "profiledir|profile-dir=s", 'Config', '--profile-dir <dir>', "Override the user profile directory/folder"],
	update		=> [ 2, "update|u", 'Config', '--update, -u', "Update get_iplayer if a newer one exists"],
	webrequest	=> [ 1, "webrequest=s", 'Config', '--webrequest <urlencoded string>', 'Specify all options as a urlencoded string of "name=val&name=val&..."' ],

	# Display
	conditions	=> [ 1, "conditions", 'Display', '--conditions', 'Shows GPLv3 conditions'],
	debug		=> [ 1, "debug", 'Display', '--debug', "Debug output"],
	dumpoptions	=> [ 1, "dumpoptions|dumpopts|dump-options", 'Display', '--dump-options', 'Dumps all options with their internal option key names'],
	helpbasic	=> [ 2, "help-basic|usage|bh|hb|helpbasic|basichelp|basic-help", 'Display', '--helpbasic, --usage', "Basic help text"],
	help		=> [ 2, "help|h", 'Display', '--help, -h', "Intermediate help text"],
	helplong	=> [ 2, "help-long|advanced|long-help|longhelp|lh|hl|helplong", 'Display', '--helplong', "Advanced help text"],
	hide		=> [ 1, "hide", 'Display', '--hide', "Hide previously recorded programmes"],
	info		=> [ 2, "i|info", 'Display', '--info, -i', "Show full programme metadata and availability of modes and subtitles (max 50 matches)"],
	list		=> [ 1, "list=s", 'Display', '--list <categories|channel>', "Show a list of available categories/channels for the selected type and exit"],
	listformat	=> [ 1, "listformat=s", 'Display', '--listformat <format>', "Display programme data based on a user-defined format string (such as <pid>, <name> etc)"],
	listplugins	=> [ 1, "listplugins", 'Display', '--listplugins', "Display a list of currently available plugins or programme types"],
	manpage		=> [ 1, "manpage=s", 'Display', '--manpage <file>', "Create man page based on current help text"],
	nocopyright	=> [ 1, "nocopyright", 'Display', '--nocopyright', "Don't display copyright header"],
	page		=> [ 1, "page=n", 'Display', '--page <number>', "Page number to display for multipage output"],
	pagesize	=> [ 1, "pagesize=n", 'Display', '--pagesize <number>', "Number of matches displayed on a page for multipage output"],
	quiet		=> [ 1, "q|quiet|silent", 'Display', '--quiet, -q', "No logging output"],
	series		=> [ 0, "series", 'Display', '--series', "Display Programme series names only with number of episodes"],
	showcacheage	=> [ 1, "showcacheage|show-cache-age", 'Config', '--show-cache-age', "Displays the age of the selected programme caches then exit"],
	showoptions	=> [ 1, "showoptions|showopts|show-options", 'Display', '--show-options', 'Shows options which are set and where they are defined'],
	sortmatches	=> [ 1, "sortmatches|sort=s", 'Display', '--sort <fieldname>', "Field to use to sort displayed matches"],
	sortreverse	=> [ 1, "sortreverse", 'Display', '--sortreverse', "Reverse order of sorted matches"],
	streaminfo	=> [ 1, "streaminfo", 'Display', '--streaminfo', "Returns all of the media stream urls of the programme(s)"],
	terse		=> [ 0, "terse", 'Display', '--terse', "Only show terse programme info (does not affect searching)"],
	tree		=> [ 0, "tree", 'Display', '--tree', "Display Programme listings in a tree view"],
	verbose		=> [ 1, "verbose|v", 'Display', '--verbose, -v', "Verbose"],
	warranty	=> [ 1, "Display", 'Display', '--warranty', 'Displays warranty section of GPLv3'],

	# External Program
	atomicparsley	=> [ 0, "atomicparsley|atomic-parsley=s", 'External Program', '--atomicparsley <path>', "Location of AtomicParsley tagger binary"],
	id3v2		=> [ 0, "id3tag|id3v2=s", 'External Program', '--id3v2 <path>', "Location of id3v2 or id3tag binary"],
	mplayer		=> [ 0, "mplayer=s", 'External Program', '--mplayer <path>', "Location of mplayer binary"],

	# Deprecated

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
	my $msg = shift;
	# Make sure quiet can be overridden by verbose and debug options
	if ( $opt->{verbose} || $opt->{debug} || ! $opt->{quiet} ) {
		# Only send messages to STDERR if pvr or stdout options are being used.
		if ( $opt->{stdout} || $opt->{pvr} || $opt->{stderr} || $opt->{stream} ) {
			print STDERR $msg;
		} else {
			print STDOUT $msg;
		}
	}
}


# Pre-Parse the cmdline using the opt_format hash so that we know some of the options before we properly parse them later
# Parse options with passthru mode (i.e. ignore unknown options at this stage) 
# need to save and restore @ARGV to allow later processing)
my @argv_save = @ARGV;
$opt_pre->parse( 1 );
@ARGV = @argv_save;
# Copy a few options over to opt so that logger works
$opt->{debug} = $opt->{verbose} = 1 if $opt_pre->{debug};
$opt->{verbose} = 1 if $opt_pre->{verbose};
$opt->{quiet} = 1 if $opt_pre->{quiet};
$opt->{pvr} = 1 if $opt_pre->{pvr};
$opt->{stdout} = 1 if $opt_pre->{stdout} || $opt_pre->{stream};


# This is where all profile data/caches/cookies etc goes
my $profile_dir;
# This is where system-wide default options are specified
my $optfile_system;

# Options directories specified by env vars
if ( defined $ENV{GETIPLAYERUSERPREFS} && $ENV{GETIPLAYERSYSPREFS} ) {
	$profile_dir = $opt_pre->{profiledir} || $ENV{GETIPLAYERUSERPREFS};
	$optfile_system = $ENV{GETIPLAYERSYSPREFS};

# Otherwise look for windows style file locations
} elsif ( defined $ENV{USERPROFILE} ) {
	$profile_dir = $opt_pre->{profiledir} || $ENV{USERPROFILE}.'/.get_iplayer';
	$optfile_system = $ENV{ALLUSERSPROFILE}.'/get_iplayer/options';

# Options on unix-like systems
} elsif ( defined $ENV{HOME} ) {
	$profile_dir = $opt_pre->{profiledir} || $ENV{HOME}.'/.get_iplayer';
	$optfile_system = '/etc/get_iplayer/options';
	# Show warning if this deprecated location exists and is not a symlink
	if ( -f '/var/lib/get_iplayer/options' && ! -l '/var/lib/get_iplayer/options' ) {
		logger "WARNING: System-wide options file /var/lib/get_iplayer/options will be deprecated in future, please use /etc/get_iplayer/options instead\n";
	}
}
# Make profile dir if it doesnt exist
mkpath $profile_dir if ! -d $profile_dir;


# get list of additional user plugins and load plugin
my $plugin_dir_system = '/usr/share/get_iplayer/plugins';
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
	my $presetname = StringUtils::sanitize_path( $opt_pre->{preset} );
	$optfile_preset = "${profile_dir}/presets/${presetname}";
	logger "INFO: Using user options preset '${presetname}'\n";
}
logger "DEBUG: User Preset Options File: $optfile_preset\n" if defined $optfile_preset && $opt->{debug};


# Parse cmdline opts definitions from each Programme class/subclass
Options->get_class_options( $_ ) for qw( Streamer Programme Pvr );
Options->get_class_options( progclass($_) ) for progclass();
Options->get_class_options( "Streamer::$_" ) for qw( mms rtmp rtsp iphone mms 3gp http );


# Parse the cmdline using the opt_format hash
Options->usage( 0 ) if not $opt_cmdline->parse();


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
	logger request_url_retry( create_ua( 'get_iplayer' ), 'http://www.gnu.org/licenses/gpl-3.0.txt'."\n", 1);
	exit 1;
}

# Force plugins update if no plugins found
if ( ! keys %plugin_files ) {
	logger "WARNING: Running the updater again to obtain plugins.\n";
	$opt->{pluginsupdate} = 1;
}
# Update this script if required
update_script() if $opt->{update} || $opt->{pluginsupdate};



########## Global vars ###########

#my @cache_format = qw/index type name pid available episode versions duration desc channel categories thumbnail timeadded guidance web/;
my @history_format = qw/pid name episode type timeadded mode filename versions duration desc channel categories thumbnail guidance web/;
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
my $cookiejar		= "${profile_dir}/cookies";
my $namedpipe 		= "${profile_dir}/namedpipe.$$";
my $lwp_request_timeout	= 20;
my $info_limit		= 40;
my $proxy_save;

# Option dependant var definitions
my $bin;
my $binopts;
my @search_args = @ARGV;



########### Main processing ###########

# Use --webrequest to specify options in urlencoded format
if ( $opt->{webrequest} ) {
	# parse GET args
	my @webopts = split /[\&\?]/, $opt->{webrequest};
	for (@webopts) {
		# URL decode it
		$_ = main::url_decode( $_ );
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
# Assume search term is '.*' if nothing is specified - i.e. lists all programmes
push @search_args, '.*' if ! $search_args[0];

# Auto-detect http:// url or <type>:http:// in a search term and set it as a --pid option (disable if --fields is used).
if ( $search_args[0] =~ m{^(\w+:)?http://} && ( ! $opt->{pid} ) && ( ! $opt->{fields} ) ) {
	$opt->{pid} = $search_args[0];
}

# PVR Lockfile location (keep global so that cleanup sub can unlink it)
my $lockfile;
$lockfile = $profile_dir.'/pvr_lock' if $opt->{pvr} || $opt->{pvrsingle} || $opt->{pvrscheduler};

# Create new PVR instance
# $pvr->{searchname}->{<option>} = <value>;
my $pvr = Pvr->new();
# Set some class-wide values
$pvr->setvar('pvr_dir', "${profile_dir}/pvr/" );

# PVR functions
if ( $opt->{pvradd} ) {
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
	$pvr->queue( @search_args );

} elsif ( $opt->{pvrscheduler} ) {
	if ( $opt->{pvrscheduler} < 1800 ) {
		main::logger "ERROR: PVR schedule duration must be at least 1800 seconds\n";
		exit 5;
	};
	# PVR Lockfile detection (with 12 hrs stale lockfile check)
	lockfile( 43200 ) if ! $opt->{test};
	my $interval = $opt->{pvrscheduler};
	# Ensure the caches refresh every run (assume cache refreshes take at most 300 seconds)
	$opt_cmdline->{expiry} = $interval - 300;
	main::logger "INFO: Scheduling the PVR to run every $interval secs\n";
	while ( 1 ) {
		my $start_time = time();
		$opt_cmdline->{pvr} = 1;
		$pvr->run();
		my $remaining = $interval - ( time() - $start_time );
		if ( $remaining > 0 ) {
			main::logger "INFO: Sleeping for $remaining secs\n";
			sleep $remaining;
		}
	}

} elsif ( $opt->{pvr} ) {
	# PVR Lockfile detection (with 12 hrs stale lockfile check)
	lockfile( 43200 ) if ! $opt->{test};
	$pvr->run();
	unlink $lockfile;

} elsif ( $opt->{pvrsingle} ) {
	# PVR Lockfile detection (with 12 hrs stale lockfile check)
	lockfile( 43200 ) if ! $opt->{test};
	$pvr->run( $opt->{pvrsingle} );
	unlink $lockfile;

# Record prog specified by --pid option
} elsif ( $opt->{pid} ) {
	my $hist = History->new();
	find_matches( $hist );

# Show history
} elsif ( $opt->{history} ) {
	my $hist = History->new();
	$hist->load();
	# ensure we don't change any recordings
	$opt->{nowrite} = 1;
	$hist->show( @search_args );

# Else just process command line args
} else {
	my $hist = History->new();
	download_matches( $hist, find_matches( $hist, @search_args ) );
	purge_downloaded_files( $hist, 30 );
}
exit 0;



# Use the specified options to process the matches in specified array
# Usage: find_matches( \%pids_history, @search_args )
# Returns: array of objects to be downloaded
#      or: number of failed/remaining programmes to record using the match (excluding previously recorded progs) if --pid is specified
sub find_matches {
	my $hist = shift;
	my @search_args = @_;
	# Show options
	$opt->display('Current options') if $opt->{verbose};
	# $prog{pid}->object hash
	my %prog;
	# obtain prog object given index. e.g. $index_prog{$index_no}->{element};
	my %index_prog;
	# hash of prog types specified
	my %type;
	logger "INFO: Search args: '".(join "','", @search_args)."'\n" if $opt->{verbose};

	# Load history if we need it
	$hist->load() if $opt->{hide};

	# Ensure lowercase types
	$opt->{type} = lc( $opt->{type} );
	# Expand 'all' type to comma separated list all prog types
	$opt->{type} = join( ',', progclass() ) if $opt->{type} =~ /(all|any)/i;
	$type{$_} = 1 for split /,/, $opt->{type};
	# --stream is the same as --stdout --nowrite
	if ( $opt->{stream} ) {
		$opt->{nowrite} = 1;
		$opt->{stdout} = 1;
		delete $opt->{stream};
	}
	# Redirect STDOUT to player command if one is specified
	if ( $opt->{player} && $opt->{nowrite} && $opt->{stdout} ) {
		open (STDOUT, "| $opt->{player}") || die "ERROR: Cannot open player command\n";
		STDOUT->autoflush(1);
		binmode STDOUT;
	}
	# Default to type=tv if no type option is set
	$type{tv}		= 1 if keys %type == 0;

	# External Binaries
	$bin->{mplayer}		= $opt->{mplayer} || 'mplayer';
	delete $binopts->{mplayer};
	push @{ $binopts->{mplayer} }, '-nolirc';
	push @{ $binopts->{mplayer} }, '-v' if $opt->{debug};
	push @{ $binopts->{mplayer} }, '-really-quiet' if $opt->{quiet};

	$bin->{ffmpeg}		= $opt->{ffmpeg} || 'ffmpeg';

	$bin->{lame}		= $opt->{lame} || 'lame';
	delete $binopts->{lame};
	$binopts->{lame}	= '-f';
	$binopts->{lame}	.= ' --quiet ' if $opt->{quiet};

	$bin->{vlc}		= $opt->{vlc} || 'cvlc';
	delete $binopts->{vlc};
	push @{ $binopts->{vlc} }, '-vv' if $opt->{debug};

	$bin->{id3v2}		= $opt->{id3v2} || 'id3v2';
	$bin->{atomicparsley}	= $opt->{atomicparsley} || 'AtomicParsley';

	$bin->{tee}		= 'tee';

	$bin->{flvstreamer}	= $opt->{flvstreamer} || $opt->{rtmpdump} || 'flvstreamer';
	delete $binopts->{flvstreamer};
	push @{ $binopts->{flvstreamer} }, ( '--timeout', 10 );
	push @{ $binopts->{flvstreamer}	}, '--quiet' if $opt->{quiet};
	push @{ $binopts->{flvstreamer}	}, '--verbose' if $opt->{verbose};
	push @{ $binopts->{flvstreamer}	}, '--debug' if $opt->{debug};

	# quote binaries which allows for spaces in the path (only required if used via a shell)
	for ( $bin->{lame}, $bin->{tee} ) {
		s!^(.+)$!"$1"!g;
	}
	
	# Set --subtitles if --subsonly is used
	if ( $opt->{subsonly} ) {
		$opt->{subtitles} = 1;
	}

	# Set --thumbnail if --thumbonly is used
	if ( $opt->{thumbonly} ) {
		$opt->{thumb} = 1;
	}

	# Set --get && --nowrite if --metadataonly is used
	if ( $opt->{metadataonly} ) {
		if ( ! $opt->{metadata} ) {
			main::logger "ERROR: Please specify metadata type using --metadata=<type>\n";
			exit 2;
		}
	}

	# List all options and where they are set from then exit
	if ( $opt_cmdline->{showoptions} ) {
		# Show all options andf where set from
		$opt_file->display('Options from Files');
		$opt_cmdline->display('Options from Command Line');
		$opt->display('Options Used');
		logger "Search Args: ".join(' ', @search_args)."\n\n";
	}

	# Sanity check some conflicting options
	if ( $opt->{nowrite} && ! $opt->{stdout} ) {
		logger "ERROR: Cannot record to nowhere\n";
		exit 1;
	}

	# Sanity check valid --type specified
	for (keys %type) {
		if ( not progclass($_) ) {
			logger "ERROR: Invalid type '$_' specified. Valid types are: ".( join ',', progclass() )."\n";
			exit 3;
		}
	}
	
	# Web proxy
	$opt->{proxy} = $ENV{HTTP_PROXY} || $ENV{http_proxy} if not $opt->{proxy};
	logger "INFO: Using Proxy $opt->{proxy}\n" if $opt->{proxy};

	# Display the ages of the selected caches in seconds
	if ( $opt->{showcacheage} ) {
		for ( keys %type ) {
			my $cachefile = "${profile_dir}/${_}.cache";
			main::logger "INFO: $_ cache age: ".( time() - stat($cachefile)->mtime )." secs\n" if -f $cachefile;
		}
		exit 0;
	}

	# Get prog by arbitrary '<type>:<pid>' or just '<pid>' (using the specified types)(then exit)
	if ( $opt->{pid} ) {
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
			@try_types = (keys %type);
		}
		logger "INFO: Will try prog types: ".(join ',', @try_types)."\n" if $opt->{verbose};
		return 0 if ( ! $opt->{multimode} ) && $hist->check( $pid );
	
		# Maybe we don't want to populate caches - this slows down --pid recordings ...
		# Populate cache with all specified prog types (strange perl bug?? - @try_types is empty after these calls if done in a $_ 'for' loop!!)
		# only get links and possibly refresh caches if > 1 type is specified
		# else only load cached data from file if it exists.
		my $load_from_file_only;
		$load_from_file_only = 1 if $#try_types == 0;
		for my $t ( @try_types ) {
			get_links( \%prog, \%index_prog, $t, $load_from_file_only );
		}

		# Try to get pid using each speficied prog type
		my $retcode;
		for my $prog_type ( @try_types ) {
			logger "INFO Trying to stream pid using type $prog_type\n";
			# Force prog type and create new prog instance if it doesn't exist
			my $this;
			if ( not $prog{$pid}->{pid} ) {
				logger "INFO: pid not found in $prog_type cache\n";
				$this = progclass($prog_type)->new( 'pid' => $pid, 'type' => $prog_type );
				# if only one type is specified then we can clean up the pid which might actually be a url
				if ( $#try_types == 0 ) {
					logger "INFO: Cleaning pid Old: '$this->{pid}', " if $opt->{verbose};
					$this->clean_pid;
					logger " New: '$this->{pid}'\n" if $opt->{verbose};
				}
				# Display pid for recording
				list_progs( \%type, $this );
				$retcode = $this->download_retry_loop( $hist );
				last if ! $retcode;
			} else {
				logger "INFO: pid found in cache\n";
				$this = $prog{$pid};
				# Display pid for recording
				list_progs( \%type, $this );
				$retcode = $this->download_retry_loop( $hist );
				last if ! $retcode;
				# If it is in the cache then we'll not need to try the other types regardless of success
				last;
			}
		}
		# return zero on success
		return $retcode;
	}

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
			### perl bug here too ???
			# Get stream links from web site or from cache (also populates all hashes) specified in --type option
			get_links( \%prog, \%index_prog, $_ ) for keys %type;
			$got_cache{$_} = 1 for keys %type;
	}

	# Parse remaining args
	my @match_list;
	my @index_search_args;
	for ( @search_args ) {
		chomp();

		# If Numerical value < $max_index and the object exists from loaded prog types
		if ( /^[\d]+$/ && $_ <= $max_index ) {
			if ( defined $index_prog{$_} ) {
				logger "INFO: Search term '$_' is an Index value\n" if $opt->{verbose};
				push @match_list, $index_prog{$_};
			} else {
				# Add to another list to search in other prog types
				push @index_search_args, $_;
			}

		# If PID then find matching programmes with 'pid:<pid>'
		} elsif ( m{^\s*pid:(.+?)\s*$}i ) {
			if ( defined $prog{$1} ) {
				logger "INFO: Search term '$1' is a pid\n" if $opt->{verbose};
				push @match_list, $prog{$1};
			} else {
				logger "INFO: Search term '$1' is a non-existent pid, use --pid instead and/or specify the correct programme type\n";
			}

		# Else assume this is a programme name regex
		} else {
			logger "INFO: Search term '$_' is a substring\n" if $opt->{verbose};
			push @match_list, get_regex_matches( \%prog, $_ );
		}
	}
	
	# List elements (i.e. 'channel' 'categories') if required and exit
	if ( $opt->{list} ) {
		list_unique_element_counts( \%type, $opt->{list}, @match_list );
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
				$type{$prog_type} = 1;
				# Get $prog_type stream links
				get_links( \%prog, \%index_prog, $prog_type );
				$got_cache{$prog_type} = 1;
			}
		}
		# Now check again if the index number exists in the cache before adding this prog to the match list
		if ( defined $index_prog{$index}->{pid} ) {
			push @match_list, $index_prog{$index} if defined $index_prog{$index}->{pid};
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
			if ( $hist->{ $this->{pid} } ) {
				logger "DEBUG: Ignoring Prog: '$this->{index}: $this->{name} - $this->{episode}'\n" if $opt->{debug};
			} else {
				push @pruned, $this;
			}
		}
		@match_list = @pruned;
	}
		
	# Display list for recording
	list_progs( \%type, @match_list );

	# Write HTML and XML files if required (with search options applied)
	create_html( @match_list ) if $opt->{html};
	create_xml( $opt->{fxd}, @match_list ) if $opt->{fxd};
	create_xml( $opt->{mythtv}, @match_list ) if $opt->{mythtv};

	return @match_list;
}



sub download_matches {
	my $hist = shift;
	my @match_list = @_;

	# Do the recordings based on list of index numbers if required
	my $failcount;
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
	my $ua = create_ua();
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
		my $this = @matches[$count];
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
					$this->list_entry( '', 0, $number_of_types );
				}
			}
		}
		# Get info, create metadata, subtitles and/or thumbnail file (i.e. don't stream/record)
		if ( $opt->{info} || $opt->{metadataonly} || $opt->{thumbonly} || $opt->{subsonly} || $opt->{streaminfo} ) {
			$this->get_metadata_general();
			$this->get_metadata( $ua );
			# Search versions for versionlist versions
			my @versions = $this->generate_version_list;
			# Use first version in list if a version list is not specified
			$this->{version} = $versions[0] || 'default';
			$this->generate_filenames( $ua, $this->file_prefix_format() );
			# info
			$this->display_metadata( sort keys %{ $this } ) if $opt->{info};
			# subs
			if ( $opt->{subsonly} ) {
				# skip for non-tv
				$this->download_subtitles( $ua, "$this->{dir}/$this->{fileprefix}.srt" ) if $this->{type} eq 'tv';
			}
			# metadata
			$this->create_metadata_file if $opt->{metadataonly};
			# thumbnail
			$this->download_thumbnail if $opt->{thumbonly} && $this->{thumbnail};
			# streaminfo
			if ( $opt->{streaminfo} ) {
				main::display_stream_info( $this, $this->{verpids}->{$version}, $version );
				$opt->{quiet} = 0;
			}
			# remove offending metadata
			delete $this->{filename}, $this->{filepart}, $this->{ext};
		}
	}
	logger "\nINFO: ".($#matches + 1)." Matching Programmes\n" if ( $opt->{pvr} && $#matches >= 0 ) || ! $opt->{pvr};
}



# Returns matching programme objects using supplied regex
# Usage: get_regex_matches ( \%prog, $regex )
sub get_regex_matches {
	my $progref = shift;
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
	
	# Determine search for fields
	my @searchfields;
	@searchfields = split /\s*,\s*/, lc( $opt->{fields} ) if $opt->{fields};

	# Loop through each prog object
	for my $this ( values %{$progref} ) {
		# Only include programmes matching channels and category regexes
		if ( $this->{channel} =~ /$channel_regex/i
		  && $this->{categories} =~ /$category_regex/i
		  && ( ( not defined $this->{versions} ) || $this->{versions} =~ /$versions_regex/i )
		  && $this->{channel} !~ /$channel_exclude_regex/i
		  && $this->{name} !~ /$exclude_regex/i
		  && $this->{categories} !~ /$category_exclude_regex/i
		  && ( ( not defined $this->{timeadded} ) || $this->{timeadded} >= $now - ($since * 3600) )
		  && ( ( not defined $this->{timeadded} ) || $this->{timeadded} < $now - ($before * 3600) )
		) {
			# Custom search fields
			if ( @searchfields ) {
				for my $field ( @searchfields ) {
					$download_hash{ $this->{index} } = $this if $this->{$field} =~ /$download_regex/i;
				}
			# Normal name / long search
			} else {
				# Search prognames/pids while excluding channel_regex and category_regex
				$download_hash{ $this->{index} } = $this if $this->{name} =~ /$download_regex/i;
				# Also search long descriptions and episode data if -l is specified
				$download_hash{ $this->{index} } = $this if $opt->{long} && ( $this->{desc} =~ /$download_regex/i || $this->{episode} =~ /$download_regex/i );
			}
		}
	}

	my @match_list;
	# Add all matching prog objects to array
	for my $this ( sort {$a <=> $b} keys %download_hash ) {
		push @match_list, $download_hash{ $this };
	}

	return @match_list;
}



# Usage: sort_index( \%prog, \%index_prog, [$prog_type], [sortfield] )
# Populates the index if the prog hash as well as creating the %index_prog hash
# Should be run after any number of get_links methods
sub sort_index {
	my $progref = shift;
	my $index_progref = shift;
	my $prog_type = shift;
	my $sortfield = shift || 'name';
	my $counter = 1;
	my @sort_key;
	
	# Add index field based on alphabetical sorting by $sortfield
	# Start index counter at 'min' for this prog type
	$counter = progclass($prog_type)->index_min if defined $prog_type;

	# Create unique array of '<$sortfield|pid>' for this prog type
	for my $pid ( keys %{$progref} ) {
		# skip prog not of correct type and type is defined
		next if defined $prog_type && $progref->{$pid}->{type} ne $prog_type;
		push @sort_key, "$progref->{$pid}->{$sortfield}|$pid";
	}
	# Sort by $sortfield and index 
	for (sort @sort_key) {
		# Extract pid
		my $pid = (split /\|/)[1];

		# Insert prog instance var of the index number
		$progref->{$pid}->{index} = $counter;

		# Add the object reference into %index_prog hash
		$index_progref->{ $counter } = $progref->{$pid};

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



# Returns classname for prog type or if not specified, an array of all prog types
sub progclass {
	my $prog_type = shift;
	if ( $prog_type ) {
		return $prog_types{$prog_type};
	} elsif ( not defined $prog_type ) {
		return keys %prog_types;
	} else {
		main::logger "ERROR: Programe Type '$prog_type' does not exist. Try using --flush\n";
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
#	http://www.bbc.co.uk/cbbc/programmes/schedules.(json|yaml|xml)
#	# TV index on programmes tv
#	http://www.bbc.co.uk/tv/programmes/a-z/by/*/player
#	# TV + Radio
#	http://www.bbc.co.uk/programmes/a-z/by/*/player
#	# All TV (limit has effect of limiting to 2.? times number entries kB??)
#	# seems that only around 50% of progs are available here compared to programmes site:
#	http://feeds.bbc.co.uk/iplayer/categories/tv/list/limit/200
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
sub get_links {
	my $progref = shift;
	my $index_progref = shift;
	my $prog_type = shift;
	my $only_load_from_cache = shift;
	# Define cache file format (maybe this is better determined from the header line of the cache file)
	my @cache_format = qw/index type name pid available episode versions duration desc channel categories thumbnail timeadded guidance web/;
	
	my $now = time();
	my $cachefile = "${profile_dir}/${prog_type}.cache";

	# Read cache into %pid_old and %index_prog_old if cache exists
	my %prog_old;
	my %index_prog_old;

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
			my %record_entries;
			# Update fields in %prog hash for $pid
			$record_entries{$_} = shift @record for @cache_format_old;
			$prog_old{ $record_entries{pid} } = \%record_entries;
			$index_prog_old{ $record_entries{index} }  = $record_entries{pid};
		}
		close (CACHE);
		logger "INFO: got ".(keys %prog_old)." cache entries for $prog_type\n" if $opt->{verbose};
	} else {
		logger "INFO: No cache file exists for $prog_type\n" if $opt->{verbose};
	}

	# if a cache file doesn't exist/corrupted/empty, flush option is specified or original file is older than $cache_sec then download new data
	my $cache_secs = $opt->{expiry} || main::progclass( $prog_type )->expiry() || 14400;
	main::logger "DEBUG: Cache expiry time for $prog_type is ${cache_secs} secs - refresh in ".( stat($cachefile)->mtime + $cache_secs - $now )." secs\n" if $opt->{debug} && -f $cachefile && ! $opt->{flush};
	if ( (! $only_load_from_cache) && ( 
			(! keys %prog_old) || 
			(! -f $cachefile) || 
			$opt->{flush} || 
			($now >= ( stat($cachefile)->mtime + $cache_secs ))
			)
		) {

		# Get links for specific type of programme class
		if ( progclass( $prog_type )->get_links( $progref, $prog_type ) != 0 ) {
			# failed - leave cache unchanged
			main::logger "ERROR: Failed to retrieve programmes for $prog_type - skipping\n";
			return 0;
		}

		# Sort index for this prog type
		sort_index( $progref, $index_progref, $prog_type );
		
		# Open cache file for writing
		unlink $cachefile;
		my $now = time();
		if ( open(CACHE, "> $cachefile") ) {
			print CACHE "#".(join '|', @cache_format)."\n";
			for (sort {$a <=> $b} keys %{$index_progref}) {
				# prog object
				my $this = $index_progref->{$_};
				# Only write entries for correct prog type
				if ($this->{type} eq $prog_type) {
					# Merge old and new data to retain timestamps
					# if the entry was in old cache then retain timestamp from old entry
					if ( $prog_old{ $this->{pid} }{timeadded} ) {
						$this->{timeadded} = $prog_old{ $this->{pid} }{timeadded};
					# Else this is a new entry
					} else {
						$this->{timeadded} = $now;
						$this->list_entry( 'Added: ' );
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


	# Else copy data from existing cache file into new prog instances
	} else {
		for my $pid ( keys %prog_old ) {

			# Create new prog instance
			$progref->{$pid} = progclass( lc($prog_old{$pid}{type}) )->new( 'pid' => $pid );

			for (@cache_format) {
				$progref->{$pid}->{$_} = $prog_old{$pid}{$_};
			}
		}
		# Add prog objects to %index_prog hash
		$index_progref->{$_} = $progref->{ $index_prog_old{$_} } for keys %index_prog_old;
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
	my %data;
	if ( not defined $prog->{streams}->{$version} ) {
		logger "INFO: Getting media stream metadata for $prog->{name} - $prog->{episode}, $verpid ($version)\n" if $prog->{pid};
		%data = $prog->get_stream_data( $verpid );
		$prog->{streams}->{$version} = \%data;
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
		'User-Agent'	=> $user_agent{coremedia},
		'Accept'	=> '*/*',
		'Range'        => "bytes=${start}-${end}",
	);

	# Use url prepend if required
	if ( $opt->{proxy} =~ /^prepend:/ ) {
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
		return if $opt->{quiet};
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
		return if $opt->{quiet};
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



# Returns a random user agent string
sub random_ua {
	# Create user agents list
	my @user_agent_list = (
		'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/<RAND>.8 (KHTML, like Gecko) Chrome/2.0.178.0 Safari/<RAND>.8',
		'Mozilla/5.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50<RAND>; Media Center PC 5.0; c .NET CLR 3.0.0<RAND>6; .NET CLR 3.5.30<RAND>; InfoPath.1; el-GR)',
		'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50<RAND>; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30<RAND>; InfoPath.1)',
		'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; YPC 3.2.0; SLCC1; .NET CLR 2.0.50<RAND>; .NET CLR 3.0.04<RAND>)',
		'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; tr) AppleWebKit/<RAND>.4+ (KHTML, like Gecko) Version/4.0dp1 Safari/<RAND>.11.2',
		'Opera/9.64 (X11; Linux i686; U; en) Presto/2.1.1',
		'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50<RAND>; .NET CLR 3.5.30<RAND>; .NET CLR 3.0.30<RAND>; Media Center PC 6.0; InfoPath.2; MS-RTC LM 8)',
		'Mozilla/6.0 (Windows; U; Windows NT 7.0; en-US; rv:1.9.0.8) Gecko/2009032609 Firefox/3.0.9 (.NET CLR 3.5.30<RAND>)',
	);

	# Randomize strings
	my $code = sprintf( "%03d", int(rand(1000)) );
	my $uas = $user_agent_list[rand @user_agent_list];
	$uas =~ s/<RAND>/$code/g;
	logger "DEBUG: Using user-agent string: '$uas'\n" if $opt->{debug};
	return $uas;
}



# Generic
# create_ua( <agentname>|'', [<cookie mode>] )
# cookie mode:	0: retain cookies
#		1: no cookies
#		2: retain cookies but discard if site requires it
sub create_ua {
	# Use either the key from the function arg if it exists or a random ua string
	my $agent = $user_agent{ "$_[0]" } || random_ua();
	my $nocookiejar = $_[1] || 0;
	my $ua = LWP::UserAgent->new;
	$ua->timeout( $lwp_request_timeout );
	$ua->proxy( ['http'] => $opt->{proxy} ) if $opt->{proxy} && $opt->{proxy} !~ /^prepend:/;
	$ua->agent( $agent );
	main::logger "DEBUG: Using user-agent '$agent'\n" if $opt->{debug};
	# Using this slows down stco parsing!!
	#$ua->default_header( 'Accept-Encoding', 'gzip,deflate' );
	$ua->conn_cache(LWP::ConnCache->new());
	#$ua->conn_cache->total_capacity(50);
	$ua->cookie_jar( HTTP::Cookies->new( file => $cookiejar, autosave => 1, ignore_discard => 1 ) ) if not $nocookiejar;
	$ua->cookie_jar( HTTP::Cookies->new( file => $cookiejar, autosave => 1 ) ) if $nocookiejar == 2;
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
	$file = '/dev/null' if $opt->{nowrite};
	if ($file) {
		if ( ! open(FH, ">> $file") ) {
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
	my $version_url	= 'http://linuxcentre.net/get_iplayer/VERSION-get_iplayer';
	my $update_url	= 'http://linuxcentre.net/get_iplayer/get_iplayer';
	my $changelog_url = 'http://linuxcentre.net/get_iplayer/CHANGELOG.txt';
	my $latest_ver;
	# Get version URL
	my $script_file = $0;
	my $script_url;
	my %plugin_url;
	my $ua = create_ua('update');

	# Are we flagged as installed using a pkg manager?
	if ( $opt->{packagemanager} ) {
		if ( $opt->{packagemanager} =~ /(apt|deb|dpkg)/i ) {
			logger "INFO: Please run the following commands to update get_iplayer using $opt->{packagemanager}\n".
			"  wget http://linuxcentre.net/get_iplayer/packages/get-iplayer-current.deb\n".
			"  sudo dpkg -i get-iplayer-current.deb\n".
			"  sudo apt-get -f install\n";
		} elsif ( $opt->{packagemanager} =~ /yum/i ) {
			logger "INFO: Please run the following commands as root to update get_iplayer using $opt->{packagemanager}\n".
			"  wget http://linuxcentre.net/get_iplayer/packages/get_iplayer-current.noarch.rpm\n".
			"  yum --nogpgcheck localinstall get_iplayer-current.noarch.rpm\n";
		} elsif ( $opt->{packagemanager} =~ /rpm/i ) {
			logger "INFO: Please run the following command as root to update get_iplayer using $opt->{packagemanager}\n".
			"  rpm -Uvh http://linuxcentre.net/get_iplayer/packages/get_iplayer-current.noarch.rpm\n";
		} elsif ( $opt->{packagemanager} =~ /disable/i ) {
			logger "ERROR: get_iplayer should only be updated using your local package management system, for more information see http://linuxcentre.net/installation\n";
		} else {
			logger "ERROR: get_iplayer was installed using '$opt->{packagemanager}' package manager please refer to the update documentation at http://linuxcentre.net/getiplayer/installation/\n";
		}
		exit 1;
	} 

	# If the get_iplayer script is unwritable then quit - makes it harder for deb/rpm installed scripts to be overwritten
	if ( ! -w $script_file ) {
		logger "ERROR: $script_file is not writable - aborting update (maybe a package manager was used to install get_iplayer?)\n";
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
	logger "INFO: Checking for latest version from linuxcentre.net\n";
	if ( $latest_ver = request_url_retry($ua, $version_url, 3 ) ) {
		chomp($latest_ver);
		# Compare version numbers
		if ( $latest_ver > $version || $opt->{force} || $opt->{pluginsupdate} ) {
			# reformat version number
			$latest_ver = sprintf('%.2f', $latest_ver);
			logger "INFO: Newer version $latest_ver available\n" if $latest_ver > $version;
			
			# Get the manifest of files to be updated
			my $base_url = "${update_url}-${latest_ver}";
			my $res;
			if ( not $res = request_url_retry($ua, "$base_url/MANIFEST.txt", 3 ) ) {
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
				logger "INFO: Change Log: http://linuxcentre.net/get_iplayer/CHANGELOG.txt\n";
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
			print XML "\t\t<container title=\"".encode_entities( $name )." ($program_count{$name})\">\n" if $opt->{fxd};
			print XML "\t<Streams>\n" if $opt->{mythtv};
			print XML "\t\t<Name>".encode_entities( $name )."</Name>\n" if $opt->{mythtv};
			for my $this (@_) {
				my $pid = $this->{pid};
				# loop through and find matches for each progname
				if ( $this->{name} eq $name ) {
					my $episode = encode_entities( $this->{episode} );
					my $desc = encode_entities( $this->{desc} );
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
			print XML "\t\t<container title=\"".encode_entities( $channel )."\">\n" if $opt->{fxd};
			print XML
				"\t<Feed>\n".
				"\t\t<Name>".encode_entities( $channel )."</Name>\n".
				"\t\t<Provider>BBC</Provider>\n".
				"\t\t<Streams>\n" if $opt->{mythtv};
			for my $name ( sort keys %program_index ) {
				# Do we have any of this prog $name on this $channel?
				my $match;
				for ( @{ $channels{$channel} } ) {
					$match = 1 if $_ eq $name;
				}
				if ( $match ) {
					print XML "\t\t\t<container title=\"".encode_entities( $name )." ($program_count{$name})\">\n" if $opt->{fxd};
					#print XML "\t\t<Stream>\n" if $opt->{mythtv};
					for my $this (@_) {
						# loop through and find matches for each progname for this channel
						my $pid = $this->{pid};
						if ( $this->{channel} eq $channel && $this->{name} eq $name ) {
							my $episode = encode_entities( $this->{episode} );
							my $desc = encode_entities( $this->{desc} );
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
									"\t\t\t\t<Name>".encode_entities( $name )."</Name>\n".
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
			'Q-R' => '[qt]',
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
				my $name = encode_entities( $this->{name} );
				my $episode = encode_entities( $this->{episode} );
				my $desc = encode_entities( $this->{desc} );
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



# Usage: create_html( @prog_objects )
sub create_html {
	my %name_channel;
	# Create local web page
	if ( open(HTML, "> $opt->{html}") ) {
		print HTML '<html><head></head><body><table border=1>';
		for my $this (@_) {
			# Skip if pid isn't in index
			my $pid = $this->{pid} || next;
			# Skip if already recorded and --hide option is specified
			if (! defined $name_channel{ "$this->{name}|$this->{channel}" }) {
				print HTML $this->list_entry_html();
			} else {
				print HTML $this->list_entry_html( 1 );
			}
			$name_channel{ "$this->{name}|$this->{channel}" } = 1;
		}
		print HTML '</table></body>';
		close (HTML);
	} else {
		logger "Couldn't open html file $opt->{html} for writing\n";
	}
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
	if ( $opt->{proxy} =~ /^prepend:/ ) {
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
	return $res->decoded_content if $res->header('Content-Encoding') eq 'gzip';

	return $res->content;
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
			
	# Load the history if it is empty
	$hist->load() if ! keys %{ $hist };
				
	# Return if disabled or running in a typically non-interactive mode
	return 0 if $opt->{nopurge} || $opt->{stdout} || $opt->{nowrite} || $opt->{quiet};
	
	for my $pid ( keys %{ $hist } ) {
		my $record = $hist->{$pid};
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
		main::logger "Do you wish to delete them now (--nopurge will prevent this check) (yes/NO) ?\n";
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
# Show channels for currently specified types in @matchlist - an array of progrefs
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

	main::logger "\n\nINFO: Command: ".(join ' ', @cmd)."\n\n" if $opt->{verbose};

	# Define what to do with STDOUT and STDERR of the child process
	my $fh_child_out = ">&STDOUT";
	my $fh_child_err = ">&STDERR";

	if ( $mode eq 'STDOUT' ) {
		$fh_child_out = $fh_child_err = ">&STDOUT";
		#$system_suffix = '2>&1';
	} elsif ( $mode eq 'STDERR' ) {
		$fh_child_out = $fh_child_err = ">&STDERR";
		#$system_suffix = '1>&2';
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



# Generic
# Signal handler to clean up after a ctrl-c or kill
sub cleanup {
	my $signal = shift;
	logger "\nINFO: Cleaning up $0 (got signal $signal)\n"; # if $opt->{verbose};
	unlink $namedpipe;
	unlink $lockfile;
	# Execute default signal handler
	$SIGORIG{$signal}->() if $SIGORIG{$signal};
	exit 1;
}



# Generic
# Make a filename/path sane (optionally allow fwd slashes)
sub StringUtils::sanitize_path {
	my $string = shift;
	my $allow_fwd_slash = shift || 0;

	# Remove fwd slash if reqd
	$string =~ s/\//_/g if ! $allow_fwd_slash;

	# Replace backslashes with _ regardless
	$string =~ s/\\/_/g;
	# Sanitize by default
	$string =~ s/\s/_/g if (! $opt->{whitespace}) && (! $allow_fwd_slash);
	$string =~ s/[^\w_\-\.\/\s]//gi if ! $opt->{whitespace};
	$string =~ s/[\|\\\?\*\<\"\:\>\+\[\]\/]//gi if $opt->{fatfilename};
	return $string;
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

	for my $name (keys %{$opt_format_ref} ) {
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
	my $text = sprintf "get_iplayer v%.2f, ", $version;
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
		'.TH GET_IPLAYER "1" "January 2010" "Phil Lewis" "get_iplayer Manual"',
		'.SH NAME', 'get_iplayer - Stream Recording tool and PVR for BBC iPlayer, BBC Podcasts and more',
		'.SH SYNOPSIS',
		'\fBget_iplayer\fR [<options>] [<regex|index> ...]',
		'.PP',
		'\fBget_iplayer\fR \fB--get\fR [<options>] <regex|index> ...',
		'.br',
		'\fBget_iplayer\fR <url> \fB--type\fR=<type> [<options>]',
		'.PP',
		'\fBget_iplayer\fR \fB--pid\fR=<pid|url> [\fB--type\fR=<type> <options>]',
		'.PP',
		'\fBget_iplayer\fR \fB--stream\fR [<options>] <regex|index> | mplayer \fB-cache\fR 3072 -',
		'.PP',
		'\fBget_iplayer\fR \fB--stream\fR [<options>] \fB--type\fR=<type> \fB--pid\fR=<pid|url> | mplayer \fB-cache\fR 3072 -',
		'.PP',
		'\fBget_iplayer\fR \fB--stream\fR [<options>] \fB--type\fR=livetv,liveradio <regex|index> \fB--player\fR="mplayer -cache 128 -"',
		'.PP',
		'\fBget_iplayer\fR \fB--update\fR',
		'.SH DESCRIPTION',
		'\fBget_iplayer\fR lists, searches and records BBC iPlayer TV/Radio, BBC Podcast programmes. Other 3rd-Party plugins may be available.',
		'.PP',
		'\fBget_iplayer\fR has three modes: recording a complete programme for later playback, streaming a programme',
		'directly to a playback application, such as mplayer; and as a Personal Video Recorder (PVR), subscribing to',
		'search terms and recording programmes automatically. It can also stream or record live BBC iPlayer output',
		'.PP',
		'If given no arguments, \fBget_iplayer\fR updates and displays the list of currently available programmes.',
		'Each available programme has a numerical identifier, \fBpid\fR.',
		'\fBget_iplayer\fR records BBC iPlayer programmes by pretending to be an iPhone, which means that some programmes in the list are unavailable for recording.',
		'It can also utilise the \fBrtmpdump\fR or \fBflvstreamer\fR tools to record programmes from RTMP flash streams at various qualities.',
		'.PP',
		'In PVR mode, \fBget_iplayer\fR can be called from cron to record programmes to a schedule.',
		'.SH "OPTIONS"' if $manpage;
	push @usage, "Usage ( Also see http://linuxcentre.net/getiplayer/documentation ):";
	push @usage, " Search Programmes:             get_iplayer [<options>] [<regex|index> ...]";
	push @usage, " Record Programmes:             get_iplayer --get [<options>] <regex|index> ...";
	push @usage, "                                get_iplayer <url> [--type=<type>]";
	push @usage, "                                get_iplayer --pid=<pid|url> --type=<type>";
	push @usage, " Stream Programme to Player:    get_iplayer --stream <index> | mplayer -cache 3072 -" if $helplevel == 1;
	push @usage, " Stream BBC Embedded Media      get_iplayer --stream --type=<type> --url=<URL> | mplayer -cache 128 -" if $helplevel != 2;
	push @usage, " Stream Live iPlayer Programme  get_iplayer --stream --type=livetv,liveradio <regex|index> --player='mplayer -cache 128 -'" if $helplevel != 2;
	push @usage, " Update get_iplayer:            get_iplayer --update [--force]";
	push @usage, " Basic Help:                    get_iplayer --basic-help" if $helplevel != 2;
	push @usage, " Intermediate Help:             get_iplayer --help" if $helplevel == 2;
	push @usage, " Advanced Help:                 get_iplayer --long-help" if $helplevel != 1;

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
	for my $section ( 'Search', 'Display', 'Recording', 'Download', 'Output', 'PVR', 'Config', 'External Program', 'Misc' ) {
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
			push @dumplines, sprintf(" %-20s %-32s %s", $name, $name_syntax{$name}, $name_desc{$name} ) if $dumpopts;
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
			'get_iplayer is written and maintained by Phil Lewis <iplayer2 (at sign) linuxcentre.net>.',
			'.PP',
			'This manual page was originally written by Jonathan Wiltshire <debian@jwiltshire.org.uk> for the Debian project (but may be used by others).',
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

	# Print options dump and quit
	} elsif ( $dumpopts ) {
		main::logger join "\n", @dump, "\n";
	
	# Print usage and quit
	} else {
		main::logger join "\n", @usage, "\n";
	}

	exit 1;
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
	return '^(help|debug|get|pvr|prefs|preset|warranty|conditions)';
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
		main::logger "INFO: Deleted option '$_' = '$this_cmdline->{$_}'\n" if defined $this_cmdline->{$_} && defined $entry->{$_};
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
	open (OPT, "< $optfile") || die ("ERROR: Cannot read options file $optfile\n");
	while(<OPT>) {
		/^\s*([\w\-_]+)\s+(.*)\s*$/;
		next if not defined $1;
		# Error if the option is not valid
		if ( not defined $optname->{$1} ) {
			main::logger "ERROR: Invalid option in $optfile: '$1 = $2'\n";
			main::logger "INFO: Please remove and use --dump-options to display all valid options\n";
			exit 10;
		}
		# Warn if it is listed as a deprecated internal option name
		if ( @{ $opt_format_ref->{$1} }[2] eq 'Deprecated' ) {
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
	for ( grep !/$regex/i, sort keys %{$this} ) {
		main::logger "\t$_ = $this->{$_}\n" if defined $this->{$_} && $this->{$_};
	}
	main::logger "\n";
	return 0;
}




########################################################

################ History default class #################
package History;

use Env qw[@PATH];
use Fcntl;
use File::Copy;
use File::Path;
use File::stat;
use strict;

# Class vars
# Global options
my $opt_format_ref;

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
	# should this be $main::type ?
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


# Uses global @history_format
# Adds prog to history file (with a timestamp) so that it is not rerecorded after deletion
# Does not require a load()
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
	# Temporarily add timestamp then delete it later
	#my $timeadded = $prog->{timeadded};
	$prog->{timeadded} = time();
	# Write each field into a line in the history file
	print HIST $prog->{$_}.'|' for @history_format;
	print HIST "\n";
	close HIST;
	#delete $prog->{timestamp};
	#$prog->{timeadded} = $timeadded;
	return 0;
}



# Uses global @history_format
# returns, for all the pids in the history file, $history->{pid}->{key} = value
sub load {
	my $hist = shift;

	# Return if force option specified or stdout streaming only
	return 0 if $opt->{force} || $opt->{stdout} || $opt->{nowrite};

	main::logger "INFO: Loading download history\n" if $opt->{verbose};
	if ( ! open(HIST, "< $historyfile") ) {
		main::logger "WARNING: Cannot read $historyfile\n\n" if $opt->{verbose};
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
			$record_entries->{$_} = shift @record;
		}
		# Create new history entry
		if ( defined $hist->{ $record_entries->{pid} } ) {
			main::logger "WARNING: duplicate pid $record_entries->{pid} in history\n" if $opt->{debug};
			# Append filename and modes - could be a multimode entry
			$hist->{ $record_entries->{pid} }->{mode} .= ','.$record_entries->{mode};
			$hist->{ $record_entries->{pid} }->{filename} .= ','.$record_entries->{filename};
			main::logger "DEBUG: Loaded and merged '$record_entries->{pid}' = '$record_entries->{name} - $record_entries->{episode}' from history\n" if $opt->{debug};
		} else {
			# workaround empty names
			#$record_entries->{name} = 'pid:'.$record_entries->{pid} if ! $record_entries->{name};
			$hist->{ $record_entries->{pid} } = History::new();
			$hist->{ $record_entries->{pid} } = $record_entries;
			main::logger "DEBUG: Loaded '$record_entries->{pid}' = '$record_entries->{name} - $record_entries->{episode}' from history\n" if $opt->{debug};
		}
	}
	close (HIST);
	return 0;
}



# Lists current history items (assumes loaded first)
# Requires a load()
sub show {
	my $hist = shift;
	my %prog;
	my ( @search_args ) = ( @_ );
	my %progtypes = main::progclass();

	# This is a 'well dirty' hack to allow all the Programme class methods to be used on the history objects
	# Basically involves copying all history objects into prog objects and then calling the required method

	# Sort index by timestamp
	my %index_hist;
	main::sort_index( \%{ $hist }, \%index_hist, undef, 'timeadded' );

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
		$prog{ $progrec->{pid} } = $progrec;
	}

	# Parse remaining args
	my @match_list;
	for ( @search_args ) {
		chomp();

		# If Numerical value < $max_index and the object exists from loaded prog types
		if ( /^[\d]+$/ && $_ <= $max_index ) {
			if ( defined $index_hist{$_} ) {
				main::logger "INFO: Search term '$_' is an Index value\n" if $opt->{verbose};
				push @match_list, $prog{ $index_hist{$_}->{pid} };
			}

		# If PID then find matching programmes with 'pid:<pid>'
		} elsif ( m{^\s*pid:(.+?)\s*$}i ) {
			if ( defined $prog{$1} ) {
				main::logger "INFO: Search term '$1' is a pid\n" if $opt->{verbose};
				push @match_list, $prog{$1};
			} else {
				main::logger "INFO: Search term '$1' is a non-existent pid, use --pid instead\n";
			}

		# Else assume this is a programme name regex
		} else {
			main::logger "INFO: Search term '$_' is a substring\n" if $opt->{verbose};
			push @match_list, main::get_regex_matches( \%prog, $_ );
		}
	}

	# De-dup matches and retain order then list matching programmes in history
	main::list_progs( undef, main::make_array_unique_ordered( @match_list ) );

	return 0;
}



# Generic
# Checks history for previous download of this pid
# Does not require a load()
sub check {
	my $hist = shift;
	my $pid = shift;
	my $mode = shift;
	return 0 if ! $pid;

	# Return if force option specified or stdout streaming only
	return 0 if $opt->{force} || $opt->{stdout} || $opt->{nowrite};

	if ( ! open(HIST, "< $historyfile") ) {
		main::logger "WARNING: Cannot read $historyfile\n\n" if $opt->{verbose};
		return 0;
	}
	my @entries = grep /^$pid/, <HIST>;
	close HIST;

	# Find and parse first matching history lines
	for my $entry ( @entries ) {
		my ( $name, $episode, $histmode ) = ( split /\|/, $entry )[1,2,5];
		chomp $name;
		chomp $episode;
		chomp $histmode;
		main::main::logger "DEBUG: Found PID='$pid' with MODE='$histmode' in download history\n" if $opt->{debug};
		if ( $opt->{multimode} ) {
			# Strip any number off the end of the mode names for the comparison
			$mode =~ s/\d+$//g;
			$histmode =~ s/\d+$//g;
			if ( $mode eq $histmode ) {
				main::logger "INFO: $name - $episode ($pid / $mode) Already in download history ($historyfile) - use --force to override\n";
				return 1;
			}
		} else {
			main::logger "INFO: $name - $episode ($pid) Already in download history ($historyfile) - use --force to override\n";
			return 1;
		}
	}
	main::logger "INFO: Programme not in download history\n" if $opt->{verbose};
	return 0;
}




#################### Programme class ###################

package Programme;

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


# Filter out channel names matched with option --ignorechannels
sub channels_filtered {
	my $prog = shift;
	my %channels = %{ $prog->channels() };
	# Ignore matching channels as required
	my $ignore_channel_regex = '^ROUGEVALUE$';
	# Create a regex from any comma separated values
	$ignore_channel_regex = '('.(join '|', ( split /,/, $opt->{ignorechannels} ) ).')' if $opt->{ignorechannels};
	for my $channel ( keys %channels ) {
		if ( $channels{$channel} =~ /$ignore_channel_regex/i ) {
			main::logger "INFO: Ignoring channel $channels{$channel}\n" if $opt->{verbose};
			delete $channels{$channel};
		}
	}
	return \%channels;
}


sub channels {
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


# Return metadata of the prog
sub get_metadata {
	my $prog = shift;
	my $ua = shift;
	$prog->{modes}->{default} = $prog->modelist();
	$prog->get_verpids( $ua ) if keys %{ $prog->{verpids} } == 0;
	$prog->{versions} = join ',', sort keys %{ $prog->{verpids} };
}


# Return metadata which is generic such as time and date
sub get_metadata_general {
	my $prog = shift;
	my @t = localtime();
	#($second, $minute, $hour, $dayOfMonth, $month, $yearOffset, $dayOfWeek, $dayOfYear, $daylightSavings) = localtime();
	$prog->{dldate} = sprintf "%02s-%02s-%02s", $t[5] + 1900, $t[4] + 1, $t[3];
	$prog->{dltime} = sprintf "%02s:%02s:%02s", $t[2], $t[1], $t[0];
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
		# else just print out key value pair
		} else {
			main::logger sprintf "%-15s %s\n", $_.':', $data{$_} if $data{$_};		
		}
	}
	main::logger "\n";
	return 0;
}



# Return hash of version => verpid given a pid
# Also put verpids in $prog->{verpids}->{<version>} = <verpid>
sub get_verpids {
	my $prog = shift;
	$prog->{verpids}->{'default'} = 1;
}



# Download Subtitles, convert to srt(SubRip) format and apply time offset
sub download_subtitles {
	# return failed...
	return 1;
}



# Usage: generate_version_list ($prog)
# Returns sorted array of versions
sub generate_version_list {
	my $prog = shift;
	
	# Default Order with which to search for programme versions (can be overridden by --versionlist option)
	my @version_search_order = qw/ default original signed audiodescribed opensubtitled shortened lengthened other /;
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
		main::logger "INFO: No versions of this programme were selected (".(join ',', sort keys %{ $prog->{verpids} })." are available)\n";
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
	my $ua = main::create_ua();

	# This pre-gets all the metadata - not entirely necessary but it does help - maybe only have when --metadata or --command is used
	# Also need full metadata for AtomicParsley or if --fileprefix is used
	$prog->get_metadata_general();
	if ( $opt->{fileprefix} || $opt->{metadata} || $opt->{command} || main::exists_in_path( 'atomicparsley' ) ) {
		$prog->get_metadata( $ua );
	}

	# Look up version pids for this prog - this does nothing if above get_metadata has alredy completed
	$prog->get_verpids( $ua ) if keys %{ $prog->{verpids} } == 0;

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
				my %streamdata = $prog->get_stream_data( $prog->{verpids}->{$version} );
				$prog->{streams}->{$version} = \%streamdata;
			}

			########## mode loop ########
			# record prog depending on the prog type

			# only use modes that exist
			my @modes;
			my @available_modes = sort keys %{ $prog->{streams}->{$version} };
			for my $modename ( split /,/, $modelist ) {
				# find all numbered modes starting with this modename
				push @modes, sort { $a <=> $b } grep /^$modename(\d+)?$/, @available_modes;
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
				main::logger "INFO: No specified modes ($modelist) available for this programme with version '$version' (try using --modes=".(join ',', sort keys %available_modes_short).")\n";
				next;
			}
			main::logger "INFO: ".join(',', @modes)." modes will be tried for version $version\n";

			# Expand the modes into a loop
			for my $mode ( @modes ) {
				chomp( $mode );
				main::logger "INFO: Trying $mode mode to record $prog->{type}: $prog->{name} - $prog->{episode}\n";
				$prog->{mode} = $mode;

				# If multimode is used, skip only modes which are in the history
				next if $opt->{multimode} && $hist->check( $prog->{pid}, $mode );

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
	$retries = $opt->{attempts} || 20 if $mode =~ /^flash/;

	# Retry loop
	for ($count = 1; $count <= $retries; $count++) {
		main::logger "INFO: Attempt number: $count / $retries\n" if $opt->{verbose};

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
				if ( ! $opt->{nowrite} ) {
					$hist->add( $prog );
					$prog->tag_file;
				}
				$prog->download_thumbnail if $opt->{thumb};
				$prog->create_metadata_file if $opt->{metadata};
				if ( ! $opt->{nowrite} ) {
					$prog->run_user_command( $opt->{command} ) if $opt->{command};
				}
			}
			$prog->report() if $opt->{pvr};
			return 0;

		# Retry this mode
		} elsif ( $retcode eq 'retry' && $count < $retries ) {
			main::logger "WARNING: Retry recording for '$prog->{name} - $prog->{episode} ($prog->{pid})'\n";
			# Try to get stream data for this version/mode - retries require new auth data
			my %streamdata = $prog->get_stream_data( $version_pid );
			$prog->{streams}->{$version} = \%streamdata;
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



# Add id3 tag to MP3/AAC files if required
sub tag_file {
	my $prog = shift;

	# Return if file does not exist
	return if ! -f $prog->{filename};

	if ( $prog->{filename} =~ /\.(aac|mp3|m4a)$/i ) {
		# Create ID3 tagging options for external tagger program (escape " for shell)
		my ( $id3_name, $id3_episode, $id3_desc, $id3_channel ) = ( $prog->{name}, $prog->{episode}, $prog->{desc}, $prog->{channel} );
		s|"|\\"|g for ($id3_name, $id3_episode, $id3_desc, $id3_channel);
		# Only tag if the required tool exists
		if ( main::exists_in_path('id3v2') ) {
			main::logger "INFO: id3 tagging $prog->{ext} file\n";
			my @cmd = (
				$bin->{id3v2}, 
				'--artist', $id3_channel,
				'--album', $id3_name,
				'--song', $id3_episode,
				'--comment', 'Description:'.$id3_desc,
				'--year', (localtime())[5] + 1900,
				$prog->{filename},
			);
			if ( main::run_cmd( 'STDERR', @cmd ) ) {
				main::logger "WARNING: Failed to tag $prog->{ext} file\n";
				return 2;
			}
		} else {
			main::logger "WARNING: Cannot tag $prog->{ext} file\n" if $opt->{verbose};
		}

	} elsif ( $prog->{filename} =~ /\.(mp4|m4v)$/i ) {
		# Create mp4 tagging options for external tagging program.
		my $tags;
		for my $tag ( keys %{$prog} ) {
			# Used for firstbcast etc which are a version based HASH
			if ( ref$prog->{$tag} eq 'HASH' ) {
				$tags->{$tag} = $prog->{$tag}->{$prog->{version}};
			} else {
				$tags->{$tag} = $prog->{$tag};
			}
			$tags->{$tag} =~ s|"|\\"|g;
		}

		# Make 'duration' == 'length' for the selected version
		$tags->{duration} = $prog->{durations}->{$prog->{version}} if $prog->{durations}->{$prog->{version}};

		# Only tag if the required tool exists
		if ( main::exists_in_path( 'atomicparsley' ) ) {
			# Download Thubnail file as well for inclusion into MP4 stream.
			# Apple TV/iTunes will use it.
			main::logger "INFO: mp4 tagging $prog->{ext} file\n";

			# extract year from firstbcast e.g. 2009-10-05T22:35:00+01:00
			#$year =~ s/^.*(20\d\d|19\d\d).*$/$1/g;
			# If year isn't set correctly in the information, then assume today.
			$tags->{firstbcast} = (localtime())[5] + 1900 if ! $tags->{firstbcast};

			# Add guidance if set
			$tags->{guidance} = 'clean';
			$tags->{guidance} = 'explicit' if $prog->{guidance};

			# Show type
			my $stik = 'TV Show';
			$stik = 'Movie' if $tags->{categories} =~ m{(film|movie)}i;

			# Download the thumbnail if it doesn't already exist
			$prog->download_thumbnail if ! -f $prog->{thumbfile};

			# Strip series and episode text from name, longname, episode
			for my $tag ( qw/name longname episode/ ) {
				$tags->{$tag} =~ s/(:\s*)?(Series|Episode)\s*\d+(:\s*)?//gi;
			}
			my $title = "$tags->{longname} - $tags->{episode}";
			# strip any trailing '-' and whitespace
			$title =~ s/[\s\-]*$//g;

			# Build the command
			my @cmd = (
				$bin->{atomicparsley}, $prog->{filename},
				'--TVNetwork',	$tags->{channel},
				'--description',$tags->{desc},
				'--comment',	$tags->{desc},
				'--title',	$title,
				'--TVShowName',	$tags->{longname},
				'--TVEpisode',	$tags->{pid},
				'--artist',	$tags->{name},
				'--year',	$tags->{firstbcast},
				'--advisory',	$tags->{guidance},
				'--genre',	$tags->{categories},
				'--stik',	$stik,
				'--overWrite',	# Saves temp files being left around.
			);

			# Add the thumbnail if one was downloaded
			push @cmd, "--artwork", $prog->{thumbfile} if -f $prog->{thumbfile};

			# Add the series and episode numbers if they are defined
			push @cmd, "--TVSeasonNum", $prog->{seriesnum} if $prog->{seriesnum};
			push @cmd, "--TVEpisodeNum", $prog->{episodenum} if $prog->{episodenum};

			# time of recording - this messes up iTunes somewhat
			#push @cmd, "--purchaseDate", "$prog->{dldate}T$prog->{dltime}Z" if $prog->{dldate} && $prog->{dltime};

			# After running, clean up thumbnail file unless it is required using the thumbnail option.
			if ( main::run_cmd( 'STDERR', @cmd ) ) {
				main::logger "WARNING: Failed to tag $prog->{ext} file\n";
				unlink $prog->{thumbfile} if ! $opt->{thumb};
				return 2;
			}
			unlink $prog->{thumbfile} if ! $opt->{thumb};
		}
	}
}



# Create a metadata file if required
sub create_metadata_file {
	my $prog = shift;
	my $template;
	my $filename;

	# XML templaye for XBMC movies
	$filename->{xbmc_movie} = "$prog->{dir}/$prog->{fileprefix}.nfo";
	$template->{xbmc_movie} = '
	<movie>
		<title>[name] - [episode]</title>
		<outline>[desc]</outline>
		<plot>[desc]</plot>
		<tagline></tagline>
		<runtime>[duration]</runtime>
		<thumb>[thumbnail]</thumb>
		<id>[pid]</id>
		<filenameandpath>[dir]/[fileprefix].[ext]</filenameandpath>
		<trailer></trailer>
		<genre>[categories]</genre>
		<year>[firstbcast]</year>
		<credits>[channel]</credits>
        </movie>
	';

	# XML template for XBMC
	$filename->{xbmc} = "$prog->{dir}/$prog->{fileprefix}.nfo";
	$template->{xbmc} = '
	<episodedetails>
		<title>[name] - [episode]</title>
		<rating>10.00</rating>
		<season>[seriesnum]</season>
		<episode>[episodenum]</episode>
		<plot>[desc]</plot>
		<credits>[channel]</credits>
		<aired>[firstbcast]</aired>
	</episodedetails>
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
		print XML $text;
		close XML;
	} else {
		main::logger "WARNING: Couldn't write to metadata file '$filename->{ $opt->{metadata} }'\n";
	}
}



# Usage: print $prog{$pid}->substitute('<name>-<pid>-<episode>', [mode], [begin regex tag], [end regex tag]);
# Return a string with formatting fields substituted for a given pid
# sanitize_mode == 0 then sanitize final string but dont sanitize '/' in field values
# sanitize_mode == 1 then sanitize final string and also sanitize '/' in field values
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
	my $replace;

	# Make 'duration' == 'length' for the selected version
	$self->{duration} = $self->{durations}->{$version} if $self->{durations}->{$version};

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

		main::logger "DEBUG: Substitute ($version): '$key' => '$value'\n" if $opt->{debug};
		# Remove/replace all non-nice-filename chars if required
		if ($sanitize_mode == 0) {
			$replace = StringUtils::sanitize_path( $value );
		# html entity encode
		} elsif ($sanitize_mode == 3) {
			$replace = encode_entities( $value );
		# escape these chars: ! ` \ "
		} elsif ($sanitize_mode == 4) {
			$replace = $value;
			$replace =~ s/([\!"\\`])/\\$1/g;
		} else {
			$replace = $value;
		}
		$key = $tag_begin.$key.$tag_end;
		$string =~ s|$key|$replace|gi;
	}

	# Remove/replace all non-nice-filename chars if required except for fwd slashes
	if ( $sanitize_mode == 0 || $sanitize_mode == 1 ) {
		return StringUtils::sanitize_path( $string, 1 );
	} else {
		return $string;
	}
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
		$prog->get_metadata($ua);
		$prog->get_metadata_general();
	}

	# Determine direcotry and find it's absolute path
	if ( $^O !~ /^MSWin32$/ ) {
		$prog->{dir} = abs_path( $opt->{ 'output'.$prog->{type} } || $opt->{output} || $ENV{IPLAYER_OUTDIR} || '.' );
	} else {
		$prog->{dir} = $opt->{ 'output'.$prog->{type} } || $opt->{output} || $ENV{IPLAYER_OUTDIR} || '.';
	}
	
	# Add modename to default format string if multimode option is used
	$format .= ' <mode>' if $opt->{multimode};

	$prog->{fileprefix} = $opt->{fileprefix} || $format;

	# get $name, $episode from title
	my ( $name, $episode ) = Programme::bbciplayer::split_title( $prog->{title} ) if $prog->{title};
	$prog->{name} = $name if $name && ! $prog->{name};
	$prog->{episode} = $episode if $episode && ! $prog->{episode};
	# store the name extracted from the title metadata in <longname> else just use the <name> field
	$prog->{longname} = $name || $prog->{name};


	# substitute fields and sanitize $prog->{fileprefix}
	main::logger "DEBUG: Substituted '$prog->{fileprefix}' as " if $opt->{debug};
	$prog->{fileprefix} = $prog->substitute( $prog->{fileprefix} );

	# Truncate filename to 240 chars (allows for extra stuff to keep it under system 256 limit)
	$prog->{fileprefix} = substr( $prog->{fileprefix}, 0, 240 );
	main::logger "'$prog->{fileprefix}'\n" if $opt->{debug};

	# Spaces
	$prog->{fileprefix} =~ s/\s+/_/g if ! $opt->{whitespace};

	# Change the date in the filename to ISO8601 format if required
	$prog->{fileprefix} =~ s|(\d\d)[/_](\d\d)[/_](20\d\d)|$3-$2-$1|g if $opt->{isodate};

	# Don't create subdir if we are only testing recordings
	# Create a subdir for programme sorting option
	if ( $opt->{subdir} ) {
		my $subdir = $prog->substitute( '<longname>' );
		$prog->{dir} .= "/${subdir}";
		$prog->{dir} =~ s|\/\/|\/|g;
		main::logger("INFO: Creating subdirectory $prog->{dir} for programme\n") if $opt->{verbose};
	}

	# Create a subdir if there are multiple parts
	if ( $multipart ) {
		$prog->{dir} .= "/$prog->{fileprefix}";
		$prog->{dir} .= s|\/\/|\/|g;
		main::logger("INFO: Creating multi-part subdirectory $prog->{dir} for programme\n") if $opt->{verbose};
	}

	# Create dir if it does not exist
	mkpath("$prog->{dir}") if (! -d "$prog->{dir}") && (! $opt->{test});

	main::logger("\rINFO: File name prefix = $prog->{fileprefix}                 \n");

	# Use a dummy file ext if one isn't set - helps with readability of metadata
	$prog->{ext} = 'EXT' if ! $prog->{ext};
	
	# Don't override the {filename} if it is already set (i.e. for history info)
	$prog->{filename} = "$prog->{dir}/$prog->{fileprefix}.$prog->{ext}" if $prog->{filename} =~ /\.EXT$/ || ! $prog->{filename};
	$prog->{filepart} = "$prog->{dir}/$prog->{fileprefix}.partial.$prog->{ext}";

	# Create symlink filename if required
	if ( $opt->{symlink} ) {
		# Substitute the fields for the pid
		$prog->{symlink} = $prog->substitute( $opt->{symlink} );
		main::logger("INFO: Symlink file name will be '$prog->{symlink}'\n") if $opt->{verbose};
		# remove old symlink
		unlink $prog->{symlink} if -l $prog->{symlink} && ! $opt->{test};
	}

	# overwrite/error if the file already exists and is going to be written to
	if (
		( ! $opt->{nowrite} )
		&& -f $prog->{filename} 
		&& stat($prog->{filename})->size > $prog->min_download_size()
	) {
		if ( $opt->{overwrite} ) {
			main::logger("INFO: Overwriting file $prog->{filename}\n\n");
			unlink $prog->{filename};
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
		$prog->{thumbfile} = "$prog->{dir}/$prog->{fileprefix}.${ext}";
	}

	main::logger "DEBUG: File prefix:        $prog->{fileprefix}\n" if $opt->{debug};
	main::logger "DEBUG: File ext:           $prog->{ext}\n" if $opt->{debug};
	main::logger "DEBUG: Directory:          $prog->{dir}\n" if $opt->{debug};
	main::logger "DEBUG: Partial Filename:   $prog->{filepart}\n" if $opt->{debug};
	main::logger "DEBUG: Final Filename:     $prog->{filename}\n" if $opt->{debug};
	main::logger "DEBUG: Thumnail Filename:  $prog->{thumbfile}\n" if $opt->{debug};
	main::logger "DEBUG: Raw Mode: $opt->{raw}\n" if $opt->{debug};

	# Check path length is < 256 chars
	if ( length( $prog->{filepart} ) > 255 ) {
		main::logger("ERROR: Generated filename is too long, please use --fileprefix option to shorten it to below 250 characters ('$prog->{filepart}')\n\n");
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

	# remove old symlink
	unlink $symlink if -l $symlink;
	# Create symlink
	symlink $target, $symlink;
	main::logger "INFO: Created symlink from '$symlink' -> '$target'\n" if $opt->{verbose};
}



# Get time ago made available (x days y hours ago) from '2008-06-22T05:01:49Z' and specified epoch time
# Or, Get time in epoch from '2008-06-22T05:01:49Z' or '2008-06-22T05:01:49[+-]NN:NN' if no specified epoch time
sub get_time_string {
	$_ = shift;
	my $diff = shift;

	# extract $year $mon $mday $hour $min $sec $tzhour $tzmin
	my ($year, $mon, $mday, $hour, $min, $sec, $tzhour, $tzmin);
	($year, $mon, $mday, $hour, $min, $sec) = ($1, $2, $3, $4, $5, $6) if m{(\d\d\d\d)\-(\d\d)\-(\d\d)T(\d\d):(\d\d):(\d\d)};

	# positive TZ offset
	($tzhour, $tzmin) = ($1, $2) if m{\d\d\d\d\-\d\d\-\d\dT\d\d:\d\d:\d\d\+(\d\d):(\d\d)};
	# negative TZ offset
	($tzhour, $tzmin) = ($1*-1, $2*-1) if m{\d\d\d\d\-\d\d\-\d\dT\d\d:\d\d:\d\d\-(\d\d):(\d\d)};
	# ending in 'Z'
	($tzhour, $tzmin) = (0, 0) if m{\d\d\d\d\-\d\d\-\d\dT\d\d:\d\d:\d\dZ};

	main::logger "DEBUG: $_ = $year, $mon, $mday, $hour, $min, $sec, $tzhour, $tzmin\n" if $opt->{debug};
	# Sanity check date data
	return '' if $year < 1970 || $mon < 1 || $mon > 12 || $mday < 1 || $mday > 31 || $hour < 0 || $hour > 24 || $min < 0 || $min > 59 || $sec < 0 || $sec > 59 || $tzhour < -13 || $tzhour > 13 || $tzmin < -59 || $tzmin > 59;
	# Year cannot be > 2032 so limit accordingly :-/
	$year = 2038 if $year > 2038;
	# Calculate the seconds difference between epoch_now and epoch_datestring and convert back into array_time
	my $epoch = timegm($sec, $min, $hour, $mday, ($mon-1), ($year-1900), undef, undef, 0) - $tzhour*60*60 - $tzmin*60;
	my $rtn;
	if ( $diff ) {
		# Return time ago
		if ( $epoch < $diff ) {
			my @time = gmtime( $diff - ( timegm($sec, $min, $hour, $mday, ($mon-1), ($year-1900), undef, undef, 0) - $tzhour*60*60 - $tzmin*60 ) );
			# The time() func gives secs since 1970, gmtime is since 1900
			my $years = $time[5] - 70;
			$rtn = "$years years " if $years;
			$rtn .= "$time[7] days $time[2] hours ago";
			return $rtn;
		# Return time to go
		} elsif ( $epoch > $diff ) {
			my @time = gmtime( ( timegm($sec, $min, $hour, $mday, ($mon-1), ($year-1900), undef, undef, 0) - $tzhour*60*60 - $tzmin*60 ) - $diff );
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
		return timegm($sec, $min, $hour, $mday, ($mon-1), ($year-1900), undef, undef, 0) - $tzhour*60*60 - $tzmin*60;
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
		$image = main::request_url_retry( main::create_ua('get_iplayer'), $prog->{thumbnail}, 1);
		if (! $image ) {
			main::logger "ERROR: Thumbnail Download failed\n";
			return 1;
		} else {
			main::logger "INFO: Downloaded Thumbnail to '$file'\n";
		}

	} else {
		# Return if we have no url
		main::logger "INFO: Thumbnail not available\n" if $opt->{verbose};
		return 2;
	}

	# Write to file
	unlink($file);
	open( my $fh, "> $file" );
	binmode $fh;
	print $fh $image;
	close $fh;

	return 0;
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
		# May aswell set the web page metadata here if not set
		$prog->{web} = $prog->{pid} if ! $prog->{web};
		# Scrape the EMP web page and get playlist URL
		my $xml = main::request_url_retry( $ua, $url, 3 );
		if ( ! $xml ) {
			main::logger "\rERROR: Failed to get EMP page from BBC site\n\n";
			return;
		}
		# flatten
		$xml =~ s/\n/ /g;
		# Find playlist URL in various guises
		if ( $xml =~ m{<param\s+name="playlist"\s+value="(http.+?)"}i ) {
			$url = $1;
		# setPlaylist("http://www.bbc.co.uk/mundo/meta/dps/2009/06/emp/090625_video_festival_ms.emp.xml")
		# emp.setPlaylist("http://www.bbc.co.uk/learningzone/clips/clips/p_chin/bb/p_chin_ch_05303_16x9_bb.xml")
		} elsif ( $xml =~ m{setPlaylist\("(http.+?)"\)}i ) {
			$url = $1;
		# playlist = "http://www.bbc.co.uk/worldservice/meta/tx/flash/live/eneuk.xml";
		} elsif ( $xml =~ m{\splaylist\s+=\s+"(http.+?)";}i ) {
			$url = $1;
		# iplayer Programmes page format (also rewrite the pid)
		# href="http://www.bbc.co.uk/iplayer/episode/b00ldhj2"
		} elsif ( $xml =~ m{href="http://www.bbc.co.uk/iplayer/episode/(b0[a-z0-9]{6})"} ) {
			$prog->{pid} = $1;
			$url = 'http://www.bbc.co.uk/iplayer/playlist/'.$1;
		} elsif ( $url =~ m{^http.+.xml$} ) {
			# Just keep the url as it is probably already an xml playlist
		## playlist: "http://www.bbc.co.uk/iplayer/playlist/bbc_radio_one",
		#} elsif ( $xml =~ m{playlist: "http.+?playlist\/(\w+?)"}i ) {
		#	$prog->{pid} = $1;
		#	$url = 'http://www.bbc.co.uk/iplayer/playlist/'.$prog->{pid};
		}
		# URL decode url
		$url = main::url_decode( $url );
	# iPlayer LiveTV or PID
	} else {
		$url = 'http://www.bbc.co.uk/iplayer/playlist/'.$prog->{pid};
	}
	
	main::logger "INFO: iPlayer metadata URL = $url\n" if $opt->{verbose};
	#main::logger "INFO: Getting version pids for programme $prog->{pid}        \n" if ! $opt->{verbose};

	# send request
	my $xml = main::request_url_retry( $ua, $url, 3 );
	if ( ! $xml ) {
		main::logger "\rERROR: Failed to get version pid metadata from iplayer site\n\n";
		return 0;
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

	# Detect noItems or no programmes
	if ( $xml =~ m{<noItems\s+reason="noMedia"} || $xml !~ m{kind="(programme|radioProgramme)"} ) {
		main::logger "\rWARNING: No programmes are available for this pid\n";
		return 0;
	}

	# Get title
	# <title>Amazon with Bruce Parry: Episode 1</title>
	my ( $title, $prog_type );
	$title = $1 if $xml =~ m{<title>\s*(.+?)\s*<\/title>};

	# Get type
	$prog_type = 'tv' if grep /kind="programme"/, $xml;
	$prog_type = 'radio' if grep /kind="radioProgramme"/, $xml;

	# Split into <item kind="programme"> sections
	my $prev_version;
	for ( split /<item\s+kind="(radioProgramme|programme)"/, $xml ) {
		main::logger "DEBUG: Block: $_\n" if $opt->{debug};
		my ($verpid, $version);

		# Treat live streams accordingly
		# Live TV
		if ( m{\s+simulcast="true"} ) {
			$version = 'default';
			$verpid = "http://www.bbc.co.uk/emp/simulcast/".$1.".xml" if m{\s+live="true"\s+identifier="(.+?)"};
			main::logger "INFO: Using Live TV: $verpid\n" if $opt->{verbose} && $verpid;

		# Live/Non-live EMP tv/radio XML URL
		} elsif ( $prog->{pid} =~ /^http/i && $url =~ /^http.+xml$/ ) {
			$version = 'default';
			$verpid = $url;
			main::logger "INFO: Using Live/Non-live EMP tv/radio XML URL: $verpid\n" if $opt->{verbose} && $verpid;

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
			$version = 'default';
			main::logger "INFO: Using Live radio: $verpid\n" if $opt->{verbose} && $verpid;

		# Not Live standard TV and Radio
		} else {
			#  duration="3600" identifier="b00dp4xn" group="b00dlrc8" publisher="pips">
			$verpid = $1 if m{\s+duration=".*?"\s+identifier="(.+?)"};
			# <alternate id="default" />
			if ( m{<alternate\s+id="(.+?)"} ) {
				my $curr_version = lc($1);
				$version = lc($1);
				# if current version is already defined, add a numeric suffix
				if ( $prog->{verpids}->{$curr_version} ) {
					my $vercount = 1;
					# Search for the next free suffix
					while ( $prog->{verpids}->{$curr_version} ) {
						$vercount++;
						$curr_version = $version.$vercount;
					}
					$version = $curr_version;
				}
			# If this item has no version name then append $count to previous version found (a hack but I think it works)
			} else {
				# determine version name and trailing count (if any)
				$prev_version =~ m{^(.+)(\d*)$};
				my $prev_count = $2 || 1;
				$prev_version = $1 || 'default';
				$prev_count++;
				$version = $prev_version.$prev_count;
			}
			main::logger "INFO: Using Not Live standard TV and Radio: $verpid\n" if $opt->{verbose} && $verpid;
		}

		next if ! ($verpid && $version);
		$prev_version = $version;
		$prog->{verpids}->{$version} = $verpid;
		$prog->{durations}->{$version} = $1 if m{duration="(\d+?)"};
		main::logger "INFO: Version: $version, VersionPid: $verpid, Duration: $prog->{durations}->{$version}\n" if $opt->{verbose};  
	}

	# Add to prog hash
	$prog->{versions} = join ',', keys %{ $prog->{verpids} };
	$prog->{title} = decode_entities($title);
	return 0;
}



# get full episode metadata given pid and ua. Uses two different urls to get data
sub get_metadata {
	my $prog = shift;
	my $ua = shift;
	my $metadata;
	my $entry;
	my $prog_feed_url = 'http://feeds.bbc.co.uk/iplayer/episode/'; # $pid

	my ($name, $episode, $desc, $available, $channel, $expiry, $meddesc, $longdesc, $summary, $versions, $guidance, $prog_type, $categories, $player, $thumbnail, $seriesnum, $episodenum, $seriestitle, $episodetitle, $nametitle );

	# This URL works for all prog types:
	# http://www.bbc.co.uk/iplayer/playlist/${pid}

	# This URL only works for TV progs:
	# http://www.bbc.co.uk/iplayer/metafiles/episode/${pid}.xml

	# This URL works for tv/radio prog types:
	# http://www.bbc.co.uk/iplayer/widget/episodedetail/episode/${pid}/template/mobile/service_type/tv/

	# This URL works for tv/radio prog types (has long synopsis):
	# http://www.bbc.co.uk/programmes/{pid}.rdf

	# This URL works for tv/radio prog types:
	# http://feeds.bbc.co.uk/iplayer/episode/$pid

	# Works for all Verison PIDs to get the last/first broadcast dates
	# http://www.bbc.co.uk/programmes/<verpid>.rdf

	main::logger "DEBUG: Getting Metadata for $prog->{pid}:\n" if $opt->{debug};

	# Entry format
	#<?xml version="1.0" encoding="utf-8"?>                                      
	#<?xml-stylesheet href="http://www.bbc.co.uk/iplayer/style/rss.css" type="text/css"?>
	#<feed xmlns="http://www.w3.org/2005/Atom" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:media="http://search.yahoo.com/mrss/" xml:lang="en-GB">
	#  <title>BBC iPlayer - Episode Detail: Edith Bowman: 22/09/2008</title>                                                                          
	#  <subtitle>Sara Cox sits in for Edith with another Cryptic Randomizer.</subtitle>
	#  <updated>2008-09-29T10:59:45Z</updated>
	#  <id>tag:feeds.bbc.co.uk,2008:/iplayer/feed/episode/b00djtfh</id>
	#  <link rel="related" href="http://www.bbc.co.uk/iplayer" type="text/html" />
	#  <link rel="self" href="http://feeds.bbc.co.uk/iplayer/episode/b00djtfh" type="application/atom+xml" />
	#  <author>
	#    <name>BBC</name>
	#    <uri>http://www.bbc.co.uk</uri>
	#  </author>
	#  <entry>
	#    <title type="text">Edith Bowman: 22/09/2008</title>
	#    <id>tag:feeds.bbc.co.uk,2008:PIPS:b00djtfh</id>
	#    <updated>2008-09-15T01:28:36Z</updated>
	#    <summary>Sara Cox sits in for Edith with another Cryptic Randomizer.</summary>
	#    <content type="html">
	#      &lt;p&gt;
	#        &lt;a href=&quot;http://www.bbc.co.uk/iplayer/episode/b00djtfh?src=a_syn30&quot;&gt;
	#          &lt;img src=&quot;http://www.bbc.co.uk/iplayer/images/episode/b00djtfh_150_84.jpg&quot; alt=&quot;Edith Bowman: 22/09/2008&quot; /&gt;
	#        &lt;/a&gt;
	#      &lt;/p&gt;
	#      &lt;p&gt;
	#        Sara Cox sits in for Edith with movie reviews and great new music, plus another Cryptic Randomizer.
	#      &lt;/p&gt;
	#    </content>
	#    <link rel="alternate" href="http://www.bbc.co.uk/iplayer/episode/b00djtfh?src=a_syn31" type="text/html" title="Edith Bowman: 22/09/2008">
	#      <media:content medium="audio" duration="10800">
	#        <media:title>Edith Bowman: 22/09/2008</media:title>
	#        <media:description>Sara Cox sits in for Edith with movie reviews and great new music, plus another Cryptic Randomizer.</media:description>
	#        <media:player url="http://www.bbc.co.uk/iplayer/episode/b00djtfh?src=a_syn31" />
	#        <media:category scheme="urn:bbc:metadata:cs:iPlayerUXCategoriesCS" label="Entertainment">9100099</media:category>
	#        <media:category scheme="urn:bbc:metadata:cs:iPlayerUXCategoriesCS" label="Music">9100006</media:category>
	#        <media:category scheme="urn:bbc:metadata:cs:iPlayerUXCategoriesCS" label="Pop &amp; Chart">9200069</media:category>
	#        <media:rating scheme="urn:simple">adult</media:rating>
	#        <media:credit role="Production Department" scheme="urn:ebu">BBC Radio 1</media:credit>
	#        <media:credit role="Publishing Company" scheme="urn:ebu">BBC Radio 1</media:credit>
	#        <media:thumbnail url="http://www.bbc.co.uk/iplayer/images/episode/b00djtfh_86_48.jpg" width="86" height="48" />
	#        <media:thumbnail url="http://www.bbc.co.uk/iplayer/images/episode/b00djtfh_150_84.jpg" width="150" height="84" />
	#        <media:thumbnail url="http://www.bbc.co.uk/iplayer/images/episode/b00djtfh_178_100.jpg" width="178" height="100" />
	#        <media:thumbnail url="http://www.bbc.co.uk/iplayer/images/episode/b00djtfh_512_288.jpg" width="512" height="288" />
	#        <media:thumbnail url="http://www.bbc.co.uk/iplayer/images/episode/b00djtfh_528_297.jpg" width="528" height="297" />
	#        <media:thumbnail url="http://www.bbc.co.uk/iplayer/images/episode/b00djtfh_640_360.jpg" width="640" height="360" />
	#        <dcterms:valid>
	#          start=2008-09-22T15:44:20Z;
	#          end=2008-09-29T15:02:00Z;
	#          scheme=W3C-DTF
	#        </dcterms:valid>
	#      </media:content>
	#    </link>
	#    <link rel="self" href="http://feeds.bbc.co.uk/iplayer/episode/b00djtfh?format=atom" type="application/atom+xml" title="22/09/2008" />
	#    <link rel="related" href="http://www.bbc.co.uk/programmes/b006wks4/microsite" type="text/html" title="Edith Bowman" />
	#    <link rel="parent" href="http://feeds.bbc.co.uk/iplayer/programme_set/b006wks4" type="application/atom+xml" title="Edith Bowman" />
	#  </entry>
	#</feed>

	# Don't get metadata from this URL if the pid contains a full url (problem: this still tries for BBC iPlayer live channels)
	if ( $prog->{pid} !~ m{^http}i ) {
		$entry = main::request_url_retry($ua, $prog_feed_url.$prog->{pid}, 3, '', '');
		decode_entities($entry);
		main::logger "DEBUG: $prog_feed_url.$prog->{pid}:\n$entry\n\n" if $opt->{debug};
		# Flatten
		$entry =~ s|\n| |g;

		if ( $entry =~ m{<dcterms:valid>\s*start=.+?;\s*end=(.*?);} ) {
			$expiry = $1;
			$prog->{expiryrel} = Programme::get_time_string( $expiry, time() );
		}
		$available = $1 if $entry =~ m{<dcterms:valid>\s*start=(.+?);\s*end=.*?;};
		$prog_type = $1 if $entry =~ m{medium=\"(\w+?)\"};
		$prog_type = 'tv' if $prog_type eq 'video';
		$prog_type = 'radio' if $prog_type eq 'audio';
		$desc = $1 if $entry =~ m{<media:description>\s*(.*?)\s*<\/media:description>};
		$meddesc = '';
		$meddesc = $1 if $entry =~ m{<content type="html">\s*(.+?)\s*</content>};
		decode_entities( $meddesc );
		$meddesc =~ s|^.+<p>\s*(.+?)\s*</p>|$1|g;
		$meddesc =~ s|[\n\r]| |g;
		$summary = $1 if $entry =~ m{<summary>\s*(.*?)\s*</summary>};
		$guidance = $1 if $entry =~ m{<media:rating scheme="urn:simple">(.+?)<\/media:rating>};
		$player = $1 if $entry =~ m{<media:player\s*url=\"(.*?)\"\s*\/>};
		# Get all thumbnails into elements of thumbnailN with increasing width
		my %thumbnails;
		for ( split /<media:thumbnail/, $entry ) {
			my ( $url, $width );
			( $url, $width ) = ( $1, $2 ) if m{\s+url="\s*(http://.+?)\s*"\s+width="\s*(\d+)\s*"\s+height="\s*\d+\s*"};
			$thumbnails{ $width } = $url if $width && $url;
		}
		my $count = 1;
		for ( sort {$a <=> $b} keys %thumbnails ) {
			$prog->{ 'thumbnail'.$count } = $thumbnails{ $_ };
			$thumbnails{ $count } = $thumbnails{ $_ };
			$count++;
		}
		# Use the default cache thumbnail unless --thumbsize=NNN is used where NNN is either the width or thumbnail index number
		$thumbnail = $thumbnails{ $opt->{thumbsize} } if $thumbnails{ $opt->{thumbsize} };
		$name = $1 if $entry =~ m{<title\s+type="text">(.+?)[:<]};
		$episode = $1 if $entry =~ m{<title\s+type="text">.+?:\s+(.+?)<};
		$channel = $1 if $entry =~ m{<media:credit\s+role="Publishing Company"\s+scheme="urn:ebu">(.+?)<};

		# Get the title from the atom link refs only to determine the episode and series number
		$episodetitle = $1 if $entry =~ m{<link\s+rel="self"\s+href="http.+?/episode/.+?"\s+type="application/atom\+xml"\s+title="(.+?)"};
		$seriestitle = $1 if $entry =~ m{<link\s+rel="parent"\s+href="http.+?/programme_set/.+?"\s+type="application/atom\+xml"\s+title="(.+?)"};
		$nametitle = $1 if $entry =~ m{<link\s+rel="related"\s+href="http.+?/programmes/.+?"\s+type="text/html"\s+title="(.+?)"};

		my @cats;
		for (split /<media:category scheme=\".+?\"/, $entry) {
			push @cats, $1 if m{\s*label="(.+?)">\d+<\/media:category>};
		}
		$categories = join ',', @cats;
	}


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
	if ( $prog->{pid} =~ /^\w{8}$/ ) {
		$entry = main::request_url_retry($ua, 'http://www.bbc.co.uk/programmes/'.$prog->{pid}.'.rdf', 3, '', '');
		decode_entities($entry);
		main::logger "DEBUG: $prog_feed_url.$prog->{pid}:\n$entry\n\n" if $opt->{debug};
		# Flatten
		$entry =~ s|[\n\r]| |g;
		$longdesc = $1 if $entry =~ m{<po:long_synopsis>\s*(.+?)\s*</po:long_synopsis>};
	}


	# Get list of available modes for each version available
	# populate version pid metadata if we don't have it already
	$prog->get_verpids( $ua ) if keys %{ $prog->{verpids} } == 0;
	$versions = join ',', sort keys %{ $prog->{verpids} };
	my $modes;
	my $mode_sizes;
	my $first_broadcast;
	my $last_broadcast;
	# Do this for each version tried in this order (if they appeared in the content)
	for my $version ( sort keys %{ $prog->{verpids} } ) {
		# Set duration for this version if it is not defined
		$prog->{durations}->{$version} = $prog->{duration} if $prog->{duration} =~ /\d+/ && ! $prog->{durations}->{$version};
		# Try to get stream data for this version if it isn't already populated
		if ( not defined $prog->{streams}->{$version} ) {
			my %all_stream_data = get_stream_data($prog, $prog->{verpids}->{$version} );
			# Add streamdata to object
			$prog->{streams}->{$version} = \%all_stream_data;
		}
		$modes->{$version} = join ',', sort keys %{ $prog->{streams}->{$version} };
		# Estimate the file sizes for each mode
		my @sizes;
		for my $mode ( sort keys %{ $prog->{streams}->{$version} } ) {
			next if ( ! $prog->{durations}->{$version} ) || (! $prog->{streams}->{$version}->{$mode}->{bitrate} );
			push @sizes, sprintf( "%s=%.0fMB", $mode, $prog->{streams}->{$version}->{$mode}->{bitrate} * $prog->{durations}->{$version} / 8.0 / 1024.0 );
		}
		$mode_sizes->{$version} = join ',', @sizes;
		
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
		my ( $first, $last, $first_string, $last_string ) = ( 9999999999, 0, 'Never', 'Never' );

		# <po:(First|Repeat)Broadcast>
		#  <po:schedule_date rdf:datatype="http://www.w3.org/2001/XMLSchema#date">2009-06-06</po:schedule_date>
		#    <event:time>
		#        <timeline:Interval>
		#              <timeline:start rdf:datatype="http://www.w3.org/2001/XMLSchema#dateTime">2009-06-06T21:30:00+01:00</timeline:start>
		for ( split /<po:(First|Repeat)Broadcast>/, $rdf ) {
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
			if ( $epoch > $last ) {
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
		}
	}

	# Extract the seriesnum
	if ( "$prog->{name} $prog->{episode}" =~ m{Series (\d+)} ) {
		$prog->{seriesnum} = $1;
	} elsif ( $seriestitle =~ m{Series (\d+)} ) {
		$prog->{seriesnum} = $1;
	}

	# Extract the episode num
	if ( "$prog->{name} $prog->{episode}" =~ m{Episode (\d+)} ) {
		$prog->{episodenum} = $1;
	} elsif ( $prog->{episode} =~ m{^(\d+)\.\s+} ) {
		$prog->{episodenum} = $1;
	} elsif ( $episodetitle =~ m{^(\d+)\.\s+} ) {
		$prog->{episodenum} = $1;
	}

	# Fill in from cache if not got from metadata
	$prog->{name} 		= $name || $prog->{name};
	$prog->{episode} 	= $episode || $prog->{episode} || $prog->{name};
	$prog->{type}		= $prog_type || $prog->{type};
	$prog->{channel}	= $channel || $prog->{channel};
	$prog->{expiry}		= $expiry || $prog->{expiry};
	$prog->{versions}	= $versions;
	$prog->{guidance}	= $guidance || $prog->{guidance};
	$prog->{categories}	= $categories || $prog->{categories};
	$prog->{desc}		= $longdesc || $meddesc || $desc || $prog->{desc} || $summary;
	$prog->{player}		= $player;
	$prog->{thumbnail}	= $thumbnail || $prog->{thumbnail};
	$prog->{modes}		= $modes;
	$prog->{modesizes}	= $mode_sizes;
	return 0;
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
		1	=> '_86_48.jpg',
		2	=> '_150_84.jpg',
		3	=> '_178_100.jpg',
		4	=> '_512_288.jpg',
		5	=> '_528_297.jpg',
		6	=> '_640_360.jpg',
		7	=> '_832_468.jpg',
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



sub get_stream_data_cdn {
	my ( $data, $mattribs, $mode, $streamer, $ext ) = ( @_ );

	# Public Non-Live EMP Video without auth
	#if ( $cattribs->{kind} eq 'akamai' && $cattribs->{identifier} =~ /^public\// ) {
	#	$data{$mode}{bitrate} = 480; # ??
	#	$data{$mode}{swfurl} = "http://news.bbc.co.uk/player/emp/2.11.7978_8433/9player.swf";
	# Live TV, Live EMP Video or Non-public EMP video
	#} elsif ( $cattribs->{kind} eq 'akamai' ) {
	#	$data{$mode}{bitrate} = 480; # ??

	my $count = 1;
	for my $cattribs ( @{ $mattribs->{connections} } ) {
		# Common attributes
		# swfurl = Default iPlayer swf version
		my $conn = {
			swfurl		=> "http://www.bbc.co.uk/emp/10player.swf?revision=14200_14320",
			ext		=> $ext,
			streamer	=> $streamer,
			bitrate		=> $mattribs->{bitrate},
			server		=> $cattribs->{server},
			identifier	=> $cattribs->{identifier},
			authstring	=> $cattribs->{authString},
			priority	=> $cattribs->{priority},
		};

		# Akamai CDN
		if ( $cattribs->{kind} eq 'akamai' ) {
			# Set the live flag if this is not an ondemand stream
			$conn->{live} = 1 if $cattribs->{application} =~ /^live/;
			# Default appication is 'ondemand'
			$cattribs->{application} = 'ondemand' if ! $cattribs->{application};

			# if the authString is not set and this is a live (i.e. simulcast) then try to get an authstring
			# Maybe should this be general for all CDNs?
			if ( ! $cattribs->{authString} ) {
				# Build URL
				my $media_stream_live_prefix = 'http://www.bbc.co.uk/mediaselector/4/gtis/stream/';
				my $url = ${media_stream_live_prefix}."?server=$cattribs->{server}&identifier=$cattribs->{identifier}&kind=$cattribs->{kind}&application=$cattribs->{application}";
				my $xml = main::request_url_retry( main::create_ua(), $url, 3, undef, undef, 1 );
				main::logger "\n$xml\n" if $opt->{debug};
				$cattribs->{authString} = $1 if $xml =~ m{<token>(.+?)</token>};
				$conn->{authstring} = $cattribs->{authString};
			}

			if ( $cattribs->{authString} ) {
				### ??? live and Live TV, Live EMP Video or Non-public EMP video:
				$conn->{playpath} = "$cattribs->{identifier}?auth=$cattribs->{authString}&aifp=v001";
			} else {
				$conn->{playpath} = $cattribs->{identifier};
			}
			if ( $cattribs->{authString} ) {
				$conn->{streamurl} = "rtmp://$cattribs->{server}:1935/$cattribs->{application}?_fcs_vhost=$cattribs->{server}&auth=$cattribs->{authString}&aifp=v001&slist=$cattribs->{identifier}";
			} else {
				$conn->{streamurl} = "rtmp://$cattribs->{server}:1935/$cattribs->{application}?_fcs_vhost=$cattribs->{server}&undefined";
			}
			# Remove offending mp3/mp4: at the start of the identifier (don't remove in stream url)
			$cattribs->{identifier} =~ s/^mp[34]://;
			if ( $cattribs->{authString} ) {
				$conn->{application} = "$cattribs->{application}?_fcs_vhost=$cattribs->{server}&auth=$cattribs->{authString}&aifp=v001&slist=$cattribs->{identifier}";
			} else {
				$conn->{application} = "$cattribs->{application}?_fcs_vhost=$cattribs->{server}&undefined";
			}
			# Port 1935? for live?
			$conn->{tcurl} = "rtmp://$cattribs->{server}:80/$conn->{application}";

		# Limelight CDN
		} elsif ( $cattribs->{kind} eq 'limelight' ) {
			decode_entities( $cattribs->{authString} );
			$conn->{playpath} = "$cattribs->{identifier}?$cattribs->{authString}";
			# Remove offending mp3/mp4: at the start of the identifier (don't remove in stream url)
			### Not entirely sure if this is even required for video modes either??? - not reqd for aac and low
			# $conn->{playpath} =~ s/^mp[34]://g;
			$conn->{streamurl} = "rtmp://$cattribs->{server}:1935/ondemand?_fcs_vhost=$cattribs->{server}&auth=$cattribs->{authString}&aifp=v001&slist=$cattribs->{identifier}";
			$conn->{application} = $cattribs->{application};
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

		# Unknown CDN
		} else {
			new_stream_report($mattribs, $cattribs) if $opt->{verbose};
			next;
		}

		get_stream_set_type( $conn, $mattribs, $cattribs );

                # Add to data structure
                # Find the next free mode name
                while ( defined $data->{$mode.$count} ) {
                        $count++;
                };
                $data->{$mode.$count} = $conn;

		# Add to data structure - including priority
		#$count = 1;
		#$count = $cattribs->{priority} if defined $cattribs->{priority};
		# Find the next free mode name
		#while ( defined $data->{ sprintf('%s%03d', $mode, $count) } ) {
		#	$count++;
		#};
		#$data->{ sprintf('%s%03d', $mode, $count) } = $conn;
		
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
	my %data;
	my $media_stream_data_prefix = 'http://www.bbc.co.uk/mediaselector/4/mtis/stream/'; # $verpid
	my $media_stream_live_prefix = 'http://www.bbc.co.uk/mediaselector/4/gtis/stream/'; # $verpid

	# Setup user agent with redirection enabled
	my $ua = main::create_ua();
	$opt->{quiet} = 0 if $opt->{streaminfo};

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

	# Live simulcast verpid: http://www.bbc.co.uk/emp/simulcast/bbc_one_london.xml
	} elsif ( $verpid =~ /http:/ ) {
		$xml = main::request_url_retry( $ua, $verpid, 3, undef, undef, 1 );
		main::logger "\n$xml\n" if $opt->{debug};
		@medias = parse_metadata( $xml );

	# Could also use Javascript based one: 'http://www.bbc.co.uk/iplayer/mediaselector/4/js/stream/$verpid
	} else {
		$xml = main::request_url_retry( $ua, $media_stream_data_prefix.$verpid, 3, undef, undef, 1 );
		main::logger "\n$xml\n" if $opt->{debug};
		@medias = parse_metadata( $xml );
	}

	# Parse and dump structure
	my $mode;
	for my $mattribs ( @medias ) {
		
		# New iphone stream
		if ( $mattribs->{service} eq 'iplayer_streaming_http_mp4' ) {
			# Fix/remove some audio stream attribs
			if ( $prog->{type} eq 'radio' ) {
				$mattribs->{bitrate} = 128;
				delete $mattribs->{width};
				delete $mattribs->{height};
			}
			get_stream_data_cdn( \%data, $mattribs, 'iphone', 'iphone', 'mov' );
		
		
		# flashhd modes
		} elsif (	$mattribs->{kind} eq 'video' &&
				$mattribs->{type} eq 'video/mp4' &&
				$mattribs->{encoding} eq 'h264'
		) {
			# Determine classifications of modes based mainly on bitrate

			# flashhd modes
			if ( $mattribs->{bitrate} > 3000 ) {
				get_stream_data_cdn( \%data, $mattribs, 'flashhd', 'rtmp', 'mp4' );

			# flashvhigh modes
			} elsif ( $mattribs->{bitrate} > 1200 ) {
				get_stream_data_cdn( \%data, $mattribs, 'flashvhigh', 'rtmp', 'mp4' );

			# flashhigh modes
			} elsif ( $mattribs->{bitrate} > 700 ) {
				get_stream_data_cdn( \%data, $mattribs, 'flashhigh', 'rtmp', 'mp4' );

			# flashstd modes
			} elsif ( $mattribs->{bitrate} > 400 && $mattribs->{width} >= 500 ) {
				get_stream_data_cdn( \%data, $mattribs, 'flashstd', 'rtmp', 'mp4' );

			}
			
		# flashnormal modes (also live and EMP modes)
		} elsif (	$mattribs->{kind} eq 'video' &&
				$mattribs->{type} eq 'video/x-flv' &&
				$mattribs->{encoding} eq 'vp6'
		) {
			get_stream_data_cdn( \%data, $mattribs, 'flashnormal', 'rtmp', 'avi' );

		# flashlow modes
		} elsif (	$mattribs->{kind} eq 'video' &&
				$mattribs->{type} eq 'video/x-flv' &&
				$mattribs->{encoding} eq 'spark'
		) {
			get_stream_data_cdn( \%data, $mattribs, 'flashlow', 'rtmp', 'avi' );

		# flashnormal modes without encoding specifed - assume vp6
		} elsif (	$mattribs->{kind} eq 'video' &&
				$mattribs->{type} eq 'video/x-flv'
		) {
			$mattribs->{encoding} = 'vp6';
			get_stream_data_cdn( \%data, $mattribs, 'flashnormal', 'rtmp', 'avi' );

		# n95 modes
		} elsif (	$mattribs->{kind} eq 'video' &&
				$mattribs->{type} eq 'video/mpeg' &&
				$mattribs->{encoding} eq 'h264'
		) {
			# n95_wifi modes
			if ( $mattribs->{bitrate} > 140 ) {
				$mattribs->{width} = $mattribs->{width} || 320;
				$mattribs->{height} = $mattribs->{height} || 176;
				get_stream_data_cdn( \%data, $mattribs, 'n95_wifi', '3gp', '3gp' );

			# n95_3g modes
			} else {
				$mattribs->{width} = $mattribs->{width} || 176;
				$mattribs->{height} = $mattribs->{height} || 96;
				get_stream_data_cdn( \%data, $mattribs, 'n95_3g', '3gp', '3gp' );
			}

		# WMV drm modes - still used?
		} elsif (	$mattribs->{kind} eq 'video' &&
				$mattribs->{type} eq 'video/wmv'
		) {
			$mattribs->{width} = $mattribs->{width} || 320;
			$mattribs->{height} = $mattribs->{height} || 176;
			get_stream_data_cdn( \%data, $mattribs, 'mobile_wmvdrm', 'http', 'wmv' );
			# Also DRM (same data - just remove _mobile from href and identfier)
			$mattribs->{width} = 672;
			$mattribs->{height} = 544;
			get_stream_data_cdn( \%data, $mattribs, 'wmvdrm', 'http', 'wmv' );
			$data{wmvdrm}{identifier} =~ s/_mobile//g;
			$data{wmvdrm}{streamurl} =~ s/_mobile//g;

		# flashaac modes
		} elsif (	$mattribs->{kind} eq 'audio' &&
				$mattribs->{type} eq 'audio/mp4'
				# This also catches worldservice who happen not to set the encoding type
				# && $mattribs->{encoding} eq 'aac'
		) {
			# flashaachigh
			if (  $mattribs->{bitrate} >= 192 ) {
				get_stream_data_cdn( \%data, $mattribs, 'flashaachigh', 'rtmp', 'aac' );

			# flashaacstd
			} elsif ( $mattribs->{bitrate} >= 96 ) {
				get_stream_data_cdn( \%data, $mattribs, 'flashaacstd', 'rtmp', 'aac' );

			# flashaaclow
			} else {
				get_stream_data_cdn( \%data, $mattribs, 'flashaaclow', 'rtmp', 'aac' );
			}

		# flashaudio modes
		} elsif (	$mattribs->{kind} eq 'audio' &&
				$mattribs->{type} eq 'audio/mpeg'
				#&& $mattribs->{encoding} eq 'mp3'
		) {
			get_stream_data_cdn( \%data, $mattribs, 'flashaudio', 'rtmp', 'mp3' );

		# RealAudio modes
		} elsif (	$mattribs->{type} eq 'audio/real' &&
				$mattribs->{encoding} eq 'real'
		) {
			get_stream_data_cdn( \%data, $mattribs, 'realaudio', 'rtsp', 'mp3' );

		# wma modes
		} elsif (	$mattribs->{type} eq 'audio/wma' &&
				$mattribs->{encoding} eq 'wma'
		) {
			get_stream_data_cdn( \%data, $mattribs, 'wma', 'mms', 'wma' );

		# aac3gp modes
		} elsif (	$mattribs->{kind} eq '' &&
				$mattribs->{type} eq 'audio/mp4' &&
				$mattribs->{encoding} eq 'aac'
		) {
			# Not sure how to stream these yet
			#$mattribs->{kind} = 'sis';
			#get_stream_data_cdn( \%data, $mattribs, 'aac3gp', 'http', 'aac' );

		# Subtitles modes
		} elsif (	$mattribs->{kind} eq 'captions' &&
				$mattribs->{type} eq 'application/ttaf+xml'
		) {
			get_stream_data_cdn( \%data, $mattribs, 'subtitles', 'http', 'srt' );

		# Catch unknown
		} else {
			new_stream_report($mattribs, undef) if $opt->{verbose};
		}	
	}

	# Report modes found
	if ( $opt->{verbose} ) {
		main::logger "INFO: Found mode $_: $data{$_}{type}\n" for sort keys %data;
	}

	# Return a hash with media => url if '' is specified - otherwise just the specified url
	if ( ! $media ) {
		return %data;
	} else {
		# Make sure this hash exists before we pass it back...
		$data{$media}{exists} = 0 if not defined $data{$media};
		return $data{$media};
	}
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
use POSIX qw(mkfifo);
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
		'bbc_one'			=> 'BBC One',
		'bbc_two'			=> 'BBC Two',
		'bbc_three'			=> 'BBC Three',
		'bbc_four'			=> 'BBC Four',
		'cbbc'				=> 'CBBC',
		'cbeebies'			=> 'CBeebies',
		'bbc_news24'			=> 'BBC News 24',
		'bbc_parliament'		=> 'BBC Parliament',
		'bbc_one_northern_ireland'	=> 'BBC One Northern Ireland',
		'bbc_one_scotland'		=> 'BBC One Scotland',
		'bbc_one_wales'			=> 'BBC One Wales',
		'bbc_webonly'			=> 'BBC Web Only',
		'bbc_hd'			=> 'BBC HD',
		'bbc_alba'			=> 'BBC Alba',
		'categories/news/tv'		=> 'BBC News',
		'categories/sport/tv'		=> 'BBC Sport',
		'categories/signed'		=> 'Signed',
		'categories/audiodescribed'	=> 'Audio Described',
		'popular/tv'			=> 'Popular',
		'highlights/tv'			=> 'Highlights',
	};
}


# Class cmdline Options
sub opt_format {
	return {
		tvmode		=> [ 1, "tvmode|vmode=s", 'Recording', '--tvmode <mode>,<mode>,...', "TV Recoding modes: iphone,rtmp,flashhd,flashvhigh,flashhigh,flashstd,flashnormal,flashlow,n95_wifi (default: iphone,flashhigh,flashstd,flashnormal)"],
		outputtv	=> [ 1, "outputtv=s", 'Output', '--outputtv <dir>', "Output directory for tv recordings"],
		vlc		=> [ 0, "vlc=s", 'External Program', '--vlc <path>', "Location of vlc or cvlc binary"],
		rtmptvopts	=> [ 1, "rtmp-tv-opts|rtmptvopts=s", 'Recording', '--rtmp-tv-opts <options>', "Add custom options to flvstreamer/rtmpdump for tv"],
	};
}



# Method to return optional list_entry format
sub optional_list_entry_format {
	my $prog = shift;
	return ", $prog->{channel}, $prog->{categories}, $prog->{versions}";
}



# Returns the modes to try for this prog type
sub modelist {
	my $prog = shift;
	my $mlist = $opt->{tvmode} || $opt->{modes};
	
	# Defaults
	if ( ! $mlist ) {
		if ( ! main::exists_in_path('flvstreamer') ) {
			main::logger "WARNING: Not using flash modes since flvstreamer/rtmpdump is not found\n" if $opt->{verbose};
			$mlist = 'iphone';
		} else {
			$mlist = 'iphone,flashhigh,flashstd,flashnormal';
		}
	}
	# Deal with BBC TV fallback modes and expansions
	# Valid modes are iphone,rtmp,flashhigh,flashnormal,flashlow,n95_wifi
	# 'rtmp' or 'flash' => 'flashhigh,flashnormal'
	$mlist = main::expand_list($mlist, 'best', 'flashhd,flashvhigh,flashhigh,iphone,flashstd,flashnormal,flashlow');
	$mlist = main::expand_list($mlist, 'flash', 'flashhigh,flashstd,flashnormal');
	$mlist = main::expand_list($mlist, 'rtmp', 'flashhigh,flashstd,flashnormal');

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
		my $ua = main::create_ua();
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
		
	# If this is an iPlayer pid (not a pid page on BBC programmes site)
	if ( $prog->{pid} =~ m{^([pb]0[a-z0-9]{6})$} ) {
		# extract b??????? format from any URL containing it
		$prog->{pid} = $1;

	} elsif ( $prog->{pid} =~ m{^http.+\/([pb]0[a-z0-9]{6})\/?.*$} && $prog->{pid} !~ m{/programmes/} ) {
		# extract b??????? format from any URL containing it
		$prog->{pid} = $1;

	# If this is a BBC *iPlayer* Live channel
	# e.g. http://www.bbc.co.uk/iplayer/playlive/bbc_radio_fourfm/
	} elsif ( $prog->{pid} =~ m{http.+bbc\.co\.uk/iplayer}i ) {
		# Remove extra URL path for URLs like 'http://www.bbc.co.uk/iplayer/playlive/bbc_one_london/' or 'http://www.bbc.co.uk/iplayer/tv/bbc_one'
		$prog->{pid} =~ s/^http.+\/(.+?)\/?$/$1/g;
	# Else this is an embedded media player URL (live or otherwise)
	} elsif ($prog->{pid} =~ m{^http}i ) {
		# Just leave the URL as the pid
	}
}



# Usage: Programme::tv->get_links( \%prog, 'tv' );
# Uses: %{ channels() }, \%prog
sub get_links {
	shift; # ignore obj ref
	my $progref = shift;
	my $prog_type = shift;
	# Hack to get correct 'channels' method because this methods is being shared with Programme::radio
	my %channels = %{ main::progclass($prog_type)->channels_filtered() };
	my $channel_feed_url = 'http://feeds.bbc.co.uk/iplayer'; # /$channel/list
	my $bbc_prog_page_prefix = 'http://www.bbc.co.uk/programmes'; # /$pid
	my $thumbnail_prefix = 'http://www.bbc.co.uk/iplayer/images/episode';

	my $xml;
	my $feed_data;
	my $res;
	main::logger "INFO: Getting $prog_type Index Feeds\n";
	# Setup User agent
	my $ua = main::create_ua();

	# Download index feed
	# Sort feeds so that category based feeds are done last - this makes sure that the channels get defined correctly if there are dups
	my @channel_list;
	push @channel_list, grep !/(categor|popular|highlights)/, keys %channels;
	push @channel_list, grep  /categor/, keys %channels;
	push @channel_list, grep  /popular/, keys %channels;
	push @channel_list, grep  /highlights/, keys %channels;
	for ( @channel_list ) {

		my $url = "${channel_feed_url}/$_/list/limit/400";
		main::logger "DEBUG: Getting feed $url\n" if $opt->{verbose};
		$xml = main::request_url_retry($ua, $url, 3, '.', "WARNING: Failed to get programme index feed for $_ from iplayer site\n");
		main::logger "INFO: Got ".(grep /<entry/, split /\n/, $xml)." programmes\n" if $opt->{verbose};
		decode_entities($xml);
		
		# Feed as of August 2008
		#	 <entry>
		#	   <title type="text">Bargain Hunt: Series 18: Oswestry</title>
		#	   <id>tag:feeds.bbc.co.uk,2008:PIPS:b0088jgs</id>
		#	   <updated>2008-07-22T00:23:50Z</updated>
		#	   <content type="html">
		#	     &lt;p&gt;
		#	       &lt;a href=&quot;http://www.bbc.co.uk/iplayer/episode/b0088jgs?src=a_syn30&quot;&gt;
		#		 &lt;img src=&quot;http://www.bbc.co.uk/iplayer/images/episode/b0088jgs_150_84.jpg&quot; alt=&quot;Bargain Hunt: Series 18: Oswestry&quot; /&gt;
		#	       &lt;/a&gt;
		#	     &lt;/p&gt;
		#	     &lt;p&gt;
		#	       The teams are at an antiques fair in Oswestry showground. Hosted by Tim Wonnacott.
		#	     &lt;/p&gt;
		#	   </content>
		#	   <category term="Factual" />
		#          <category term="Guidance" />
		#	   <category term="TV" />
		#	   <link rel="via" href="http://www.bbc.co.uk/iplayer/episode/b0088jgs?src=a_syn30" type="text/html" title="Bargain Hunt: Series 18: Oswestry" />
		#       </entry>
		#

		### New Feed
		#  <entry>
		#    <title type="text">House of Lords: 02/07/2008</title>
		#    <id>tag:bbc.co.uk,2008:PIPS:b00cd5p7</id>
		#    <updated>2008-06-24T00:15:11Z</updated>
		#    <content type="html">
		#      <p>
		#	<a href="http://www.bbc.co.uk/iplayer/episode/b00cd5p7?src=a_syn30">
		#	  <img src="http://www.bbc.co.uk/iplayer/images/episode/b00cd5p7_150_84.jpg" alt="House of Lords: 02/07/2008" />
		#	</a>
		#      </p>
		#      <p>
		#	House of Lords, including the third reading of the Health and Social Care Bill. 1 July.
		#      </p>
		#    </content>
		#    <category term="Factual" scheme="urn:bbciplayer:category" />
		#    <link rel="via" href="http://www.bbc.co.uk/iplayer/episode/b00cd5p7?src=a_syn30" type="application/atom+xml" title="House of Lords: 02/07/2008">
		#    </link>
		#  </entry>

		### Newer feed (Sept 2009)
		#  <entry>
		#    <title type="text">BBC Proms: 2009: Prom 65: Gustav Mahler Jugend Orchester</title>
		#    <id>tag:feeds.bbc.co.uk,2008:PIPS:b00mgw03</id>
		#    <updated>2009-09-05T03:29:07Z</updated>
		#    <content type="html">
		#      &lt;p&gt;
		#        &lt;a href=&quot;http://www.bbc.co.uk/iplayer/episode/b00mgw03/BBC_Proms_2009_Prom_65_Gustav_Mahler_Jugend_Orchester/&quot;&gt;
		#          &lt;img src=&quot;http://node1.bbcimg.co.uk/iplayer/images/episode/b00mgw03_150_84.jpg&quot; alt=&quot;BBC Proms: 2009: Prom 65: Gustav Mahler Jugend Orchester&quot; /&gt;
		#        &lt;/a&gt;
		#      &lt;/p&gt;
		#      &lt;p&gt;
		#        The Gustav Mahler Youth Orchestra perform works by Mahler, Richard Strauss and Ligeti.
		#      &lt;/p&gt;
		#    </content>
		#    <category term="Music" />
		#    <category term="Classical" />
		#    <category term="TV" />
		#    <link rel="alternate" href="http://www.bbc.co.uk/iplayer/episode/b00mgw03/BBC_Proms_2009_Prom_65_Gustav_Mahler_Jugend_Orchester/" type="text/html" title="BBC Proms: 2009: Prom 65: Gustav Mahler Jugend Orchester">
		#      <media:content>
		#        <media:thumbnail url="http://node1.bbcimg.co.uk/iplayer/images/episode/b00mgw03_150_84.jpg" width="150" height="84" />
		#      </media:content>
		#    </link>
		#    <link rel="self" href="http://feeds.bbc.co.uk/iplayer/episode/b00mgw03" type="application/atom+xml" title="Prom 65: Gustav Mahler Jugend Orchester" />
		#    <link rel="related" href="http://www.bbc.co.uk/programmes/b007v097/microsite" type="text/html" title="BBC Proms" />
		#  </entry>


		# Parse XML

		# get list of entries within <entry> </entry> tags
		my @entries = split /<entry>/, $xml;
		# Discard first element == header
		shift @entries;

		foreach my $entry (@entries) {
			my ( $title, $name, $episode, $desc, $pid, $available, $channel, $duration, $thumbnail, $version, $guidance );
			
			my $entry_flat = $entry;
			$entry_flat =~ s/\n/ /g;

			# <id>tag:bbc.co.uk,2008:PIPS:b008pj3w</id>
			$pid = $1 if $entry =~ m{<id>.*PIPS:(.+?)</id>};

			# <title type="text">Richard Hammond's Blast Lab: Series Two: Episode 11</title>
			# <title type="text">Skate Nation: Pro-Skate Camp</title>
			$title = $1 if $entry =~ m{<title\s*.*?>\s*(.*?)\s*</title>};

			# determine name and episode from title
			( $name, $episode ) = Programme::bbciplayer::split_title( $title );
			# This is not the availability!
			# <updated>2008-06-22T05:01:49Z</updated>
			#$available = Programme::get_time_string( $1, time() ) if $entry =~ m{<updated>(\d{4}\-\d\d\-\d\dT\d\d:\d\d:\d\d.).*?</updated>};

			#<p>    House of Lords, including the third reading of the Health and Social Care Bill. 1 July.   </p>    </content>
			$desc = $1 if $entry =~ m{<p>\s*(.*?)\s*</p>\s*</content>};
			# Remove unwanted html tags
			$desc =~ s!</?(br|b|i|p|strong)\s*/?>!!gi;

			# Parse the categories into hash
			# <category term="Factual" />
			my @category;
			for my $line ( grep /<category/, (split /\n/, $entry) ) {
				push @category, $1 if $line =~ m{<category\s+term="(.+?)"};
			}
			# strip commas - they confuse sorting and spliting later
			s/,//g for @category;

			# Extract channel
			$channel = $channels{$_};

			main::logger "DEBUG: '$pid, $name - $episode, $channel'\n" if $opt->{debug};

			# Merge and Skip if this pid is a duplicate
			if ( defined $progref->{$pid} ) {
				main::logger "WARNING: '$pid, $progref->{$pid}->{name} - $progref->{$pid}->{episode}, $progref->{$pid}->{channel}' already exists (this channel = $channel)\n" if $opt->{verbose};
				# Since we use the 'Signed' (or 'Audio Described') channel to get sign zone/audio described data, merge the categories from this entry to the existing entry
				if ( $progref->{$pid}->{categories} ne join(',', sort @category) ) {
					my %cats;
					$cats{$_} = 1 for ( @category, split /,/, $progref->{$pid}->{categories} );
					main::logger "INFO: Merged categories for $pid from $progref->{$pid}->{categories} to ".join(',', sort keys %cats)."\n" if $opt->{verbose};
					$progref->{$pid}->{categories} = join(',', sort keys %cats);
				}

				# If this a popular or highlights programme then add these tags to categories
				my %cats;
				$cats{$_} = 1 for ( @category, split /,/, $progref->{$pid}->{categories} );
				$cats{Popular} = 1 if $channel eq 'Popular';
				$cats{Highlights} = 1 if $channel eq 'Highlights';
				$progref->{$pid}->{categories} = join(',', sort keys %cats);

				# If this is a dupicate pid and the channel is now Signed then both versions are available
				$version = 'signed' if $channel eq 'Signed';
				$version = 'audiodescribed' if $channel eq 'Audio Described';
				# Add version to versions for existing prog
				$progref->{$pid}->{versions} = join ',', main::make_array_unique_ordered( (split /,/, $progref->{$pid}->{versions}), $version );
				next;
			}

			# Set guidance based on category
			$guidance = 'Yes' if grep /guidance/i, @category;

			# Check for signed-only or audiodescribed-only version from Channel
			if ( $channel eq 'Signed' ) {
				$version = 'signed';
			} elsif ( $channel eq 'Audio Described' ) {
				$version = 'audiodescribed';
			} else {
				$version = 'default';
			}

			# Default to 150px width thumbnail;
			my $thumbsize = $opt->{thumbsizecache} || 150;

			# build data structure
			$progref->{$pid} = main::progclass($prog_type)->new(
				'pid'		=> $pid,
				'name'		=> $name,
				'versions'	=> $version,
				'episode'	=> $episode,
				'desc'		=> $desc,
				'guidance'	=> $guidance,
				'available'	=> 'Unknown',
				'duration'	=> 'Unknown',
				'thumbnail'	=> "${thumbnail_prefix}/${pid}".Programme::bbciplayer->thumb_url_suffixes->{ $thumbsize },
				'channel'	=> $channel,
				'categories'	=> join(',', sort @category),
				'type'		=> $prog_type,
				'web'		=> "${bbc_prog_page_prefix}/${pid}.html",
			);
		}
	}
	main::logger "\n";
	return 0;
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
	if ( $mode =~ /^flash/ && ! main::exists_in_path('flvstreamer')) {
		main::logger "WARNING: Required program flvstreamer/rtmpdump does not exist (see http://linuxcentre.net/getiplayer/installation and http://linuxcentre.net/getiplayer/download)\n";
		return 'next';
	}
	# Force raw mode if ffmpeg is not installed
	if ( $mode =~ /^flash/ && ! main::exists_in_path('ffmpeg')) {
		main::logger "\nWARNING: ffmpeg does not exist - not converting flv file\n";
		$opt->{raw} = 1;
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


	# Determine the correct filenames for this recording
	if ( $prog->generate_filenames( $ua, $prog->file_prefix_format() ) ) {
		# Create symlink if required
		$prog->create_symlink( $prog->{symlink}, $prog->{filename}) if $opt->{symlink};
		return 'skip';
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
		$prog->download_subtitles( $ua, $subfile );
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

	# Rename the subtitle file accordingly
	move($subfile, $subfile_done) if $opt->{subtitles} && -f $subfile;

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
	
	$suburl = $prog->{streams}->{$prog->{version}}->{subtitles1}->{streamurl};
	# Return if we have no url
	if (! $suburl) {
		main::logger "INFO: Subtitles not available\n";
		return 2;
	}

	main::logger "INFO: Getting Subtitles from $suburl\n" if $opt->{verbose};

	# Open subs file
	unlink($file);
	open( my $fh, "> $file" );
	binmode $fh;

	# Download subs
	$subs = main::request_url_retry($ua, $suburl, 2);
	if (! $subs ) {
		main::logger "ERROR: Subtitle Download failed\n";
		return 1;
	} else {
		# Dump raw subs into a file if required
		if ( $opt->{subsraw} ) {
			unlink("$prog->{dir}/$prog->{fileprefix}.ttxt");
			main::logger "INFO: 'Downloading Raw Subtitles to $prog->{dir}/$prog->{fileprefix}.ttxt'\n";
			open( my $fhraw, "> $prog->{dir}/$prog->{fileprefix}.ttxt");
			binmode $fhraw;
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
	my $count = 1;
	my @lines = grep /<p\s.*begin=/, split /\n/, $subs;
	for ( @lines ) {
		my ( $begin, $end, $sub );
		# Remove <br /> elements
		s|<br.*?>| |g;
		# Remove >1 spaces
		s|\s{2,}| |g;
		( $begin, $end, $sub ) = ( $1, $2, $3 ) if m{<p\s+.*begin="(.+?)".+end="(.+?)".*?>(.+?)<\/p>};
		if ($begin && $end && $sub ) {
			# Format numerical field widths
			$begin = sprintf( '%02d:%02d:%02d,%02d', split /[:\.,]/, $begin );
			$end = sprintf( '%02d:%02d:%02d,%02d', split /[:\.,]/, $end );
			# Add trailing zero if ttxt format only uses hundreths of a second
			$begin .= '0' if $begin =~ m{,\d\d$};
			$end .= '0' if $end =~ m{,\d\d$};
			if ($opt->{suboffset}) {
				$begin = main::subtitle_offset( $begin, $opt->{suboffset} );
				$end = main::subtitle_offset( $end, $opt->{suboffset} );
			}
			# Separate individual lines based on <span>s
			$sub =~ s|<span.*?>(.*?)</span>|\n$1\n|g;
			if ($sub =~ m{\n}) {
				chomp($sub);
				$sub =~ s|^\n?|- |;
				$sub =~ s|\n+|\n- |g;
			}
			decode_entities($sub);
			# Write to file
			print $fh "$count\n";
			print $fh "$begin --> $end\n";
			print $fh "$sub\n\n";
			$count++;
		}
	}	
	close $fh;

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
sub index_max { return 19999 };
sub channels {
	return {
		'bbc_1xtra'				=> 'BBC 1Xtra',
		'bbc_radio_one'				=> 'BBC Radio 1',
		'bbc_radio_two'				=> 'BBC Radio 2',
		'bbc_radio_three'			=> 'BBC Radio 3',
		'bbc_radio_four'			=> 'BBC Radio 4',
		'bbc_radio_five_live'			=> 'BBC Radio 5 live',
		'bbc_radio_five_live_sports_extra'	=> 'BBC 5 live Sports Extra',
		'bbc_6music'				=> 'BBC 6 Music',
		'bbc_7'					=> 'BBC 7',
		'bbc_asian_network'			=> 'BBC Asian Network',
		'bbc_radio_foyle'			=> 'BBC Radio Foyle',
		'bbc_radio_scotland'			=> 'BBC Radio Scotland',
		'bbc_radio_nan_gaidheal'		=> 'BBC Radio Nan Gaidheal',
		'bbc_radio_ulster'			=> 'BBC Radio Ulster',
		'bbc_radio_wales'			=> 'BBC Radio Wales',
		'bbc_radio_cymru'			=> 'BBC Radio Cymru',
		'bbc_world_service'			=> 'BBC World Service',
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
		'popular/radio'				=> 'Popular',
		'highlights/radio'			=> 'Highlights',
	};
}


# Class cmdline Options
sub opt_format {
	return {
		radiomode	=> [ 1, "radiomode|amode=s", 'Recording', '--radiomode <mode>,<mode>,...', "Radio Recording mode(s): iphone,flashaac,flashaachigh,flashaacstd,flashaaclow,flashaudio,realaudio,wma (default: iphone,flashaachigh,flashaacstd,flashaudio,realaudio,flashaaclow)"],
		bandwidth 	=> [ 1, "bandwidth=n", 'Recording', '--bandwidth', "In radio realaudio mode specify the link bandwidth in bps for rtsp streaming (default 512000)"],
		lame		=> [ 0, "lame=s", 'External Program', '--lame <path>', "Location of lame binary"],
		outputradio	=> [ 1, "outputradio=s", 'Output', '--outputradio <dir>', "Output directory for radio recordings"],
		wav		=> [ 1, "wav", 'Recording', '--wav', "In radio realaudio mode output as wav and don't transcode to mp3"],
		rtmpradioopts	=> [ 1, "rtmp-radio-opts|rtmpradioopts=s", 'Recording', '--rtmp-radio-opts <options>', "Add custom options to flvstreamer/rtmpdump for radio"],
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
	return ", $prog->{channel}, $prog->{categories}";
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
		if ( ! main::exists_in_path('flvstreamer') ) {
			main::logger "WARNING: Not using flash modes since flvstreamer/rtmpdump is not found\n" if $opt->{verbose};
			$mlist = 'iphone,realaudio,wma';
		} else {
			$mlist = 'iphone,flashaachigh,flashaacstd,flashaudio,realaudio,flashaaclow,wma';
		}
	}
	# Deal with BBC Radio fallback modes and expansions
	# Valid modes are iphone,rtmp,flashaac,flashaudio,realaudio,wmv
	# 'rtmp' or 'flash' => 'flashaudio,flashaac'
	# flashaac => flashaachigh,flashaacstd,flashaaclow
	# flashaachigh => flashaachigh1,flashaachigh2
	$mlist = main::expand_list($mlist, 'best', 'flashaachigh,flashaacstd,iphone,flashaudio,realaudio,flashaaclow,wma');
	$mlist = main::expand_list($mlist, 'flash', 'flashaudio,flashaac');
	$mlist = main::expand_list($mlist, 'rtmp', 'flashaudio,flashaac');
	$mlist = main::expand_list($mlist, 'flashaac', 'flashaachigh,flashaacstd,flashaaclow');

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
	} elsif ( $prog->{pid} =~ m{^http.+\/([bpw]0[a-z0-9]{6})\/?.*$} && $prog->{pid} !~ m{/programmes/} ) {
		# extract b??????? format from any URL containing it
		$prog->{pid} = $1;

	# If this is a BBC *iPlayer* Live channel
	#} elsif ( $prog->{pid} =~ m{http.+bbc\.co\.uk/iplayer/console/}i ) {
	#	# Just leave the URL as the pid

	# e.g. http://www.bbc.co.uk/iplayer/playlive/bbc_radio_fourfm/
	} elsif ( $prog->{pid} =~ m{http.+bbc\.co\.uk/iplayer}i ) {
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
	my $progref = shift;
	my $prog_type = shift;
	# Hack to get correct 'channels' method because this methods is being shared with Programme::radio
	my %channels = %{ main::progclass($prog_type)->channels_filtered() };

	for ( sort keys %channels ) {

			# Extract channel
			my $channel = $channels{$_};
			my $pid = $_;
			my $name = $channels{$_};
			my $episode = 'live';
			main::logger "DEBUG: '$pid, $name - $episode, $channel'\n" if $opt->{debug};

			# build data structure
			$progref->{$pid} = main::progclass($prog_type)->new(
				'pid'		=> $pid,
				'name'		=> $name,
				'versions'	=> 'default',
				'episode'	=> $episode,
				'desc'		=> "Live stream of $name",
				'guidance'	=> '',
				#'thumbnail'	=> "http://static.bbc.co.uk/mobile/iplayer_widget/img/ident_${pid}.png",
				'thumbnail'	=> "http://www.bbc.co.uk/iplayer/img/station_logos/${pid}.png",
				'channel'	=> $channel,
				#'categories'	=> join(',', @category),
				'type'		=> $prog_type,
				'web'		=> "http://www.bbc.co.uk/iplayer/playlive/${pid}/",
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
		'bbc_one'			=> 'BBC One',
		'bbc_two'			=> 'BBC Two',
		'bbc_three'			=> 'BBC Three',
		'bbc_four'			=> 'BBC Four',
		'cbbc'				=> 'CBBC',
		'cbeebies'			=> 'CBeebies',
		'bbc_news24'			=> 'BBC News 24',
		'bbc_parliament'		=> 'BBC Parliament',
	};
}


# Class cmdline Options
sub opt_format {
	return {
		livetvmode	=> [ 1, "livetvmode=s", 'Recording', '--livetvmode <mode>,<mode>,...', "Live TV Recoding modes: flashhd,flashvhigh,flashhigh,flashstd,flashnormal (default: flashhd,flashvhigh,flashhigh,flashstd,flashnormal)"],
		outputlivetv	=> [ 1, "outputlivetv=s", 'Output', '--outputlivetv <dir>', "Output directory for live tv recordings"],
		rtmplivetvopts	=> [ 1, "rtmp-livetv-opts|rtmplivetvopts=s", 'Recording', '--rtmp-livetv-opts <options>', "Add custom options to flvstreamer/rtmpdump for livetv"],
	};
}



# This gets run before the download retry loop if this class type is selected
sub init {
	# Force certain options for Live 
	# Force only one try if live and recording to file
	$opt->{attempts} = 1 if ( ! $opt->{attempts} ) && ( ! $opt->{nowrite} );
	# Force to skip checking download history if live
	$opt->{force} = 1;
}



# Returns the modes to try for this prog type
sub modelist {
	my $prog = shift;
	my $mlist = $opt->{livetvmode} || $opt->{modes};
	
	# Defaults
	if ( ! $mlist ) {
		$mlist = 'flashhd,flashvhigh,flashhigh,flashstd,flashnormal';
	}
	# Deal with BBC TV fallback modes and expansions
	# Valid modes are rtmp,flashhigh,flashstd
	# 'rtmp' or 'flash' => 'flashhigh,flashnormal'
	$mlist = main::expand_list($mlist, 'best', 'flashhd,flashvhigh,flashhigh,flashstd,flashnormal,flashlow');
	$mlist = main::expand_list($mlist, 'flash', 'flashhd,flashvhigh,flashhigh,flashstd,flashnormal,flashlow');
	$mlist = main::expand_list($mlist, 'rtmp', 'flashhd,flashvhigh,flashhigh,flashstd,flashnormal,flashlow');

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
		'bbc_1xtra'				=> 'BBC 1Xtra',
		'bbc_radio_one'				=> 'BBC Radio 1',
		'bbc_radio_two'				=> 'BBC Radio 2',
		'bbc_radio_three'			=> 'BBC Radio 3',
		'bbc_radio_fourfm'			=> 'BBC Radio 4 FM',
		'bbc_radio_fourlw'			=> 'BBC Radio 4 LW',
		'bbc_radio_five_live'			=> 'BBC Radio 5 live',
		'bbc_radio_five_live_sports_extra'	=> 'BBC 5 live Sports Extra',
		'bbc_6music'				=> 'BBC 6 Music',
		'bbc_7'					=> 'BBC 7',
		'bbc_asian_network'			=> 'BBC Asian Network',
		'bbc_radio_foyle'			=> 'BBC Radio Foyle',
		'bbc_radio_scotland'			=> 'BBC Radio Scotland',
		'bbc_radio_nan_gaidheal'		=> 'BBC Radio Nan Gaidheal',
		'bbc_radio_ulster'			=> 'BBC Radio Ulster',
		'bbc_radio_wales'			=> 'BBC Radio Wales',
		'bbc_radio_cymru'			=> 'BBC Radio Cymru',
		'http://www.bbc.co.uk/worldservice/includes/1024/screen/audio_console.shtml?stream=live' => 'BBC World Service',
		'bbc_world_service' 			=> 'BBC World Service Intl',
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
	};
}


# Class cmdline Options
sub opt_format {
	return {
		liveradiomode	=> [ 1, "liveradiomode=s", 'Recording', '--liveradiomode <mode>,<mode>,..', "Live Radio Recording modes: flashaac,realaudio,wma"],
		outputliveradio	=> [ 1, "outputliveradio=s", 'Output', '--outputliveradio <dir>', "Output directory for live radio recordings"],
		rtmpliveradioopts => [ 1, "rtmp-liveradio-opts|rtmpliveradioopts=s", 'Recording', '--rtmp-liveradio-opts <options>', "Add custom options to flvstreamer/rtmpdump for liveradio"],
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
	# Force to skip checking download history if live
	$opt->{force} = 1;
}



# Returns the modes to try for this prog type
sub modelist {
	my $prog = shift;
	my $mlist = $opt->{liveradiomode} || $opt->{modes};
	
	# Defaults
	if ( ! $mlist ) {
		if ( ! main::exists_in_path('flvstreamer') ) {
			main::logger "WARNING: Not using flash modes since flvstreamer/rtmpdump is not found\n" if $opt->{verbose};
			$mlist = 'realaudio,wma';
		} else {
			$mlist = 'flashaachigh,flashaacstd,realaudio,flashaaclow,wma';
		}
	}
	# Deal with BBC Radio fallback modes and expansions
	# Valid modes are rtmp,flashaac,realaudio,wmv
	# 'rtmp' or 'flash' => 'flashaac'
	# flashaac => flashaachigh,flashaacstd,flashaaclow
	# flashaachigh => flashaachigh1,flashaachigh2
	$mlist = main::expand_list($mlist, 'best', 'flashaachigh,flashaacstd,realaudio,flashaaclow,wma');
	$mlist = main::expand_list($mlist, 'flash', 'flashaac');
	$mlist = main::expand_list($mlist, 'rtmp', 'flashaac');
	$mlist = main::expand_list($mlist, 'flashaac', 'flashaachigh,flashaacstd,flashaaclow');

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

	# Create url with appended 12 digit random number /mediaselector/3/auth/iplayer_streaming_http_mp4/b0067vmx?r=101477348958
	# http://www.bbc.co.uk/mediaselector/3/auth/iplayer_streaming_http_mp4
	my $iphone_download_prefix = 'http://www.bbc.co.uk/mediaselector/3/auth/iplayer_streaming_http_mp4';
	my $url_1 = ${iphone_download_prefix}.'/'.${pid}.'?r='.(sprintf "%012.0f", 999999999999*rand(0) );
	main::logger "INFO: iphone stream URL = $url_1\n" if $opt->{verbose};

	# This doesn't work through url-prepend proxies
	## Use url prepend if required
	#if ( $opt->{proxy} =~ /^prepend:/ ) {
	#	$url_1 = $opt->{proxy}.main::url_encode( $url_1 );
	#	$url_1 =~ s/^prepend://g;
	#}

	# Stage 2: e.g. "Location: http://download.iplayer.bbc.co.uk/iplayer_streaming_http_mp4/121285241910131406.mp4?token=iVXexp1yQt4jalB2Hkl%2BMqI25nz2WKiSsqD7LzRmowrwXGe%2Bq94k8KPsm7pI8kDkLslodvHySUyU%0ApM76%2BxEGtoQTF20ZdFjuqo1%2B3b7Qmb2StOGniozptrHEVQl%2FYebFKVNINg%3D%3D%0A"
	#main::logger "\rGetting iplayer iphone URL         " if (! $opt->{verbose}) && ! $opt->{streaminfo};
	my $h = new HTTP::Headers(
		'User-Agent'	=> $user_agent{coremedia},
		'Accept'	=> '*/*',
		'Range'		=> 'bytes=0-1',
	);
	my $req = HTTP::Request->new ('GET', $url_1, $h);
	# send request (use simple_request here because that will not allow redirects)
	my $res = $ua->simple_request($req);
	# Get resulting Location header (i.e. redirect URL)
	my $url = $res->header("location");
	if ( ! $res->is_redirect ) {
		main::logger "ERROR: Failed to get iphone redirect from iplayer site\n\n";
		return '';
	}
	# Extract redirection Location URL
	$url =~ s/^Location: (.*)$/$1/g;
	# If we get a Redirection containing statuscode=404 then this prog is not yet ready
	if ( $url =~ /statuscode=404/ ) {
		main::logger "\rERROR: iphone stream is not yet ready\n" if $opt->{verbose};
		return '';
	} elsif ( $url =~ /statuscode=403/ ) {
		main::logger "\rERROR: iphone stream is not permitted for recording\n" if $opt->{verbose};
		return '';
	}

	return $url;
}



# %prog (only for %prog for mode and tagging)
# Get the h.264/mp3 stream
# ( $ua, $url_2, $prog '0|1 == rearrange moov' )
sub get {
	my ( $stream, $ua, $url_2, $prog ) = @_;
	my $childpid;
	my $rearrange = 0;
	my $iphone_block_size	= 0x2000000; # 32MB

	# Stage 3a: Download 1st byte to get exact file length
	main::logger "INFO: Stage 3 URL = $url_2\n" if $opt->{verbose};

	# Override the $rearrange value is --raw option is specified
	$rearrange = 1 if $prog->{type} eq 'tv' && not $opt->{raw};
	main::logger "DEBUG: Rearrang mov file mode = $rearrange (type: $prog->{type}, raw: $opt->{raw})\n" if $opt->{debug};
		
	# Use url prepend if required
	if ( $opt->{proxy} =~ /^prepend:/ ) {
		$url_2 = $opt->{proxy}.main::url_encode( $url_2 );
		$url_2 =~ s/^prepend://g;
	}

	# Setup request header
	my $h = new HTTP::Headers(
		'User-Agent'	=> $user_agent{coremedia},
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
	# default to this if we are not rearranging (tells the download chunk loop where to stop - i.e. EOF instead of end of mdat atom)
	my $moov_start = $download_len + 1;
	my $header;
	if ($rearrange) {
		# Get ftyp+wide header etc
		$mdat_start = 0x1c;
		my $buffer = main::download_block(undef, $url_2, $ua, 0, $mdat_start + 4);
		# Get bytes upto (but not including) mdat atom start -> $header
		$header = substr($buffer, 0, $mdat_start);
		
		# Detemine moov start
		# Get mdat_length_chars from downloaded block
		my $mdat_length_chars = substr($buffer, $mdat_start, 4);
		my $mdat_length = bytestring_to_int($mdat_length_chars);
		main::logger "DEBUG: mdat_length = ".main::get_hex($mdat_length_chars)." = $mdat_length\n" if $opt->{debug};
		main::logger "DEBUG: mdat_length (decimal) = $mdat_length\n" if $opt->{debug};
		# The MOOV box starts one byte after MDAT box ends
		$moov_start = $mdat_start + $mdat_length;
	}

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

	if ($rearrange) {
		# if cookie fails then trigger a retry after deleting cookiejar
		# Determine orginal moov atom length so we can work out if the partially recorded file has the moov atom in it already
		$moov_length = bytestring_to_int( main::download_block( undef, $url_2, $ua, $moov_start, $moov_start+3 ) );
		main::logger "INFO: original moov atom length = $moov_length                          \n" if $opt->{verbose};
		# Sanity check this moov length - chances are that were being served up a duff file if this is > 10% of the file size or < 64k
		if ( $moov_length > (${moov_start}/9.0) || $moov_length < 65536 ) {
			main::logger "WARNING: Bad file recording, deleting cookie                 \n";
			$ua->cookie_jar( HTTP::Cookies->new( file => $cookiejar, autosave => 0, ignore_discard => 0 ) );
			unlink $cookiejar;
			unlink $prog->{filepart};
			return 'retry';
		}

		# we still need an accurate moovlength for the already downloaded moov atom for resume restart_offset.....
		# If we have no existing file, a file which doesn't yet even have the moov atom, or using stdout (or no-write option)
		# (allow extra 1k on moov_length for metadata when testing)
		if ( $opt->{stdout} || $opt->{nowrite} || stat($prog->{filepart})->size < ($moov_length+$mdat_start+1024) ) {
			# get moov chunk into memory
			$moovdata = main::download_block( undef, $url_2, $ua, $moov_start, (${download_len}-1) );
			main::logger "                                                                                                         \r" if $opt->{hash};
			# Create new udta atom with child atoms for metadata
			my $udta_new = create_qt_atom('udta',
				create_qt_atom( chr(0xa9).'nam', $prog->{name}.' - '.$prog->{episode}, 'string' ).
				create_qt_atom( chr(0xa9).'alb', $prog->{name}, 'string' ).
				create_qt_atom( chr(0xa9).'trk', $prog->{episode}, 'string' ).
				create_qt_atom( chr(0xa9).'aut', $prog->{channel}, 'string' ).
				create_qt_atom( chr(0xa9).'ART', $prog->{channel}, 'string' ).
				create_qt_atom( chr(0xa9).'des', $prog->{desc}, 'string' ).
				create_qt_atom( chr(0xa9).'cmt', 'Recorded using get_iplayer', 'string' ).
				create_qt_atom( chr(0xa9).'req', 'QuickTime 6.0 or greater', 'string' ).
				create_qt_atom( chr(0xa9).'day', (localtime())[5] + 1900, 'string' )
			);
			# Insert new udta atom over the old one and get the new $moov_length (and update moov atom size field)
			replace_moov_udta_atom ( $udta_new, $moovdata );

			# Process the moov data so that we can relocate it (change the chunk offsets that are absolute)
			# Also update moov+_length to be accurate after metadata is added etc
			$moov_length = relocate_moov_chunk_offsets( $moovdata );
			main::logger "INFO: New moov atom length = $moov_length                          \n" if $opt->{verbose};
			# write moov atom to file next (yes - were rearranging the file - header+moov+mdat - not header+mdat+moov)
			main::logger "INFO: Appending ftype+wide+moov atoms to $prog->{filepart}\n" if $opt->{verbose};
			# Write header atoms (ftyp, wide)
			print $fh $header if ! $opt->{nowrite};
			print STDOUT $header if $opt->{stdout};
			# Write moov atom
			print $fh $moovdata if ! $opt->{nowrite};
			print STDOUT $moovdata if $opt->{stdout};
			# If were not resuming we want to only start the download chunk loop from mdat_start 
			$restart_offset = $mdat_start;
		}

		# Get accurate moov_length from file (unless stdout or nowrite options are specified)
		# Assume header+moov+mdat atom layout
		if ( (! $opt->{stdout}) && (! $opt->{nowrite}) && stat($prog->{filepart})->size > ($moov_length+$mdat_start) ) {
				main::logger "INFO: Getting moov atom length from partially recorded file $prog->{filepart}\n" if $opt->{verbose};
				if ( ! open( MOOVDATA, "< $prog->{filepart}" ) ) {
					main::logger "ERROR: Cannot Read partially recorded file\n";
					return 'next';
				}
				my $data;
				seek(MOOVDATA, $mdat_start, 0);
				if ( read(MOOVDATA, $data, 4, 0) != 4 ) {
					main::logger "ERROR: Cannot Read moov atom length from partially recorded file\n";
					return 'next';
				}
				close MOOVDATA;
				# Get moov atom size from file
				$moov_length = bytestring_to_int( substr($data, 0, 4) );
				main::logger "INFO: moov atom length (from partially recorded file) = $moov_length                          \n" if $opt->{verbose};
		}
	}

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



# Usage: moov_length = relocate_moov_chunk_offsets(<binary string>)
sub relocate_moov_chunk_offsets {
	my $moovdata = $_[0];
	# Change all the chunk offsets in moov->stco atoms and add moov_length to them all
	# get moov atom length
	my $moov_length = bytestring_to_int( substr($moovdata, 0, 4) );
	# Use index() to search for a string within a string
	my $i = -1;
	while (($i = index($moovdata, 'stco', $i)) > -1) {

		# determine length of atom (4 bytes preceding stco)
		my $stco_len = bytestring_to_int( substr($moovdata, $i-4, 4) );
		main::logger "INFO: Found stco atom at moov atom offset: $i length $stco_len\n" if $opt->{verbose};

		# loop through all chunk offsets in this atom and add offset (== moov atom length)
		for (my $j = $i+12; $j < $stco_len+$i-4; $j+=4) {
			my $chunk_offset = bytestring_to_int( substr($moovdata, $j, 4) );
			$chunk_offset += $moov_length;
			# write back bytes into $moovdata
			write_msb_value_at_offset( $moovdata, $j, $chunk_offset );
		}
		# skip over this whole atom now it is processed
		$i += $stco_len;
	}
	# Write $moovdata back to calling string
	$_[0] = $moovdata;
	return $moov_length;
}



# Replace the moov->udta atom with a new user-supplied one and update the moov atom size
# Usage: replace_moov_udta_atom ( $udta_new, $moovdata )
sub replace_moov_udta_atom {
	my $udta_new = $_[0];
	my $moovdata = $_[1];

	# get moov atom length
	my $moov_length = bytestring_to_int( substr($moovdata, 0, 4) );

	# Find the original udta atom start 
	# Use index() to search for a string within a string ($i will point at the beginning of the atom)
	my $i = index($moovdata, 'udta', -1) - 4;

	# determine length of atom (4 bytes preceding the name)
	my $udta_len = bytestring_to_int( substr($moovdata, $i, 4) );
	main::logger "INFO: Found udta atom at moov atom offset: $i length $udta_len\n" if $opt->{verbose};

	# Save the data before the udta atom
	my $moovdata_before_udta = substr($moovdata, 0, $i);

	# Save the remainder portion of data after the udta atom for later
	my $moovdata_after_udta = substr($moovdata, $i, $moovdata - $i + $udta_len);

	# Old udta atom should we need it
	### my $udta_old = substr($moovdata, $i, $udta_len);

	# Create new moov atom
	$moovdata = $moovdata_before_udta.$udta_new.$moovdata_after_udta;
	
	# Recalculate the moov size and insert into moovdata
	write_msb_value_at_offset( $moovdata, 0, length($moovdata) );
	
	# Write $moovdata back to calling string
	$_[1] = $moovdata;

	return 0;
}



# Converts a string of chars to it's MSB decimal value
sub bytestring_to_int {
	# Reverse to LSB order
        my $buf = reverse shift;
        my $dec = 0;
        for (my $i=0; $i<length($buf); $i++) {
		# Multiply byte value by 256^$i then accumulate
                $dec += (ord substr($buf, $i, 1)) * 256 ** $i;
        }
        #main::logger "DEBUG: Decimal value = $dec\n" if $opt->{verbose};
        return $dec;
}



# Write the msb 4 byte $value starting at $offset into the passed string
# Usage: write_msb_value($string, $offset, $value)
sub write_msb_value_at_offset {
	my $offset = $_[1];
	my $value = $_[2];
	substr($_[0], $offset+0, 1) = chr( ($value >> 24) & 0xFF );
	substr($_[0], $offset+1, 1) = chr( ($value >> 16) & 0xFF );
	substr($_[0], $offset+2, 1) = chr( ($value >>  8) & 0xFF );
	substr($_[0], $offset+3, 1) = chr( ($value >>  0) & 0xFF );
	return 0;
}



# Returns a string containing an QT atom
# Usage: create_qt_atom(<atome name>, <atom data>, ['string'])
sub create_qt_atom {
	my ($name, $data, $prog_type) = (@_);
	if (length($name) != 4) {
		main::logger "ERROR: Inavlid QT atom name length '$name'\n";
		exit 1;
	}
	# prepend string length if this is a string type
	if ( $prog_type eq 'string' ) {
		my $value = length($data);
		$data = '1111'.$data;
		# overwrite '1111' with total atom length in 2-byte MSB + 0x0 0x0
		substr($data, 0, 1) = chr( ($value >> 8) & 0xFF );
		substr($data, 1, 1) = chr( ($value >> 0) & 0xFF );
		substr($data, 2, 1) = chr(0);
		substr($data, 3, 1) = chr(0);
	}
	my $atom = '0000'.$name.$data;
	# overwrite '0000' with total atom length in MSB
	write_msb_value_at_offset( $atom, 0, length($name.$data) + 4 );
	return $atom;
}



################### Streamer::rtmp class #################
package Streamer::rtmp;

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


sub opt_format {
	return {
		ffmpeg		=> [ 0, "ffmpeg=s", 'External Program', '--ffmpeg <path>', "Location of ffmpeg binary"],
		rtmpport	=> [ 1, "rtmpport=n", 'Recording', '--rtmpport <port>', "Override the RTMP port (e.g. 443)"],
		flvstreamer	=> [ 0, "flvstreamer|rtmpdump=s", 'External Program', '--flvstreamer <path>', "Location of flvstreamer/rtmpdump binary"],
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
	my $mode	= $prog->{mode};
	push @cmdopts, ( split /\s+/, $streamdata{extraopts} ) if $streamdata{extraopts};

	my $file_tmp;
	my @cmd;
	
	if ( $opt->{raw} ) {
		$file_tmp = $prog->{filepart};
	} else {
		$file_tmp = $prog->{filepart}.'.flv'
	}

	# Remove failed file recording (below a certain size) - hack to get around flvstreamer/rtmpdump not returning correct exit code
	if ( -f $file_tmp && stat($file_tmp)->size < $prog->min_download_size() ) {
		unlink( $file_tmp );
	}
		
	# Add custom options to flvstreamer/rtmpdump for this type if specified with --rtmp-<type>-opts
	if ( defined $opt->{'rtmp'.$prog->{type}.'opts'} ) {
		push @cmdopts, ( split /\s+/, $opt->{'rtmp'.$prog->{type}.'opts'} );
	}

	# rtmpdump/flvstreamer version detection e.g. 'RTMPDump v1.5' or 'FLVStreamer v1.7a'
	my $rtmpver;
	chomp( $rtmpver = (grep /^(RTMPDump|FLVStreamer)/, `"$bin->{flvstreamer}" 2>&1`)[0] );
	$rtmpver =~ s/^\w+\s+v([\.\d]+).*$/$1/g;
	main::logger "INFO: $bin->{flvstreamer} version $rtmpver\n" if $opt->{verbose};
	main::logger "INFO: RTMP_URL: $url_2, tcUrl: $tcurl, application: $application, authString: $authstring, swfUrl: $swfurl, file: $prog->{filepart}, file_done: $prog->{filename}\n" if $opt->{verbose};

	# Save the effort and don't support < v1.5
	if ( $rtmpver < 1.5 ) {
		main::logger "WARNING: rtmpdump >= 1.5 or flvstreamer is required - please upgrade\n";
		return 'next';
	}

	# Add --live option if required
	if ( $streamdata{live} ) {
		if ( $rtmpver < 1.8 ) {
			main::logger "WARNING: Please use flvstreamer v1.8 or later for more reliable live streaming\n";
		}
		push @cmdopts, '--live';
	}

	# Add start stop options if defined
	if ( $opt->{start} || $opt->{stop} ) {
		if ( $rtmpver < 1.8 ) {
			main::logger "ERROR: Please use flvstreamer v1.8c or later for start/stop features\n";
			exit 4;
		}
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
	if ( $opt->{stdout} && $opt->{nowrite} ) {
		if ( $rtmpver < 1.7) {
			push @cmdopts, ( '-o', '-' );
		}
	} else {
		push @cmdopts, ( '--resume', '-o', $file_tmp );
	}
	push @cmdopts, @{ $binopts->{flvstreamer} } if $binopts->{flvstreamer};
	
	my $return;
	# Different invocation depending on version
	# if playpath is defined
	if ( $playpath ) {
		@cmd = (
			$bin->{flvstreamer},
			'--port', $port,
			'--protocol', $protocol,
			'--playpath', $playpath,
			'--host', $server,
			'--swfUrl', $swfurl,
			'--tcUrl', $tcurl,
			'--app', $application,
			@cmdopts,
		);
	# Using just streamurl (i.e. no playpath defined)
	} else {
		@cmd = (
			$bin->{flvstreamer},
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
	return 'retry' if $return && -f $file_tmp && stat($file_tmp)->size > $prog->min_download_size();

	# If file is too small or non-existent then delete and try next mode
	if ( (! -f $file_tmp) || ( -f $file_tmp && stat($file_tmp)->size < $prog->min_download_size()) ) {
		main::logger "WARNING: Failed to stream file $file_tmp via RTMP\n";
		unlink $file_tmp;
		return 'next';
	}
	
	# Retain raw flv format if required
	if ( $opt->{raw} ) {
		move($file_tmp, $prog->{filename}) if $file_tmp ne $prog->{filename} && ! $opt->{stdout};
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
	# Convert flv to aac/mp4a
	} elsif ( $mode =~ /flashaac/ ) {
		# This works as long as we specify aac and not mp4a
		@cmd = (
			$bin->{ffmpeg},
			'-i', $file_tmp,
			'-vn',
			'-acodec', 'copy',
			'-y', $prog->{filepart},
		);
	# Convert video flv to mp4/avi if required
	} else {
		@cmd = (
			$bin->{ffmpeg},
			'-i', $file_tmp,
			'-vcodec', 'copy',
			'-acodec', 'copy',
			'-f', $prog->{ext},
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
	move($prog->{filepart}, $prog->{filename}) if $prog->{filepart} ne $prog->{filename} && ! $opt->{stdout};
	
	# Re-symlink file
	$prog->create_symlink( $prog->{symlink}, $prog->{filename} ) if $opt->{symlink};

	main::logger "INFO: Recorded $prog->{filename}\n";
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
			main::logger sprintf $format, @sizes, ($total_size_new - $total_size) / (time() - $start_time) / 1024.0 * 8.0;
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
		# Commented out cos this is stream-only - don't want anything in history as a result
		#main::logger "INFO: Copying $url to $prog->{filepart}\n" if $opt->{verbose};
		#if ( ! copy( $url, $prog->{filepart} ) ) {
		#	main::logger "\rERROR: Recording failed\n";
			main::logger "\rERROR: Recording failed - this is a stream-only programme\n";
			return 'next';
		#}
		#move $prog->{filepart}, $prog->{filename} if $prog->{filepart} ne $prog->{filename};
		## symlink file
		#$prog->create_symlink( $prog->{symlink}, $prog->{filename} ) if $opt->{symlink};
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
		pvr		=> [ 0, "pvr|pvrrun|pvr-run", 'PVR', '--pvr', "Runs the PVR using all saved PVR searches (intended to be run every hour from cron etc)"],
		pvrsingle	=> [ 0, "pvrsingle|pvr-single=s", 'PVR', '--pvr-single <search name>', "Runs a named PVR search"],
		pvradd		=> [ 0, "pvradd|pvr-add=s", 'PVR', '--pvradd <search name>', "Save the named PVR search with the specified search terms"],
		pvrdel		=> [ 0, "pvrdel|pvr-del=s", 'PVR', '--pvrdel <search name>', "Remove the named search from the PVR searches"],
		pvrdisable	=> [ 0, "pvrdisable|pvr-disable=s", 'PVR', '--pvr-disable <search name>', "Disable (not delete) a named PVR search"],
		pvrenable	=> [ 0, "pvrenable|pvr-enable=s", 'PVR', '--pvr-enable <search name>', "Enable a previously disabled named PVR search"],
		pvrlist		=> [ 0, "pvrlist|pvr-list", 'PVR', '--pvrlist', "Show the PVR search list"],
		pvrqueue	=> [ 0, "pvrqueue|pvr-queue", 'PVR', '--pvrqueue', "Add currently matched programmes to queue for later one-off recording using the --pvr option"],
		pvrscheduler	=> [ 0, "pvrscheduler|pvr-scheduler=n", 'PVR', '--pvrscheduler <seconds>', "Runs the PVR using all saved PVR searches every <seconds>"],
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
	my $single = shift;

	# Don't attempt to record programmes with pids in history
	my $hist = History->new();
	$hist->load();

	# Load all PVR searches
	$pvr->load_list();

	# For each PVR search (or single one if specified)
	my @names = ( $single ) || ( sort {lc $a cmp lc $b} keys %{$pvr} );
	main::logger "Running PVR Searches:\n";
	for my $name ( @names ) {
		# Ignore if this search is disabled
		if ( $pvr->{$name}->{disable} ) {
			main::logger "\nSkipping '$name' (disabled)\n" if $opt->{verbose};
			next;
		}
		main::logger "$name\n";
		# Clear then Load options for specified pvr search name
		my @search_args = $pvr->load_options($name);

		## Display all options used for this pvr search
		#$opt->display('Default Options', '(help|debug|get|^pvr)');

		# Switch on --hide option
		$opt->{hide} = 1;
		# Dont allow --flush with --pvr
		$opt->{flush} = '';
		# Do the recording (force --get option)
		$opt->{get} = 1 if ! $opt->{test};

		# If this is a one-off queue pid entry then delete the PVR entry upon successful recoding(s)
		if ( $pvr->{$name}->{pid} ) {
			my $failcount = main::find_matches( $hist );
			$pvr->del( $name ) if not $failcount;

		# Just make recordings of matching progs
		} else {
			main::download_matches( $hist, main::find_matches( $hist, @search_args ) );
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
	$hist->load();

	# PID and TYPE specified
	if ( $opt_cmdline->{pid} ) {
		# ensure we only have one prog type defined
		if ( $opt->{type} && $opt->{type} !~ /,/ ) {
			# Add to PVR if not already in download history (unless multimode specified)
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
	for ( grep !/(webrequest|nocopyright|^test|metadataonly|subsonly|thumbonly|stdout|^get|update|^save|^prefs|help|expiry|nowrite|tree|terse|streaminfo|listformat|^list|showoptions|hide|info|pvr.*)$/, sort {lc $a cmp lc $b} keys %{$opt_cmdline} ) {
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



# Save the array options specified as a PVR search
sub save {
	my $pvr = shift;
	my $name = shift;
	my @options = @_;
	# Sanitize name
	$name = StringUtils::sanitize_path( $name );
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
	for ( sort {$a <=> $b} keys %{ $pvr->{$name} } ) {
		# Add to list of search args if this is not an option
		if ( /^search\d+$/ ) {
			main::logger "INFO: $_ = $pvr->{$name}->{$_}\n" if $opt->{verbose};
			push @search_args, $pvr->{$name}{$_};
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



############## End OO ##############
