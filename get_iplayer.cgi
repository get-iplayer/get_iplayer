#!/usr/bin/perl
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
my $VERSION = '0.30';

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
	my $text = sprintf "get_iplayer PVR Manager v%.2f, ", $VERSION;
	$text .= <<'EOF';
Copyright (C) 2009 Phil Lewis
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
$opt_cmdline->{ffmpeg} = 'ffmpeg' if ! $opt_cmdline->{ffmpeg};
$opt_cmdline->{listen} = '0.0.0.0' if ! $opt_cmdline->{listen};
# Search for get_iplayer
if ( ! $opt_cmdline->{getiplayer} ) {
	for ( './get_iplayer', './get_iplayer.cmd', './get_iplayer.pl', '/usr/bin/get_iplayer' ) {
		$opt_cmdline->{getiplayer} = $_ if -x $_;
	}
}

# Path to get_iplayer (+ set HOME env var cos apache seems to not set it)
my $home = $ENV{HOME};

my %prog;
my @pids;
my @displaycols;

# Field names grabbed from get_iplayer
my @headings = qw( index thumbnail pid available type name episode versions duration desc channel categories timeadded guidance web);

# Default Displayed headings
my @headings_default = qw( thumbnail type name episode desc channel categories );

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
	'name,episode'		=> 'Name+Episode',
	'name,episode,desc'	=> 'Name+Episode+Desc',
);

# Lookup table for nice field name headings
my %sorttype = (
	index		=> 'numeric',
	duration	=> 'numeric',
	timeadded	=> 'numeric',
);

my %prog_types = (
	tv	=> 'BBC TV',
	radio	=> 'BBC Radio',
	podcast	=> 'BBC Podcast',
	itv	=> 'ITV',
	livetv	=> 'Live BBC TV',
	liveradio => 'Live BBC Radio',
);
my %prog_types_order = (
	1	=> 'tv',
	2	=> 'radio',
	3	=> 'podcast',
	4	=> 'itv',
	5	=> 'livetv',
	6	=> 'liveradio',
);
# Get list of currently valid and prune %prog types and add new entry
chomp( my @plugins = split /,/, `$opt_cmdline->{getiplayer} --nopurge --nocopyright --listplugins` );
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
	'search_progs'			=> \&search_progs,	# Main Programme Listings
	'pvr_queue'			=> \&pvr_queue,		# Queue Recording of Selected Progs
	'pvr_list'			=> \&show_pvr_list,	# Show all current PVR searches
	'pvr_del'			=> \&pvr_del,		# Delete selected PVR searches
	'pvr_add'			=> \&pvr_add,
	'pvr_run'			=> \&pvr_run,
	'show_info'			=> \&show_info,
	'flush'				=> \&flush,
	'update_script'			=> \&update_script,
);



##### Options #####
my $opt;

# Options Ordering on page
my @order_basic_opts = qw/ SEARCH SEARCHFIELDS PAGESIZE SORT PROGTYPES /;
my @order_adv_opts = qw/ VERSIONLIST CATEGORY EXCLUDECATEGORY CHANNEL EXCLUDECHANNEL HIDE SINCE /;
my @order_settings = qw/ OUTPUT MODES PROXY /;
my @hidden_opts = qw/ SAVE ADVANCED REVERSE PAGENO INFO NEXTPAGE /;
# Any params that should never get into the get_iplayer pvr-add search
my @nosearch_params = qw/ /;

# Store options definition here as hash of 'name' => [options]
	$opt->{SEARCH} = {
		title	=> 'Search', # Title
		webvar	=> 'SEARCH', # webvar
		optkey	=> 'search', # option key
		type	=> 'text', # type
		default	=> '.*', # default
		value	=> 20, # width values
		save	=> 0,
	};
	
	$opt->{SEARCHFIELDS} = {
		title	=> 'Search in', # Title
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
		webvar	=> 'PAGESIZE', # webvar
		type	=> 'popup', # type
		default	=> 20, # default
		value	=> ['10','25','50','100','200','400'], # values
		onChange=> "form.NEXTPAGE.value='search_progs'; submit()",
		save	=> 1,
	};

	$opt->{SORT} = {
		title	=> 'Sort by', # Title
		webvar	=> 'SORT', # webvar
		type	=> 'popup', # type
		label	=> \%fieldname, # labels
		default	=> 'index', # default
		value	=> [@headings], # values
		onChange=> "form.NEXTPAGE.value='search_progs'; submit()",
		save	=> 1,
	};

	$opt->{PROGTYPES} = {
		title	=> 'Programme type', # Title
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
		webvar	=> 'MODES', # webvar
		optkey	=> 'modes', # option
		type	=> 'text', # type
		default	=> 'flashaac,flashaudio,flashhigh,iphone,flashnormal,realaudio', # default
		value	=> 40, # width values
		save	=> 1,
	};
	
	$opt->{OUTPUT} = {
		title	=> 'Override Recordings Folder', # Title
		webvar	=> 'OUTPUT', # webvar
		optkey	=> 'output', # option
		type	=> 'text', # type
		default	=> '', # default
		value	=> 40, # width values
		save	=> 1,
	};
	
	$opt->{PROXY} = {
		title	=> 'Web Proxy URL', # Title
		webvar	=> 'PROXY', # webvar
		optkey	=> 'proxy', # option
		type	=> 'text', # type
		default	=> '', # default
		value	=> 40, # width values
		save	=> 1,
	};
	
	$opt->{VERSIONLIST} = {
		title	=> 'Programme Version', # Title
		webvar	=> 'VERSIONLIST', # webvar
		optkey	=> 'versionlist', # option
		type	=> 'text', # type
		default	=> 'default', # default
		value	=> 40, # width values
		save	=> 1,
	};

	$opt->{CATEGORY} = {
		title	=> 'Categories Containing', # Title
		webvar	=> 'CATEGORY', # webvar
		optkey	=> 'category', # option
		type	=> 'text', # type
		default	=> '', # default
		value	=> 40, # width values
		save	=> 1,
	};

	$opt->{EXCLUDECATEGORY} = {
		title	=> 'Exclude Categories Containing', # Title
		webvar	=> 'EXCLUDECATEGORY', # webvar
		optkey	=> 'excludecategory', # option
		type	=> 'text', # type
		default	=> '', # default
		value	=> 40, # width values
		save	=> 1,
	};

	$opt->{CHANNEL} = {
		title	=> 'Channels Containing', # Title
		webvar	=> 'CHANNEL', # webvar
		optkey	=> 'channel', # option
		type	=> 'text', # type
		default	=> '', # default
		value	=> 40, # width values
		save	=> 1,
	};

	$opt->{EXCLUDECHANNEL} = {
		title	=> 'Exclude Channels Containing', # Title
		webvar	=> 'EXCLUDECHANNEL', # webvar
		optkey	=> 'excludechannel', # option
		type	=> 'text', # type
		default	=> '', # default
		value	=> 40, # width values
		save	=> 1,
	};

	$opt->{HIDE} = {
		title	=> 'Hide Recorded', # Title
		webvar	=> 'HIDE', # webvar
		optkey	=> 'hide', # option
		type	=> 'radioboolean', # type
		default	=> '0', # value
		save	=> 1,
	};

	$opt->{SINCE} = {
		title	=> 'Added Since (hours)', # Title
		webvar	=> 'SINCE', # webvar
		optkey	=> 'since', # option
		type	=> 'text', # type
		value	=> 3, # width values
		default => '',
		save	=> 1,
	};

	### Non-visible options ##
	$opt->{COLS} = {
		webvar	=> 'COLS', # webvar
		default	=> undef, # width values
		save	=> 0,
	};

	# Make sure we go to the correct nextpage for processing
	$opt->{NEXTPAGE} = {
		webvar  => 'NEXTPAGE',
		type	=> 'hidden',
		default	=> 'search_progs',
		save	=> 0,
	};

	# Reverse sort value
	$opt->{REVERSE} = {
		webvar  => 'REVERSE',
		type	=> 'hidden',
		default	=> 0,
		save	=> 1,
	};

	# Make sure we go to the correct next page no.
	$opt->{PAGENO} = {
		webvar  => 'PAGENO',
		type	=> 'hidden',
		default	=> 1,
		save	=> 0,
	};

	# Remeber the status of the Advanced options display
	$opt->{ADVANCED} = {
		webvar	=> 'ADVANCED', # webvar
		type	=> 'hidden', # type
		default	=> 'no', # value
		save	=> 1,
	};

	# Save the status of the Advanced options settings
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


### Perl CGI Web Server ###
use Socket;
use IO::Socket;
my $IGNOREEXIT = 0;
# If the port number is specified then run embedded web server
if ( $opt_cmdline->{port} > 0 ) {
	# Setup signal handlers
	$SIG{INT} = $SIG{PIPE} = \&cleanup;
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
			Reuse => 1
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
			if ( $request{URL} =~ /^\/?(iplayer|stream|record|playlist|genplaylist|opml|runpvr|)\/?$/ ) {
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
				run_cgi( $client, $query_string, $request{URL}, $request{host} );

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
	run_cgi( *STDOUT );
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
		$val =~ s/%(..)/chr(hex($1))/eg;
		push @data, "$key=$val";
	}
	return join '&', @data;
}



sub run_cgi {
	# Get filehandle for output
	$fh = shift;
	my $query_string = shift;
	my $request_url = shift;
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

	# Stream
	if ( $request_url =~ /^\/?stream/i ) {
		my $type = $cgi->param( 'OUTTYPE' ) || 'flv';
		# Remove fileprefix
		$type =~ s/^.*\.//g;
		# Stream mime types
		my %mimetypes = (
			wav 	=> 'audio/x-wav',
			flac	=> 'audio/x-flac',
			mp3 	=> 'audio/mpeg',
			rm	=> 'audio/x-pn-realaudio',
			mov 	=> 'video/quicktime',
			mp4	=> 'video/x-flv',
			avi	=> 'video/x-flv',
			flv	=> 'video/x-flv',
			asf	=> 'video/x-ms-asf',
		);

		# Default mime type depending on mode
		$type = 'flv' if $opt->{MODES}->{current} =~ /^flash/ && ! $type;

		# If type is defined
		if ( $mimetypes{$type} ) {

			# Output headers
			# to stream 
			# This will enable seekable -Accept_Ranges=>'bytes',
			my $headers = $cgi->header( -type => $mimetypes{$type}, -Connection => 'close' );

			# Send the headers to the browser
			print $se "\r\nHEADERS:\n$headers\n"; #if $opt_cmdline->{debug};
			print $fh $headers;

			# Default Recipies
			# Need to determine --type and then set the default --modes and default outtype for conversion if required
			# No conversion for iphone radio as mp3
			$type = undef if $opt->{MODES}->{current} eq 'iphone' && $type eq 'mp3';
			# No conversion for realaudio radio as rm
			$type = undef if $opt->{MODES}->{current} eq 'realaudio' && $type eq 'rm';
			# No conversion for flv
			$type = undef if $type eq 'flv';
			# Don't set type and convert if video
			$type = undef if $mimetypes{$type} =~ /^video/;

			stream_prog( $cgi->param( 'PID' ), $opt->{MODES}->{current}, $type, $cgi->param( 'BITRATE' ) );
		} else {
			print $se "ERROR: Aborting client thread - output mime type is undetermined\n";
		}

	# Record file
	} elsif ( $request_url =~ /^\/?record/i ) {
		# Output headers
		# To save file
		my $headers = $cgi->header( -type => 'video/quicktime', -attachment => $cgi->param('FILENAME').'.mov' || $cgi->param('PID').'.mov' );

		# Send the headers to the browser
		print $se "\r\nHEADERS:\n$headers\n"; #if $opt_cmdline->{debug};
		print $fh $headers;

		stream_mov( $cgi->param('PID') );

	# Get a playlist for a specified 'PROGTYPES'
	} elsif ( $request_url =~ /^\/?playlist/i ) {
		# Output headers
		my $headers = $cgi->header( -type => 'audio/x-mpegurl' );

		# Send the headers to the browser
		print $se "\r\nHEADERS:\n$headers\n"; #if $opt_cmdline->{debug};
		print $fh $headers;
		# ( host, outtype, modes, type, bitrate )
		print $fh get_playlist( $request_host, $cgi->param('OUTTYPE') || 'flv', $opt->{MODES}->{current}, $opt->{PROGTYPES}->{current} , $cgi->param('BITRATE') || '', $opt->{SEARCH}->{current}, $opt->{SEARCHFIELDS}->{current} || 'name' );

	# Get a playlist for a specified 'PROGTYPES'
	} elsif ( $request_url =~ /^\/?opml/i ) {
		# Output headers
		my $headers = $cgi->header( -type => 'text/xml' );

		# Send the headers to the browser
		print $se "\r\nHEADERS:\n$headers\n"; #if $opt_cmdline->{debug};
		print $fh $headers;
		# ( host, outtype, modes, type, bitrate )
		print $fh get_opml( $request_host, $cgi->param('OUTTYPE') || 'flv', $opt->{MODES}->{current}, $opt->{PROGTYPES}->{current} , $cgi->param('BITRATE') || '', $opt->{SEARCH}->{current}, $cgi->param('LIST') || '' );

	# Get a playlist for a selected progs in form
	} elsif ( $request_url =~ /^\/?genplaylist/i ) {
		# Output headers
		my $headers = $cgi->header( -type => 'audio/x-mpegurl' );
		# To save file
		#my $headers = $cgi->header( -type => 'audio/x-mpegurl', -attachment => 'get_iplayer.m3u' );

		# Send the headers to the browser
		print $se "\r\nHEADERS:\n$headers\n"; #if $opt_cmdline->{debug};
		print $fh $headers;
		# ( host, outtype, modes, type, bitrate )
		print $fh create_playlist_m3u( $request_host, $cgi->param('OUTTYPE') || 'flv', $cgi->param('BITRATE') || '' );

	# HTML page
	} elsif ( $request_url =~ /^\/?(iplayer|)$/i ) {
		# Output headers
		http_headers();
	
		# html start
		begin_html();

		# Page Routing
		form_header();
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
	print $se "INFO: Starting Manual PVR Run\n";
	# Redirect both STDOUT and STDERR to client browser socket
	open(STDOUT, ">&", $fh )   || die "can't dup client to stdout";
	# Unbuffered output
	STDOUT->autoflush(1);
	STDERR->autoflush(1);
	my $cmd = "$opt_cmdline->{getiplayer} --nopurge --nocopyright --hash --pvr";
	print $se "DEBUG: running: $cmd\n";
	print $fh '<pre>';
	# Before stderr
	my $before_se = $se;
	open(STDERR, ">&", $fh )   || die "can't dup client to stderr";
	system $cmd;
	# Restore stderr
	$se = $before_se;
	print $fh '</pre>';
	print $fh p("PVR Run complete");
}



sub stream_mov {
	my $pid = shift;

	print $se "INFO: Start Streaming $pid to browser\n";
	open(STDOUT, ">&", $fh )   || die "can't dup client to stdout";
	my @cmd = ( $opt_cmdline->{getiplayer}, '--nocopyright', get_iplayer_webrequest_args( 'nopurge=1', 'modes=iphone', 'stream=1', "pid=$pid" ) );
	print $se "DEBUG: running: ".(join ' ', @cmd)."\n";
	system @cmd;

	print $se "INFO: Finished Streaming $pid to browser\n";

	return 0;
}



sub stream_prog {
	my $pid = shift;
	my $modes = shift || 'flash,iphone';
	my $type = shift;
	my $bitrate = shift;
	
	print $se "INFO: Start Streaming $pid to browser using modes '$modes' and output type '$type' and bitrate '$bitrate'\n";

	open(STDOUT, ">&", $fh ) || die "can't dup client to stdout";
	# Enable buffering
	STDOUT->autoflush(0);
	$fh->autoflush(0);
	my @cmd = ( $opt_cmdline->{getiplayer}, '--nocopyright', get_iplayer_webrequest_args( 'nopurge=1', "modes=$modes", 'stream=1', "pid=$pid" ) );
	my $command = join(' ', @cmd);

	# If conversion is necessary
	if ( $type && ! $bitrate ) {
		$command .= " | $opt_cmdline->{ffmpeg} -i - -vn -f $type -";
	} elsif ($type && $bitrate ) {
		$command .= " | $opt_cmdline->{ffmpeg} -i - -vn -ab ${bitrate}k -f $type -";
	}

	print $se "DEBUG: Command: $command\n";
	system $command;

	print $se "INFO: Finished Streaming $pid to browser\n";

	return 0;
}



sub get_playlist {
	my ( $request_host, $outtype, $modes, $type, $bitrate, $search, $searchfields ) = ( @_ );
	my @playlist;
	$outtype =~ s/^.*\.//g;

	print $se "INFO: Getting playlist for type '$type' using modes '$modes' and bitrate '$bitrate'\n";
	my $cmd = $opt_cmdline->{getiplayer}.' --nocopyright '.get_iplayer_webrequest_args( 'nopurge=1', "type=$type", 'listformat=<pid>|<name>|<episode>|<desc>', "fields=$searchfields", "search=$search" );
	my @out = `$cmd`;

	push @playlist, "#EXTM3U\n";

	# Extract and rewrite into m3u format
	for ( grep !/^Added:/ , @out ) {
		chomp();
		my ($pid, $name, $episode, $desc) = (split /\|/)[0,1,2,3];
		next if ! ( $pid && $name );
		# Format required, e.g.
		##EXTINF:-1,BBC Radio - BBC Radio One (High Quality Stream)
		#http://localhost:1935/stream?PID=liveradio:bbc_radio_one&MODES=flashaac&OUTTYPE=bbc_radio_one.wav
		#
		push @playlist, "#EXTINF:-1,$type - $name - $episode - $desc";
		push @playlist, "http://${request_host}/stream?PID=${type}:${pid}&MODES=${modes}&OUTTYPE=${pid}.${outtype}\n";
	}

	return join ("\n", @playlist);
}



sub create_playlist_m3u {
	my ( $request_host, $outtype, $bitrate ) = ( @_ );
	my @playlist;
	push @playlist, "#EXTM3U\n";

	my @record = ( $cgi->param( 'PROGSELECT' ) );

	# Create m3u from all selected '<type>|<pid>|<name>|<episode>' entries in the PVR
	for (@record) {
		chomp();
		my ( $type, $pid, $name, $episode ) = ($1, $2, $3, $4) if m{^(.+?)\|(.+?)\|(.+?)\|(.+?)$};
		# Format required, e.g.
		##EXTINF:-1,BBC Radio - BBC Radio One (High Quality Stream)
		#http://localhost:1935/stream?PID=liveradio:bbc_radio_one&MODES=flashaac&OUTTYPE=bbc_radio_one.wav
		#
		push @playlist, "#EXTINF:-1,$type - $name - $episode";
		push @playlist, "http://${request_host}/stream?PID=${type}:${pid}&MODES=$opt->{current}->{modes}&OUTTYPE=${pid}.${outtype}\n";
	}

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
		my $cmd = $opt_cmdline->{getiplayer}.' --nocopyright '.get_iplayer_webrequest_args( 'nopurge=1', "type=$type", 'listformat=<pid>|<name>|<episode>|<desc>', "search=$search" );
		print $se "DEBUG: Command: $cmd\n";
		for ( grep !/^Added:/, `$cmd` ) {
			chomp();
			# Strip unprinatble chars
			s/(.)/(ord($1) > 127) ? "" : $1/egs;
			my ($pid, $name, $episode, $desc) = (split /\|/)[0,1,2,3];
			next if ! ( $pid && $name );
			# Format required, e.g.
			#http://localhost:1935/stream?PID=liveradio:bbc_radio_one&MODES=flashaac&OUTTYPE=bbc_radio_one.wav
			push @playlist, "\t\t<outline URL=\"".encode_entities("http://${request_host}/stream?PID=${type}:${pid}&MODES=${modes}&OUTTYPE=${pid}.${outtype}")."\"  bitrate=\"${bitrate}\" source=\"get_iplayer\" title=\"".encode_entities("$name - $episode - $desc")."\" text=\"".encode_entities("$name - $episode - $desc")."\" type=\"audio\" />";
		}

	# Channels/Names etc
	} elsif ($list) {
	
		# Header
		push @playlist, "\t<head>\n\t\t\n\t</head>";
		push @playlist, "\t<body>";

		# Extract and rewrite into playlist format
		my $cmd = $opt_cmdline->{getiplayer}.' --nocopyright '.get_iplayer_webrequest_args( 'nopurge=1', "type=$type", "list=$list", "channel=$search" );
		print $se "DEBUG: Command: $cmd\n";
		for ( grep !/^Added:/, `$cmd` ) {
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
			push @playlist, "\t\t<outline URL=\"".encode_entities("http://${request_host}/opml?PROGTYPES=${type}&SEARCH=${itemregex}${suffix}&MODES=${modes}&OUTTYPE=a.wav")."\" text=\"".encode_entities("$item")."\" title=\"".encode_entities("$item")."\" type=\"playlist\" />";
		}

	}

	# Footer
	push @playlist, "\t</body>\n</opml>";

	return join ("\n", @playlist);
}


# Update script
# Generic
# Updates and overwrites this script - makes backup as <this file>.old
# Update logic:
# If the get_iplayer.cgi script is unwritable then quit
# update script
sub update_script {
	my $update_url	= 'http://linuxcentre.net/get_iplayer/get_iplayer.cgi';
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
		print $fh p("Update Failed");
	} else {
		print $fh p("Update Succeeded - please restart the get_iplayer PVR Manager service");
	}

	return 0;
}



sub create_ua {
	my $ua = LWP::UserAgent->new;
	$ua->timeout( 10 );
	$ua->agent( "get_iplayer PVR Manager updater version $VERSION" );
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



sub get_pvr_list {
	my $pvrsearch;
	my $out = `$opt_cmdline->{getiplayer} --nocopyright --pvrlist`;
	
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
                  ($title, $class, $onclick) = ("Sort by Reverse $heading", 'sorted pointer', "form.NEXTPAGE.value='pvr_list'; form.PVRSORT.value='$heading'; form.PVRREVERSE.value=1; submit()");
                } else {
                  ($title, $class, $onclick) = ("Sort by $heading", 'unsorted pointer', "form.NEXTPAGE.value='pvr_list'; form.PVRSORT.value='$heading'; submit()");
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
			push @row, td( {-class=>'search'}, $pvrsearch->{$name}->{$_} );
		}
		push @html, Tr( {-class=>'search'}, @row );
	}

	
	# Search form
	print $fh start_form(
		-name   => "form",
		-method => "POST",
	);

	print $fh button(
		-class		=> 'search',
		-name		=> 'Delete Selected PVR Entries',
		-onClick 	=> "form.NEXTPAGE.value='pvr_del'; submit()",
	);

	print $fh table( {-class=>'search'} , @html );
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
		my $cmd = $opt_cmdline->{getiplayer}.' --nocopyright '.get_iplayer_webrequest_args( "pvrdel=$name" );
		print $fh p("Command: $cmd") if $opt_cmdline->{debug};
		my $cmdout = `$cmd`;
		return p("ERROR: ".$out) if $? && not $IGNOREEXIT;
		print $fh p("Deleted: $name");
		$out .= $cmdout;
	}
	print $fh pre($out);
	return $out;
}



sub show_info {
	my $progdata = ( $cgi->param( 'INFO' ) );
	my $out;
	my @html;
	my ( $type, $pid ) = split /\|/, $progdata;

	# Queue all selected '<type>|<pid>' entries in the PVR
	chomp();
	my $cmd = $opt_cmdline->{getiplayer}.' --nocopyright '.get_iplayer_webrequest_args( 'nopurge=1', "type=$type", 'info=1', "search=pid:$pid" );
	print $fh p("Command: $cmd") if $opt_cmdline->{debug};
	my @cmdout = `$cmd`;
	return p("ERROR: ".@cmdout) if $? && not $IGNOREEXIT;
	print $fh p("Info for $pid");
	for ( grep !/^Added:/, @cmdout ) {
		my ( $key, $val ) = ( $1, $2 ) if m{^(\w+?):\s*(.+?)\s*$};
		next if $key =~ /(^$|^\d+$)/ || $val =~ /Matching Program/i;
		$out .= "$key: $val\n";
		push @html, Tr( { -class => 'info' }, th( { -class => 'info' }, $key ).td( { -class => 'info' }, $val ) );
	}
	print $fh table( { -class => 'info' }, @html );
	return $out;
}



sub pvr_queue {
	my @record = ( $cgi->param( 'PROGSELECT' ) );
	my $out;

	# Queue all selected '<type>|<pid>' entries in the PVR
	for (@record) {
		chomp();
		my ( $type, $pid, $name, $episode ) = ($1, $2, $3, $4) if m{^(.+?)\|(.+?)\|(.+?)\|(.+?)$};
		my $comment = "$name - $episode";
		$comment =~ s/\'\"//g;
		$comment =~ s/[^\s\w\d\-:\(\)]/_/g;
		my $cmd = $opt_cmdline->{getiplayer}.' --nocopyright '.get_iplayer_webrequest_args( "type=$type", 'pvrqueue=1', "pid=$pid", "comment=$comment (queued: ".localtime().')' );
		print $fh p("Command: $cmd") if $opt_cmdline->{debug};
		my $cmdout = `$cmd`;
		return p("ERROR: ".$out) if $? && not $IGNOREEXIT;
		print $fh p("Queued: $type: '$name - $episode' ($pid)");
		$out .= $cmdout;
	}
	print $fh pre($out);
	return $out;
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
	my $cmdline = '--webrequest="'.join('&', @cmdopts).'"';
	return $cmdline;
}



sub pvr_add {

	my $out;
	my @params = get_search_params();

	# Only allow alphanumerics,_,-,. here for security reasons
	my $searchname = "$opt->{SEARCH}->{current}_$opt->{SEARCHFIELDS}->{current}_$opt->{PROGTYPES}->{current}";
	$searchname =~ s/[^\w\-\. \+\(\)]/_/g;

	# Check how many matches first
	get_progs( @params );
	my $matches = keys %prog;
	if ( $matches > 30 ) {
		print $fh p("ERROR: Search term '$opt->{SEARCH}->{current}' currently matches $matches programmes - keep below 30 current matches");
		return 1;
	} else {
		print $fh p("Current Matches: ".(keys %prog));
	}

	my $cmd  = $opt_cmdline->{getiplayer}.' '.get_iplayer_webrequest_args( "pvradd=$searchname", build_cmd_options( @params ) );
	print $se "Command: $cmd";
	print $fh p("Command: $cmd") if $opt_cmdline->{debug};
	my $cmdout = `$cmd`;
	return p("ERROR: ".$out) if $? && not $IGNOREEXIT;
	print $fh p("Added PVR Search ($searchname):\n\tTypes: $opt->{PROGTYPES}->{current}\n\tSearch: $opt->{SEARCH}->{current}\n\tSearch Fields: $opt->{SEARCHFIELDS}->{current}\n");
	print $fh pre($out);

	return $out;
}


# Build templated HTML for an option specified by passed hashref
sub build_option_html {
	my $arg = shift;
	
	my $title = $arg->{title};
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
		push @html, th( { -class => 'options' }, $title ).
		td( { -class => 'options' },
			checkbox(
				-class		=> 'options',
				-name		=> $webvar,
				-id		=> "option_$webvar",
				-label		=> '',
				#-value 		=> 1,
				-checked	=> $current,
				-override	=> 1,
			)
		);


	# On/Off
	} elsif ( $type eq 'radioboolean' ) {
		push @html, th( { -class => 'options' }, $title ).
		td( { -class => 'options' },
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
		my @keylist = sort keys %{ $value };
		my $count = 0;
		while ( @keylist ) {
			my $val = $value->{shift @keylist};
			$element .=
				td( { -class => 'options' },
					table ( { -class => 'options_embedded' }, Tr( { -class => 'options_embedded' }, td( { -class => 'options_embedded' }, [
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
			
		push @html, th( { -class => 'options' }, $title ).td( { -class => 'options' }, $inner_table );
	# Popup type
	} elsif ( $type eq 'popup' ) {
		my @value = $arg->{value};
		push @html, th( { -class => 'options' }, $title ).
		td( { -class => 'options' }, 
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
		push @html, th( { -class => 'options' }, $title ).
		td( { -class => 'options' },
			textfield(
				-class		=> 'options',
				-name		=> $webvar,
				-value		=> $current,
				-size		=> $value,
				-onKeyDown	=> 'return submitonEnter(event);',
			)
		);

	}
	#return table( { -class=>'options' }, Tr( { -class=>'options' }, @html ) );
	return @html;
}


sub flush {
	my $typelist = join(",", $cgi->param( 'PROGTYPES' )) || 'tv';
	print $se "INFO: Flushing\n";
	open(STDOUT, ">&", $fh )   || die "can't dup client to stdout";
	my $cmd  = $opt_cmdline->{getiplayer}.' --nocopyright '.get_iplayer_webrequest_args( 'flush=1', 'nopurge=1', "type=$typelist", "search=no search just flush" );
	print $se "DEBUG: running: $cmd\n";
	print $fh '<pre>';
	system $cmd;
	print $fh '</pre>';
	print $fh p("Flushed Programme Caches for Types: $typelist");
}



sub search_progs {
	# Set default status for progtypes
	my %type;
	$type{$_} = 1 for split /,/, $opt->{PROGTYPES}->{current};
	$opt->{PROGTYPES}->{status} = \%type;

	# Determine which cols to display
	get_display_cols();

	# Get prog data
	my $response;
	my @params = get_search_params();
	if ( $response = get_progs( @params ) ) {
		print $fh p("ERROR: get_iplayer returned non-zero:").br().p( join '<br>', $response );
		return 1;
	}

	# Sort
	@pids = get_sorted( \%prog, $opt->{SORT}->{current}, $opt->{REVERSE}->{current} );

	my ($first, $last, @pagetrail) = pagetrail( $opt->{PAGENO}->{current}, $opt->{PAGESIZE}->{current}, $#pids+1, 7 );


	# Default displaycols
	my @html;
	push @html, "<tr>";
	push @html, th( { -class => 'search' }, checkbox( -class=>'search', -title=>'Select/Unselect All Programmes', -onClick=>"check_toggle(document.form, 'PROGSELECT')", -name=>'SELECTOR', -value=>'1', -label=>'' ) );
	# Pad empty column for R/S
	push @html, th( { -class => 'search' }, 'Play / Queue' );
	# Display data in nested table
	for my $heading (@displaycols) {

		# Sort by column click and change display class (colour) according to sort status
		my ($title, $class, $onclick);
		if ( $opt->{SORT}->{current} eq $heading && not $opt->{REVERSE}->{current} ) {
			($title, $class, $onclick) = ("Sort by Reverse $heading", 'sorted pointer', "form.NEXTPAGE.value='search_progs'; form.SORT.value='$heading'; form.REVERSE.value=1; submit()");
		} else {
			($title, $class, $onclick) = ("Sort by $heading", 'unsorted pointer', "form.NEXTPAGE.value='search_progs'; form.SORT.value='$heading'; form.REVERSE.value=0; submit()");
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
						).
						th({ -class => 'search' },
							checkbox(
								-class		=> 'search',
								-name		=> 'COLS',
								-label		=> '',
								-value 		=> $heading,
								-checked	=> 1,
								-override	=> 1,
								-onChange	=> "form.NEXTPAGE.value='search_progs'; submit()"
							)
						)
					]
				)
			)
		);
	}
	push @html, "</tr>";

	# Build each prog row
	for ( my $i = $first; $i < $last && $i <= $#pids; $i++ ) {
		my $pid = $pids[$i]; 
		my @row;
		push @row, td( {-class=>'search'},
			checkbox(
				-class		=> 'search',
				-name		=> 'PROGSELECT',
				-label		=> '',
				-value 		=> "$prog{$pid}->{type}|$pid|$prog{$pid}->{name}|$prog{$pid}->{episode}",
				-checked	=> 0,
				-override	=> 1,
			)
		);
		# Record and stream links
		# Fix output type and mode per prog type
		my %streamopts = (
			radio		=> '&MODES=iphone&OUTTYPE=mp3',
			tv		=> '&MODES=iphone&OUTTYPE=mov',
			livetv		=> '&MODES=flashnormal&OUTTYPE=flv',
			liveradio	=> '&MODES=flash&BITRATE=320&OUTTYPE=mp3',
			itv		=> '&OUTTYPE=asf',
		);
		push @row, td( {-class=>'search'}, 
			a( { -class=>'search', -title=>'Play Now', -href=>'/playlist?PROGTYPES='.CGI::escape($prog{$pid}->{type}).'&SEARCH='.CGI::escape($pid).'&SEARCHFIELDS=pid&MODES=flash,iphone,realaudio&OUTTYPE=out.flv' }, 'Play' )
			.'|'.
			a( { -class=>'search', -title=>'Queue for Recording', -href=>'/?NEXTPAGE=pvr_queue&PROGSELECT='.CGI::escape("$prog{$pid}->{type}|$pid|$prog{$pid}->{name}|$prog{$pid}->{episode}") }, 'Queue' )
			#.'/'.
			#a( { -class=>'search', -title=>'Record', -href=>'/record?PID='.CGI::escape("$prog{$pid}->{type}:$pid").'&FILENAME='.CGI::escape("$prog{$pid}->{name}_$prog{$pid}->{episode}_$pid") }, 'R' )
			#.'/'.
			#a( { -class=>'search', -title=>'Stream mov', -href=>'/stream?PID='.CGI::escape("$prog{$pid}->{type}:$pid").$streamopts{ $prog{$pid}->{type} } }, 'S' )
		);

		for ( @displaycols ) {
			if ( /^thumbnail$/ ) {
				push @row, td( {-class=>'search'}, a( { -title=>"Open URL", -class=>'search', -href=>$prog{$pid}->{web} }, img( { -class=>'search', -height=>40, -src=>$prog{$pid}->{$_} } ) ) );
			} else {
				push @row, td( {-class=>'search'}, label( { -class=>'search', -title=>"Click for full info", -onClick=>"form.NEXTPAGE.value='show_info'; form.INFO.value='$prog{$pid}->{type}|$pid'; submit()" }, $prog{$pid}->{$_} ) );
			}
		}
		push @html, Tr( {-class=>'search'}, @row );
	}


	# Search form
	print $fh start_form(
		-name   => "form",
		-method => "POST",
	);


	# Generate the html for all these options in THIS ORDER
	# Build basic options tables + hidden
	my @optrows_basic;
	push @optrows_basic, td( { -class=>'options' }, label( { -class => 'options_heading' }, 'Search Options:' ) );
	for ( @order_basic_opts, @hidden_opts ) {
		push @optrows_basic, build_option_html( $opt->{$_} );
	}
	# Build Advanced options table cells
	my @optrows_advanced;
	if ( @order_adv_opts ) {
		push @optrows_advanced, td( { -class=>'options' }, label( { -class => 'options_heading' }, 'Advanced Search Options:' ) );
		for ( @order_adv_opts ) {
			push @optrows_advanced, build_option_html( $opt->{$_} );
		}
	}
	# Add 'Settings' title (if required)
	my @optrows_settings;
	if ( @order_settings ) {
		push @optrows_advanced, td( { -class=>'options' }, label( { -class => 'options_heading' }, 'Other Settings:' ) );
		# Build Settings table cells
		for ( @order_settings ) {
			push @optrows_advanced, build_option_html( $opt->{$_} );
		}
	}

	# Set advanced options cell status and label
	my $adv_style;
	my $adv_label;
	if ( $opt->{ADVANCED}->{current} eq 'no' || not $opt->{ADVANCED}->{current} ) {
		$adv_style = "display: none;";
		$adv_label = 'Show Advanced Options';
	} else {
		$adv_style = "display: table;";
		$adv_label = 'Hide Advanced Options';
	}

	# Render outer options table frame (keeping advanced cell initially hidden)
	print $fh table( { -class=>'options_outer' },
		Tr( { -class=>'options_outer' },
			td( { -class=>'options_outer' },
				# Advanced Options button
				label( {
					-class		=> 'options_outer pointer',
					-id		=> 'advanced_opts_button',
					-onClick	=> "toggle_display( 'option_ADVANCED', 'advanced_opts', 'advanced_opts_button', 'Show Advanced Options', 'Hide Advanced Options' );",
					},
					$adv_label,
				),
			),
			td( { -class=>'options_outer' },
				# Save Options button
				label( {
					-class		=> 'options_outer pointer',
					-onClick	=> "form.SAVE.value=1; submit();",
					},
					'Remember Options',
				),
			)
		),
		Tr( { -class=>'options_outer' }, 
			td( { -class=>'options_outer' },
				table( { -class=>'options' }, Tr( { -class=>'options' }, [ @optrows_basic ] ) )
			).
			td( { -class=>'options_outer', -id=>'advanced_opts', -style=>"$adv_style" },
				table( { -class=>'options' }, Tr( { -class=>'options' }, [ @optrows_advanced ] ) )
			)
		),
	);

	# Render options actions
	print $fh div( { -class=>'action' },
		ul( { -class=>'action' },
			li( { -class=>'action' }, [
				a( { -class=>'action', -onClick  => "form.NEXTPAGE.value='search_progs'; form.PAGENO.value=1; form.submit()", },
					'Search'
				),
				a( { -class=>'action', -onClick => "form.NEXTPAGE.value='pvr_queue'; form.submit()", },
					'Queue for Recording'
				),
				a( { -class=>'action', -onClick => "form.NEXTPAGE.value='create_playlist_m3u'; form.action='genplaylist'; form.submit(); form.action='';", },
					'Create Playlist'
				),
				a( { -class=>'action', -onClick => "form.NEXTPAGE.value='pvr_add'; form.submit()", },
					'Add Current Search to PVR'
				),
				a( { -class=>'action', -onClick => "form.NEXTPAGE.value='flush'; form.submit()", },
					'Refresh Cache'
				),
			]),
		),
	);

	print $fh @pagetrail;
	print $fh table( {-class=>'search' }, @html );
	print $fh @pagetrail;

	print $fh div( {id=>'status'} );

	my @columnselect;
	for my $heading (@headings) {
		next if grep(/$heading/i, @displaycols);
		push @columnselect, (
			Tr( { -class=>'colselect' }, 
				td( { -class=>'colselect' }, [
					checkbox(
						-class		=> 'colselect',
						-name		=> 'COLS',
						-label		=> $fieldname{$heading},
						-value 		=> $heading,
						-checked	=> 0,
						-override	=> 1,
						-onChange	=> "form.NEXTPAGE.value='search_progs'; submit()",
					)
				])
			)
		);
	}
	unshift @columnselect, Tr( { -class=>'colselect' }, th( { -class=>'colselect' }, "Enable these columns:" ) ) if @columnselect;

	# Display drop down menu with multiple select for columns shown
	print $fh table( { -class => 'colselect' }, @columnselect );


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
		-onClick	=> "form.NEXTPAGE.value='search_progs'; form.PAGENO.value=$page-1; submit()",},
		"<<",
	)) if $page > 1;

	push @pagetrail, td( { -class=>'pagetrail pointer' }, label( {
		-title		=> "Page 1",
		-class		=> 'pagetrail pointer',
		-onClick	=> "form.NEXTPAGE.value='search_progs'; form.PAGENO.value=1; submit()",},
		"1",
	)) if $page > 1;

	push @pagetrail, td( { -class=>'pagetrail' }, '...' ) if $page > $trailsize+2;

 	for (my $pn=$page-$trailsize; $pn <= $page+$trailsize; $pn++) {
		push @pagetrail, td( { -class=>'pagetrail pointer' }, label( {
			-title		=> "Page $pn",
			-class		=> 'pagetrail pointer',
			-onClick	=> "form.NEXTPAGE.value='search_progs'; form.PAGENO.value='$pn'; submit()",},
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
		-onClick	=> "form.NEXTPAGE.value='search_progs'; form.PAGENO.value=$pages; submit()",},
		"$pages",
	)) if $page < $pages;

	push @pagetrail, td( { -class=>'pagetrail pointer' }, label( {
		-title		=> "Next Page",
		-class		=> 'pagetrail pointer',
		-onClick	=> "form.NEXTPAGE.value='search_progs'; form.PAGENO.value=$page+1; submit()",},
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
	my $cmd = $opt_cmdline->{getiplayer}.' --nocopyright '.get_iplayer_webrequest_args( build_cmd_options( @params ), 'nopurge=1', "listformat=ENTRY${fields}" );

	print $se "DEBUG: Command: $cmd\n";
	my @list = `$cmd`;
	return join("\n", @list) if $? && not $IGNOREEXIT;

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

		# store record in the prog global hash (prog => pid)
		$prog{ $record->{'pid'} } = $record;
	}
}



#
# Get the columns to display
#
sub get_display_cols {
        @displaycols = ();

        # Determine which columns to display (all if $cols not defined)
        my $cols = join(",", $cgi->param( 'COLS' )) || '';

        # Re-sort selected display columns into original header order
        my @columns = split /,/, $cols;
        for my $heading (@headings) {
          push @displaycols, $heading if grep /^$heading$/, @columns;
        }

	# Make sure we select all if no cols are specified
	@displaycols = @headings_default if $#displaycols < 0;

	return 0;
}



######################################################################
#
#   begin_html
#      Sets "title", Sends <HTML> and <BODY> flags
#
######################################################################
sub begin_html {
	print $fh "<html>";
	print $fh "<HEAD><TITLE>get_iplayer PVR Manager</TITLE>\n";
	insert_stylesheet();
	print $fh "</HEAD>\n";
	insert_javascript();
	print $fh "<body>\n";
}



# Send HTTP headers to browser
sub http_headers {
	my $mimetype = 'text/html';
	my $filename = shift;
	
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
	print $fh $headers;
}



#############################################
#
# Form Header 
#
#############################################
sub form_header {
	my $nextpage = shift || $cgi->param( 'NEXTPAGE' );

	print $fh $cgi->start_form(
			-name   => "formheader",
			-method => "POST",
	);
	
	#print $fh  table( { -id=>'centered', -class=>'title' }, Tr( { -class=>'title' }, td( { -class=>'title' },
	#	a( { -class=>'title', -href => "http://linuxcentre.net/getiplayer/" }, 
	#		label({ -class=>'title' },
	#			'get_iplayer PVR Manager',
	#		)
	#	)
	#)));

	# Only highlight the 'Update PVR Manager' option if the script is writable
	my $update_element = a( { -class=>'nav darker' }, 'Update PVR Manager' );
	$update_element = a( { -class=>'nav', -onClick => "formheader.NEXTPAGE.value='update_script'; formheader.submit()", }, 'Update PVR Manager' ) if -w $0;

	print $fh div( { -class=>'nav' },
		ul( { -class=>'nav' },
			li( { -class=>'nav' }, [
				a( { -class=>'nav', -href=>"/" },
					img({
						-title => 'get_iplayer PVR Manager',
						-class => 'nav',
						-width => 174,
						-height => 32,
						-src => "http://linuxcentre.net/get_iplayer/contrib/iplayer_logo.gif",
					}),
				),
				#a( { -class=>'nav', -onClick  => "history.back()", },
				#	'Back'
				#),
				a( { -class=>'nav', -onClick => "formheader.NEXTPAGE.value='search_progs'; formheader.submit()", },
					'Home'
				),
				a( { -class=>'nav', -onClick => "formheader.NEXTPAGE.value='pvr_list'; formheader.submit()", },
					'PVR List'
				),
				a( { -class=>'nav', -onClick => "formheader.NEXTPAGE.value='pvr_run'; formheader.submit()", },
					'Run PVR'
				),
				$update_element,
				a( { -class=>'nav', -onClick => "parent.location='http://linuxcentre.net/projects/get_iplayer-pvr-manager/'", },
					'Help'
				),
			]),
		),
	);

	print $fh hidden( -name => "NEXTPAGE", -value => 'search_progs', -override => 1 );
	print $fh $cgi->end_form();
	
	#hr({-size=>1});
}



#############################################
#
# Form Footer 
#
#############################################
sub form_footer {
	print $fh p( b({-class=>"footer"},
		sprintf( "get_iplayer PVR Manager v%.2f, &copy;2009 Phil Lewis - Licensed under GPLv3", $VERSION )
	));
}


#############################################
#
# End HTML
#
#############################################
sub html_end {
	print $fh "\n</body>";
	print $fh "\n</html>\n";
}



# Gets and sets the CGI parameters (POST/Cookie) in the $opt hash - also sets $opt{VAR}->{current} from default or POST
sub process_params {
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



#############################################
#
# Javascript Functions here
#
#############################################
sub insert_javascript {

	print $fh <<EOF;

	<script type="text/javascript">

	//
	// Hide show an element (and modify the text of the button/label)
	// e.g. document.getElementById('advanced_opts').style.display='table';
	//
	function toggle_display( optid, hideid, labelid, showtext, hidetext) {
	
		// get unique element for specified id
		var e = document.getElementById(hideid);
		var l = document.getElementById(labelid);

		// toggle hide and show
		// then update the text value of the calling element
		if ( e.style.display != 'none' ) {
			e.style.display = 'none';
			l.textContent = showtext;
			document.getElementById(optid).value = 'no';
		} else {
			e.style.display = '';
			l.textContent = hidetext;
			document.getElementById(optid).value = 'yes';
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
					// First check if the box is checked
					if(e.checked == false) {
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

	.darker			{ color: #ADADAD; }

	BODY			{ color: #FFF; background: black; font-size: 90%; font-family: verdana, sans-serif; }
	IMG			{ border: 0; }
	INPUT			{ border: 0 none; background: #ddd; }

	TABLE.title 		{ font-size: 150%; border-spacing: 0px; padding: 0px; }
	A.title			{ color: #F54997; text-decoration: none; font-weight: bold; font-family: Arial,Helvetica,sans-serif; }

	/* Nav bar */
	DIV.nav			{ font-family: Arial,Helvetica,sans-serif; background-color: #000; color: #FFF; }
	UL.nav			{ padding-left: 0px; background-color: #000; font-size: 100%; font-weight: bold; height: 44px; margin: 0; margin-left: 0px; list-style-image: none; overflow: hidden; }
	LI.nav			{ cursor: pointer; cursor: hand; padding-left: 0px; border-top: 1px solid #888; border-right: 1px solid #666; border-bottom: 1px solid #666; display: inline; float: left; height: 42px; margin: 0; margin-left: 2px; width: 16.2%; }
	A.nav			{ display: block; height: 42px; line-height: 42px; text-align: center; text-decoration: none; }
	IMG.nav			{ padding: 7px; display: block; text-align: center; text-decoration: none; }
	A.nav:hover		{ color: #ADADAD; text-decoration: none; }

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

	TABLE.options		{ font-size: 100%; text-align: left; border-spacing: 0px; padding: 0; white-space: nowrap; }
	TR.options		{ white-space: nowrap; }
	TH.options		{ width: 20px }
	TD.options		{ width: 20px }
	LABEL.options		{ font-size: 100%; } 
	INPUT.options		{ font-size: 100%; } 
	SELECT.options		{ font-size: 100%; } 

	TABLE.options_outer	{ font-size: 70%; text-align: left; border-spacing: 10px 0px; padding: 0; white-space: nowrap; }
	TR.options_outer	{ vertical-align: top; white-space: nowrap; }
	TH.options_outer	{ }
	TD.options_outer	{ }
	LABEL.options_outer	{ font-weight: bold; font-size: 110%; color: #4A4; } 
	LABEL.options_heading	{ font-weight: bold; font-size: 110%; color: #CCC; } 
	
	/* Action bar */
	DIV.action		{ padding-top: 10px; padding-bottom: 10px; font-family: Arial,Helvetica,sans-serif; background-color: #000; color: #FFF; }
	UL.action		{ padding-left: 0px; background-color: #000; font-size: 100%; font-weight: bold; height: 24px; margin: 0; margin-left: 0px; list-style-image: none; overflow: hidden; }
	LI.action		{ cursor: pointer; cursor: hand; padding-left: 0px; border-top: 1px solid #888; border-left: 1px solid #666; border-right: 1px solid #666; border-bottom: 1px solid #666; display: inline; float: left; height: 22px; margin: 0; margin-left: 2px; width: 19.5%; }
	A.action		{ display: block; height: 42px; line-height: 22px; text-align: center; text-decoration: none; }
	IMG.action		{ padding: 7px; display: block; text-align: center; text-decoration: none; }
	A.action:hover		{ color: #ADADAD; text-decoration: none; }

	TABLE.pagetrail		{ font-size: 70%; text-align: center; font-weight: bold; border-spacing: 10px 0; padding: 0px; }
	#centered		{ height:20px; margin:0px auto 0; position: relative; }
	LABEL.pagetrail		{ Color: #FFF; }
	LABEL.pagetrail-current	{ Color: #F54997; }

	TABLE.colselect		{ font-size: 70%; Color: #fff; background: #333; border-spacing: 2px; padding: 0; }
	TR.colselect		{ text-align: left; }
	TH.colselect		{ font-weight: bold; }
	INPUT.colselect		{ font-size: 70%; }
	LABEL.colselect		{ font-size: 70%; }
	
	TABLE.search		{ font-size: 70%; Color: #fff; background: #333; border-spacing: 2px; padding: 0; width: 100%; }
	TABLE.searchhead	{ font-size: 110%; border-spacing: 0px; padding: 0; width: 100%; }
	TR.search		{ background: #444; }
	TR.search:hover		{ background: #555; }
	TH.search		{ Color: #FFF; text-align: center; background: #000; text-align: center; }
	TD.search		{ text-align: left; }
	A.search		{ Color: #FFF; text-decoration: none; }
	LABEL.search		{ text-decoration: none; }
	INPUT.search		{ font-size: 70%; background: #DDD; }
	LABEL.sorted            { Color: #CFC; }
	LABEL.unsorted          { Color: #FFF; }
	LABEL.sorted_reverse    { Color: #FCC; }

	TABLE.info		{ font-size: 70%; Color: #fff; background: #333; border-spacing: 2px; padding: 0; }
	TR.info			{ background: #444; }
	TR.info:hover		{ background: #555; }
	TH.info			{ Color: #FFF; text-align: center; background: #000; text-align: center; }
	TD.info			{ text-align: left; }

	B.footer		{ font-size: 70%; color: #777; font-weight: normal; }
	</STYLE>
EOF

}
