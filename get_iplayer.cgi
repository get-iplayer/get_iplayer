#!/usr/bin/perl
#
# The world's most insecure web-based PVR manager and streaming proxy for get_iplayer
# ** WARNING ** Never run this in an untrusted environment or facing the internet
#
#    Copyright (C) 2009-2010 Phil Lewis
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

my $VERSION = 2.82;

use strict;
use CGI ':all';
use CGI::Cookie;
use IO::File;
use File::Copy;
use HTML::Entities;
use URI::Escape;
use LWP::ConnCache;
#use LWP::Debug qw(+);
use LWP::UserAgent;
use IO::Handle;
use Getopt::Long;
use Cwd 'abs_path';
use File::Basename;
use constant IS_WIN32 => $^O eq 'MSWin32' ? 1 : 0;
$| = 1;
my $fh;
# Send log messages to this fh
my $se = *STDERR;

my $opt_cmdline;
$opt_cmdline->{debug} = 0;
# Allow bundling of single char options
Getopt::Long::Configure ("bundling");
# cmdline opts take precedence
GetOptions(
	"help|h"			=> \$opt_cmdline->{help},
	"listen|address|l=s"		=> \$opt_cmdline->{listen},
	"port|p=n"			=> \$opt_cmdline->{port},
	"ffmpeg=s"			=> \$opt_cmdline->{ffmpeg},
	"getiplayer|get_iplayer|g=s"	=> \$opt_cmdline->{getiplayer},
	"debug"				=> \$opt_cmdline->{debug},
) || die usage();

# Display usage if old method of invocation is used or --help
usage() if $opt_cmdline->{help} || @ARGV;


# Usage
sub usage {
	my $text = sprintf "get_iplayer Web PVR Manager v%.2f, ", $VERSION;
	$text .= <<'EOF';
Copyright (C) 2009-2010 Phil Lewis
  This program comes with ABSOLUTELY NO WARRANTY; This is free software, 
  and you are welcome to redistribute it under certain conditions; 
  See the GPLv3 for details.

Options:
 --listen,-l       Use the built-in web server and listen on this interface address (default: 0.0.0.0)
 --port,-p         Use the built-in web server and listen on this TCP port
 --getiplayer,-g   Path to the get_iplayer script
 --ffmpeg          Path to the ffmpeg binary
 --debug           Debug mode
 --help,-h         This help text
EOF
	print $text;
	exit 1;
}	


# Some defaults
my $default_modes = 'flashaachigh,flashaacstd,flash,realaudio,flashaaclow';
$opt_cmdline->{ffmpeg} = 'ffmpeg' if ! $opt_cmdline->{ffmpeg};
$opt_cmdline->{listen} = '0.0.0.0' if ! $opt_cmdline->{listen};
# Search for get_iplayer
if ( ! $opt_cmdline->{getiplayer} ) {
	for ( './get_iplayer', './get_iplayer.cmd', './get_iplayer.pl', '/usr/bin/get_iplayer' ) {
		$opt_cmdline->{getiplayer} = $_ if -x $_;
	}
}
if ( ( ! $opt_cmdline->{getiplayer} ) || ! -f $opt_cmdline->{getiplayer} ) {
	print "ERROR: Cannot find get_iplayer, please specify its location using the --getiplayer option.\n";
	exit 2;
}

# Path to get_iplayer (+ set HOME env var cos apache seems to not set it)
my $home = $ENV{HOME};

my %prog;
my @pids;
my @displaycols;

# Field names to be grabbed from get_iplayer
my @headings = qw( 
	index
	thumbnail
	pid
	available
	type
	name
	episode
	versions
	duration
	desc
	channel
	categories
	timeadded
	guidance
	web
	seriesnum
	episodenum
	filename
	mode
);

# Default Displayed headings
my @headings_default = qw( thumbnail type name episode desc channel categories timeadded );

# Lookup table for nice field name headings
my %fieldname = (
	index			=> 'Index',
	pid			=> 'Pid',
	available		=> 'Availability',
	type			=> 'Type',
	name			=> 'Name',
	episode			=> 'Episode',
	versions		=> 'Versions',
	duration		=> 'Duration',
	desc			=> 'Description',
	channel			=> 'Channel',
	categories		=> 'Categories',
	thumbnail		=> 'Image',
	timeadded		=> 'Time Added',
	guidance		=> 'Guidance',
	web			=> 'Web Page',
	pvrsearch		=> 'PVR Search',
	comment			=> 'Comment',
	filename		=> 'Filename',
	mode			=> 'Mode',
	seriesnum		=> 'Series Number',
	episodenum		=> 'Episode Number',
	'name,episode'		=> 'Name+Episode',
	'name,episode,desc'	=> 'Name+Episode+Desc',
);

my %cols_order = ();
my %cols_names = ();

my %prog_types = (
	tv	=> 'BBC TV',
	radio	=> 'BBC Radio',
	podcast	=> 'BBC Podcast',
	livetv	=> 'Live BBC TV',
	liveradio => 'Live BBC Radio',
);

my %prog_types_order = (
	1	=> 'tv',
	2	=> 'radio',
	3	=> 'podcast',
	4	=> 'livetv',
	5	=> 'liveradio',
);

# Get list of currently valid and prune %prog types and add new entry
chomp( my @plugins = split /,/, join "\n", get_cmd_output( $opt_cmdline->{getiplayer}, '--nopurge', '--nocopyright', '--listplugins' ) );
for my $type (keys %prog_types) {
	if ( $prog_types{$type} && not grep /$type/, @plugins ) {
		# delete from %prog_types hash
		delete $prog_types{$type};
		# Delete from %prog_types_order hash
		for ( keys %prog_types_order ) {
			delete $prog_types_order{$_} if $prog_types_order{$_} eq $type; 
		}
	}
}
for my $type ( @plugins ) {
	if ( not $prog_types{$type} ) {
		$prog_types{$type} = $type;
		# Add to %prog_types_order hash
		my $max = scalar( keys %prog_types_order ) + 1;
		$prog_types_order{$max} = $type;
	}
}
#print "DEBUG: prog_types_order: $_ => $prog_types_order{$_}\n" for sort keys %prog_types_order;

my $icons_base_url = './icons/';

my $cgi;
my $nextpage;

# Page routing based on NEXTPAGE CGI parameter
my %nextpages = (
	'search_progs'		=> \&search_progs,	# Main Programme Listings
	'search_history'	=> \&search_history,	# Recorded Programme Listings
	'pvr_queue'		=> \&pvr_queue,		# Queue Recording of Selected Progs
	'recordings_delete'	=> \&recordings_delete,	# Delete Files for Selected Recordings
	'pvr_list'		=> \&show_pvr_list,	# Show all current PVR searches
	'pvr_del'		=> \&pvr_del,		# Delete selected PVR searches
	'pvr_add'		=> \&pvr_add,
	'pvr_edit'		=> \&pvr_edit,
	'pvr_save'		=> \&pvr_save,
	'pvr_run'		=> \&pvr_run,
	'record_now'		=> \&record_now,
	'show_info'		=> \&show_info,
	'refresh'		=> \&refresh,
	'update_script'		=> \&update_script,
);



##### Options #####
my $opt;

# Options Layout on page tabs
my $layout;
$layout->{BASICTAB}->{title} = 'Search Options',
$layout->{BASICTAB}->{heading} = 'Search Options:',
$layout->{BASICTAB}->{order} = [ qw/ SEARCH SEARCHFIELDS PROGTYPES HISTORY URL / ];

$layout->{SEARCHTAB}->{title} = 'Advanced Search';
$layout->{SEARCHTAB}->{heading} = 'Advanced Search Options:';
$layout->{SEARCHTAB}->{order} = [ qw/ VERSIONLIST EXCLUDE CATEGORY EXCLUDECATEGORY CHANNEL EXCLUDECHANNEL SINCE BEFORE FUTURE / ],

$layout->{DISPLAYTAB}->{title} = 'Display';
$layout->{DISPLAYTAB}->{heading} = 'Display Options:';
$layout->{DISPLAYTAB}->{order} = [ qw/ SORT REVERSE PAGESIZE HIDE HIDEDELETED / ];

$layout->{COLUMNSTAB}->{title} = 'Columns';
$layout->{COLUMNSTAB}->{heading} = 'Column Options:';
$layout->{COLUMNSTAB}->{order} = [ qw/ COLS / ];

$layout->{RECORDINGTAB}->{title} = 'Recording';
$layout->{RECORDINGTAB}->{heading} = 'Recording Options:';
$layout->{RECORDINGTAB}->{order} = [ qw/ OUTPUT MODES PROXY SUBTITLES METADATA THUMB PVRHOLDOFF FORCE AUTOWEBREFRESH AUTOPVRRUN REFRESHFUTURE / ];

$layout->{STREAMINGTAB}->{title} = 'Streaming';
$layout->{STREAMINGTAB}->{heading} = 'Streaming Options:';
$layout->{STREAMINGTAB}->{order} = [ qw/ BITRATE VSIZE VFR STREAMTYPE / ];

$layout->{HIDDENTAB}->{title} = '';
$layout->{HIDDENTAB}->{heading} = '';
$layout->{HIDDENTAB}->{order} = [ qw/ SAVE SEARCHTAB COLUMNSTAB DISPLAYTAB RECORDINGTAB STREAMINGTAB PAGENO INFO NEXTPAGE ACTION / ];

# Order of displayed tab buttoms (BASICTAB and HIDDEN are always displayed regardless of order)
$layout->{taborder} = [ qw/ BASICTAB SEARCHTAB DISPLAYTAB COLUMNSTAB RECORDINGTAB STREAMINGTAB HIDDENTAB / ];

# Any params that should never get into the get_iplayer pvr-add search
my @nosearch_params = qw/ /;

### Perl CGI Web Server ###
use Socket;
use IO::Socket;
my $IGNOREEXIT = 0;
# If the port number is specified then run embedded web server
if ( $opt_cmdline->{port} > 0 ) {
	# Autoreap zombies
	$SIG{CHLD} = 'IGNORE';
	# Need this because with $SIG{CHLD} = 'IGNORE', backticks and systems calls always return -1
	$IGNOREEXIT = 1;
	for (;;) {
		# Setup and create socket
		my $server = new IO::Socket::INET(
			Proto => 'tcp',
			LocalAddr => $opt_cmdline->{listen},
			LocalPort => $opt_cmdline->{port},
			Listen => SOMAXCONN,
			Reuse => 1,
		);
		$server or die "Unable to create server socket: $!";
		print $se "INFO: Listening on $opt_cmdline->{listen}:$opt_cmdline->{port}\n";
		print $se "WARNING: Insecure Remote access is allowed, use --listen=127.0.0.1 to limit to this host only\n" if $opt_cmdline->{listen} ne '127.0.0.1';
		# Await requests and handle them as they arrive
		while (my $client = $server->accept()) {
			my $procid = fork();
			die "Cannot fork" unless defined $procid;
			# Parent
			if ( $procid ) {
				close $client;
				next;
			}
			# Child
			$client->autoflush(1);
			my %request = ();
			my $query_string;
			my %data;
			{
				# Read Request
				local $/ = Socket::CRLF;
				while (<$client>) {
					# Main http request
					chomp;
					if (/\s*(\w+)\s*([^\s]+)\s*HTTP\/(\d.\d)/) {
						$request{METHOD} = uc $1;
						$request{URL} = $2;
						$request{HTTP_VERSION} = $3;
					# Standard headers
					} elsif (/:/) {
						my ( $type, $val ) = split /:/, $_, 2;
						$type =~ s/^\s+//;
						for ($type, $val) {
							s/^\s+//;
							s/\s+$//;
						}
						$request{lc $type} = $val;
						print "REQUEST HEADER: $type: $val\n" if $opt_cmdline->{debug};
					# POST data
					} elsif (/^$/) {
						read( $client, $request{CONTENT}, $request{'content-length'} ) if defined $request{'content-length'};
						last;
					}
				}
			}

			# Determine method and parse parameters
			if ($request{METHOD} eq 'GET') {
				if ($request{URL} =~ /(.*)\?(.*)/) {
					$request{URL} = $1;
					$request{CONTENT} = $2;
					$query_string = $request{CONTENT};
				}
				$data{"_method"} = "GET";
	
			} elsif ($request{METHOD} eq 'POST') {
				$query_string = parse_post_form_string( $request{CONTENT} );
				$data{"_method"} = "POST";
	
			} else {
				$data{"_method"} = "ERROR";
			}

			# Log Request
			print $se "$data{_method}: $request{URL}\n";

			# Is this the CGI or some other file request?
			if ( $request{URL} =~ /^\/?(iplayer|stream|recordings_delete|playlist.*|genplaylist.*|opml|)\/?$/ ) {
				# remove any vars that might affect the CGI
				#%ENV = ();
				@ARGV = ();
				# Setup CGI http vars
				print $se "QUERY_STRING = $query_string\n" if defined $query_string;
				$ENV{'QUERY_STRING'} = $query_string;
				$ENV{'REQUEST_URI'} = $request{URL};
				$ENV{'COOKIE'} = $request{cookie};
				$ENV{'SERVER_PORT'} = $opt_cmdline->{port};
				# respond OK to browser
				print $client "HTTP/1.1 200 OK", Socket::CRLF;
				# Invoke CGI
				run_cgi( $client, $query_string, $request{URL}, 'http://'.$request{host}.'/' );

			# Else 404
			} else {
				print $se "ERROR: 404 Not Found\n";
				print $client "HTTP/1.1 404 Not Found", Socket::CRLF;
				print $client Socket::CRLF;
				print $client "<html><body>404 Not Found</body></html>";
				$data{"_status"} = "404";
			}

			# Close Connection
			close $client;
			# Exit child
			exit 0;
		}
	}

# If we're running as a proper CGI from a web server...
} else {
	# If we were called by a webserver and not the builtin webserver then seed some vars
	my $prefix = $ENV{REQUEST_URI};
	my $request_uri;
	# remove trailing query
	$prefix =~ s/\?.*$//gi;
	my $query_string = $ENV{QUERY_STRING};
	my $request_host = "http://$ENV{SERVER_NAME}:$ENV{SERVER_PORT}${prefix}";
	# determine whether http or https
	my $request_protocol = 'http';
	if ( defined $ENV{'HTTPS'} ) {
		$request_protocol = $ENV{'HTTPS'}=='on'?'https':'http';
	}
	my $request_host = "${request_protocol}://$ENV{SERVER_NAME}:$ENV{SERVER_PORT}${prefix}";
	$home = $ENV{HOME};
	# Read POSTed data from STDIN if this is a form POST
	if ( $ENV{REQUEST_METHOD} eq 'POST' ) {
		my $content;
		while ( <STDIN> ) {
			$content .= $_;
		}
		$query_string = parse_post_form_string( $content );
	}
	run_cgi( *STDOUT, $query_string, undef, $request_host );
}

exit 0;



sub cleanup {
	my $signal = shift;
	print $se "INFO: Cleaning up PID $$ (signal = $signal)\n";
	exit 0;
}



sub parse_post_form_string {
	my $form = $_[0];
	my @data;
	while ( $form =~ /Content-Disposition:(.+?)--/sg ) {
		$_ = $1;
		# form-data; name = "KEY"
		m{name.+?"(.+?)"[\n\r\s]*(.+)}sg;
		my ($key, $val) = ( $1, $2 );
		next if ! $1;
		$val =~ s/[\r\n]//g;
		$val =~ s/\+/ /g;
		# Decode entities first
		decode_entities($val);
		# url encode each entry
		$val =~ s/([^A-Za-z0-9])/sprintf("%%%02X", ord($1))/seg;
		push @data, "$key=$val";
	}
	return join '&', @data;
}



sub run_cgi {
	# Get filehandle for output
	$fh = shift;
	my $query_string = shift;
	my $request_uri = shift;
	my $request_host = shift;

	# Clean globals
	%prog = ();
	@pids = ();
	@displaycols = ();

	# new cgi instance
	$cgi->delete_all() if defined $cgi;
	$cgi = new CGI( $query_string );

	# Get next page
	$nextpage = $cgi->param( 'NEXTPAGE' ) || 'search_progs';

	# Process All options
	process_params();

	# Set HOME env var for forked processes
	$ENV{HOME} = $home;

	my $action = $cgi->param( 'ACTION' ) || $request_uri;
	# Strip the leading '/' to get the action
	$action =~ s|^\/||g;
	# rewrite short-form backwards compatible URIs
	# e.g. http://server/stream?args -> http://server/get_iplayer.cgi?ACTION=stream&args

	# Stream from get_iplayer STDOUT (optionally transcoding if required)
	if ( $action eq 'stream' ) {
		my $ext = $cgi->param( 'OUTTYPE' ) || 'flv';
		# Remove fileprefix
		$ext =~ s/^.*\.//g;
		# lowecase
		$ext = lc( $ext );
		# Stream mime types (tweaked to work well in vlc)
		my %mimetypes = (
			wav 	=> 'audio/x-wav',
			flac	=> 'audio/x-flac',
			mp3 	=> 'audio/mpeg',
			aac	=> 'audio/mpeg',
			m4a	=> 'audio/mpeg',
			rm	=> 'audio/x-pn-realaudio',
			mov 	=> 'video/quicktime',
			mp4	=> 'video/x-flv',
			avi	=> 'video/x-flv',
			flv	=> 'video/x-flv',
			asf	=> 'video/x-ms-asf',
		);

		# Default mime type depending on mode
		####$ext = 'flv' if $opt->{MODES}->{current} =~ /^flash/ && ! $ext;

		# Streamtype overrides any outtype
		$ext = $opt->{STREAMTYPE}->{current} if $opt->{STREAMTYPE}->{current} !~ /(none|^$)/i;

		# If mimetype is defined
		if ( $mimetypes{$ext} ) {
			my $notranscode = 0;

			# flv audio
			$mimetypes{flv} = 'audio/x-flv' if $opt->{PROGTYPES}->{current} =~ m{^(radio|liveradio|podcast)$};

			# Output headers to stream 
			# This will enable seekable: -Accept_Ranges=>'bytes',
			my $headers = $cgi->header( -type => $mimetypes{$ext}, -Connection => 'close' );

			# Send the headers to the browser
			print $se "\r\nHEADERS:\n$headers\n"; #if $opt_cmdline->{debug};
			print $fh $headers;

			# Default Recipies
			# Need to determine --type and then set the default --modes and default outtype for conversion if required
			if ( $opt->{PROGTYPES}->{current} eq 'livetv' ) {
				print $se "INFO: Transcoding disabled for livetv\n";
				$notranscode = 1;
				$ext = 'flv';
			}
			# No conversion for iphone radio as mp3
			$ext = undef if $opt->{MODES}->{current} eq 'iphone' && $ext eq 'mp3';
			# No conversion for realaudio radio as rm
			$ext = undef if $opt->{MODES}->{current} eq 'realaudio' && $ext eq 'rm';
			# stream mp3 natively
			$ext = undef if $ext eq 'mp3';
			# No conversion for flv
			## $ext = undef if $ext eq 'flv';
			# Disable transcoing if none is specified as OUTTYPE/STREAMTYPE - no point in doing this as we have then no idea of the mimetype
			### Need a way to disable transcoding here - pass and check STREAMTYPE?
			if ( $opt->{STREAMTYPE}->{current} =~ /none/i ) {
				print $se "INFO: Transcoding disabled (OUTTYPE=none)\n";
				$ext = undef;
				$notranscode = 1;
			}
			# no transcode if $ext is undefined
			stream_prog( $mimetypes{$ext}, $cgi->param( 'PID' ), $cgi->param( 'PROGTYPES' ), $opt->{MODES}->{current}, $ext, $notranscode, $opt->{BITRATE}->{current}, $opt->{VSIZE}->{current}, $opt->{VFR}->{current} );
		} else {
			print $se "ERROR: Aborting client thread - output mime type is undetermined\n";
		}

	} elsif ( $action eq 'direct' ) {
		# get filename first
		my $progtype = $cgi->param( 'PROGTYPES' );
		my $pid = $cgi->param( 'PID' );
		# If the modes list f set to nothing
		#my $mode = $opt->{MODES}->{current} || $opt->{MODES}->{default};
		my $mode = $cgi->param( 'MODES' );
		my $filename = get_direct_filename( $pid, $mode, $progtype );
		# Use OUTTYPE for transcoding if required - get output ext
		# $cgi->param('STREAMTYPE') || $cgi->param('OUTTYPE') || 'flv' if $action eq 'playlistdirect';
		my $ext = lc( $cgi->param('STREAMTYPE') || $cgi->param( 'OUTTYPE' ) );
		# Remove fileprefix
		$ext =~ s/^.*\.//g;
		# get file source ext
		my $src_ext = $filename;
		$src_ext =~ s/^.*\.//g;
		# Stream mime types
		my %mimetypes = (
			wav 	=> 'audio/x-wav',
			flac	=> 'audio/x-flac',
			aac	=> 'audio/mpeg',
			m4a	=> 'audio/mpeg',
			mp3 	=> 'audio/mpeg',
			rm	=> 'audio/x-pn-realaudio',
			mov 	=> 'video/quicktime',
			mp4	=> 'video/mp4',
			avi	=> 'video/x-flv',
			flv	=> 'video/x-flv',
			asf	=> 'video/x-ms-asf',
		);

		# default recipies
		# Disable transcoding if none is specified as OUTTYPE/STREAMTYPE
		my $notranscode = 0;
		if ( $ext =~ /none/i ) {
			print $se "INFO: Transcoding disabled (OUTTYPE=none)\n";
			$ext = $src_ext;
			$notranscode = 1;

		# cannot stream mp4/avi so transcode to flv
		# Add types here which you want re-muxed into flv
		#if ( $src_ext =~ m{^(mp4|avi|mov|mp3|aac)$} && ! $ext ) {
		} elsif ( $src_ext =~ m{^(mp4|avi|mov)$} && ! $ext ) {
			$ext = 'flv';

		# Else Default to no transcoding
		} elsif ( ! $ext ) {
			$ext = $src_ext;
		}

		print $se "INFO: Streaming OUTTYPE:$ext MIMETYPE=$mimetypes{$ext} FILE:$filename to client\n";

		# If type is defined
		if ( $mimetypes{$ext} ) {

			# Output headers
			# to stream 
			# This will enable seekable -Accept_Ranges=>'bytes',
			my $headers = $cgi->header( -type => $mimetypes{$ext}, -Connection => 'close' );

			# Send the headers to the browser
			print $se "\r\nHEADERS:\n$headers\n"; #if $opt_cmdline->{debug};
			print $fh $headers;

			stream_file( $filename, $mimetypes{$ext}, $src_ext, $ext, $notranscode, $cgi->param( 'BITRATE' ), $cgi->param( 'VSIZE' ), $cgi->param( 'VFR' ) );
		} else {
			print $se "ERROR: Aborting client thread - output mime type is undetermined\n";
		}

	# Get a playlist for a specified 'PROGTYPES'
	} elsif ( $action eq 'playlist' || $action eq 'playlistdirect' || $action eq 'playlistfiles' ) {
		# Output headers
		my $headers = $cgi->header( -type => 'audio/x-mpegurl' );

		# Send the headers to the browser
		print $se "\r\nHEADERS:\n$headers\n"; #if $opt_cmdline->{debug};
		print $fh $headers;

		# determine output type
		my $outtype = $cgi->param('OUTTYPE') || 'flv';
		$outtype = $cgi->param('STREAMTYPE') || $cgi->param('OUTTYPE') || 'flv' if $action eq 'playlistdirect';

		# ( host, outtype, modes, progtype, bitrate, search, searchfields, action )
		print $fh create_playlist_m3u_single( $request_host, $outtype, $opt->{MODES}->{current}, $opt->{PROGTYPES}->{current} , $cgi->param('BITRATE') || '', $opt->{SEARCH}->{current}, $opt->{SEARCHFIELDS}->{current} || 'name', $action );

	# Get a playlist for a specified 'PROGTYPES'
	} elsif ( $action eq 'opml' ) {
		# Output headers
		my $headers = $cgi->header( -type => 'text/xml' );

		# Send the headers to the browser
		print $se "\r\nHEADERS:\n$headers\n"; #if $opt_cmdline->{debug};
		print $fh $headers;
		# ( host, outtype, modes, type, bitrate )
		print $fh get_opml( $request_host, $cgi->param('OUTTYPE') || 'flv', $opt->{MODES}->{current}, $opt->{PROGTYPES}->{current} , $cgi->param('BITRATE') || '', $opt->{SEARCH}->{current}, $cgi->param('LIST') || '' );

	# Get a playlist for a selected progs in form
	} elsif ( $action eq 'genplaylist' || $action eq 'genplaylistdirect' || $action eq 'genplaylistfile' ) {
		# Output headers
		my $headers = $cgi->header( -type => 'audio/x-mpegurl' );
		# To save file
		#my $headers = $cgi->header( -type => 'audio/x-mpegurl', -attachment => 'get_iplayer.m3u' );

		# Send the headers to the browser
		print $se "\r\nHEADERS:\n$headers\n"; #if $opt_cmdline->{debug};
		print $fh $headers;
		
		# determine output type
		my $outtype = $cgi->param('OUTTYPE') || 'flv';
		$outtype = $cgi->param('STREAMTYPE') || $cgi->param('OUTTYPE') if $action eq 'genplaylistdirect';

		# ( host, outtype, modes, bitrate, action )
		print $fh create_playlist_m3u_multi( $request_host, $outtype, $cgi->param('BITRATE') || '', $action );

	# HTML page
	} else {
		# Output header and html start
		begin_html( $request_host );

		# Page Routing
		form_header( $request_host );
		#print $fh $cgi->Dump();
		if ( $opt_cmdline->{debug} ) {
			print $fh $cgi->Dump();
			#for my $key (sort keys %ENV) {
			#    print $fh $key, " = ", $ENV{$key}, "\n";
			#}    
		}
		if ($nextpages{$nextpage}) {
			# call the correct subroutine
			$nextpages{$nextpage}->();
		}

		form_footer();
		html_end();
	}

	$cgi->delete_all();

	return 0;
}


sub pvr_run {
	print $fh "<strong><p>The PVR will auto-run every $opt->{AUTOPVRRUN}->{current} hour(s) if you leave this page open</p></strong>" if $opt->{AUTOPVRRUN}->{current};
	print $se "INFO: Starting PVR Run\n";
	my @cmd = (
		$opt_cmdline->{getiplayer},
		'--nopurge',
		'--nocopyright',
		'--hash',
		'--pvr',
	);
	#print $se "DEBUG: running: $cmd\n";
	print $fh '<pre>';
	# Redirect both STDOUT and STDERR to client browser socket
	run_cmd( $fh, $fh, 1, @cmd );
	print $fh '</pre>';
	print $fh p("PVR Run complete");

	# Load the refresh tab if required
	my $autopvrrun = $cgi->cookie( 'AUTOPVRRUN' ) || $cgi->param( 'AUTOPVRRUN' );

	# Render options actions
	print $fh div( { -class=>'action' },
		ul( { -class=>'action' },
			li( { -class=>'action' }, [
				a(
					{
						-class=>'action',
						-title => 'Run PVR Now',
						-onClick  => "RefreshTab( '?NEXTPAGE=pvr_run&AUTOPVRRUN=$autopvrrun', ".(1000*3600*$autopvrrun).", 1 );",
					},
					'PVR Run Now'
				),
				a(
					{
						-class=>'action',
						-title => 'Close',
						-onClick  => "window.close()",
					},
					'Close'
				),
			]),
		),
	);
}



sub record_now {
	my @record;
	# The 'Record' action button uses SEARCH to pass it's pvr_queue data
	if ( $cgi->param( 'SEARCH' ) ) {
		push @record, $cgi->param( 'SEARCH' );
	} else {
		@record = ( $cgi->param( 'PROGSELECT' ) );
	}

	my @params = get_search_params();
	my $out;

	# If a URL was specified by the User (assume auto mode list is OK):
	if ( $opt->{URL}->{current} =~ m{^http://} ) {
		push @record, "$opt->{PROGTYPES}->{current}|$opt->{URL}->{current}|$opt->{URL}->{current}|-";
	}

	print $fh "<strong><p>Please leave this page open until the recording completes</p></strong>";
	# Render options actions
	print $fh div( { -class=>'action' },
		ul( { -class=>'action' },
			li( { -class=>'action' }, [
				a(
					{
						-class=>'action',
						-title => 'Close',
						-onClick  => "window.close()",
					},
					'Close'
				),
			]),
		),
	);
	print $fh "<p>Recording The Following Programmes</p><ul>\n";
	for (@record) {
		chomp();
		my ( $type, $pid, $name, $episode ) = (split /\|/)[0,1,2,3];
		next if ! ($type && $pid );
		print $fh "<li>$name - $episode ($pid)</li>\n";
	}
	print $fh "</ul><br />\n";
	print $se "INFO: Starting Recording Now\n";
	# Queue all selected 'TYPE|PID|NAME|EPISODE|MODE|CHANNEL' entries in the PVR
	for (@record) {
		chomp();
		my ( $type, $pid, $name, $episode ) = (split /\|/)[0,1,2,3];
		next if ! ($type && $pid );
		my $comment = "$name - $episode";
		my @cmd = (
			$opt_cmdline->{getiplayer},
			'--nopurge',
			'--nocopyright',
			'--expiry=999999999',
			'--hash',
			'--webrequest',
			get_iplayer_webrequest_args(
				"pid=$pid",
				"type=$type",
				build_cmd_options( grep !/^(HISTORY|SINCE|BEFORE|HIDEDELETED|FUTURE|SEARCH|SEARCHFIELDS|VERSIONLIST|PROGTYPES|EXCLUDEC.+)$/, @params )
			),
		);
		print $fh p("Command: ".( join ' ', @cmd ) ) if $opt_cmdline->{debug};
		print $fh '<pre>';
		# Redirect both STDOUT and STDERR to client browser socket
		run_cmd( $fh, $fh, 1, @cmd );
		print $fh '</pre>';
	}
	print $fh p("Recording complete");
	return 0;
}



sub stream_prog {
	my ( $mimetype, $pid , $type, $modes, $ext, $notranscode, $abitrate, $vsize, $vfr ) = ( @_ );
	# Default modes to try
	$modes = $default_modes if ! $modes;
	
	print $se "INFO: Start Streaming $pid to browser using modes '$modes', output ext '$ext', audio bitrate '$abitrate', video size '$vsize', video fram rate '$vfr'\n";

	my @cmd = (
		$opt_cmdline->{getiplayer},
		'--nocopyright',
		'--hash',
		'--expiry=999999999',
		'--webrequest',
		get_iplayer_webrequest_args( 'nopurge=1', "modes=$modes", 'stream=1', "pid=$pid", "type=$type" ),
	);

	# If transcoding on the fly then use shell method of calling processes with a pipe
	if ( $ext && ! $notranscode ) {

		# workaround to add quotes around the args because we are using a shell here
		for ( @cmd ) {
			s/^(.+)$/"$1"/g if ! m{^[\-\"]};
		}
		my $command = join(' ', @cmd);
		open(STDOUT, ">&", $fh ) || die "can't dup client to stdout";

		# Enable buffering
		STDOUT->autoflush(0);
		$fh->autoflush(0);

		# add ffmpeg command pipe
		my @ffcmd = build_ffmpeg_args( '-', $mimetype, $ext, $abitrate, $vsize, $vfr );

		# quote the ffmpeg binary
		$ffcmd[0] = "\"$ffcmd[0]\"";

		# Prepend the pipe
		unshift @ffcmd, '|';
		$command .= ' '.join ' ', @ffcmd;

		print $se "DEBUG: Command: $command\n";
		system( $command );

	} else {
		run_cmd( $fh, $se, 100000, @cmd );
	}

	print $se "INFO: Finished Streaming $pid to browser\n";

	return 0;
}


			
# Stream a file to browser/client
sub stream_file {
	my ( $filename, $mimetype, $src_ext, $ext, $notranscode, $abitrate, $vsize, $vfr ) = ( @_ );

	print $se "INFO: Start Direct Streaming $filename to browser using mimetype '$mimetype', output ext '$ext', audio bitrate '$abitrate', video size '$vsize', video fram rate '$vfr'\n";

	# If transcoding required (i.e. output ext != source ext) - OR, if one of the transcoing options is set
	if ( ( ! $notranscode ) && ( lc( $ext ) ne lc( $src_ext ) || $abitrate || $vsize || $vfr ) ) {
		$fh->autoflush(0);

		my @cmd = build_ffmpeg_args( $filename, $mimetype, $ext, $abitrate, $vsize, $vfr );
		run_cmd( $fh, $se, 100000, @cmd );
		print $se "INFO: Finished Streaming and transcoding $filename to browser\n";

	} else {
		print $se "INFO: Streaming file directly: $filename\n";
		if ( ! open( STREAMIN, "< $filename" ) ) {
			print $se "INFO: Cannot Read file '$filename'\n";
			exit 4;
		}

		# Read each char from command output and push to socket fh
		my $char;
		my $bytes;
		# Assume that we don't want to buffer STDERR output of the command
		my $size = 100000;
		while ( $bytes = read( STREAMIN, $char, $size ) ) {
			if ( $bytes <= 0 ) {
				close STREAMIN;
				print $se "DEBUG: Stream thread has completed\n";
				exit 0;
			} else {
				print $fh $char;
				print $se '#';
			}
			last if $bytes < $size;
		}
		close STREAMIN;
		print $se "INFO: Finished Streaming $filename to browser\n";
	}

	return 0;
}



sub build_ffmpeg_args {
		my ( $filename, $mimetype, $ext, $abitrate, $vsize, $vfr ) = ( @_ );
		my @cmd_aopts;
		if ( $abitrate =~ m{^\d+$} ) {
			# if this is flv stream output then use the AAC codec
			if ( lc( $ext ) =~ m{^(flv|aac|m4a)$} ) {
				# Tweak: ffmpeg cannot understand aac or m4a as audio output formats - force flash audio
				$ext = 'flv' if lc( $ext ) =~ m{^(aac|m4a)$} && $mimetype =~ m{^audio};
				push @cmd_aopts, ( '-acodec', 'libfaac', '-ab', "${abitrate}k" );
			# else just copy  the codec?
			} else {
				push @cmd_aopts, ( '-ab', "${abitrate}k" );
			}
		} else {
			if ( lc( $ext ) eq 'flv' ) {
				# 160k is the max for libfaac!
				push @cmd_aopts, ( '-acodec', 'libfaac', '-ab', '160k' );
			}
			# cannot copy code if for example we have an aac stream output as WAV (e.g. squeezebox liveradio flashaac)
			#push @cmd_aopts, ( '-acodec', 'copy' );
		}

		my @cmd;
		# If conversion is necessary
		# Video
		if ( $mimetype =~ m{^video} ) {
			my @cmd_vopts;

			# Apply video size
			push @cmd_vopts, ( '-s', "${vsize}" ) if $vsize =~ m{^\d+x\d+$};

			# Apply video framerate - caveat - bitrate defaults to 200k if only vfr is set
			push @cmd_vopts, ( '-r', $vfr ) if $vfr =~ m{^\d$};
			
			# -sameq is bad
			## Apply sameq if framerate only and no bitrate
			#push @cmd_vopts, '-sameq' if $vfr =~ m{^\d$} && $vsize !~ m{^\d+x\d+$};

			# Add in the codec if we are transcoding and not remuxing the stream
			if ( @cmd_vopts ) {
				push @cmd_vopts, ( '-vcodec', 'libx264' );
			} else {
				push @cmd_vopts, ( '-vcodec', 'copy' );
			}

			@cmd = (
				$opt_cmdline->{ffmpeg},
				#'-f', $src_ext, # not required?
				'-i', $filename,
				@cmd_aopts,
				@cmd_vopts,					
				'-f', $ext,
				'-',
			);
		# Audio
		} else {
			@cmd = (
				$opt_cmdline->{ffmpeg},
				#'-f', $src_ext, # not required?
				'-i', $filename,
				'-vn',
				@cmd_aopts,
				'-ac', 2,
				'-f', $ext,
				'-',
			);
		}
		print $se "DEBUG: Command args: ".(join ' ', @cmd)."\n";
		return @cmd;
}



sub create_playlist_m3u_single {
	my ( $request_host, $outtype, $modes, $type, $bitrate, $search, $searchfields, $request ) = ( @_ );
	my @playlist;
	$outtype =~ s/^.*\.//g;

	my $searchterm = $search;
	# this is already a wildcard default regex...
	if ( $search eq '.*' ) {
		$searchterm = '.*';
	# if it's a URL then bypass regex stuff
	} elsif ( $search =~ m{^http} ) {
		$searchterm = $search;
	# make search term regex friendly
	} else {
		$searchterm =~ s|([\/\.\?\+\-\*\^\(\)\[\]\{\}])|\\$1|g;
	}
		
	print $se "INFO: Getting playlist for type '$type' using modes '$modes' and bitrate '$bitrate'\n";
	my @cmd = (
		$opt_cmdline->{getiplayer},
		'--nocopyright',
		'--expiry=999999999',
		'--webrequest',
		get_iplayer_webrequest_args( 'nopurge=1', "type=$type", 'listformat=ENTRY|<pid>|<name>|<episode>|<desc>|<filename>|<mode>', "fields=$searchfields", "search=$searchterm" ),
	);
	# Only add history search if the request is of this type or is a PlayFile from localfiles type
	if ( ( $request eq 'playlistfiles' || $request eq 'playlistdirect' ) && ! ( $search =~ m{^/} && $searchfields eq 'pid' ) ) {
		push @cmd, '--history', '--skipdeleted';
	}
	my @out = get_cmd_output( @cmd );

	push @playlist, "#EXTM3U\n";

	# Extract and rewrite into m3u format
	# /home/lewispj/mp3/Rock/radiohead/Ok Computer/radiohead - (07) fitter happier.mp3||(07) Fitter Happier|, , (256kbps/44.1kHz)|<filename>|<mode>
	for ( grep !/^(Added:|Matches|$)/ , @out ) {
		chomp();
		my $url;
		my ( $pid, $name, $episode, $desc, $filename, $mode, $channel ) = (split /\|/)[1,2,3,4,5,6,7];
		#print $se "DEBUG: $pid, $name, $episode, $desc, $filename, $mode\n";
		# sanitze modes && filename
		$mode = '' if $mode eq '<mode>';
		$filename = '' if $filename eq '<filename>';

		# playlist with direct streaming for files through webserver
		if ( $request eq 'playlistdirect' ) {
			next if ! ( $pid && $type && $mode );
			$url = build_url_direct( $request_host, $type, $pid, $mode, basename( $filename ), $opt->{STREAMTYPE}->{current}, $opt->{HISTORY}->{current}, $opt->{BITRATE}->{current}, $opt->{VSIZE}->{current}, $opt->{VFR}->{current} );

		# If pid is actually a filename then use it cos this is a local file type programme
		} elsif ( $request eq 'playlistfiles' && $pid =~ m{^/} ) {
			next if ! $pid;
			$url = search_absolute_path( $pid ) if $pid;

		# playlist with local files
		} elsif ( $request eq 'playlistfiles' ) {
			next if ! $filename;
			$url = search_absolute_path( $filename );

		# playlist of proxied urls for streaming online prog via web server
		} else {
			next if ! ( $type && $pid );
			my $suffix = "${pid}.${outtype}";
			$url = build_url_stream( $request_host, $type, $pid, $mode || $modes, $suffix, $opt->{STREAMTYPE}->{current}, $opt->{BITRATE}->{current}, $opt->{VSIZE}->{current}, $opt->{VFR}->{current} );
		}

		# Format required, e.g.
		##EXTINF:-1,BBC Radio - BBC Radio One (High Quality Stream)
		push @playlist, "#EXTINF:-1,$type - $channel - $name - $episode - $desc";
		push @playlist, "$url\n";
		
	}
	print $se join ("\n", @playlist);
	return join ("\n", @playlist);
}



sub create_playlist_m3u_multi {
	my ( $request_host, $outtype, $bitrate, $request ) = ( @_ );
	my @playlist;
	push @playlist, "#EXTM3U\n";

	my @record = ( $cgi->param( 'PROGSELECT' ) );

	# If a URL was specified by the User (assume auto mode list is OK):
	if ( $opt->{URL}->{current} =~ m{^http://} ) {
		push @record, "$opt->{PROGTYPES}->{current}|$opt->{URL}->{current}|$opt->{URL}->{current}|-";
	}

	# Create m3u from all selected 'TYPE|PID|NAME|EPISODE|MODE|CHANNEL' entries in the PVR
	for (@record) {
		my $url;
		chomp();
		my ( $type, $pid, $name, $episode, $mode, $channel ) = (split /\|/)[0,1,2,3,4,5];
		next if ! ($type && $pid );

		# playlist with direct streaming fo files through webserver
		if ( $request eq 'genplaylistdirect' ) {
			$url = build_url_direct( $request_host, $type, $pid, $mode, $outtype, $opt->{STREAMTYPE}->{current}, $opt->{HISTORY}->{current}, $opt->{BITRATE}->{current}, $opt->{VSIZE}->{current}, $opt->{VFR}->{current} );

		# playlist with local files
		} elsif ( $request eq 'genplaylistfile' ) {
			# If pid is actually a filename then use it cos this is a local file type programme
			if ( $pid =~ m{^/} ) {
				my $filename = search_absolute_path( $pid );
				$url = $filename if $filename;
			} else {
				# Lookup filename (add it if defined - even if relative)
				# check for -f $filename if you want to exclude files that cannot be found
				my $filename = get_direct_filename( $pid, $mode, $type );
				$url = $filename if $filename;
			}

		# Uncomment this to make all playlists local for localfiles types
		# If pid is actually a filename then use it cos this is a local file type programme
		#} elsif ( $pid =~ m{^/} ) {
		#	my $filename = search_absolute_path( $pid );
		#	$url = $filename if $filename;

		# playlist of proxied urls for streaming online prog via web server
		} else {
			my $suffix = "${pid}.${outtype}";
			$url = build_url_stream( $request_host, $type, $pid, $mode || $opt->{MODES}->{current}, $suffix, $opt->{STREAMTYPE}->{current}, $opt->{BITRATE}->{current}, $opt->{VSIZE}->{current}, $opt->{VFR}->{current} );
		}

		# Skip empty urls
		next if ! $url;
		
		# Format required, e.g.
		##EXTINF:-1,BBC Radio - BBC Radio One (High Quality Stream)
		#http://localhost:1935/stream?PID=liveradio:bbc_radio_one&MODES=flashaac&OUTTYPE=bbc_radio_one.wav
		push @playlist, "#EXTINF:-1,$type - $channel - $name - $episode";
		push @playlist, "$url\n";

	}
	print $se join ("\n", @playlist);
	return join ("\n", @playlist);
}



sub get_opml {
	my ( $request_host, $outtype, $modes, $type, $bitrate, $search, $list ) = ( @_ );
	my @playlist;
	$outtype =~ s/^.*\.//g;

	#<?xml version="1.0" encoding="UTF-8"?>
	#<opml version="1.1">
	#  <head>
	#    <title>Grateful Dead - 1995-07-09-Chicago, IL</title>
	#  </head>
	#  <body>
	#    <outline URL="http://www.archive.org/.../gd1995-07-09d1t01_vbr.mp3" bitrate="200" source="Soundboard" text="Touch Of Grey" type="audio" />
	#    <outline URL="http://www.archive.org/.../gd1995-07-09d1t02_vbr.mp3" bitrate="203" source="Soundboard" text="Little Red Rooster" type="audio" />
	#    <outline URL="http://www.archive.org/.../gd1995-07-09d1t03_vbr.mp3" bitrate="194" source="Soundboard" text="Lazy River Road" type="audio" />
	#  </body>
	#</opml>

	print $se "INFO: Getting playlist for type '$type' using modes '$modes', bitrate '$bitrate', search='$search' and list '$list'\n";

	# Header
	push @playlist, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<opml version=\"1.1\">";

	# Programmes
	if (! $list) {

		# Header
		push @playlist, "\t<head>\n\t\t\n\t</head>";
		push @playlist, "\t<body>";

		# Extract and rewrite into playlist format
		my @out = get_cmd_output(
			$opt_cmdline->{getiplayer},
			'--nocopyright',
			'--expiry=999999999',
			'--webrequest',
			get_iplayer_webrequest_args( 'nopurge=1', "type=$type", 'listformat=<pid>|<name>|<episode>|<desc>', "search=$search" ),
		);
		for ( grep !/^(Added:|Matches|$)/, @out ) {
			chomp();
			# Strip unprinatble chars
			s/(.)/(ord($1) > 127) ? "" : $1/egs;
			my ($pid, $name, $episode, $desc) = (split /\|/)[0,1,2,3];
			next if ! ( $pid && $name );
			push @playlist, "\t\t<outline URL=\"".encode_entities( build_url_stream( $request_host, $type, $pid, $modes, $outtype ) )."\"  bitrate=\"${bitrate}\" source=\"get_iplayer\" title=\"".encode_entities("$name - $episode - $desc")."\" text=\"".encode_entities("$name - $episode - $desc")."\" type=\"audio\" />";
		}

	# Top-level Menu
	} elsif ( lc($list) eq 'menu' ) {
		my %menu = (
			'BBC Live Radio (National)' 	=> "${request_host}?ACTION=opml&PROGTYPES=liveradio&SEARCH=%20\\d&OUTTYPE=wav",
			'BBC Live Radio (All)' 		=> "${request_host}?ACTION=opml&PROGTYPES=liveradio&OUTTYPE=wav",
			'BBC iPlayer Radio Listen Again'=> "${request_host}?ACTION=opml&PROGTYPES=radio&LIST=channel",
		);

		# Header
		push @playlist, "\t<head title=\"GetIplayer\">\n\t\t\n\t</head>";
		push @playlist, "\t<body>";
		for my $item ( sort keys %menu ) {
			my $item_url = $menu{ $item };
			#http://localhost:1935/opml?PROGTYPES=<type>SEARCH=bbc+radio+1&MODES=${modes}&OUTTYPE=a.wav
			push @playlist, "\t\t<outline URL=\"".encode_entities( $item_url )."\" text=\"".encode_entities( "$item" )."\" />";
		}
		
	# Channels/Names etc
	} elsif ($list) {
	
		# Header
		push @playlist, "\t<head>\n\t\t\n\t</head>";
		push @playlist, "\t<body>";

		# Extract and rewrite into playlist format
		my @out = get_cmd_output(
			$opt_cmdline->{getiplayer},
			'--nocopyright',
			'--expiry=999999999',
			'--webrequest',
			get_iplayer_webrequest_args( 'nopurge=1', "type=$type", "list=$list", "channel=$search" ),
		);
		for ( grep !/^(Added:|Matches|$)/, @out ) {
			my $suffix;
			chomp();
			# Strip unprinatble chars
			s/(.)/(ord($1) > 127) ? "" : $1/egs;
			next if ! m{^.+\(\d+\)$};
			my $item = $_;
			s/\s*\(\d+\)$//g;
			my $itemregex = '^'.$_.'$';
			# URL encode it
			$itemregex =~ s/([^A-Za-z0-9])/sprintf("%%%02X", ord($1))/seg;
			# Stateful addition of search terms
			$suffix = '&LIST=name' if $list eq 'channel';
			# Format required, e.g.
			#http://localhost:1935/opml?PROGTYPES=<type>SEARCH=bbc+radio+1&MODES=${modes}&OUTTYPE=a.wav
			push @playlist, "\t\t<outline URL=\"".encode_entities("${request_host}?ACTION=opml&PROGTYPES=${type}&SEARCH=${itemregex}${suffix}&MODES=${modes}&OUTTYPE=a.wav")."\" text=\"".encode_entities("$item")."\" title=\"".encode_entities("$item")."\" type=\"playlist\" />";
		}

	}

	# Footer
	push @playlist, "\t</body>\n</opml>";

	return join ("\n", @playlist);
}



### Playlist URL builders
sub build_url_direct {
	my ( $request_host, $progtypes, $pid, $modes, $outtype, $streamtype, $history, $bitrate, $vsize, $vfr ) = ( @_ );
	# Sanity check
	#print $se "DEBUG: building direct playback request using:  PROGTYPES=${progtypes}  PID=${pid}  MODES=${modes}  OUTTYPE=${outtype}\n";
	# CGI::escape
	$_ = CGI::escape($_) for ( $progtypes, $pid, $modes, $outtype, $streamtype, $history, $bitrate, $vsize );
	#print $se "DEBUG: building direct playback request using:  PROGTYPES=${progtypes}  PID=${pid}  MODES=${modes}  OUTTYPE=${outtype}  BITRATE=${bitrate}  VSIZE=${vsize}  VFR=${vfr}\n";
	# Build URL
	return "${request_host}?ACTION=direct&PROGTYPES=${progtypes}&PID=${pid}&MODES=${modes}&HISTORY=${history}&OUTTYPE=${outtype}&STREAMTYPE=${streamtype}&BITRATE=${bitrate}&VSIZE=${vsize}&VFR=${vfr}";
}


# "${request_host}?ACTION=stream&PROGTYPES=${type}&PID=${pid}&MODES=${modes}&OUTTYPE=${suffix}";
sub build_url_stream {
	my ( $request_host, $progtypes, $pid, $modes, $outtype, $streamtype, $bitrate, $vsize, $vfr ) = ( @_ );
	# Sanity check
	#print $se "DEBUG: building stream playback request using:  PROGTYPES=${progtypes}  PID=${pid}  MODES=${modes}  OUTTYPE=${outtype}\n";
	# CGI::escape
	$_ = CGI::escape($_) for ( $progtypes, $pid, $modes, $outtype, $streamtype, $bitrate, $vsize, $vfr );
	#print $se "DEBUG: building stream playback request using:  PROGTYPES=${progtypes}  PID=${pid}  MODES=${modes}  OUTTYPE=${outtype}\n";
	# Build URL
	return "${request_host}?ACTION=stream&PROGTYPES=${progtypes}&PID=${pid}&MODES=${modes}&OUTTYPE=${outtype}&STREAMTYPE=${streamtype}&BITRATE=${bitrate}&VSIZE=${vsize}&VFR=${vfr}";
}


# Play from Internet/'Play':		 ?ACTION=playlist	&SEARCHFIELDS=pid	&SEARCH=$pid	&MODES=${modes}	&PROGTYPES=${type}	&OUTTYPE=${outtype}'
## 'PlayFile' - works with vlc
# Play from local file/'PlayFile'	 ?ACTION=playlistfiles	&SEARCHFIELDS=pid	&SEARCH=$pid	&MODES=${modes}	&PROGTYPES=${type}
## 'PlayWeb' - not on vlc
# Play from file on web server/'PlayWeb' ?ACTION=playlistdirect	&SEARCHFIELDS=pid	&SEARCH=$pid	&MODES=${modes}
sub build_url_playlist {
	my ( $request_host, $action, $searchfields, $search, $modes, $progtypes, $outtype, $streamtype, $bitrate, $vsize, $vfr ) = ( @_ );
	# Sanity check
	#print $se "DEBUG: building $action request using:  SEARCHFIELDS=${searchfields}  SEARCH=${search}  MODES=${modes}  PROGTYPES=${progtypes}  OUTTYPE=${outtype}\n";
	# CGI::escape
	$_ = CGI::escape($_) for ( $action, $searchfields, $search, $modes, $progtypes, $outtype, $streamtype, $bitrate, $vsize, $vfr );
	#print $se "DEBUG: building $action request using:  SEARCHFIELDS=${searchfields}  SEARCH=${search}  MODES=${modes}  PROGTYPES=${progtypes}  OUTTYPE=${outtype}\n";
	# Build URL
	return "${request_host}?ACTION=${action}&SEARCHFIELDS=${searchfields}&SEARCH=${search}&MODES=${modes}&PROGTYPES=${progtypes}&OUTTYPE=${outtype}&STREAMTYPE=${streamtype}&BITRATE=${bitrate}&VSIZE=${vsize}&VFR=${vfr}";
}



# Update script
# Generic
# Updates and overwrites this script - makes backup as <this file>.old
# Update logic:
# If the get_iplayer.cgi script is unwritable then quit
# update script
sub update_script {
	my $update_url	= 'http://www.infradead.org/get_iplayer/latest/get_iplayer.cgi';
	# Get version URL
	my $script_file = $0;
	my $ua = create_ua('update');

	# If the get_iplayer script is unwritable then quit - makes it harder for deb/rpm installed scripts to be overwritten
	if ( ! -w $script_file ) {
		print $se "ERROR: $script_file is not writable - aborting update\n";
		exit 1;
	}

	print $se "INFO: Updating $script_file (from $VERSION)\n";
	print $fh p("Updating $script_file (from $VERSION)");
	if ( update_file( $ua, $update_url, $script_file ) ) {
		print $fh p("Updating Web PVR Manager Failed");
	} else {
		print $fh p("Updating Web PVR Manager Succeeded - please restart the get_iplayer Web PVR Manager service");
	}

	print $se "INFO: Updating get_iplayer\n";
	my @cmd = (
		$opt_cmdline->{getiplayer},
		'--nocopyright',
		'--expiry=999999999',
		'--nopurge',
		'--update',
	);
	print $fh '<pre>';
	run_cmd( $fh, $se, 1, @cmd );
	print $fh '</pre>';
	print $fh p("Updated get_iplayer");

	# Render options actions
	print $fh div( { -class=>'action' },
		ul( { -class=>'action' },
			li( { -class=>'action' }, [
				a(
					{
						-class=>'action',
						-title => 'Go Back',
						-onClick  => "history.back()",
					},
					'Back'
				),
			]),
		),
	);

	return 0;
}



sub create_ua {
	my $ua = LWP::UserAgent->new;
	$ua->timeout( 10 );
	$ua->agent( "get_iplayer Web PVR Manager updater version $VERSION" );
	$ua->conn_cache(LWP::ConnCache->new());
	return $ua;
};	



# Generic
# Gets the contents of a URL and retries if it fails, returns '' if no page could be retrieved
# Usage <content> = request_url_retry(<ua>, <url>, <retries>, <succeed message>, [<fail message>]);
sub request_url_retry {

	my %OPTS = @LWP::Protocol::http::EXTRA_SOCK_OPTS;
	$OPTS{SendTE} = 0;
	@LWP::Protocol::http::EXTRA_SOCK_OPTS = %OPTS;
	
	my ($ua, $url, $retries, $succeedmsg, $failmsg) = @_;
	my $res;

	# Malformed URL check
	if ( $url !~ m{^\s*http\:\/\/}i ) {
		print $se "ERROR: Malformed URL: '$url'\n";
		return '';
	}

	my $i;
	print $se "INFO: Getting page $url\n" if $opt->{verbose};
	for ($i = 0; $i < $retries; $i++) {
		$res = $ua->request( HTTP::Request->new( GET => $url ) );
		if ( ! $res->is_success ) {
			print $se $failmsg;
		} else {
			print $se $succeedmsg;
			last;
		}
	}
	# Return empty string if we failed
	return '' if $i == $retries;

	return $res->content;
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
		print $se "ERROR: Could not download update for ${dest_file} - Update aborted\n";
		return 1;
	}
	# If the download was successful then copy over this file and make executable after making a backup of this script
	if ( -f $dest_file ) {
		if ( ! copy($dest_file, $dest_file.'.old') ) {
			print $se "ERROR: Could not create backup file ${dest_file}.old - Update aborted\n";
			return 1;
		}
	}
	# Check if file is writable
	if ( not open( FILE, "> $dest_file" ) ) {
		print $se "ERROR: $dest_file is not writable by the current user - Update aborted\n";
		return 1;
	}
	# Windows needs this
	binmode FILE;
	# Write contents to file
	print FILE $res;
	close FILE;
	chmod 0755, $dest_file;
	print $se "INFO: Downloaded $dest_file\n";
	return 0;
}



# Invokes command in @args as a system call (hopefully) without using a shell
#  Can also redirect all stdout and stderr to either: STDOUT, STDERR or unchanged
# Usage: run_cmd( <''|STDOUTFH>, <''|STDERRFH>, @args )
# Returns: exit code
# Note: doesn't appear to work with 'in memory' filehandles
sub run_cmd_unix {
	# Define what to do with STDOUT and STDERR of the child process
	my $fh_child_out = shift || "STDOUT";
	my $fh_child_err = shift || "STDERR";
	my @cmd = ( @_ );
	my $rtn;

	print $se "INFO: Command: ".(join ' ', @cmd)."\n"; # if $opt->{verbose};

	# Check if we have IPC::Open3 otherwise fallback on system()
	eval "use IPC::Open3";
	
	# probably only likely in win32
	if ($@) {
		print $se "ERROR: Please download and run latest installer - 'IPC::Open3' is not available\n";
		exit 1;

	# Use open3()
	} else {
		#print $se "INFO: open3( 0, \">&".fileno($fh_child_out).", \">&".fileno($fh_child_err).", <cmd> )\n";
		# Don't use NULL for the 1st arg of open3 otherwise we end up with a messed up STDIN once it returns
		my $procid = open3( 0, ">&".fileno($fh_child_out), ">&".fileno($fh_child_err), @cmd );
		# Wait for child to complete
		waitpid( $procid, 0 );
		$rtn = $?;
	}

	# Interpret return code	      
	return interpret_return_code( $rtn );
}



# Invokes command in @args as a system call (hopefully) without using a shell
#  Can also redirect all stdout and stderr to either: STDOUT, STDERR or unchanged
# Usage: run_cmd( $stdout_fh, $stderr_fh, <buf_size>, @args )
# Returns: exit code
sub run_cmd {

	# win32 kludge cos win is so broken
	return run_cmd_win32( @_ ) if IS_WIN32;

	# Define what to do with STDOUT and STDERR of the child process
	use IO::Select;
	use Symbol qw(gensym);
	my $fh_cmd_out = shift;
	my $fh_cmd_err = shift;
	my $size = shift;
	my $from = new IO::Handle;
	my $err = new IO::Handle;
	my @cmd = ( @_ );
	my $rtn;

	$fh_cmd_out->autoflush(1);
	$fh_cmd_err->autoflush(1);
	
	print $se "INFO: Command: ".(join ' ', @cmd)."\n"; # if $opt->{verbose};

	# Check if we have IPC::Open3 otherwise fallback on system()
	eval "use IPC::Open3";
	
	# probably only likely in win32
	if ($@) {
		print $se "ERROR: Please download and run latest installer - 'IPC::Open3' is not available\n";
		exit 1;

	# Use open3()
	} else {
		my $procid;
		# Setup signal handlers so that when the browser is closed the SIGPIPE results in sending a SIGTERM to the forked command.
		local $SIG{PIPE} = sub {
			my $signal = shift;
			print $se "\nINFO: $$ Cleaning up (signal = $signal), killing cmd PID=$procid:\n";
			for my $sig ( qw/INT PIPE TERM KILL/ ) {
				# Kill process with SIGs
				print $se "INFO: $$ killing cmd PID=$procid with SIG${sig}\n";
				kill $sig, $procid;
				sleep 1;
				if ( ! kill 0, $procid ) {
					print $se "INFO: $$ killed cmd PID=$procid\n";
					last;
				}
				sleep 4;
			}
			exit 0;
		};

		# Don't use NULL for the 1st arg of open3 otherwise we end up with a messed up STDIN once it returns
		$procid = open3( gensym, $from, $err, @cmd ) || print $se "ERROR: Could not execute command: $!\n";

		my $childpidout = fork();

		# Fork a child process to read from the indirect (STDOUT) fh of the spawned command and write it to the selected fh (browser client)
		if ( $childpidout <= 0 ) {
			# Not sure if these are necessary:
			$fh_cmd_out->autoflush(1);
			$from->autoflush(1);
			# Read each char from command output and push to socket fh
			my $char;
			my $bytes;
			while ( $bytes = read( $from, $char, $size ) ) {
				if ( $bytes <= 0 ) {
					print $se "DEBUG: STDOUT fd closed - exiting thread\n";
					exit 0;
				} else {
					print $fh_cmd_out $char;
				}
				last if $bytes < $size;
			}
			#print $se "CMD STDOUT FH EMPTY\n";
			exit 0;
		# Parent continues here
		} elsif ( defined $childpidout ) {
			print $se "DEBUG: Forked STDOUT reader with PID $childpidout\n";
		# Failed to fork
		} else {
			print $se "ERROR: Failed to fork STDOUT reader process: $!\n";
			exit 1;
		}
		
		my $childpiderr = fork();

		# Fork a child process to read from the indirect (STDERR) fh of the spawned command and write it to the selected fh (browser client)
		if ( $childpiderr <= 0 ) {
			# Not sure if these are necessary:
			$fh_cmd_err->autoflush(1);
			$err->autoflush(1);
			# Read each char from command output and push to socket fh
			my $char;
			my $bytes;
			# Assume that we don't want to buffer STDERR output of the command
			$size = 1;
			while ( $bytes = read( $err, $char, $size ) ) {
				if ( $bytes <= 0 ) {
					print $se "DEBUG: STDERR fd closed - exiting thread\n";
					exit 0;
				} else {
					print $fh_cmd_err $char;
				}
				last if $bytes < $size;
			}
			#print $se "CMD STDERR FH EMPTY\n";
			exit 0;
		# Parent continues here
		} elsif ( defined $childpiderr ) {
			print $se "DEBUG: Forked STDERR reader with PID $childpiderr\n";
		# Failed to fork
		} else {
			print $se "ERROR: Failed to fork STDERR reader process: $!\n";
			exit 1;
		}

		# Reap reader processes
		waitpid( $childpidout, 0 );
		waitpid( $childpiderr, 0 );

		# Reap command child
		waitpid( $procid, 0 );
		$rtn = $?;

		# Restore sigpipe handler for reader and writer processes
		$SIG{PIPE} = 'DEFAULT';
	}

	# Interpret return code	      
	return interpret_return_code( $rtn );
}



# Works except for where both from and err go to fh - does not die when browser closes.
# Also the browser does not get closed after cmd completes...
# Uses shell when stderr needs to be redirected to stdout
sub run_cmd_win32 {
	# Define what to do with STDOUT and STDERR of the child process
	my $fh_child_out = shift;
	my $fh_child_err = shift;
	my $size = shift;
	my @cmd = ( @_ );
	# eek! - works around win32 inability to redirect STDERR nicely
	# If the stderr is supposed to go to the same fh and stdout then add '2>&1'
	push @cmd, '2>&1' if fileno($fh_child_out) == fileno($fh_child_err);
	my $rtn;

	# Disable buffering
	$fh_child_out->autoflush(1);

	print $se "INFO: Win32 Command: ".(join ' ', @cmd)."\n"; # if $opt->{verbose};

	# Redirect $fh_child_out to STDOUT
	open(STDOUT, ">&", $fh_child_out ) || die "can't dup client to stdout";

	$rtn = system( @cmd );

	# Interpret return code	      
	return interpret_return_code( $rtn );
}



# Same as backticks but without needing a shell
# sets $?
# returns array of output
sub get_cmd_output {

	# win32 kludge cos win is so broken
	return get_cmd_output_win32( @_ ) if IS_WIN32;

	use Symbol qw(gensym);
	my @cmd = ( @_ );
	#my $to = new IO::Handle;
	my $from = new IO::Handle;
	my $error = new IO::Handle;
	my $rtn;
	my @out_from;
	my @out_error;

	#$to->autoflush(1);
	$from->autoflush(1);
	$error->autoflush(1);
	
	print $se "INFO: Command: ".(join ' ', @cmd)."\n"; # if $opt->{verbose};

	# Check if we have IPC::Open3 otherwise fallback on system()
	eval "use IPC::Open3";

	# probably only likely in win32
	if ($@) {
		print $se "ERROR: Please download and run latest installer - 'IPC::Open3' is not available\n";
		exit 1;

	# Use open3()
	} else {
		my $procid;
		# Setup signal handlers so that when the browser is closed the SIGPIPE results in sending a SIGTERM to the forked command.
		local $SIG{PIPE} = sub {
			my $signal = shift;
			print $se "\nINFO: $$ Cleaning up (signal = $signal), killing cmd PID=$procid:\n";
			for my $sig ( qw/INT PIPE TERM KILL/ ) {
				# Kill process with SIGs
				print $se "INFO: $$ killing cmd PID=$procid with SIG${sig}\n";
				kill $sig, $procid;
				sleep 1;
				if ( ! kill 0, $procid ) {
					print $se "INFO: $$ killed cmd PID=$procid\n";
					last;
				}
				sleep 4;
			}
			exit 0;
		};

		#print $se "INFO: open3( 0, \">&".fileno($fh_child_out).", \">&".fileno($fh_child_err).", <cmd> )\n";
		# Don't use NULL for the 1st arg of open3 otherwise we end up with a messed up STDIN once it returns
		$procid = open3( gensym, $from, $error, @cmd );
		# Wait for child to complete

		my $childpid = fork();
		# Child
		if ( $childpid == 0 ) {
			while ( <$error> ) {
				print $se "CMD STDERR: $_";
			}
			#print $se "CMD STDERR EMPTY\n";
			exit 0;
		# Parent
		} elsif ( defined $childpid ) {
			while ( <$from> ) {
				push @out_from, $_;
			}
		} else {
			print $se "ERROR: Could not fork STDERR reader process\n";
			exit 1;
		}
		waitpid( $childpid, 0 );

		waitpid( $procid, 0 );
		$rtn = $?;

		# Restore sigpipe handler for reader and writer processes
		$SIG{PIPE} = 'DEFAULT';
	}

	# Interpret return code	      
	interpret_return_code( $rtn );
	
	return @out_from;
}



# Still uses shell
sub get_cmd_output_win32 {
	my ( @cmd ) = ( @_ );

	# workaround to add quotes around the args because we are using a shell here
	for ( @cmd ) {
		s/^(.+)$/"$1"/g if ! m{^[\-\"]};
	}

	print $se "DEBUG: Command: ".( join ' ', @cmd )."\n";
	open( CMD, ( join ' ', @cmd ).'|' ) || print $se "ERROR: echo failed: $!\n";
	my @out = <CMD>;
	close CMD;

	# Interpret return code	      
	interpret_return_code( $? );

	return @out;
}



sub interpret_return_code {
	my $rtn = $_;
	# Interpret return code	and force return code 2 upon error      
	my $return = $rtn >> 8;
	if ( $rtn == -1 ) {
		print $se "ERROR: Command failed to execute: $!\n";
		$return = 2 if ! $return;
	} elsif ( $rtn & 128 ) {
		print $se "WARNING: Command executed but coredumped\n";
		$return = 2 if ! $return;
	} elsif ( $rtn & 127 ) {
		print $se sprintf "WARNING: Command executed but died with signal %d\n", $rtn & 127;
		$return = 2 if ! $return;
	}
	print $se sprintf "INFO: Command exit code %d\n", $return if $return;
	return $return;
}



sub get_pvr_list {
	my $pvrsearch;
	my $out = join "\n", get_cmd_output(
		$opt_cmdline->{getiplayer},
		'--nocopyright',
		'--expiry=999999999',
		'--pvrlist',
	);
	# Remove text before first pvrsearch entry
	$out =~ s/^.+?(pvrsearch\s.+)$/$1/s;
	# Parse all 'pvrsearch' elements
	for ( split /pvrsearch\s+\=\s+/, $out ) {
		next if /^get_iplayer/;
		my $name;
		$_ = "pvrsearch = $_";
		# Get each element
		while ( /([\w\-]+?)\s+=\s+(.+?)\n/sg ) {
			if ( $1 eq 'pvrsearch' ) {
				$name = $2;
			}
			$pvrsearch->{$name}->{$1} = $2;
			# Remove disabled entries
			if ( $pvrsearch->{$name}->{disable} == 1 ) {
				delete $pvrsearch->{$name};
				last;
			}
		}
	}
	return $pvrsearch;
}



sub show_pvr_list {
	my %fields;
	my $pvrsearch = get_pvr_list();
	my $sort_field = $cgi->param( 'PVRSORT' ) || 'name';
	my $reverse = $cgi->param( 'PVRREVERSE' ) || '0';

	# Sort data
	my @pvrsearches = get_sorted( $pvrsearch, $sort_field, $reverse );

	# Parse all 'pvrsearch' elements to get all fields used
	for my $name ( @pvrsearches ) {
		# Get each element
		for ( keys %{ $pvrsearch->{$name} } ) {
			$fields{$_} = 1;
		}
	}

	# Render options actions
	my $buttons = div( { -class=>'action' },
		ul( { -class=>'action' },
			li( { -class=>'action' }, [
				a(
					{
						-class=>'action',
						-title => 'Go Back',
						-onClick  => "history.back()",
					},
					'Back'
				),
				a(
					{
						-class => 'action',
						-title => 'Delete selected programmes from PVR search list',
						-onClick => "if(! check_if_selected(document.form, 'PVRSELECT')) { alert('No programmes were selected'); return false; } BackupFormVars(form); form.NEXTPAGE.value='pvr_del'; form.submit(); RestoreFormVars(form);",
					},
					'Delete'
				),
			]),
		),
	);
	
	my @html;
	my @displaycols = ( 'pvrsearch', ( grep !/pvrsearch/, ( sort keys %fields ) ) );
	# Build header row
	push @html, "<tr class=\"search\" >";
	push @html, th( { -class => 'search' }, checkbox( -class=>'search', -title=>'Select/Unselect All PVR Searches', -onClick=>"check_toggle(document.form, 'PVRSELECT')", -name=>'SELECTOR', -value=>'1', -label=>'' ) );
	# Display data in nested table
	for my $heading (@displaycols) {

	        # Sort by column click and change display class (colour) according to sort status
	        my ($title, $class, $onclick);
	        if ( $sort_field eq $heading && not $reverse ) {
                  ($title, $class, $onclick) = ("Sort by Reverse $fieldname{$heading}", 'sorted pointer', "BackupFormVars(form); form.NEXTPAGE.value='pvr_list'; form.PVRSORT.value='$heading'; form.PVRREVERSE.value=1; form.submit(); RestoreFormVars(form);");
                } else {
                  ($title, $class, $onclick) = ("Sort by $fieldname{$heading}", 'unsorted pointer', "BackupFormVars(form); form.NEXTPAGE.value='pvr_list'; form.PVRSORT.value='$heading'; form.submit(); RestoreFormVars(form); ");
                }
                $class = 'sorted_reverse pointer' if $sort_field eq $heading && $reverse;

		push @html, th( { -class => 'search' },
			label( {
				-title		=> $title,
				-class		=> $class,
				-onClick	=> $onclick,
				},
				$fieldname{$heading} || $heading,
			)
                );
        }
	push @html, "</tr>";

	# Build each row
	for my $name ( @pvrsearches ) {
		my @row;
		push @row, td( {-class=>'search'},
			checkbox(
				-class		=> 'search',
				-name		=> 'PVRSELECT',
				-label		=> '',
				-value	 	=> "$name",
				-checked	=> 0,
				-override	=> 1,
			)
		);
		for ( @displaycols ) {
			push @row, td( {-class=>'search'}, 
				label( {
					-title		=> "Click to Edit",
					-class		=> 'search',
					-onClick	=> "BackupFormVars(form); form.NEXTPAGE.value='pvr_edit'; form.PVRSEARCH.value='$name'; form.submit(); RestoreFormVars(form);",
					},
					$pvrsearch->{$name}->{$_},
				)
			);
		}
		push @html, Tr( {-class=>'search'}, @row );
	}

	
	# Search form
	print $fh start_form(
		-name   => "form",
		-method => "POST",
	);
	print $fh p("Click to Edit any PVR Search");
	# Render options actions
	print $fh $buttons;
	# Render table
	print $fh table( {-class=>'search'} , @html );
	print $fh $buttons;
	# Make sure we go to the correct nextpage for processing
	print $fh hidden(
		-name		=> "NEXTPAGE",
		-value		=> "pvr_list",
		-override	=> 1,
	);
	# Reverse sort value
	print $fh hidden(
		-name		=> "PVRREVERSE",
		-value		=> 0,
		-override	=> 1,
	);
	print $fh hidden(
		-name		=> "PVRSORT",
		-value		=> $sort_field,
		-override	=> 1,
	);
	print $fh hidden(
		-name		=> "PVRSEARCH",
		-value		=> '',
		-override	=> 1,
	);
	print $fh end_form();

	return 0;
}



# Edits a single record indicated by PVRSELECT
sub pvr_edit {
	my %fields;
	my $pvrsearch = get_pvr_list();
	my @html;

	my $pvrname = $cgi->param( 'PVRSEARCH' );

	# Determine max field length
	my $maxwidth = 30;
	for ( values %{ $pvrsearch->{$pvrname} } ) {
		$maxwidth = length($_) if length($_) > $maxwidth && $maxwidth < 200;
	}
	# Get each element
	for my $key ( keys %{ $pvrsearch->{$pvrname} } ) {
		my $val = $pvrsearch->{$pvrname}->{$key};
		# Put INPUT field here
		my $element;
		#if ( $key eq 'pvrsearch' ) {
		#	$element = $val;
		#} else {
			$element = hidden(
				-name		=> "EDITKEYS",
				-value		=> $key,
				-override	=> 1,
			).
			textfield(
				-class		=> 'edit',
				-name		=> "EDITVALUES",
				-value		=> $val,
				-size		=> $maxwidth + 20,
			);
		#}
		push @html, Tr( { -class => 'info' }, th( { -class => 'info' }, $key ).td( { -class => 'info' }, $element ) );
	}

	# Editing form
	print $fh start_form(
		-name   => "form",
		-method => "POST",
	);

	print $fh table( { -class => 'info' }, @html );

	# Render options actions
	print $fh div( { -class=>'action' },
		ul( { -class=>'action' },
			li( { -class=>'action' }, [
				a(
					{
						-class=>'action',
						-title => 'Go Back',
						-onClick  => "history.back()",
					},
					'Back'
				),
				a(
					{
						-class => 'action',
						-title => 'Save changes',
						-onClick => "BackupFormVars(form); form.NEXTPAGE.value='pvr_save'; form.submit(); RestoreFormVars(form);",
					},
					'Save Changes'
				),
			]),
		),
	);
	# Make sure we go to the correct nextpage for processing
	print $fh hidden(
		-name		=> "NEXTPAGE",
		-value		=> "pvr_add",
		-override	=> 1,
	);
	print $fh hidden(
		-name		=> "PVRSEARCH",
		-value		=> $pvrname,
		-override	=> 1,
	);
	print $fh end_form();

	return 0;
}



#
# Will return a list of pids sorted by the requested Heading
#
sub get_sorted {
	my @sorted;
	my @unsorted;
	my $data = shift;
	my $sort_field = shift;
	my $reverse = shift;
	# Lookup table for nice field name headings
	my %sorttype = (
		index		=> 'numeric',
		duration	=> 'numeric',
		timeadded	=> 'numeric',
		seriesnum	=> 'numeric',
		episodenum	=> 'numeric',
	);

	# Insert search '<key>~~~<sort_field>' for each prog in hash
	for my $key (keys %{ $data } ) {
		# generate sort column
		push @unsorted, $data->{$key}->{$sort_field}.'~~~'.$key;
	}

	# If this a purely numerical field
	if ( defined $sorttype{$sort_field} && $sorttype{$sort_field} eq 'numeric' ) {
		if ($reverse) {
			@sorted = reverse sort {$a <=> $b} @unsorted;
		} else {
			@sorted = sort {$a <=> $b} @unsorted;
		}
	# otherwise sort alphabetically
	} else {
		if ($reverse) {
			@sorted = reverse sort { lc $a cmp lc $b } @unsorted;
		} else {
			@sorted = sort { lc $a cmp lc $b } @unsorted;
		}
	}
	# Strip off seach key at beginning of each line
	s/^.*~~~// for @sorted;

	return @sorted;
}



sub pvr_del {
	my @record = ( $cgi->param( 'PVRSELECT' ) );
	my $out;

	# Queue all selected '<type>|<pid>' entries in the PVR
	for my $name (@record) {
		chomp();
		my @cmd = (
			$opt_cmdline->{getiplayer},
			'--nocopyright',
			'--expiry=999999999',
			'--webrequest',
			get_iplayer_webrequest_args( "pvrdel=$name" ),
		);
		print $fh p("Command: ".( join ' ', @cmd ) ) if $opt_cmdline->{debug};
		my $cmdout = join "", get_cmd_output( @cmd );
		return p("ERROR: ".$out) if $? && not $IGNOREEXIT;
		print $fh p("Deleted: $name");
		$out .= $cmdout;
	}
	print $fh "<pre>$out</pre>";

	# Show list below
	show_pvr_list();

	return $out;
}



sub show_info {
	my $progdata = ( $cgi->param( 'INFO' ) );
	my $out;
	my @html;
	my %prog;
	my ( $type, $pid ) = split /\|/, $progdata;

	# Queue all selected '<type>|<pid>' entries in the PVR
	chomp();
	my @cmd = (
		$opt_cmdline->{getiplayer},
		'--nocopyright',
		'--expiry=999999999',
		'--webrequest',
		get_iplayer_webrequest_args( 'nopurge=1', "type=$type", "future=$opt->{FUTURE}->{current}", "history=$opt->{HISTORY}->{current}", "skipdeleted=$opt->{HIDEDELETED}->{current}", 'info=1', 'fields=pid', "search=$pid" ),
	);
	print $fh p("Command: ".( join ' ', @cmd ) ) if $opt_cmdline->{debug};
	my @cmdout = get_cmd_output( @cmd );
	return p("ERROR: ".@cmdout) if $? && not $IGNOREEXIT;
	for ( grep !/^(Added|INFO):/, @cmdout ) {
		my ( $key, $val ) = ( $1, $2 ) if m{^(\w+?):\s*(.+?)\s*$};
		next if $key =~ /(^$|^\d+$)/ || $val =~ /Matching Program/i;
		$out .= "$key: $val\n";
		$prog{$pid}->{$key} = $val;
		# Make into a link if this value is a URL
		$val = a( { -class=>'info', -title=>'Open URL', -href=>$val }, $val ) if $val =~ m{^http://.+};
		push @html, Tr( { -class => 'info' }, th( { -class => 'info' }, $key ).td( { -class => 'info' }, $val ) );
	}
	# Show thumb if one exists
	print $fh img( { -class=>'action', -src=>$prog{$pid}->{thumbnail} } ) if $prog{$pid}->{thumbnail};
	# Set optional output dir for pvr queue if set
	my $outdir;
	$outdir = '&OUTPUT='.CGI::escape("$opt->{OUTPUT}->{current}") if $opt->{OUTPUT}->{current};
	# Render options actions
	print $fh div( { -class=>'action' },
		ul( { -class=>'action' },
			li( { -class=>'action' }, [
				a(
					{
						-class=>'action',
						-title => 'Go Back',
						-onClick  => "history.back()",
					},
					'Back'
				),
				a(
					{
						-class => 'action',
						-title => "Play '$prog{$pid}->{name} - $prog{$pid}->{episode}' Now",
						-href => build_url_playlist( '', 'playlist', 'pid', $pid, $prog{$pid}->{mode} || $default_modes, $prog{$pid}->{type}, $cgi->param( 'OUTTYPE' ) || 'out.flv', $cgi->param( 'STREAMTYPE' ), $cgi->param( 'BITRATE' ), $cgi->param( 'VSIZE' ), $cgi->param( 'VFR' ) ),
					},
					'Play'
				),
			]),
		),
	);
	print $fh table( { -class => 'info' }, @html );
	return $out;
}



# Get filename from history based on PID, MODE and TYPE
# If the PID is a filename then filename is still searched using PID and TYPE
sub get_direct_filename {
	my ( $pid, $mode, $type ) = ( @_ );
	my $out;
	my @html;
	my %prog;
	my $pidisfile;
	my $history = 1;

	print $se "DEBUG: Looking up filename for MODE=$mode TYPE=$type PID=$pid\n";
	
	# set this flag if required and unset history if pid is a file
	if ( -f $pid ) {
		print $se "DEBUG: PID is a valid filename\n";
		$pidisfile = 1;
		$history = 0;
	}

	# Skip if not defined or, if pid is a file and no type defined
	if ( $pidisfile && ! $type ) {
		print $se "ERROR: Cannot lookup filename for PID which is a filename if type is not set\n";
		return '';
	}
	if ( ( ! $pidisfile ) && ! ( $pid && $mode && $type ) ) {
		print $se "ERROR: Cannot lookup filename unless PID, MODE and TYPE are set\n";
		return '';
	}

	# make the pid regex friendly
	$pid =~ s|([\/\.\?\+\-\*\^\(\)\[\]\{\}])|\\$1|g;

	# Get the 'filename' entry from --history --info for this pid
	my @cmd = (
		$opt_cmdline->{getiplayer},
		'--nocopyright',
		'--expiry=999999999',
		'--webrequest',
		get_iplayer_webrequest_args( 'nopurge=1', "history=$history", 'fields=pid', "search=$pid", "type=$type", 'listformat=filename: <pid>|<filename>|<mode>' ),
	);
	print $se "Command: ".( join ' ', @cmd )."\n"; # if $opt_cmdline->{debug};
	my @cmdout = get_cmd_output( @cmd );
	return p("ERROR: ".@cmdout) if $? && not $IGNOREEXIT;

	# Extract the filename
	my $match = ( grep /^filename:/, @cmdout )[0];
	my $filename;
	if ( $pidisfile ) {
		$filename = $1 if $match =~ m{^filename: (\/.+?)\|<filename>\|<mode>\s*$};
	} else {
		$filename = $1 if $match =~ m{^filename: .+?\|\s*(.+?)\|$mode\s*$};
	}

	return search_absolute_path( $filename );
}



# Hack to work around relative paths in recordings history
sub search_absolute_path {
	my $filename = shift;
	my $abs_path;

	# win32 doesn't seem to like abs_path
	# rewrite win32 paths
	if ( IS_WIN32 ) {
		# add a hardcoded prefix for now if relative path (assume relative to local get_iplayer script)
		if ( $filename !~ m{^[A-Za-z]:} && $filename =~ m{^(\.|\.\.|[A-Za-z])} ) {
			$filename = dirname( abs_path( $opt_cmdline->{getiplayer} ) ).'/'.$filename;
		}
		# twiddle the / to \
		$filename =~ s!(\\/|/|\/)!\\!g;
		return $filename;
	}

	#print $se "FILENAME='$filename'";

	# Try using CWD
	if ( -f abs_path($filename) ) {
		$abs_path = abs_path($filename);

	# else try dir of get_iplayer
	} elsif ( -f dirname( abs_path( $opt_cmdline->{getiplayer} ) ).'/'.$filename ) {
		$abs_path = dirname( abs_path( $opt_cmdline->{getiplayer} ) ).'/'.$filename;

	# else try dir current output dir option
	} elsif ( $opt->{OUTPUT}->{current} && -f abs_path( $opt->{OUTPUT}->{current} ).'/'.$filename ) {
		$abs_path = abs_path( $opt->{OUTPUT}->{current} ).'/'.$filename;

	# Else just return the relative path
	} else {
		$abs_path = $filename;
	}
	
	#print $se "  ->  ABSPATH='$abs_path'\n";
	
	return $abs_path;
}



sub pvr_queue {
	# Gets the multiple selections of progs to queue from PROGSELECT
	my @record;
	# The 'Record' action button uses SEARCH to pass it's pvr_queue data
	if ( $cgi->param( 'SEARCH' ) ) {
		push @record, $cgi->param( 'SEARCH' );
	} else {
		@record = ( $cgi->param( 'PROGSELECT' ) );
	}

	my @params = get_search_params();
	my $out;

	# If a URL was specified by the User (assume auto mode list is OK):
	if ( $opt->{URL}->{current} =~ m{^http://} ) {
		push @record, "$opt->{PROGTYPES}->{current}|$opt->{URL}->{current}|$opt->{URL}->{current}|-";
	}

	print $fh "<p>Queuing The Following Programmes in the PVR</p><ul>\n";
	for (@record) {
		chomp();
		my ( $type, $pid, $name, $episode ) = (split /\|/)[0,1,2,3];
		next if ! ($type && $pid );
		print $fh "<li>$name - $episode ($pid)</li>\n";
	}
	print $fh "</ul><br />\n";
	# Queue all selected 'TYPE|PID|NAME|EPISODE|MODE|CHANNEL' entries in the PVR
	for (@record) {
		chomp();
		my ( $type, $pid, $name, $episode ) = (split /\|/)[0,1,2,3];
		next if ! ($type && $pid );
		my $comment = "$name - $episode";
		$comment =~ s/\'\"//g;
		$comment =~ s/[^\s\w\d\-:\(\)]/_/g;
		$comment =~ s/^_*//g;
		$comment =~ s/_*$//g;
		my @cmd = (
			$opt_cmdline->{getiplayer},
			'--nocopyright',
			'--expiry=999999999',
			'--webrequest',
			get_iplayer_webrequest_args(
				'pvrqueue=1',
				"pid=$pid",
				"comment=$comment (queued: ".localtime().')',
				"type=$type",
				build_cmd_options( grep !/^(HISTORY|SINCE|BEFORE|HIDEDELETED|FUTURE|SEARCH|SEARCHFIELDS|VERSIONLIST|PROGTYPES|EXCLUDEC.+)$/, @params )
			),
		);
		print $fh p("Command: ".( join ' ', @cmd ) ) if $opt_cmdline->{debug};
		my $cmdout = join "", get_cmd_output( @cmd );
		return p("ERROR: ".$out) if $? && not $IGNOREEXIT;
		print $fh p("Queued: $type: '$name - $episode' ($pid)");
		$out .= $cmdout;
	}
	print $fh "<pre>$out</pre>";

	# Show list below
	show_pvr_list();

	return $out;
}



sub recordings_delete {
	# Gets the multiple selections of progs to queue from PROGSELECT
	my @record;
	# The 'Record' action button uses SEARCH to pass it's pvr_queue data
	if ( $cgi->param( 'SEARCH' ) ) {
		push @record, $cgi->param( 'SEARCH' );
	} else {
		@record = ( $cgi->param( 'PROGSELECT' ) );
	}

	my @params = get_search_params();

	# Render options actions
	my $buttons = div( { -class=>'action' },
		ul( { -class=>'action' },
			li( { -class=>'action' }, [
				a(
					{
						-class=>'action',
						-title => 'Go Back',
						-onClick  => "history.back()",
					},
					'Back'
				),
			]),
		),
	);
	# Render options actions
	print $fh $buttons;
	print $fh "<p>Deleting the Following Programmes:</p><ul>\n";
	for (@record) {
		chomp();
		my ( $type, $pid, $name, $episode ) = (split /\|/)[0,1,2,3];
		next if ! ($type && $pid );
		print $fh "<li>$name - $episode ($pid)</li>\n";
	}
	print $fh "</ul><br />\n";
	# Queue all selected 'TYPE|PID|NAME|EPISODE|MODE|CHANNEL' entries in the PVR
	for (@record) {
		chomp();
		my ( $type, $pid, $name, $episode, $mode ) = (split /\|/)[0,1,2,3,4];
		next if ! ($mode && $pid );
		my $filename = get_direct_filename( $pid, $mode, $type );
		my $dir = dirname( $filename );
		my $fileregex = basename( $filename );
		# get the filename less the ext
		$fileregex =~ s/\.\w+$//g;
		$fileregex .= '\.\w+$';
		# Find matching files <filename>.*
		if ( opendir DIR, $dir ) {
			for my $file ( grep { /$fileregex/ } readdir(DIR) ) {
				# Use absolute path
				$file = "${dir}/${file}";
				if ( -f $file ) {
					if ( ! unlink( $file ) ) {
						print $fh p("ERROR: Failed to delete $file");
					}
				} else {
					print $fh p("ERROR: File does not exist for: $type: '$name - $episode', MODE: $mode, PID: $pid, FILENAME: $filename");
				}
			}
			print $fh p("Successfully deleted: $type: '$name - $episode', MODE: $mode, PID: $pid");
			closedir(DIR);
		} else {
			print $fh p("ERROR: Cannot open dir '$dir' for file deletion\n");
		}
	}
	# Render options actions
	print $fh $buttons;
	return '';
}



sub build_cmd_options {
	my @options;
	for ( @_ ) {
		# skip non-options
		next if $opt->{$_}->{optkey} eq '' || not defined $opt->{$_}->{optkey} || not $opt->{$_}->{optkey};
		my $value = $opt->{$_}->{current};
		push @options, "$opt->{$_}->{optkey}=$value" if $value ne '';
	}
	return @options;
}



sub get_search_params {
	my @params;
	for ( keys %{ $opt } ) {
		# skip non-options
		next if $opt->{$_}->{optkey} eq '' || not defined $opt->{$_}->{optkey} || not $opt->{$_}->{optkey};
		next if grep /^$_$/, @nosearch_params;
		push @params, $_;
	}
	return @params;
}



# Return get_iplayer command options when supplied an array of <key>=<value> options
sub get_iplayer_webrequest_args {
	my @cmdopts;
	print $se 'DEBUG: get_iplayer options: "'.join('" "', @_)."\"\n";
	for (@_) {
		push @cmdopts, CGI::escape($_);
	}
	my $cmdline = join('?', @cmdopts);
	return $cmdline;
}



sub pvr_add {

	my $out;
	my @params = get_search_params();

	# Only allow alphanumerics,_,-,. here for security reasons
	my $searchname = "$opt->{SEARCH}->{current}_$opt->{SEARCHFIELDS}->{current}_$opt->{PROGTYPES}->{current}";
	$searchname =~ s/[^\w\-\. \+\(\)]/_/g;

	# Remove a few options from leaking into a PVR search
	my @cmd = (
		$opt_cmdline->{getiplayer},
		'--nocopyright',
		'--expiry=999999999',
		'--webrequest',
		get_iplayer_webrequest_args( "pvradd=$searchname", build_cmd_options( grep !/^(HISTORY|HIDEDELETED|SINCE|BEFORE|HIDE|FORCE|FUTURE)$/, @params ) ),
	);
	print $se "DEBUG: Command: ".( join ' ', @cmd )."\n";
	print $fh p("Command: ".( join ' ', @cmd ) ) if $opt_cmdline->{debug};
	$out = join "", get_cmd_output( @cmd );
	return p("ERROR: ".$out) if $? && not $IGNOREEXIT;
	print $fh p("Added PVR Search ($searchname):\n\tTypes: $opt->{PROGTYPES}->{current}\n\tSearch: $opt->{SEARCH}->{current}\n\tSearch Fields: $opt->{SEARCHFIELDS}->{current}\n");
	print $fh "<pre>$out</pre>";

	# Show list below
	show_pvr_list();

	return $out;
}



# Delete then add again - just in case user has edited name of pvr search
sub pvr_save {
	my $out;
	my @keys = $cgi->param( 'EDITKEYS' );
	my @values = $cgi->param( 'EDITVALUES' );
	my @params;
	my @search_args;
	my $newsearchname;

	# Convert the two keys and values arrays into a KEY=VALUE params array
	for ( @keys ) {
		my $val = shift @values;
		if ( $_ eq 'pvrsearch' ) {
			$newsearchname = $val;
		# append search terms to cmdline
		} elsif ( /^search\d+$/ && $val !~ /^\-/ ) {
			push @search_args, $val;
		} else {
			push @params, $_.'='.$val;
		}
	}

	#print STDERR "ELEMENTS for save: ".(join ',', @params)."\n\n";

	# Sanity check
	if ( $newsearchname eq '' ) {
		print $fh p("No PVR Search Name Specified - not updated");
		return;
	}

	# Delete the original pvr entry
	my $searchname = $cgi->param( 'PVRSEARCH' );
	my @cmd = (
		$opt_cmdline->{getiplayer},
		'--nocopyright',
		'--expiry=999999999',
		'--webrequest',
		get_iplayer_webrequest_args( "pvrdel=$searchname" ),
	);
	print $fh p("Command: ".( join ' ', @cmd ) ) if $opt_cmdline->{debug};
	my $cmdout = join "", get_cmd_output( @cmd );
	return p("ERROR: ".$out) if $? && not $IGNOREEXIT;
	print $fh p("Deleted: $searchname");
	$out .= $cmdout;

	# Add the new pvr entry
	@cmd = (
		$opt_cmdline->{getiplayer},
		'--nocopyright',
		'--expiry=999999999',
		'--webrequest',
		get_iplayer_webrequest_args( "pvradd=$newsearchname", @params ),
		'--',
		@search_args,
	);
	print $se "DEBUG: Command: ".( join ' ', @cmd )."\n";
	print $fh p("Command: ".( join ' ', @cmd ) ) if $opt_cmdline->{debug};
	$out = join "", get_cmd_output( @cmd );
	return p("ERROR: ".$out) if $? && not $IGNOREEXIT;
	print $fh p("Added Updated PVR Search '$newsearchname'\n");
	print $fh "<pre>$out</pre>";

	# Show list below
	show_pvr_list();

	return $out;
}



# Build templated HTML for an option specified by passed hashref
sub build_option_html {
	my $arg = shift;
	
	my $title = $arg->{title};
	my $tooltip = $arg->{tooltip};
	my $webvar = $arg->{webvar};
	my $option = $arg->{option};
	my $type = $arg->{type};
	my $label = $arg->{label};
	my $current = $arg->{current};
	my $value = $arg->{value};
	my $status = $arg->{status};
	my @html;

	# On/Off
	if ( $type eq 'hidden' ) {
		push @html, hidden(
			-name		=> $webvar,
			-id		=> "option_$webvar",
			#-value		=> $arg->{default},
			-value		=> $current,
			-override	=> 1,
		);

	# On/Off
	} elsif ( $type eq 'boolean' ) {
		push @html, th( { -class => 'options', -title => $tooltip }, $title ).
		td( { -class => 'options', -title => $tooltip },
			checkbox(
				-class		=> 'options',
				-name		=> $webvar,
				-id		=> "option_$webvar",
				-label		=> '',
				#-value 	=> 1,
				-checked	=> $current,
				-override	=> 1,
			)
		);

	# On/Off
	} elsif ( $type eq 'radioboolean' ) {
		push @html, th( { -class => 'options', -title => $tooltip }, $title ).
		td( { -class => 'options', -title => $tooltip },
			radio_group(
				-class		=> 'options',
				-name		=> $webvar,
				-values		=> { 0=>'Off' , 1=>'On' },
				-default	=> $current,
				-override	=> 1,				
			)
		);

	# Multi-On/Off
	} elsif ( $type eq 'multiboolean' ) {
		my $element;
		# values in hash of $value->{<order>} => value
		# labels in hash of $label->{$value}
		# selected status in $status->{$value}
		my @keylist = sort { $a <=> $b } keys %{ $value };
		my $count = 0;
		while ( @keylist ) {
			my $val = $value->{shift @keylist};
			$element .=
				td( { -class => 'options' },
					table ( { -class => 'options_embedded', -title => $tooltip }, Tr( { -class => 'options_embedded' }, td( { -class => 'options_embedded' }, [
						checkbox(
							-class		=> 'options',
							-name		=> $webvar,
							-id		=> "option_${webvar}_$val",
							-label		=> '',
							-value 		=> $val,
							-checked	=> $status->{$val},
							-override	=> 1,
						),
						$label->{$val}
					] ) ) )
				);
			# Spread over more rows if there are many elements
			if ( not ( ($count+1) % 3 ) ) {
				$element .= '<tr class="options_embedded">';
			}
			$count++;
		}
		my $inner_table = table ( { -class => 'options_embedded' }, Tr( { -class => 'options_embedded' },
			$element
		) );
			
		push @html, th( { -class => 'options', -title => $tooltip }, $title ).td( { -class => 'options' }, $inner_table );
	# Popup type
	} elsif ( $type eq 'popup' ) {
		my @value = $arg->{value};
		push @html, th( { -class => 'options', -title => $tooltip }, $title ).
		td( { -class => 'options', -title => $tooltip }, 
			popup_menu(
				-class		=> 'options',
				-name		=> $webvar,
				-id		=> "option_$webvar",
				-values		=> @value,
				-labels		=> $label,
				-default	=> $current,
				-onChange	=> $arg->{onChange},
			)
		);

	# text field
	} elsif ( $type eq 'text' ) {
		push @html, th( { -class => 'options', -title => $tooltip }, $title ).
		td( { -class => 'options', -title => $tooltip },
			textfield(
				-class		=> 'options',
				-name		=> $webvar,
				-value		=> $current,
				-size		=> $value,
				-onKeyDown	=> 'return submitonEnter(event);',
			)
		);

	}

	return @html;
}



sub refresh {
	my $typelist = join(",", $cgi->param( 'PROGTYPES' )) || 'tv';
	my $refreshfuture = $cgi->param( 'REFRESHFUTURE' ) || 0;
	print $fh "<strong><p>The cache will auto-refresh every $opt->{AUTOWEBREFRESH}->{current} hour(s) if you leave this page open</p></strong>" if $opt->{AUTOWEBREFRESH}->{current};
	print $se "INFO: Refreshing\n";
	my @cmd = (
		$opt_cmdline->{getiplayer},
		'--nocopyright',
		'--webrequest',
		get_iplayer_webrequest_args( 'expiry=30', 'nopurge=1', "type=$typelist", "refreshfuture=$refreshfuture", "search=no search just refresh" ),
	);
	print $fh '<pre>';
	run_cmd( $fh, $se, 1, @cmd );
	print $fh '</pre>';
	print $fh p("Flushed Programme Caches for Types: $typelist");

	# Load the refresh tab if required
	my $autorefresh = $cgi->cookie( 'AUTOWEBREFRESH' ) || $cgi->param( 'AUTOWEBREFRESH' );

	# Render options actions
	print $fh div( { -class=>'action' },
		ul( { -class=>'action' },
			li( { -class=>'action' }, [
				a(
					{
						-class=>'action',
						-title => 'Refresh Cache Now',
						-onClick  => "RefreshTab( '?NEXTPAGE=refresh&PROGTYPES=$typelist&AUTOWEBREFRESH=$autorefresh', ".(1000*3600*$autorefresh).", 1 );",
					},
					'Force Refresh'
				),
				a(
					{
						-class=>'action',
						-title => 'Go Back',
						-onClick  => "window.close()",
					},
					'Close'
				),
			]),
		),
	);

}



# Just a wrapper to search_progs which defines history search settings for 'Recordings' tab
sub search_history {
	$opt->{HISTORY}->{current} = 1;
	$opt->{SORT}->{current} = 'timeadded';
	$opt->{REVERSE}->{current} = 1;
	$opt->{SINCE}->{current} = '';
	$opt->{BEFORE}->{current} = '';
	$opt->{EXCLUDE}->{current} = '';
	$opt->{CATEGORY}->{current} = '';
	$opt->{EXCLUDECATEGORY}->{current} = '';
	$opt->{CHANNEL}->{current} = '';
	$opt->{EXCLUDECHANNEL}->{current} = '';
	search_progs();
}



sub search_progs {
	# Set default status for progtypes
	my %type;
	$type{$_} = 1 for split /,/, $opt->{PROGTYPES}->{current};
	$opt->{PROGTYPES}->{status} = \%type;

	# Determine which cols to display and Set default status for cols
	get_display_cols();

	#for my $key (sort keys %ENV) {
	#	print $fh $key, " = ", $ENV{$key}, "\n<br>";
	#}    

	# Get prog data
	my @params = get_search_params();
	my ( $matchcount, $response ) = ( get_progs( @params ) );
	if ( $response ) {
		print $fh p("ERROR: get_iplayer returned non-zero:").br().p( join '<br>', $response );
		return 1;
	}

	my ($first, $last, @pagetrail) = pagetrail( $opt->{PAGENO}->{current}, $opt->{PAGESIZE}->{current}, $matchcount, 7 );

	# Default displaycols
	my @html;
	push @html, "<tr>";
	push @html, th( { -class => 'search' }, checkbox( -class=>'search', -title=>'Select/Unselect All Programmes', -onClick=>"check_toggle(document.form, 'PROGSELECT')", -name=>'SELECTOR', -value=>'1', -label=>'' ) );

	# Pad empty column for R/S
	push @html, th( { -class => 'search' }, 'Actions' );

	# Display data in nested table
	for my $heading (@displaycols) {

		# Sort by column click and change display class (colour) according to sort status
		my ($title, $class, $onclick);

		if ( $opt->{SORT}->{current} eq $heading && not $opt->{REVERSE}->{current} ) {
			($title, $class, $onclick) = ("Sort by Reverse $heading", 'sorted pointer', "form.NEXTPAGE.value='search_progs'; form.SORT.value='$heading'; form.REVERSE[0].checked=true; form.submit();");
		} else {
			($title, $class, $onclick) = ("Sort by $heading", 'unsorted pointer', "form.NEXTPAGE.value='search_progs'; form.SORT.value='$heading'; form.REVERSE[1].checked=true; form.submit();");
		}
		$class = 'sorted_reverse pointer' if $opt->{SORT}->{current} eq $heading && $opt->{REVERSE}->{current};

		push @html, 
			th( { -class => 'search' },
				table( { -class => 'searchhead' },
					Tr( { -class => 'search' }, [ 
						th( { -class => 'search' },
							label( {
								-title		=> $title,
								-class		=> $class,
								-onClick	=> $onclick,
								},
								$fieldname{$heading},
							)
						)
					]
				)
			)
		);
	}
	push @html, "</tr>";

	# Set optional output dir for pvr queue if set
	my $outdir;
	$outdir = '&OUTPUT='.CGI::escape("$opt->{OUTPUT}->{current}") if $opt->{OUTPUT}->{current};
	# Build each prog row
	my $time = time();
	for ( my $i = 0; $i <= $#pids; $i++ ) {
		my $search_class = 'search';
		my $pid = $pids[$i]; 
		my @row;

		# Grey-out history lines which files have been deleted or where the history doesn't have a filename mentioned
		if ( $opt->{HISTORY}->{current} && ! $opt->{HIDEDELETED}->{current} ) {
			if ( ( ! $prog{$pid}->{filename} ) || ! -f $prog{$pid}->{filename} ) {
					$search_class = 'search darker';
			}
		}

		# Format of PROGSELECT: TYPE|PID|NAME|EPISODE|MODE|CHANNEL
		push @row, td( {-class=>$search_class},
			checkbox(
				-class		=> $search_class,
				-name		=> 'PROGSELECT',
				-label		=> '',
				-value 		=> "$prog{$pid}->{type}|$pid|$prog{$pid}->{name}|$prog{$pid}->{episode}|$prog{$pid}->{mode}|$prog{$pid}->{channel}",
				-checked	=> 0,
				-override	=> 1,
			)
		);
		# Record and stream links
		# Fix output type and mode per prog type
		my %streamopts = (
			radio		=> '&MODES=iphone&OUTTYPE=mp3',
			tv		=> '&MODES=iphone&OUTTYPE=mov',
			livetv		=> '&MODES=flash&OUTTYPE=flv',
			liveradio	=> '&MODES=flash&BITRATE=320&OUTTYPE=mp3',
			itv		=> '&OUTTYPE=asf',
			localfiles	=> '&OUTTYPE=mp3',
		);

		my $links;
		# 'Play'
		# Search mode with filename as pid
		if ( $pid =~ m{^/} ) {
			if ( -f $pid ) {
				# Play
				$links .= a( { -class=>$search_class, -title=>"Play from file on web server", -href=>build_url_playlist( '', 'playlist', 'pid', $pid, $opt->{MODES}->{current} || $default_modes, $prog{$pid}->{type}, basename( $pid ) , $opt->{STREAMTYPE}->{current}, $opt->{BITRATE}->{current}, $opt->{VSIZE}->{current}, $opt->{VFR}->{current} ) }, 'Play' ).'<br />';
				# PlayFile
				$links .= a( { -id=>'nowrap', -class=>$search_class, -title=>"Play from local file", -href=>build_url_playlist( '', 'playlistfiles', 'pid', $pid, $prog{$pid}->{mode}, $prog{$pid}->{type}, undef, undef ) }, 'PlayFile' ).'<br />';
				# PlayDirect
				$links .= a( { -id=>'nowrap', -class=>$search_class, -title=>"Stream file into browser", -href=>build_url_direct( '', $prog{$pid}->{type}, $pid, $prog{$pid}->{mode}, $opt->{STREAMTYPE}->{current}, $opt->{STREAMTYPE}->{current}, $opt->{HISTORY}->{current}, $opt->{BITRATE}->{current}, $opt->{VSIZE}->{current}, $opt->{VFR}->{current} ) }, 'PlayDirect' ).'<br />';
			}
		# History mode
		} elsif ( $opt->{HISTORY}->{current} ) {
			if ( $opt->{HIDEDELETED}->{current} || -f $prog{$pid}->{filename} ) {
				# Play (Play Remote)
				$links .= a( { -id=>'nowrap', -class=>$search_class, -title=>"Play from file on web server", -href=>build_url_playlist( '', 'playlistdirect', 'pid', $pid, $prog{$pid}->{mode}, $prog{$pid}->{type}, 'flv', 'flv', $opt->{BITRATE}->{current}, $opt->{VSIZE}->{current}, $opt->{VFR}->{current} ) }, 'Play' ).'<br />';
				# PlayFile
				$links .= a( { -id=>'nowrap', -class=>$search_class, -title=>"Play from local file", -href=>build_url_playlist( '', 'playlistfiles', 'pid', $pid, $prog{$pid}->{mode}, $prog{$pid}->{type}, undef ) }, 'PlayFile' ).'<br />';
				# PlayDirect - depends on browser support
				$links .= a( { -id=>'nowrap', -class=>$search_class, -title=>"Stream file into browser", -href=>build_url_direct( '', $prog{$pid}->{type}, $pid, $prog{$pid}->{mode}, $opt->{STREAMTYPE}->{current}, $opt->{STREAMTYPE}->{current}, $opt->{HISTORY}->{current}, $opt->{BITRATE}->{current}, $opt->{VSIZE}->{current}, $opt->{VFR}->{current} ) }, 'PlayDirect' ).'<br />';
			}
		# Search mode
		} else {
			# Play
			$links .= a( { -class=>$search_class, -title=>"Play from Internet", -href=>build_url_playlist( '', 'playlist', 'pid', $pid, $opt->{MODES}->{current} || $default_modes, $prog{$pid}->{type}, 'out.flv', $opt->{STREAMTYPE}->{current}, $opt->{BITRATE}->{current}, $opt->{VSIZE}->{current}, $opt->{VFR}->{current} ) }, 'Play' ).'<br />';
			# Record
			$links .= label( { -id=>'nowrap', -class=>$search_class, -title=>"Record '$prog{$pid}->{name} - $prog{$pid}->{episode}' Now", -onClick => "BackupFormVars(form); form.NEXTPAGE.value='record_now'; form.SEARCH.value='".encode_entities("$prog{$pid}->{type}|$pid|$prog{$pid}->{name}|$prog{$pid}->{episode}|$prog{$pid}->{mode}")."'; form.target='_newtab_$pid'; form.submit(); RestoreFormVars(form); form.target='';" }, 'Record' ).'<br />';
			# Queue
			$links .= label( { -id=>'nowrap', -class=>$search_class, -title=>"Queue '$prog{$pid}->{name} - $prog{$pid}->{episode}' for PVR Recording", -onClick => "BackupFormVars(form); form.NEXTPAGE.value='pvr_queue'; form.SEARCH.value='".encode_entities("$prog{$pid}->{type}|$pid|$prog{$pid}->{name}|$prog{$pid}->{episode}|$prog{$pid}->{mode}")."'; form.submit(); RestoreFormVars(form);" }, 'Queue' ).'<br />';
			# Add Series
			$links .= label( {
				-id=>'nowrap', 
				-class=>'search pointer_noul',
				-title=>"Add Series '$prog{$pid}->{name}' to PVR", 
				-onClick=>"BackupFormVars(form); form.NEXTPAGE.value='pvr_add'; form.SEARCH.value='".encode_entities("^$prog{$pid}->{name}\$")."'; form.SEARCHFIELDS.value='name'; form.PROGTYPES.value='$prog{$pid}->{type}'; form.HISTORY.value='0'; form.SINCE.value=''; form.BEFORE.value=''; form.submit(); RestoreFormVars(form);" }, 'Add Series' );
		}

		# Add links to row
		push @row, td( {-class=>$search_class}, $links );

		# This builds each row in turn
		for ( @displaycols ) {
			# display thumb if defined (will have to use proxy to get file:// thumbs)
			if ( /^thumbnail$/ ) {
				# Assume a thumbnail prefix if one is missing for BBC iPlayer
				if ( $pid =~ m{^[wpb]0[a-z0-9]{6}$} && $prog{$pid}->{type} =~ /^(tv|radio)$/ ) {
					$prog{$pid}->{$_} = "http://www.bbc.co.uk/iplayer/images/episode/${pid}_150_84.jpg";
				}
				if ( $prog{$pid}->{$_} =~ m{^http://} ) {
					push @row, td( {-class=>$search_class}, a( { -title=>"Open original web URL", -class=>$search_class, -href=>$prog{$pid}->{web} }, img( { -class=>$search_class, -height=>40, -src=>$prog{$pid}->{$_} } ) ) );
				} else {
					push @row, td( {-class=>$search_class}, a( { -title=>"Open original web URL", -class=>$search_class, -href=>$prog{$pid}->{web} }, 'Open URL' ) );
				}
			# Calculate the seconds difference between epoch_now and epoch_datestring and convert back into array_time
			} elsif ( /^timeadded$/ ) {
				my @t = gmtime( $time - $prog{$pid}->{$_} );
				my $years = ($t[5]-70)."y " if ($t[5]-70) > 0;
				push @row, td( {-class=>$search_class}, label( { -class=>$search_class, -title=>"Click for full info", -onClick=>"BackupFormVars(form); form.NEXTPAGE.value='show_info'; form.INFO.value='".encode_entities("$prog{$pid}->{type}|$pid")."'; form.submit(); RestoreFormVars(form);" }, "${years}$t[7]d $t[2]h ago" ) );
			# truncate the description if it is too long
			} elsif ( /^desc$/ ) {
				my $text = $prog{$pid}->{$_};
				$text = substr($text, 0, 256).'...[more]' if length( $text ) > 256;
				push @row, td( {-class=>$search_class}, label( { -class=>$search_class, -title=>"Click for full info", -onClick=>"BackupFormVars(form); form.NEXTPAGE.value='show_info'; form.INFO.value='".encode_entities("$prog{$pid}->{type}|$pid")."'; form.submit(); RestoreFormVars(form);" }, $text ) );
			# Name / Series link
			} elsif ( /^name$/ ) {
				push @row, td( {-class=>$search_class}, label( { -class=>$search_class, -id=>'underline', -title=>"Click to list '$prog{$pid}->{$_}'",
					-onClick=>"
						BackupFormVars(form);
						form.NEXTPAGE.value='search_progs';
						form.SEARCHFIELDS.value='name';
						form.SEARCH.value='".encode_entities('^'.$prog{$pid}->{$_}.'$')."';
						form.PAGENO.value=1;
						form.submit();
						RestoreFormVars(form);
					"}, $prog{$pid}->{$_} )
				);
			# Channel link
			} elsif ( /^channel$/ ) {
				push @row, td( {-class=>$search_class}, label( { -class=>$search_class, -id=>'underline', -title=>"Click to list '$prog{$pid}->{$_}'",
					-onClick=>"
						BackupFormVars(form);
						form.NEXTPAGE.value='search_progs';
						form.CHANNEL.value='".encode_entities('^'.$prog{$pid}->{$_}.'$')."';
						form.EXCLUDECHANNEL.value='';
						form.SEARCH.value='.*';
						form.PAGENO.value=1;
						form.submit();
						RestoreFormVars(form);
					"}, $prog{$pid}->{$_} )
				);
			# Category links
			} elsif ( /^categories$/ ) {
				my @cats = split /,/, $prog{$pid}->{$_};
				for ( @cats ) {
					my $category = $_;
					$_ = label( { -class=>$search_class, -id=>'underline', -title=>"Click to list '$category'", 
						-onClick=>"
							BackupFormVars(form);
							form.NEXTPAGE.value='search_progs';
							form.EXCLUDE.value='';
							form.CATEGORY.value='".encode_entities($category)."';
							form.EXCLUDECATEGORY.value='';
							form.SEARCH.value='.*';
							form.PAGENO.value=1;
							form.submit();
							RestoreFormVars(form);
						"},
					$category );
				}
				push @row, td( {-class=>$search_class}, @cats );
			# Every other column type
			} else {
				push @row, td( {-class=>$search_class}, label( { -class=>$search_class, -title=>"Click for full info", -onClick=>"BackupFormVars(form); form.NEXTPAGE.value='show_info'; form.INFO.value='".encode_entities("$prog{$pid}->{type}|$pid")."'; form.submit(); RestoreFormVars(form);" }, $prog{$pid}->{$_} ) );
			}
		}
		push @html, Tr( {-class=>$search_class}, @row );
	}

	# Search form
	print $fh start_form(
		-name   => "form",
		-method => "POST",
	);


	# Create options tabs and buttons

	# Build tab 'buttons' (actually list labels)
	# Add options buttons into the list
	my @optrows_nav;
	my @tablist = grep !/(BASICTAB|HIDDENTAB)/, @{ $layout->{taborder} };
	for my $tabname ( @tablist ) {
		my $label = $layout->{$tabname}->{title};

		# Set the colour to grey and change tab appearance if it is selected
		my $style = 'color: #ADADAD;';
		my $class = 'options_tab';
		if ( defined $opt->{$tabname}->{current} && $opt->{$tabname}->{current} eq 'yes' ) {
			$style = 'color: #F54997;';
			$class = 'options_tab_sel';
		}
		push @optrows_nav, li( { -class=>$class, -id=>"li_${tabname}" },
			label( {
				-class		=> 'options_outer pointer_noul',
				-id		=> 'button_'.$tabname,
				-title		=> "Show $label tab",
				-style		=> $style,
				-onClick	=> "show_options_tab( '$tabname', [ '".(join "', '", @tablist )."' ] );",
			},
			$label ),
		)
	}

	# add a save button on to end of list
	my $options_buttons = ul( { -class=>'options_tab' },
		li( { -class=>'options_button' }, [
			# Apply button (same as 'Search')
			label( {
				-class		=> 'options_outer pointer_noul',
				-title		=> 'Apply Current Options',
				-onClick	=> "BackupFormVars(form); form.NEXTPAGE.value='search_progs'; form.PAGENO.value=1; form.submit(); RestoreFormVars(form);",
				},
				'Apply Settings',
			),
			# Save as Default  button
			label( {
				-class		=> 'options_outer pointer_noul',
				-title		=> 'Remember Current Options as Default',
				-onClick	=> "BackupFormVars(form); form.SAVE.value=1; form.submit(); RestoreFormVars(form);",
				},
				'Save As Default',
			),
		] )
	);

	# Build each tab with it's contained options tables
	my @opt_td;
	my @opt_td_basic;
	for my $tabname ( @{ $layout->{taborder} } ) {
		my $tab = $layout->{$tabname};
		my @order = @{ $tab->{order} };
		my $heading = $tab->{heading};
		# Set displayed tab status (i.e. style) based on posted/cookie vars (always display basic tab)
		$tab->{style} = "display: none; visibility: collapse;";
		$tab->{style} = "display: table-cell; visibility: visible;" if $tabname eq 'BASICTAB' || ( defined $opt->{$tabname}->{current} && $opt->{$tabname}->{current} eq 'yes' );

		# Each option within the tab
		my @optrows;
		#push @optrows, td( { -class=>'options' }, label( { -class => 'options_heading' }, $heading ) ) if $heading;
		for my $optname ( @order ) {
			push @optrows, build_option_html( $opt->{$optname} );
		}
		# Set the basic search tab to be rowspan=3
		if ( $tabname eq 'BASICTAB' ) {
			push @opt_td_basic, td( { -class=>'options_outer', -id=>"tab_${tabname}", -rowspan=>3, -style=>"$tab->{style}" },
				table( { -class=>'options' }, Tr( { -class=>'options' }, [ @optrows ] ) )
			);
		} else {
			push @opt_td, td( { -class=>'options_outer', -id=>"tab_${tabname}", -style=>"$tab->{style}" },
				table( { -class=>'options' }, Tr( { -class=>'options' }, [ @optrows ] ) )
			);		
		}
	}

	# Render outer options table frame (keeping some tabs hidden)
	print $fh table( { -class=>'options_outer' },
		Tr( { -class=>'options_outer' }, (join '', @opt_td_basic). td( { -class=>'options_outer' }, ul( { -class=>'options_tab' }, @optrows_nav ) ) ).
		Tr( { -class=>'options_outer' }, (join '', @opt_td) ).
		Tr( { -class=>'options_outer' }, td( { -class=>'options_outer' }, $options_buttons ) )
	);
	
	# Grey-out 'Add Current Search to PVR' button if too many programme matches
	my $add_search_class_suffix;
	$add_search_class_suffix = ' darker' if $matchcount > 30;
	my %action_button;
	$action_button{'Search'} = a(
		{
			-class => 'action',
			-title => 'Perform search based on search options',
			-onClick => "BackupFormVars(form); form.NEXTPAGE.value='search_progs'; form.PAGENO.value=1; form.submit(); RestoreFormVars(form);",
		},
		'Search'
	);
	$action_button{'Queue'} = a(
		{
			-class => 'action',
			-title => 'Queue selected programmes (or Quick URL) for one-off recording',
			-onClick => "if(! ( check_if_selected(document.form, 'PROGSELECT') ||  form.URL.value ) ) { alert('No Quick URL or programmes were selected'); return false; } BackupFormVars(form); form.SEARCH.value=''; form.NEXTPAGE.value='pvr_queue'; form.submit(); RestoreFormVars(form); form.URL.value=''; disable_selected_checkboxes(document.form, 'PROGSELECT');",
		},
		'Queue'
	);
	$action_button{'Record'} = a(
		{
			-class => 'action',
			-title => 'Immediately Record selected programmes (or Quick URL) in a new tab',
			-onClick => "if(! ( check_if_selected(document.form, 'PROGSELECT') ||  form.URL.value ) ) { alert('No Quick URL or programmes were selected'); return false; } BackupFormVars(form); form.SEARCH.value=''; form.NEXTPAGE.value='record_now'; var random=Math.floor(Math.random()*99999); form.target='_newtab_'+random; form.submit(); RestoreFormVars(form); form.target=''; form.URL.value=''; disable_selected_checkboxes(document.form, 'PROGSELECT');",
		},
		'Record'
	);
	$action_button{'Delete'} = a(
		{
			-class => 'action',
			-title => 'Permanently delete selected recorded files',
			-onClick => "if(! check_if_selected(document.form, 'PROGSELECT')) { alert('No programmes were selected'); return false; } BackupFormVars(form); form.SEARCH.value=''; form.NEXTPAGE.value='recordings_delete'; form.submit(); RestoreFormVars(form);",
		},
		'Delete'
	);
	$action_button{'Play'} = a(
		{
			-class => 'action',
			-title => 'Get a Playlist based on selected programmes (or Quick URL) to stream in your media player',
			-onClick => "if(! ( check_if_selected(document.form, 'PROGSELECT') ||  form.URL.value ) ) { alert('No Quick URL or programmes were selected'); return false; } BackupFormVars(form); form.SEARCH.value=''; form.ACTION.value='genplaylist'; form.submit(); form.ACTION.value=''; RestoreFormVars(form); form.URL.value='';",
		},
		'Play'
	);
	$action_button{'Play Files'} = a(
		{
			-class => 'action',
			-title => 'Get a Playlist based on selected programmes for local file streaming in your media player',
			-onClick => "if(! check_if_selected(document.form, 'PROGSELECT')) { alert('No programmes were selected'); return false; } BackupFormVars(form); form.SEARCH.value=''; form.ACTION.value='genplaylistfile'; form.submit(); RestoreFormVars(form);",
		},
		'Play Files'
	);
	$action_button{'Play Remote'} = a(
		{
			-class => 'action',
			-title => 'Get a Playlist based on selected programmes for remote file streaming in your media player',
			-onClick => "if(! check_if_selected(document.form, 'PROGSELECT')) { alert('No programmes were selected'); return false; } BackupFormVars(form); form.SEARCH.value=''; form.ACTION.value='genplaylistdirect'; form.submit(); RestoreFormVars(form);",
		},
		'Play Remote'
	);
	# check for an non-whitespace advanced search entries
	# excluding Programme Version and Search Future Schedule
	my $num_adv_srch = grep /\S/, (
		$opt->{EXCLUDE}->{current},
		$opt->{EXCLUDECATEGORY}->{current},
		$opt->{CATEGORY}->{current},
		$opt->{CHANNEL}->{current},
		$opt->{EXCLUDECHANNEL}->{current},
		$opt->{SINCE}->{current},
		$opt->{BEFORE}->{current}
	);
	$action_button{'Add Search to PVR'} = a(
		{
			-class => 'action'.$add_search_class_suffix,
			-title => 'Create a persistent PVR search using the current search terms (i.e. all below programmes)',
			-onClick => "var version = '$opt->{VERSIONLIST}->{current}'; if ('$opt->{SEARCH}->{current}' == '.*' && $num_adv_srch == 0 && version.toLowerCase().indexOf('default') != -1) { alert('Search = .* will download all available programmes.  Please enter a more specific search term or additional advanced search criteria (excluding $opt->{FUTURE}->{title}).'); return false; } if ('$opt->{SEARCH}->{current}' == '' ) { alert('Please enter a search term. Use Search = .* to record all programmes matching advanced search criteria.'); return false; } if ( $matchcount > 30 ) { alert('Please limit your search to result in no more than 30 current programmes'); return false; }  BackupFormVars(form); form.NEXTPAGE.value='pvr_add'; form.submit(); RestoreFormVars(form);",
		},
		'Add Search to PVR'
	);
	#my $autorefresh = $cgi->cookie( 'AUTOWEBREFRESH' ) || $cgi->param( 'AUTOWEBREFRESH' );
	$action_button{'Refresh Cache'} = a(
		{
			-class => 'action',
			-title => 'Refresh the list of programmes - can take a while',
			-onClick => "BackupFormVars(form); form.target='_newtab_refresh'; form.NEXTPAGE.value='refresh'; form.submit(); RestoreFormVars(form); form.target=''; form.NEXTPAGE.value=''; ",
			#-onClick => "window.frames['dataframe'].window.location.replace('?NEXTPAGE=refresh&AUTOWEBREFRESH=$autorefresh')",
		},
		'Refresh Cache'
	);

	# Render action bar
	my @actionbar;
	if ( $opt->{HISTORY}->{current} ) {
		push @actionbar, div( { -class=>'action' },
			ul( { -class=>'action' },
				li( { -class=>'action' }, [
					$action_button{'Search'},
					$action_button{'Delete'},
					$action_button{'Play'},
					$action_button{'Play Files'},
					$action_button{'Play Remote'},
					$action_button{'Add Search to PVR'},
				]),
			),
		);
	} else {
		push @actionbar, div( { -class=>'action' },
			ul( { -class=>'action' },
				li( { -class=>'action' }, [
					$action_button{'Search'},
					$action_button{'Record'},
					$action_button{'Play'},
					$action_button{'Queue'},
					$action_button{'Play Remote'},
					$action_button{'Add Search to PVR'},
					$action_button{'Refresh Cache'},
				]),
			),
		);
	}
	
	print $fh @actionbar;
	print $fh @pagetrail;
	print $fh table( {-class=>'search' }, @html );
	print $fh @pagetrail;
	print $fh @actionbar;

	print $fh div( {id=>'status'} );

	print $fh end_form();

	return 0;
}



# Build page trail
sub pagetrail {
	my ( $page, $pagesize, $count, $trailsize ) = ( @_ );

	# How many pages
	my $pages = int( $count / $pagesize ) + 1;
	# If we request a page that is too high
	$page = $pages if $page > $pages;
	# Calc first and last programme numbers
	my $first = $pagesize * ($page - 1);
	my $last = $first + $pagesize;
	$last = $count if $last > $count;

	#print $se "PAGETRAIL: page=$page, first=$first, last=$first, pages=$pages, trailsize=$trailsize\n";
	# Page trail
	my @pagetrail;

	push @pagetrail, td( { -class=>'pagetrail pointer' }, label( {
		-title		=> "Previous Page",
		-class		=> 'pagetrail pointer',
		-onClick	=> "BackupFormVars(form); form.NEXTPAGE.value='search_progs'; form.PAGENO.value=$page-1; form.submit(); RestoreFormVars(form);",},
		"<<",
	)) if $page > 1;

	push @pagetrail, td( { -class=>'pagetrail pointer' }, label( {
		-title		=> "Page 1",
		-class		=> 'pagetrail pointer',
		-onClick	=> "BackupFormVars(form); form.NEXTPAGE.value='search_progs'; form.PAGENO.value=1; form.submit(); RestoreFormVars(form);",},
		"1",
	)) if $page > 1;

	push @pagetrail, td( { -class=>'pagetrail' }, '...' ) if $page > $trailsize+2;

 	for (my $pn=$page-$trailsize; $pn <= $page+$trailsize; $pn++) {
		push @pagetrail, td( { -class=>'pagetrail pointer' }, label( {
			-title		=> "Page $pn",
			-class		=> 'pagetrail pointer',
			-onClick	=> "BackupFormVars(form); form.NEXTPAGE.value='search_progs'; form.PAGENO.value='$pn'; form.submit(); RestoreFormVars(form);",},
			"$pn",
		)) if $pn > 1 && $pn != $page && $pn < $pages;
		push @pagetrail, td( { -class=>'pagetrail' }, label( {
			-title          => "Current Page",
			-class          => 'pagetrail-current', },
		"$page",
		)) if $pn == $page;
	}
	push @pagetrail, td( { -class=>'pagetrail' }, '...' ) if $page < $pages-$trailsize-1;

	push @pagetrail, td( { -class=>'pagetrail pointer' }, label( {
		-title		=> "Page ".$pages,
		-class		=> 'pagetrail pointer',
		-onClick	=> "BackupFormVars(form); form.NEXTPAGE.value='search_progs'; form.PAGENO.value=$pages; form.submit(); RestoreFormVars(form);",},
		"$pages",
	)) if $page < $pages;

	push @pagetrail, td( { -class=>'pagetrail pointer' }, label( {
		-title		=> "Next Page",
		-class		=> 'pagetrail pointer',
		-onClick	=> "BackupFormVars(form); form.NEXTPAGE.value='search_progs'; form.PAGENO.value=$page+1; form.submit(); RestoreFormVars(form);",},
		">>",
	)) if $page < $pages;

	push @pagetrail, td( { -class=>'pagetrail' }, label( {
		-title		=> "Matches",
		-class		=> 'pagetrail',},
		"($count programmes)",
	));

	my @html = table( { -id=>'centered', -class=>'pagetrail' }, Tr( { -class=>'pagetrail' }, @pagetrail ));
	return ($first, $last, @html);
}



sub get_progs {
	my @params = @_;
	my $options = '';

	my $fields;
	$fields .= "|<$_>" for @headings;

	my ( @webrequest_args ) = ( build_cmd_options( grep !/^(PVRHOLDOFF)$/, @params ), 'nopurge=1', "listformat=ENTRY${fields}" );
	# Page params
	if ( $opt->{PAGENO}->{current} && $opt->{PAGESIZE}->{current} ) {
		push @webrequest_args, ( "page=$opt->{PAGENO}->{current}", "pagesize=$opt->{PAGESIZE}->{current}" );
	}
	# Sort param
	push @webrequest_args, "sortreverse=$opt->{PAGENO}->{current}" if $opt->{REVERSE}->{current};
	# sort reverse param
	push @webrequest_args, "sortmatches=$opt->{SORT}->{current}" if $opt->{SORT}->{current} && $opt->{SORT}->{current} ne 'name';
	# Run command
	my @list = get_cmd_output(
		$opt_cmdline->{getiplayer},
		'--nocopyright',
		'--expiry=999999999',
		'--webrequest',
		get_iplayer_webrequest_args( @webrequest_args ),
	);
	return ( '0', join("\n", @list) ) if $? && not $IGNOREEXIT;
	# Get total matches count
	my $matchcount = pop @list;
	$matchcount = $1 if $matchcount =~ m{^INFO:\s*(\d+?)\s+};

	for ( grep /^ENTRY/, @list ) {
		chomp();
		# Strip white space
		s/\|\s*$//;

		my $record;
		my @element = split /\|/, $_;
		shift @element;

		# Put data for this contact into temporary record hash for this user
		for (my $i=0; $i <= $#headings; $i++) {
			$record->{$headings[$i]} = $element[$i];
		}

		my $search_class = 'search';

		# get the real path if file is defined
		$record->{filename} = search_absolute_path( $record->{filename} ) if $record->{filename};

		# store record in the prog global hash (prog => pid)
		$prog{ $record->{'pid'} } = $record;
		push @pids, $record->{'pid'};
	}
	return ( $matchcount, '' );
}



#
# Get the columns to display
#
sub get_display_cols {

	@displaycols = ();
	# Set default status for columns options tab checkboxes
	my %cols_status;

	# Add some default headings for history mode
	push @headings_default, 'mode' if $opt->{HISTORY}->{current};

	# Determine which columns to display (all if $cols not defined)
	my $cols = join(",", $opt->{COLS}->{current} ) || join ',', @headings_default;
	my @columns = split /,/, $cols;

	# Re-sort selected display columns into original header order
	for my $heading (@headings) {
		if ( grep /^$heading$/, @columns ) {
			# Remove display of mode and filename if not history mode
			if ( ( ! $opt->{HISTORY}->{current} ) && $heading =~ /^(mode|filename)$/ ) {
				# skip
			} else {
				push @displaycols, $heading;
			}
			$cols_status{$heading} = 1;
		}
	}

	# Make sure we select all if no cols are specified
	@displaycols = @headings_default if $#displaycols < 0;

	# Set defaults for checkboxes
	$opt->{COLS}->{status} = \%cols_status;

	# Rebuild the hash for the checkboxes
	%cols_order = ();
	%cols_names = ();
	for ( my $i = 0; $i <= $#headings; $i++ ) {
		$cols_names{$headings[$i]} = $fieldname{$headings[$i]};
		$cols_order{$i} = $headings[$i];
	}

	return 0;
}



#############################################
#
# Form Header 
#
#############################################
sub form_header {
	my $request_host = shift;
	my $nextpage = shift || $cgi->param( 'NEXTPAGE' );

	print $fh $cgi->start_form(
			-name   => "formheader",
			-method => "POST",
	);
	
	# Only highlight the 'Update Software' option if the script is writable or is not win32
	my $update_element = a( { -class=>'nav darker' }, 'Update Software' );
	$update_element = a(
		{
			-class=>'nav',
			-title=>'Update the Web PVR Manager and get_iplayer software - please restart Web PVR Manager after updating',
			-onClick => "if (! confirm('Please restart the Web PVR Manager service once the update has completed') ) { return false; } BackupFormVars(formheader); formheader.NEXTPAGE.value='update_script'; formheader.submit(); RestoreFormVars(formheader);",
		},
		'Update Software' ) if -w $0 && ! IS_WIN32;

	# set $class for tab selection in nav bar
	my $class = {};
	$class->{search}	= 'nav_tab';
	$class->{recordings}	= 'nav_tab';
	$class->{pvrlist}	= 'nav_tab';
	$class->{pvrrun}	= 'nav_tab';
	$class->{update}	= 'nav_tab';
	$class->{search}	= 'nav_tab_sel' if ( $nextpage eq 'search_progs' || ! $nextpage ) && ! $opt->{HISTORY}->{current};
	$class->{recordings}	= 'nav_tab_sel' if $nextpage eq 'search_history' || $opt->{HISTORY}->{current};
	$class->{pvrrun}	= 'nav_tab_sel' if $nextpage eq 'pvr_run';
	$class->{pvrlist}	= 'nav_tab_sel' if $nextpage =~ m{^(pvr_list|pvr_queue|pvr_del)$};
	$class->{update}	= 'nav_tab_sel' if $nextpage eq 'update_script';

	print $fh div( { -class=>'nav' },
		ul( { -class=>'nav' },
			li( { -id=>'logo', -class=>'nav_tab' },
				a( { -class=>'nav', -href=>$request_host },
					img({
						-class => 'nav',
						-title => 'get_iplayer Web PVR Manager',
						-width => 174,
						-height => 32,
						-src => "http://linuxcentre.net/get_iplayer/contrib/iplayer_logo.gif",
						-href => $request_host,
					}),
				),
			).
			li( { -class=>$class->{search} }, a( { -class=>'nav', -title=>'Main search page', -href => $request_host }, 'Search' ) ).
			li( { -class=>$class->{recordings} }, a( { -class=>'nav', -title=>'History search page', -onClick => "BackupFormVars(formheader); formheader.NEXTPAGE.value='search_history'; formheader.submit(); RestoreFormVars(formheader);" }, 'Recordings' ) ).
			li( { -class=>$class->{pvrlist} }, a( { -class=>'nav', -title=>'List all saved PVR searches', -onClick => "BackupFormVars(formheader); formheader.NEXTPAGE.value='pvr_list'; formheader.submit(); RestoreFormVars(formheader);" }, 'PVR List' ) ).
			li( { -class=>$class->{pvrrun} }, a( { -class=>'nav', -title=>'Run the PVR now - wait for the PVR to complete', -onClick => "BackupFormVars(formheader); formheader.NEXTPAGE.value='pvr_run'; formheader.target='_newtab_pvrrun'; formheader.submit(); RestoreFormVars(formheader); formheader.target='';" }, 'Run PVR' ) ).
			li( { -class=>$class->{update} }, $update_element ).
			li( { -class=>'nav_tab' }, a( { -class=>'nav', -title=>'Show help and instructions', -href => "http://linuxcentre.net/projects/get_iplayer-pvr-manager/" }, 'Help' ) )
		),
	);
	print $fh hidden( -name => 'AUTOPVRRUN', -value => $opt->{AUTOPVRRUN}->{current}, -override => 1 );
	print $fh hidden( -name => 'NEXTPAGE', -value => 'search_progs', -override => 1 );
	print $fh $cgi->end_form();	
}



# Form Footer 
sub form_footer {
	#print $fh "<iframe src=\"about:blank\" height=\"100\" width=\"95%\" name=\"dataframe\"></iframe>";
	#print $fh "<iframe src=\"about:blank\" height=\"0\" width=\"0\" name=\"dataframe\"></iframe>";
	# <script type=\"text/javascript\">window.frames['dataframe'].window.location.replace('loadData.html');</script>
	print $fh p( b({-class=>"footer"},
		sprintf( "get_iplayer Web PVR Manager v%.2f, &copy;2009-2010 Phil Lewis - Licensed under GPLv3", $VERSION )
	));
}



# End HTML
sub html_end {
	print $fh "\n</body>";
	print $fh "\n</html>\n";
}



# Gets and sets the CGI parameters (POST/Cookie) in the $opt hash - also sets $opt{VAR}->{current} from default or POST
sub process_params {

	# Store options definition here as hash of 'name' => [options]
	$opt->{SEARCH} = {
		title	=> 'Search', # Title
		tooltip	=> 'Enter your partial text match (or regex expression)', # Tooltip
		webvar	=> 'SEARCH', # webvar
		optkey	=> 'search', # option key
		type	=> 'text', # type
		default	=> '.*', # default
		value	=> 20, # width values
		save	=> 0,
	};
	
	$opt->{URL} = {
		title	=> 'Quick URL', # Title
		tooltip	=> "Enter your URL for Recording (then click 'Record' or 'Play')", # Tooltip
		webvar	=> 'URL', # webvar
		type	=> 'text', # type
		default	=> '', # default
		value	=> 36, # width values
		save	=> 0,
	};
	
	$opt->{SEARCHFIELDS} = {
		title	=> 'Search in', # Title
		tooltip	=> 'Select which column you wish to search', # Tooltip
		webvar	=> 'SEARCHFIELDS', # webvar
		optkey	=> 'fields', # option
		type	=> 'popup', # type
		label	=> \%fieldname, # labels
		default	=> 'name', # default
		value	=> [ (@headings,'name,episode','name,episode,desc') ], # values
		save	=> 1,
	};

	$opt->{PAGESIZE} = {
		title	=> 'Programmes per Page', # Title
		tooltip	=> 'Select the number of search results displayed on each page', # Tooltip
		webvar	=> 'PAGESIZE', # webvar
		type	=> 'popup', # type
		default	=> 20, # default
		value	=> ['10','25','50','100','200','400'], # values
		onChange=> "BackupFormVars(form); form.NEXTPAGE.value='search_progs'; form.PAGENO.value=1; form.submit(); RestoreFormVars(form);",
		save	=> 1,
	};

	$opt->{SORT} = {
		title	=> 'Sort by', # Title
		tooltip	=> 'Sort the results in this order', # Tooltip
		webvar	=> 'SORT', # webvar
		type	=> 'popup', # type
		label	=> \%fieldname, # labels
		default	=> 'index', # default
		value	=> [@headings], # values
		onChange=> "BackupFormVars(form); form.NEXTPAGE.value='search_progs'; form.submit(); RestoreFormVars(form);",
		save	=> 1,
	};

	$opt->{REVERSE} = {
		title	=> 'Reverse sort', # Title
		tooltip	=> 'Reverse the sort order', # Tooltip
		webvar	=> 'REVERSE', # webvar
		type	=> 'radioboolean', # type
		#onChange=> "BackupFormVars(form); form.NEXTPAGE.value='search_progs'; form.submit(); RestoreFormVars(form);",
		default	=> '0', # value
		save	=> 1,
	};

	$opt->{PROGTYPES} = {
		title	=> 'Programme type', # Title
		tooltip	=> 'Select the programme types you wish to search', # Tooltip
		webvar	=> 'PROGTYPES', # webvar
		optkey	=> 'type', # option
		type	=> 'multiboolean', # type
		label	=> \%prog_types, # labels
		default => 'tv',
		#status	=> \%type, # default status
		value	=> \%prog_types_order, # order of values
		save	=> 1,
	};

	$opt->{MODES} = {
		title	=> 'Recording Modes', # Title
		tooltip	=> 'Comma separated list of recording modes which should be tried in order', # Tooltip
		webvar	=> 'MODES', # webvar
		optkey	=> 'modes', # option
		type	=> 'text', # type
		default	=> 'flashaachigh,flashaacstd,flashaudio,flashhigh,flashstd,flashnormal,realaudio,flashaaclow', # default
		value	=> 30, # width values
		save	=> 1,
	};
	
	$opt->{OUTPUT} = {
		title	=> 'Override Recordings Folder', # Title
		tooltip	=> 'Folder on the server where recordings should be saved', # Tooltip
		webvar	=> 'OUTPUT', # webvar
		optkey	=> 'output', # option
		type	=> 'text', # type
		default	=> '', # default
		value	=> 30, # width values
		save	=> 1,
	};
	
	$opt->{PROXY} = {
		title	=> 'Web Proxy URL', # Title
		tooltip	=> 'e.g. http://192.168.1.2:8080', # Tooltip
		webvar	=> 'PROXY', # webvar
		optkey	=> 'proxy', # option
		type	=> 'text', # type
		default	=> '', # default
		value	=> 30, # width values
		save	=> 1,
	};
	
	$opt->{VERSIONLIST} = {
		title	=> 'Programme Version', # Title
		tooltip	=> 'Comma separated list of versions to try to record in order (e.g. default,signed,audiodescribed)', # Tooltip
		webvar	=> 'VERSIONLIST', # webvar
		optkey	=> 'versionlist', # option
		type	=> 'text', # type
		default	=> 'default', # default
		value	=> 30, # width values
		save	=> 1,
	};

	$opt->{EXCLUDE} = {
		title	=> 'Exclude Programmes', # Title
		tooltip	=> 'Comma separated list of programmes to exclude. Partial word matches are supported', # Tooltip
		webvar	=> 'EXCLUDE', # webvar
		optkey	=> 'exclude', # option
		type	=> 'text', # type
		default	=> '', # default
		value	=> 30, # width values
		save	=> 1,
	};

	$opt->{CATEGORY} = {
		title	=> 'Categories Containing', # Title
		tooltip	=> 'Comma separated list of categories to match. Partial word matches are supported', # Tooltip
		webvar	=> 'CATEGORY', # webvar
		optkey	=> 'category', # option
		type	=> 'text', # type
		default	=> '', # default
		value	=> 30, # width values
		save	=> 1,
	};

	$opt->{EXCLUDECATEGORY} = {
		title	=> 'Exclude Categories Containing', # Title
		tooltip	=> 'Comma separated list of categories to exclude. Partial word matches are supported', # Tooltip
		webvar	=> 'EXCLUDECATEGORY', # webvar
		optkey	=> 'excludecategory', # option
		type	=> 'text', # type
		default	=> '', # default
		value	=> 30, # width values
		save	=> 1,
	};

	$opt->{CHANNEL} = {
		title	=> 'Channels Containing', # Title
		tooltip	=> 'Comma separated list of channels to match. Partial word matches are supported', # Tooltip
		webvar	=> 'CHANNEL', # webvar
		optkey	=> 'channel', # option
		type	=> 'text', # type
		default	=> '', # default
		value	=> 30, # width values
		save	=> 1,
	};

	$opt->{EXCLUDECHANNEL} = {
		title	=> 'Exclude Channels Containing', # Title
		tooltip	=> 'Comma separated list of channels to exclude. Partial word matches are supported', # Tooltip
		webvar	=> 'EXCLUDECHANNEL', # webvar
		optkey	=> 'excludechannel', # option
		type	=> 'text', # type
		default	=> '', # default
		value	=> 30, # width values
		save	=> 1,
	};

	$opt->{HIDE} = {
		title	=> 'Hide Recorded', # Title
		tooltip	=> 'Whether to hide programmes that have already been successfully recorded', # Tooltip
		webvar	=> 'HIDE', # webvar
		optkey	=> 'hide', # option
		type	=> 'radioboolean', # type
		default	=> '0', # value
		save	=> 1,
	};

	$opt->{FORCE} = {
		title	=> 'Force Recording', # Title
		tooltip	=> "Ignore the history and re-record a programme (Please delete the existing recording first). Doesn't apply to PVR Searches or 'Add Series'", # Tooltip
		webvar	=> 'FORCE', # webvar
		optkey	=> 'force', # option
		type	=> 'radioboolean', # type
		default	=> '0', # value
		save	=> 1,
	};

	$opt->{REFRESHFUTURE} = {
		title	=> 'Refresh Future Schedule', # Title
		tooltip	=> "When Refresh is clicked also get the future programme schedule. This will take a longer time to index.", # Tooltip
		webvar	=> 'REFRESHFUTURE', # webvar
		optkey	=> 'refreshfuture', # option
		type	=> 'radioboolean', # type
		default	=> '0', # value
		save	=> 1,
	};

	my %metadata_labels = ( ''=>'Off', xbmc=>'XBMC Episode nfo format', xbmc_movie=>'XBMC Movie nfo format', generic=>'Generic XML', freevo=>'Freevo FXD' );
	$opt->{METADATA} = {
		title	=> 'Download Meta-data', # Title
		tooltip	=> 'Format of metadata file to create when recording', # Tooltip
		webvar	=> 'METADATA', # webvar
		optkey	=> 'metadata', # option
		type	=> 'popup', # type
		#label	=> \%fieldname, # labels
		label	=> \%metadata_labels, # labels
		default	=> '', # default
		value	=> [ ( '', 'xbmc', 'xbmc_movie', 'generic', 'freevo' ) ], # values
		save	=> 1,
	};

	$opt->{SUBTITLES} = {
		title	=> 'Download Subtitles', # Title
		tooltip	=> 'Whether to download the subtitles when recording', # Tooltip
		webvar	=> 'SUBTITLES', # webvar
		optkey	=> 'subtitles', # option
		type	=> 'radioboolean', # type
		default	=> '0', # value
		save	=> 1,
	};

	$opt->{THUMB} = {
		title	=> 'Download Thumbnail', # Title
		tooltip	=> 'Whether to download the thumbnail when recording', # Tooltip
		webvar	=> 'THUMB', # webvar
		optkey	=> 'thumb', # option
		type	=> 'radioboolean', # type
		default	=> '0', # value
		save	=> 1,
	};

	$opt->{AUTOWEBREFRESH} = {
		title	=> 'Auto-Refresh Cache Interval', # Title
		tooltip	=> 'Automatically refresh the default caches in another browser tab (hours)', # Tooltip
		webvar	=> 'AUTOWEBREFRESH', # webvar
		type	=> 'text', # type
		default	=> 1, # default
		value	=> 3, # width values
		save	=> 1,
	};

	$opt->{AUTOPVRRUN} = {
		title	=> 'Auto-Run PVR Interval', # Title
		tooltip	=> 'Automatically run the PVR in another browser tab (hours)', # Tooltip
		webvar	=> 'AUTOPVRRUN', # webvar
		type	=> 'text', # type
		default	=> 4, # default
		value	=> 3, # width values
		save	=> 1,
	};

	$opt->{HISTORY} = {
		title	=> 'Search History', # Title
		tooltip	=> 'Whether to display and search programmes in the recordings history', # Tooltip
		webvar	=> 'HISTORY', # webvar
		optkey	=> 'history', # option
		type	=> 'boolean', # type
		default	=> '0', # value
		save	=> 0,
	};

	$opt->{FUTURE} = {
		title	=> 'Search Future Schedule', # Title
		tooltip	=> 'Whether to additionally display and search programmes in the future programmes schedule (will only work if Refresh future schedule option is enable and refreshed)', # Tooltip
		webvar	=> 'FUTURE', # webvar
		optkey	=> 'future', # option
		type	=> 'radioboolean', # type
		default	=> '0', # value
		save	=> 1,
	};

	$opt->{SINCE} = {
		title	=> 'Added Since (hours)', # Title
		tooltip	=> 'Only show programmes added to the local programmes cache in the past number of hours', # Tooltip
		webvar	=> 'SINCE', # webvar
		optkey	=> 'since', # option
		type	=> 'text', # type
		value	=> 3, # width values
		default => '',
		save	=> 1,
	};

	$opt->{BEFORE} = {
		title	=> 'Added Before (hours)', # Title
		tooltip	=> 'Only show programmes added to the local programmes cache over this number of hours ago', # Tooltip
		webvar	=> 'BEFORE', # webvar
		optkey	=> 'before', # option
		type	=> 'text', # type
		value	=> 3, # width values
		default => '',
		save	=> 1,
	};

	$opt->{PVRHOLDOFF} = {
		title	=> 'PVR Hold off period (hours)', # Title
		tooltip	=> 'Wait this number of hours before allowing the PVR to record a programme. This sometimes helps when the flashhd version is delayed in being made available.', # Tooltip
		webvar	=> 'PVRHOLDOFF', # webvar
		optkey	=> 'before', # option
		type	=> 'text', # type
		value	=> 3, # width values
		default => '',
		save	=> 1,
	};

	my %vsize_labels = ( ''=>'Native', '1280x720'=>'1280x720', '832x468'=>'832x468', '640x360'=>'640x360', '512x288'=>'512x288', '480x272'=>'480x272', '320x176'=>'320x176', '176x96'=>'176x96' );
	$opt->{VSIZE} = {
		title	=> 'Remote Streaming Video Size', # Title
		tooltip	=> "Video size '<width>x<height>' to transcode remotely played files - leave blank for native size", # Tooltip
		webvar	=> 'VSIZE', # webvar
		type	=> 'popup', # type
		label	=> , \%vsize_labels, # labels
		default	=> '', # default
		value	=> [ (sort {$a <=> $b} keys %vsize_labels) ], # values
		save	=> 1,
	};

	$opt->{BITRATE} = {
		title	=> 'Remote Audio Bitrate', # Title
		tooltip	=> 'Remote Audio Bitrate (in kbps) to transcode remotely played files - leave blank for native bitrate', # Tooltip
		webvar	=> 'BITRATE', # webvar
		type	=> 'text', # type
		value	=> 3, # width values
		default => '',
		save	=> 1,
	};

	$opt->{VFR} = {
		title	=> 'Remote Video Frame Rate', # Title
		tooltip	=> 'Remote Video Frame Rate (in frames per second) to transcode remotely played files - leave blank for native framerate', # Tooltip
		webvar	=> 'VFR', # webvar
		type	=> 'text', # type
		value	=> 2, # width values
		default => '',
		save	=> 1,
	};

	my %streamtype_labels = ( ''=>'Auto', 'none'=>'Disable Transcoding', 'flv'=>'Flash Video (flv)', 'mov'=>'Quicktime (mov)', 'asf'=>'Advanced Streaming Format (asf)', 'avi'=>'AVI', 'mp3'=>'MP3 (Audio Only)', 'aac'=>'AAC (Audio Only)', 'wav'=>'WAV (Audio Only)', 'flac'=>'FLAC (Audio Only)' );
	$opt->{STREAMTYPE} = {
		title	=> "Remote Streaming type", # Title
		tooltip	=> "Force the output to be this type when using 'Play Remote' for 'PlayDirect' streaming(e.g. flv, mov). Specify 'none' to disable transcoding/remuxing.  Leave blank for auto-detection", # Tooltip
		webvar	=> 'STREAMTYPE', # webvar
		type	=> 'popup', # type
		label	=> , \%streamtype_labels, # labels
		default	=> '', # default
		value	=> [ '', 'none', 'flv', 'mov', 'asf', 'avi', 'mp3', 'aac', 'wav', 'flac' ], # values
		onChange=> "form.submit();",
		save	=> 1,
	};

	# Whether to hide deleted programmes from the Recordings display.
	$opt->{HIDEDELETED} = {
		title	=> 'Hide Deleted Recordings', # Title
		tooltip	=> 'Whether to hide deleted programmes from the recordings history list', # Tooltip
		webvar	=> 'HIDEDELETED', # webvar
		optkey	=> 'skipdeleted', # option
		type	=> 'radioboolean', # type
		default	=> 0, # value
		save	=> 1,
	};

	# Which columns to display
	$opt->{COLS} = {
		title	=> 'Enable Columns', # Title
		tooltip	=> 'Select the columns you wish to display', # Tooltip
		webvar	=> 'COLS', # webvar
		#optkey	=> 'type', # option
		type	=> 'multiboolean', # type
		label	=> \%cols_names, # labels
		#status	=> \%cols_status, # default status
		value	=> \%cols_order, # order of values
		save	=> 1,
	};

	# Make sure we go to the correct nextpage for processing
	$opt->{NEXTPAGE} = {
		webvar  => 'NEXTPAGE',
		type	=> 'hidden',
		default	=> 'search_progs',
		save	=> 0,
	};

	# Make sure we go to the correct nextpage for processing
	$opt->{ACTION} = {
		webvar  => 'ACTION',
		type	=> 'hidden',
		default	=> '',
		save	=> 0,
	};

	# Make sure we go to the correct next page no.
	$opt->{PAGENO} = {
		webvar  => 'PAGENO',
		type	=> 'hidden',
		default	=> 1,
		save	=> 0,
	};

	# Remeber the status of the tab options display
	for my $tabname ( grep !/BASICTAB/, @{ $layout->{taborder} } ) {
		my $default = 'no';
		# By default only show advanced search tab
		$default = 'yes' if $tabname eq 'SEARCHTAB';
		$opt->{$tabname} = {
			webvar	=> $tabname, # webvar
			type	=> 'hidden', # type
			default	=> $default, # value
			save	=> 0,
		};
	}

	# Save the status of the Advanced Search options and preferences settings
	$opt->{SAVE} = {
		webvar	=> 'SAVE', # webvar
		type	=> 'hidden', # type
		default	=> '0', # value
		save	=> 0,
	};

	# INFO for page info if clicked
	$opt->{INFO} = {
		webvar  => 'INFO',
		type	=> 'hidden',
		default	=> 0,
		save	=> 0,
	};


	# Go through each of the options defined above
	for ( keys %{ $opt } ) {
		# Ignore cookies if we are saving new ones
		if ( not $cgi->param('SAVE') ) {
			if ( defined $cgi->param($_) ) {
				print $se "DEBUG: GOT Param  $_ = ".$cgi->param($_)."\n" if $opt_cmdline->{debug};
				$opt->{$_}->{current} = join ",", $cgi->param($_);
			} elsif (  defined $cgi->cookie($_) ) {
				print $se "DEBUG: GOT Cookie $_ = ".$cgi->cookie($_)."\n" if $opt_cmdline->{debug};
				$opt->{$_}->{current} = join ",", $cgi->cookie($_);
			} else {
				$opt->{$_}->{current} =  join ",", $opt->{$_}->{default};
			}
			print $se "DEBUG: Using $_ = $opt->{$_}->{current}\n--\n" if $opt_cmdline->{debug};
			
		} else {
			$opt->{$_}->{current} = join(",", $cgi->param($_) ) || $opt->{$_}->{default} if not defined $opt->{$_}->{current};
		}
	}
}



######################################################################
#
#   begin_html
# 
#   Send HTTP headers to browser
#   Sets "title", Sends <HTML> and <BODY> flags
#
######################################################################
sub begin_html {
	my $request_host = shift;
	my $mimetype = 'text/html';
	
	# Save settings if selected
	my @cookies;
	if ( $cgi->param('SAVE') ) {
		print $se "DEBUG: Sending cookies\n";
		for ( %{ $opt } ) {
			# skip if opt not allowed to be saved
			next if not $opt->{$_}->{save};
			my $cookie = $cgi->cookie( -name=>$_, -value=>$opt->{$_}->{current}, -expires=>'+1y' );
			push @cookies, $cookie;
			print $se "DEBUG: Sending cookie: $cookie\n" if $opt_cmdline->{debug};
		}
		# Ensure SAVE state is reset to off
		$opt->{SAVE}->{current} = 0;
	}

	# Send the headers to the browser
	my $headers = $cgi->header(
		-type		=> $mimetype,
		-charset	=> 'utf-8',
		-cookie		=> [@cookies],
	);
	print $se "\nHEADERS:\n$headers\n" if $opt_cmdline->{debug};

	# Build body element and page title differently depending on the type of page
	# Load the refresh tab if required
	my $body_element;
	my $title;
	my $autorefresh = $cgi->cookie( 'AUTOWEBREFRESH' ) || $cgi->param( 'AUTOWEBREFRESH' );
	my $autopvrrun  = $cgi->cookie( 'AUTOPVRRUN' ) || $cgi->param( 'AUTOPVRRUN' );
	if ( $autorefresh && $cgi->param( 'NEXTPAGE' ) eq 'refresh' ) {
		$body_element = "<BODY onLoad=\"javascript:RefreshTab( '${request_host}?NEXTPAGE=refresh&AUTOWEBREFRESH=$autorefresh&PROGTYPES=$opt->{PROGTYPES}->{current}', ".(1000*3600*$autorefresh)." );\">";
		$title = 'Refreshing Cache: get_iplayer Web PVR Manager';
	} elsif ( $autopvrrun && $cgi->param( 'NEXTPAGE' ) eq 'pvr_run' ) {
		$body_element = "<BODY onLoad=\"javascript:RefreshTab( '${request_host}?NEXTPAGE=pvr_run&AUTOPVRRUN=$autopvrrun', ".(1000*3600*$autopvrrun)." );\">";
		$title = 'Running PVR: get_iplayer Web PVR Manager';
	} else {
		$body_element = "<body>\n";
		$title = sprintf "get_iplayer Web PVR Manager v%.2f", $VERSION;
	}

	# Write out the page http and html headers
	print $fh $headers;
	print $fh '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">'."\n";
	print $fh "<html>";
	print $fh "<HEAD><TITLE>$title</TITLE>\n";
	insert_stylesheet();
	print $fh "</HEAD>\n";
	insert_javascript();
	print $fh $body_element;
}



#############################################
#
# Javascript Functions here
#
#############################################
sub insert_javascript {

	print $fh <<EOF;

	<script type="text/javascript">
	
	function RefreshTab(url, time, force ) {
		if ( force ) {
			window.location.href = url;
		}
		setTimeout( "RefreshTab('" + url + "'," + time + ", 1 )", time );
	}


	// global hash table for saving copy of form
	var form_backup = {};
	
	//
	// Copy all non-grouped form values into a global hash
	//
	function BackupFormVars( form ) {
		// empty out array
		for(var key in form_backup) {
			delete( form_backup[key] );
		}

		// copy forms elements
		var elem = form.elements;
		for(var i = 0; i < elem.length; i++) {
			// exclude radio and checkbox types - can be duplicate names in groups...
			if ( elem[i].type != "checkbox" && elem[i].type != "radio" ) {
				form_backup[ elem[i].name ] = elem[i].value;
			}
		} 
	}

	//
	// Copy all form values in the global hash into the specified form
	//	
	function RestoreFormVars( form ) {
		// copy form elements
		for(var key in form_backup) {
			form.elements[ key ].value = form_backup[key];
			// delete element
			delete( form_backup[key] );
		}
	}

	//
	// Hide show an element (and modify the text of the button/label)
	// e.g. document.getElementById('advanced_opts').style.display='table';
	//
	// Usage: show_options_tab( SELECTEDID, [ 'TAB1', 'TAB2' ] );
	// Displays first tab in list or tab suffixes
	// tab_TAB1 is the table element
	// option_TAB1 is the form variable
	// button_TAB1 is the label
	//
	function show_options_tab( selectedid, tabs ) {

		// selected tab element
		var selected_tab = document.getElementById( 'tab_' + selectedid );

		// Loop through the above tab elements
		for(var i = 0; i < tabs.length; i++) {
			var li     = document.getElementById( 'li_' + tabs[i] );
			var tab    = document.getElementById( 'tab_' + tabs[i] );
			var option = document.getElementById( 'option_' + tabs[i] );
			var button = document.getElementById( 'button_' + tabs[i] );
			if ( tab == selected_tab ) {
				tab.style.display = 'table-cell';
				tab.style.visibility = 'visible';
				option.value = 'yes';
				//button.innerHTML = '- ' + button.innerHTML.substring(2);
				button.style.color = '#F54997';
				//li.style.borderBottom = '0px solid #666';
				li.className = 'options_tab_sel';
			} else {
				tab.style.display = 'none';
				tab.style.visibility = 'collapse';
				option.value = 'no';
				//button.innerHTML = '+ ' + button.innerHTML.substring(2);
				button.style.color = '#ADADAD';
				//li.style.borderBottom = '1px solid #666';
				li.className = 'options_tab';
			}
		}
		return true;
	}
	
	//
	// Check/Uncheck all checkboxes named <name>
	//
	function check_toggle(f, name) {
		var empty_fields = "";
		var errors = "";
		var check;

		if (f.SELECTOR.checked == true) {
			check = 1;
		} else {
			check = 0;
		}

		// Loop through the elements of the form
		for(var i = 0; i < f.length; i++) {
			var e = f.elements[i];
			if (e.type == "checkbox" && e.name == name) {
				if (check == 1) {
					// First check if the box is checked (don't check a disabled box)
					if(e.checked == false && e.disabled == false) {
						e.checked = true;
					}
				} else {
					// First check if the box is not checked
					if(e.checked == true) {
						e.checked = false;
					}
				}
			}
		}
		return true;
	}

	//
	// Warn if none of the checkboxes named <name> are selected
	//
	function check_if_selected(f, name) {
		// Loop through the elements of the form
		for(var i = 0; i < f.length; i++) {
			var e = f.elements[i];
			if (e.type == "checkbox" && e.name == name && e.checked == true) {
				return true;
			}
		}
		return false;
	}

	//
	// Disable checkboxes named <name> that are selected
	//
	function disable_selected_checkboxes(f, name) {
		var empty_fields = "";
		var errors = "";
		var check;

		// Loop through the elements of the form
		for(var i = 0; i < f.length; i++) {
			var e = f.elements[i];
			if (e.type == "checkbox" && e.name == name) {
				// First check if the box is checked
				if(e.checked == true) {
					e.checked = false;
					e.disabled = true;
				}
			}
		}
		return true;
	}

	//
	// Submit Search only if enter is pressed from a textfield
	// Called as: onKeyDown="return submitonEnter(event);"
	//
	function submitonEnter(evt){
		var charCode = (evt.which) ? evt.which : event.keyCode
		if ( charCode == "13" ) {
			document.form.NEXTPAGE.value='search_progs';
			document.form.PAGENO.value=1;
			document.form.submit();
		}
	}

	</SCRIPT>
EOF
}



#############################################
#
# CSS1 Styles here
#
#############################################
sub insert_stylesheet {
	print $fh <<EOF;

	<STYLE type="text/css">
	
	.pointer		{ cursor: pointer; cursor: hand; }
	.pointer:hover		{ text-decoration: underline; }

	.pointer_noul		{ cursor: pointer; cursor: hand; }

	.extra_border		{ border-left: 2px solid #666; }
	.all_borders		{ border-left: 2px solid #666; border-right: 2px solid #666; border-top: 2px solid #666; border-bottom: 2px solid #666; }

	.darker			{ color: #7D7D7D; }
	#logo			{ width: 190px; border-width: 0 0 1px 0; }
	#underline		{ text-decoration: underline; }
	#nowrap			{ white-space: nowrap; }
	#smaller80pc		{ font-size: 80%; }

	BODY			{ color: #FFF; background: black; font-size: 90%; font-family: verdana, sans-serif; }
	IMG			{ border: 0; }
	INPUT			{ border: 0 none; background: #ddd; }
	A			{ color: #FFF; text-decoration: none; }
	A:hover			{ text-decoration: none; }

	TABLE.title 		{ font-size: 150%; border-spacing: 0px; padding: 0px; }
	A.title			{ color: #F54997; font-weight: bold; font-family: Arial,Helvetica,sans-serif; }

	/* Nav bar */
	DIV.nav			{ font-family: Arial,Helvetica,sans-serif; background-color: #000; color: #FFF; }
	UL.nav			{ cursor: pointer; cursor: hand; padding-left: 0px; background-color: #000; font-size: 100%; font-weight: bold; height: 44px; margin: 0; margin-left: 0px; list-style-image: none; overflow: hidden; }
	LI.nav_tab		{ padding-left: 0px; border-top: 1px solid #444; border-left: 1px solid #444; border-right: 1px solid #444; border-bottom: 1px solid #888; display: inline; float: left; height: 42px; margin: 0; width: 13%; }
	LI.nav_tab_sel		{ padding-left: 0px; border-top: 1px solid #888; border-left: 1px solid #888; border-right: 1px solid #888; border-bottom: 0px solid #888; display: inline; float: left; height: 42px; margin: 0; width: 13%; }
	A.nav			{ display: block; height: 42px; line-height: 42px; text-align: center; }
	IMG.nav			{ padding: 7px; display: block; text-align: center; text-decoration: none; }
	A.nav:hover		{ color: #ADADAD; }

	TABLE.header		{ font-size: 80%; border-spacing: 1px; padding: 0; }
	INPUT.header		{ font-size: 80%; } 
	SELECT.header		{ font-size: 80%; } 

	TABLE.types		{ font-size: 70%; text-align: left; border-spacing: 0px; padding: 0; }
	TR.types		{ white-space: nowrap; }
	TD.types		{ width: 20px }
	
	TABLE.options_embedded	{ font-size: 100%; text-align: left; border-spacing: 0px; padding: 0; white-space: nowrap; }
	TR.options_embedded	{ white-space: nowrap; }
	TH.options_embedded	{ width: 20px }
	TD.options_embedded	{ width: 20px }

	/*DIV.options		{ padding-top: 10px; padding-bottom: 10px; font-family: Arial,Helvetica,sans-serif; background-color: #000; color: #FFF; }*/
	/* options_tab */
	UL.options_tab		{ text-align: left; cursor: pointer; cursor: hand; list-style-type: none; display: inline; padding-left: 0px; background-color: #000; font-size: 100%; font-weight: bold; height: 24px; margin: 0; margin-left: 0px; list-style-image: none; overflow: hidden; }
	/* selected tab button */
	LI.options_tab_sel	{ padding-left: 10px; padding-right: 10px; padding-bottom: 2px; padding-top: 2px; border-top: 1px solid #888; display: inline; float: left; border-left: 1px solid #888; border-right: 1px solid #888; border-bottom: 0px solid #888; margin: 0; margin-left: 0px; margin-bottom: 5px; }
	/* unselected tab button */
	LI.options_tab		{ padding-left: 10px; padding-right: 10px; padding-bottom: 2px; padding-top: 2px; border-top: 1px solid #444; display: inline; float: left; border-left: 1px solid #444; border-right: 1px solid #444; border-bottom: 1px solid #888; margin: 0; margin-left: 0px; margin-bottom: 5px; }
	/* unselected tab button */
	LI.options_button	{ padding-left: 10px; padding-right: 10px; padding-bottom: 2px; padding-top: 2px; border-top: 1px solid #888; display: inline; float: left; border-left: 1px solid #888; border-right: 1px solid #888; border-bottom: 1px solid #888; margin: 0; margin-right: 5px; margin-bottom: 5px; }

	TABLE.options		{ font-size: 100%; text-align: left; border-spacing: 0px; padding: 0; white-space: nowrap; }
	TR.options		{ white-space: nowrap; }
	TH.options		{ padding-right: 4px; text-align: left; }
	TD.options		{ }
	LABEL.options		{ font-size: 100%; } 
	INPUT.options[type="radio"],INPUT.options[type="checkbox"] { font-size: 100%; background:none; }
	INPUT.options		{ font-size: 100%; } 
	SELECT.options		{ font-size: 100%; } 

	TABLE.options_outer	{ font-size: 70%; text-align: left; border-spacing: 0px 0px; padding: 0; white-space: nowrap; overflow: visible; table-layout: fixed; }
	TR.options_outer	{ vertical-align: top; white-space: nowrap; }
	TH.options_outer	{ }
	TD.options_outer	{ padding-right: 50px; }
	LABEL.options_outer	{ font-weight: bold; font-size: 120%; color: #F54997; font-family: Arial,Helvetica,sans-serif; } 
	LABEL.options_heading	{ font-weight: bold; font-size: 110%; color: #CCC; } 
	
	/* Action bar */
	DIV.action		{ padding-top: 10px; padding-bottom: 10px; font-family: Arial,Helvetica,sans-serif; background-color: #000; color: #FFF; }
	UL.action		{ padding-left: 0px; background-color: #000; font-size: 100%; font-weight: bold; height: 24px; margin: 0; margin-left: 0px; list-style-image: none; overflow: hidden; }
	LI.action		{ cursor: pointer; cursor: hand; padding-left: 0px; border-top: 1px solid #888; border-left: 1px solid #666; border-right: 1px solid #666; border-bottom: 1px solid #666; display: inline; float: left; height: 22px; margin: 0; margin-left: 2px; width: 13.0%; }
	A.action		{ color: #FFF; display: block; height: 42px; line-height: 22px; text-align: center; }
	IMG.action		{ padding: 7px; display: block; text-align: center; text-decoration: none; }
	A.action:hover		{ color: #ADADAD; }

	TABLE.pagetrail		{ font-size: 70%; text-align: center; font-weight: bold; border-spacing: 10px 0; padding: 0px; }
	#centered		{ height:20px; margin:0px auto 0; position: relative; }
	LABEL.pagetrail		{ color: #FFF; }
	LABEL.pagetrail-current	{ color: #F54997; }

	TABLE.colselect		{ font-size: 70%; color: #fff; background: #333; border-spacing: 2px; padding: 0; }
	TR.colselect		{ text-align: left; }
	TH.colselect		{ font-weight: bold; }
	INPUT.colselect		{ font-size: 70%; }
	LABEL.colselect		{ font-size: 70%; }
	
	TABLE.search		{ font-size: 70%; color: #fff; background: #333; border-spacing: 2px; padding: 0; width: 100%; }
	TABLE.searchhead	{ font-size: 110%; border-spacing: 0px; padding: 0; width: 100%; }
	TR.search		{ background: #444; }
	TR.search:hover		{ background: #555; }
	TH.search		{ color: #FFF; text-align: center; background: #000; text-align: center; }
	TD.search		{ text-align: left; }
	A.search		{ }
	LABEL.search		{ text-decoration: none; }
	INPUT.search		{ font-size: 70%; background: none; }
	LABEL.sorted            { color: #CFC; }
	LABEL.unsorted          { color: #FFF; }
	LABEL.sorted_reverse    { color: #FCC; }
	INPUT.edit		{ font-size: 100%; background: #DDD; }

	TABLE.info		{ font-size: 70%; color: #fff; background: #333; border-spacing: 2px; padding: 0; }
	TR.info			{ background: #444; }
	TR.info:hover		{ background: #555; }
	TH.info			{ color: #FFF; text-align: center; background: #000; text-align: center; }
	TD.info			{ text-align: left; }
	A.info			{ text-decoration: underline; }
	A.info:hover		{ }

	B.footer		{ font-size: 70%; color: #777; font-weight: normal; }
	</STYLE>
EOF

}
