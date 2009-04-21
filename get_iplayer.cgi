#!/usr/bin/perl
#
# The Worlds most insecure web manager for get_iplayer
# ** WARNING ** Never run this in an untrusted environment or facing the internet
#
# (C) Phil Lewis, 2009
# License: GPLv3
#
my $VERSION = '0.11';

# Features:
# * Search for progs
# * Lists/Adds/Removes PVR entries
#
# Installation:
# * By default this will run as apache user and save all settings files in /var/www/.get_iplayer
# * Change the $get_iplayer variable to tell this script where get_iplayer can be found (may need to set $HOME also)
# * Ensure that the output dir ($home) is writable by apache user
# * Add a line in /etc/crontab to do the pvr downloads: "0 * * * * apache /usr/bin/get_iplayer --pvr 2>/dev/null"
# * in apache config, add a line like: ScriptAlias /get_iplayer.cgi "/path/to/get_iplayer.cgi"
# * Access using http://<your web server>/get_iplayer.cgi
#
# Caveats:
# * Sometimes takes a while to load page while refreshing caches
#
# Todo:
# * Manual flush of Indicies (maybe normally set --expiry to 99999999 and warn that indicies are out of date)
# * Add loads of options
# * in general, take presentation data out of the html and into css, take scripting out of the html and into the js

use strict;
use CGI ':all';
use IO::File;
use URI::Escape;
my $DEBUG = 0;
$| = 1;
my $fh;



# Path to get_iplayer (+ set HOME env var cos apache seems to not set it)
my $home = $ENV{HOME};
my $get_iplayer = '/usr/bin/get_iplayer';
my $get_iplayer_cmd = "export HOME=$home; $get_iplayer";

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
#	hulu	=> 'Hulu TV',
);

my $icons_base_url = './icons/';

my $cgi;
my $nextpage;

# Page routing based on NEXTPAGE CGI parameter
my %nextpages = (
	'search_progs'			=> \&search_progs,	# Main Programme Listings
	'pvr_queue'			=> \&pvr_queue,		# Queue Download of Selected Progs
	'pvr_list'			=> \&show_pvr_list,	# Show all current PVR searches
	'pvr_del'			=> \&pvr_del,		# Delete selected PVR searches
	'pvr_add'			=> \&pvr_add,
	'show_info'			=> \&show_info,
	'flush'				=> \&flush,
#	'pvr_enable'			=> \&pvr_enable,
#	'pvr_disable'			=> \&pvr_disable,
);


### Crude Single-Threaded Perl CGI Web Server ###
use Socket;
use IO::Socket;
my $IGNOREEXIT = 0;
my $port = shift @ARGV;
# If the specified port number is  > 1024 then run embedded web server
if ( $port =~ /\d+/ && $port > 1024 ) {
	my $port = 1935;
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
			LocalPort => $port,
			Listen => SOMAXCONN,
			Reuse => 1
		);
		$server or die "Unable to create server socket: $!";
		print "INFO: Listening on port $port\n";
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
					# POST data
					} elsif (/^$/) {
						read( $client, $request{CONTENT}, $request{'content-length'} ) if defined $request{'content-length'};
						last;
					}
				}
			}

			# Determine method and parse parameters
			if ($request{METHOD} eq 'GET') {
				#if ($request{URL} =~ /(.*)\?(.*)/) {
				#	$request{URL} = $1;
				#	$request{CONTENT} = $2;
				#	%data = parse_form($request{CONTENT});
				#} else {
				#	%data = ();
				#}
				$data{"_method"} = "GET";
	
			} elsif ($request{METHOD} eq 'POST') {
				$query_string = parse_post_form_string( $request{CONTENT} );
				$data{"_method"} = "POST";
	
			} else {
				$data{"_method"} = "ERROR";
			}

			# Serve image file
#			my $localfile = $home.$request{URL};
#	
#			# Send Response
#			if (open(FILE, "<$localfile")) {
#				print $client "HTTP/1.0 200 OK", Socket::CRLF;
#				print $client "Content-type: text/html", Socket::CRLF;
#				print $client Socket::CRLF;
#				my $buffer;
#				while (read(FILE, $buffer, 4096)) {
#					print $client $buffer;
#				}
#				$data{"_status"} = "200";
#			} else {
#				print $client "HTTP/1.0 404 Not Found", Socket::CRLF;
#				print $client Socket::CRLF;
#				print $client "<html><body>404 Not Found</body></html>";
#				$data{"_status"} = "404";
#			}
#			close(FILE);

			# Log Request
			print "$data{_method}: ${home}$request{URL}\n";

			# Is this the CGI ?
			if ( $request{URL} =~ /^\/?iplayer/ ) {
				# remove any vars that might affect the CGI
				%ENV = ();
				@ARGV = ();
				# Setup CGI http vars
				print "QUERY_STRING = $query_string\n" if defined $query_string;
				$ENV{'QUERY_STRING'} = $query_string;
				$ENV{'REQUEST_URI'} = $request{URL};
				$ENV{'SERVER_PORT'} = $port;
				# respond OK to browser
				print $client "HTTP/1.0 200 OK", Socket::CRLF;
				# Invoke CGI
				run_cgi( $client, $query_string );

			# Else 404
			} else {
				print "ERROR: 404 Not Found\n";
				print $client "HTTP/1.0 404 Not Found", Socket::CRLF;
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
	print "INFO: Cleaning up PID $$\n";
	exit 1;
}



sub parse_form {
	my $data = $_[0];
	my %data;
	for (split /&/, $data) {
		my ($key, $val) = split /=/;
		$val =~ s/\+/ /g;
		$val =~ s/%(..)/chr(hex($1))/eg;
		$data{$key} = $val;
	}
	return %data;
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



# Use --webrequest to specify options in urlencoded format
sub parse_url_args {
	my @args;
	# parse GET args
	my @webopts = split /[\&\?]/, $_[0];
	for (@webopts) {
		# URL decode it
		s/\%([A-Fa-f0-9]{2})/pack('C', hex($1))/seg;
		my ( $optname, $value );
		# opt val pair
		if ( m{^\s*([\w\-]+?)[\s=](.+)$} ) {
			( $optname, $value ) = ( $1, $2 );
		# flag only
		} elsif ( m{^\s*([\w\-]+)$} ) {
			( $optname, $value ) = ( $1, 1 );
		}
		# if the option is valid then add it
		if ( $optname && defined $value ) {
			push @args, "$optname=$value";
			print "OPT: $optname=$value\n";
		}
	}
	return @args;
}


sub run_cgi {
	# Get filehandle for output
	$fh = shift;
	my $query_string = shift;
	
	# Clean globals
	%prog = ();
	@pids = ();
	@displaycols = ();

	# new cgi instance
	$cgi->delete_all() if defined $cgi;
	$cgi = new CGI( $query_string );

	begin_html();

	# Page Routing
	$nextpage = $cgi->param( 'NEXTPAGE' ) || 'search_progs';
	form_header();
	if ( $DEBUG ) {
		print $fh $cgi->Dump();
		for my $key (sort keys %ENV) {
		    print $fh $key, " = ", $ENV{$key}, "\n";
		}    
	}
	if ($nextpages{$nextpage}) {
		# call the correct subroutine
		$nextpages{$nextpage}->();
	}

	form_footer();
	html_end();

	$cgi->delete_all();

	return 0;
}


sub get_pvr_list {
	my $pvrsearch;
	my $out = `$get_iplayer_cmd --nocopyright --pvrlist 2>&1`;
	
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
                  ($title, $class, $onclick) = ("Sort by Reverse $heading", 'sorted', "form.NEXTPAGE.value='pvr_list'; form.PVRSORT.value='$heading'; form.PVRREVERSE.value=1; submit()");
                } else {
                  ($title, $class, $onclick) = ("Sort by $heading", 'unsorted', "form.NEXTPAGE.value='pvr_list'; form.PVRSORT.value='$heading'; submit()");
                }
                $class = 'sorted_reverse' if $sort_field eq $heading && $reverse;

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
	my @download = ( $cgi->param( 'PVRSELECT' ) );
	my $out;

	# Queue all selected '<type>|<pid>' entries in the PVR
	for my $name (@download) {
		chomp();
		my $cmd = "$get_iplayer_cmd --nocopyright --pvrdel '$name' 2>&1";
		print $fh p("Command: $cmd");
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
	my $cmd = "$get_iplayer_cmd --nocopyright --info --fields=pid --type=$type $pid 2>&1";
	print $fh p("Command: $cmd");
	my @cmdout = `$cmd`;
	return p("ERROR: ".@cmdout) if $? && not $IGNOREEXIT;
	print $fh p("Info for $pid");
	for ( @cmdout ) {
		my ( $key, $val ) = ( $1, $2 ) if m{^(\w+?):\s*(.+?)\s*$};
		next if $key =~ /(^$|^\d+$)/ || $val =~ /Matching Program/i;
		$out .= "$key: $val\n";
		push @html, Tr( { -class => 'info' }, th( { -class => 'info' }, $key ).td( { -class => 'info' }, $val ) );
	}
	print $fh table( { -class => 'info' }, @html );
	return $out;
}



sub pvr_queue {
	my @download = ( $cgi->param( 'PROGSELECT' ) );
	my $out;

	# Queue all selected '<type>|<pid>' entries in the PVR
	for (@download) {
		chomp();
		my ( $type, $pid, $name, $episode ) = ($1, $2, $3, $4) if m{^(.+?)\|(.+?)\|(.+?)\|(.+?)$};
		my $comment = "$name - $episode";
		$comment =~ s/\'\"//g;
		$comment =~ s/[^\s\w\d\-:\(\)]/_/g;		
		my $cmd = "$get_iplayer_cmd --nocopyright --type $type --pid '$pid' --pvrqueue --comment '$comment (queued: ".localtime().")' 2>&1";
		print $fh p("Command: $cmd");
		my $cmdout = `$cmd`;
		return p("ERROR: ".$out) if $? && not $IGNOREEXIT;
		print $fh p("Queued: $type: '$name - $episode' ($pid)");
		$out .= $cmdout;
	}
	print $fh pre($out);
	return $out;
}



sub pvr_add {
	my $search = shift || $cgi->param( 'SEARCH' ) || '.*';
	my $searchfields = join(",", $cgi->param( 'SEARCHFIELDS' )) || 'name';
	my $typelist = join(",", $cgi->param( 'PROGTYPES' )) || 'tv';
	my $out;

	# Only allow alphanumerics,_,-,. here for security reasons
	my $searchname = "${search}_${searchfields}_${typelist}";
	#$searchname =~ s/(["'&])/\\$1/g;
	$searchname =~ s/[^\w\-\. \+\(\)]/_/g;
	

	# Check how many matches first
	get_progs( $typelist, $search, $searchfields );
	my $matches = keys %prog;
	if ( $matches > 30 ) {
		print $fh p("ERROR: Search term '$search' currently matches $matches programmes - keep below 30 current matches");
		return 1;
	} else {
		print $fh p("Current Matches: ".(keys %prog));
	}

	my $cmd  = "$get_iplayer_cmd --pvradd '$searchname' --type $typelist --versions default --fields $searchfields -- $search";
	print $fh p("Command: $cmd");
	my $cmdout = `$cmd`;
	return p("ERROR: ".$out) if $? && not $IGNOREEXIT;
	print $fh p("Added PVR Search ($searchname):\n\tTypes: $typelist\n\tSearch: $search\n\tSearch Fields: $searchfields\n");
	print $fh pre($out);

	return $out;
}


# Build templated HTML for an option specified as
# '<Option text>', <webvar>, <get_iplayer opt>, 'onoff', 	'status: 1|0'
# '<Option text>', <webvar>, <get_iplayer opt>, 'multionoff',	<hashref 'order => value' >, <hashref 'values => label'>, <hash ref: 'value => status'>
# '<Option text>', <webvar>, <get_iplayer opt>, 'popup',	'<default>', \%<hash for multi or popup values>
# '<Option text>', <webvar>, <get_iplayer opt>, 'text',	'<default>', \%<hash for multi or popup values>
# '<Option text>', <webvar>, <get_iplayer opt>, 'filebrowse',	'<default>', \%<hash for multi or popup values>
# e.g.
# 'Programme type', 'PROGTYPES', '--types', 'multionoff', \%{ tv => 1 }, \%{ tv => 'BBC TV', radio => 'BBC Radio', podcast => 'BBC Podcast', itv => 'ITV' }
# 'Output Folder', 'OUTDIR', '--output', 'filebrowse', ''
# 'Hide Downloaded Programmes', 'HIDE', '--hide', 'onoff'

# 'Programme type', 'PROGTYPES', '--types', 'multionoff', { 1=>tv, 2=>radio, 3=>podcast, 4=>itv}, { tv => 'BBC TV', radio => 'BBC Radio', podcast => 'BBC Podcast', itv => 'ITV' } , { tv => 1 }


sub build_option_html {
	my $text = shift;
	my $webvar = shift;
	my $option = shift;
	my $opttype = shift;
	my $label = shift;
	my $default = shift;
	my @html;

	# On/Off
	if ( $opttype eq 'onoff' ) {
		my $value = shift;
		push @html, th( { -class => 'options' }, $text );
		push @html, td( { -class => 'options' }, [
			'',
			checkbox(
				-class		=> 'options',
				-name		=> $webvar,
				-label		=> '',
				-value 		=> 1,
				-checked	=> $value,
				-override	=> 1,
			)
		] );


	# Multi-On/Off
	} elsif ( $opttype eq 'multionoff' ) {
		my $value = shift;
		# values in hash of $value->{<order>} => value
		# labels in hash of $label->{$value}
		# selected status in $default->{$value}
		push @html, th( { -class => 'options' }, $text );
		for (sort keys %{ $value } ) {
			my $val = $value->{$_};
			push @html,
				td( { -class => 'options' }, [
					'',
					$label->{$val},
					checkbox(
						-class		=> 'options',
						-name		=> $webvar,
						-label		=> '',
						-value 		=> $val,
						-checked	=> $default->{$val},
						-override	=> 1,
					)
				]
			);
		}

	# Popup type
	} elsif ( $opttype eq 'popup' ) {
		my @value = @_;
		push @html, th( { -class => 'options' }, $text );
		push @html, td( { -class => 'options' }, [
			'',
			popup_menu(
				-class		=> 'options',
				-name		=> $webvar,
				-values		=> @value,
				-labels		=> $label,
				-default	=> $default,
			)
		] );

	# text field
	} elsif ( $opttype eq 'text' ) {
		my $value = shift;
		push @html, th( { -class => 'options' }, $text );
		push @html, td( { -class => 'options' }, [
			'',
			textfield(
				-class		=> 'options',
				-name		=> $webvar,
				-value		=> $default,
				-size		=> $value,
			)
		] );

	}
	return table( { -class=>'options' }, Tr( { -class=>'options' }, @html ) );
}


sub flush {
	my $typelist = join(",", $cgi->param( 'PROGTYPES' )) || 'tv';
	my $out;

	my $cmd  = "$get_iplayer_cmd --nocopyright --flush --type $typelist";
	print $fh p("Command: $cmd");
	my $cmdout = `$cmd`;
	return p("ERROR: ".$out) if $? && not $IGNOREEXIT;
	print $fh p("Flushed Programme Caches for Types: $typelist");
	print $fh pre($out);

	return $out;
}



sub search_progs {
	my $search = shift || $cgi->param( 'SEARCH' ) || '.*';
	my $cols = join(",", $cgi->param( 'COLS' )) || undef;
	my $searchfields = join(",", $cgi->param( 'SEARCHFIELDS' )) || 'name';
	my $typelist = join(",", $cgi->param( 'PROGTYPES' )) || 'tv';
	my $vmode = $cgi->param( 'VMODE' ) || 'iphone,flashhigh,flashnormal';
	my $amode = $cgi->param( 'AMODE' ) || 'iphone,flashaudio,flashaac,realaudio';
	my $pagesize = $cgi->param( 'PAGESIZE' ) || 17;
	my $pageno = $cgi->param( 'PAGE' ) || 1;
	my $since = $cgi->param( 'SINCE' );
	my $hide = $cgi->param( 'HIDE' ) || 0;
	my @html;
	my %type;
	my %vmode;


	# Populate %type, %vmode
	$type{$_} = 1 for split /,/, $typelist;

	# Determine which cols to display
	get_display_cols();

	# Get prog data
	my $response;
	if ( $response = get_progs( $typelist, $search, $searchfields, $hide, $since ) ) {
		print $fh p("ERROR: get_iplayer returned non-zero:").br().p( join '<br>', $response );
		return 1;
	}

        my $sort_field = $cgi->param( 'SORT' ) || 'name';
        my $reverse = $cgi->param( 'REVERSE' ) || '0';

	# Sort
	@pids = get_sorted( \%prog, $sort_field, $reverse );

	my ($first, $last, @pagetrail) = pagetrail( $pageno, $pagesize, $#pids+1, 7 );


	# Default displaycols
	push @html, "<tr>";
	push @html, th( { -class => 'search' }, checkbox( -class=>'search', -title=>'Select/Unselect All Programmes', -onClick=>"check_toggle(document.form, 'PROGSELECT')", -name=>'SELECTOR', -value=>'1', -label=>'' ) );
	# Display data in nested table
	for my $heading (@displaycols) {

		# Sort by column click and change display class (colour) according to sort status
		my ($title, $class, $onclick);
		if ( $sort_field eq $heading && not $reverse ) {
			($title, $class, $onclick) = ("Sort by Reverse $heading", 'sorted', "form.NEXTPAGE.value='search_progs'; form.SORT.value='$heading'; form.REVERSE.value=1; submit()");
		} else {
			($title, $class, $onclick) = ("Sort by $heading", 'unsorted', "form.NEXTPAGE.value='search_progs'; form.SORT.value='$heading'; submit()");
		}
		$class = 'sorted_reverse' if $sort_field eq $heading && $reverse;

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
		for ( @displaycols ) {
			if ( ! /thumbnail/ ) {
				push @row, td( {-class=>'search'}, label( { -class=>'search', -title=>"Click for full info", -onClick=>"form.NEXTPAGE.value='show_info'; form.INFO.value='$prog{$pid}->{type}|$pid'; submit()" }, $prog{$pid}->{$_} ) );
			} else {
				push @row, td( {-class=>'search'}, a( { -class=>'search', -href=>$prog{$pid}->{web} }, img( { -class=>'search', -height=>40, -src=>$prog{$pid}->{$_} } ) ) );
			}
		}
		push @html, Tr( {-class=>'search'}, @row );
	}

	##### Options #####
	my @optrows;

	# Search form
	print $fh start_form(
		-name   => "form",
		-method => "POST",
	);

	push @optrows, build_option_html(
		'Search', # Title
		'SEARCH', # webvar
		'--search', # option
		'text', # type
		undef,
		$search, # default
		20, # width values
	);
	push @optrows, build_option_html(
		'Search in', # Title
		'SEARCHFIELDS', # webvar
		'--fields', # option
		'popup', # type
		\%fieldname, # labels
		$searchfields, # default
		[ (@headings,'name,episode','name,episode,desc') ], # values
	);

	#### -onChange	=> "form.NEXTPAGE.value='search_progs'; submit()",
	push @optrows, build_option_html(
		'Programmes per Page', # Title
		'PAGESIZE', # webvar
		'', # option
		'popup', # type
		undef, # labels
		$pagesize, # default
		['17','50','100','200','500'], # values
	);

	#### -onChange 	=> "form.NEXTPAGE.value='search_progs'; submit()",
	push @optrows, build_option_html(
		'Sort by', # Title
		'SORT', # webvar
		'', # option
		'popup', # type
		\%fieldname, # labels
		$sort_field, # default
		[@headings], # values
	);

	push @optrows, build_option_html(
		'Programme type', # Title
		'PROGTYPES', # webvar
		'--types', # option
		'multionoff', # type
		\%prog_types, # labels
		\%type, # default status
		{ 1=>'tv', 2=>'radio', 3=>'podcast', 4=>'itv' }, # order of values
	);

	# 0=>'iphone', 1=>'flashhd', 2=>'flashvhigh', 3=>'flashhigh', 4=>'flashnormal', 5=>'flashlow', 6=>'n95_wifi', 7=>'n95_3gp'
	push @optrows, build_option_html(
		'Video Download Modes', # Title
		'VMODE', # webvar
		'--vmode', # option
		'text', # type
		undef,
		$vmode, # default
		40, # width values
	);
	
	push @optrows, build_option_html(
		'Audio Download Modes', # Title
		'AMODE', # webvar
		'--amode', # option
		'text', # type
		undef,
		$amode, # default
		40, # width values
	);

	push @optrows, build_option_html(
		'Hide Downloaded', # Title
		'HIDE', # webvar
		'--hide', # option
		'onoff', # type
		undef, 
		undef,
		$hide, # value
	);

	push @optrows, build_option_html(
		'Added Since (hours)', # Title
		'SINCE', # webvar
		'--since', # option
		'text', # type
		undef,
		$since, # default
		3, # width values
	);
	
	print $fh table( { -class=>'options' }, Tr( { -class=>'options' }, [ @optrows ] ) );

	print $fh table( { -class=>'options' },
		Tr( { -class=>'options' },
			td( { -class=>'options' }, [
				# Seacrh button
				button(
					-class		=> 'options',
					-tabindex	=> '1',
					-name		=> "Search",
					-onClick 	=> "form.NEXTPAGE.value='search_progs'; submit()",
				),
				# Flush button
				button(
					-class		=> 'options',
					-name		=> 'Refresh Caches (takes a while)',
					-onClick 	=> "form.NEXTPAGE.value='flush'; submit()",
				),
			]),
		),
	);
	

	print $fh table( { -class=>'options' },
		Tr( { -class=>'options' },
			td( { -class=>'options' }, [
				button(
					-class		=> 'options',
					-name		=> 'Queue Selected for Download',
					-onClick 	=> "form.NEXTPAGE.value='pvr_queue'; submit()",
				),
				button(
					-class		=> 'options',
					-name		=> 'Add Current Search to PVR',
					-onClick 	=> "form.NEXTPAGE.value='pvr_add'; submit()",
				),
				"Results ".($first+1)." - $last of ".($#pids+1),
			]),
		),
	);
	print $fh @pagetrail;
	print $fh table( {-class=>'search' }, @html );
	print $fh @pagetrail;

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
	print $fh (
          table( { -class => 'colselect' }, @columnselect ).
          # Make sure we go to the correct nextpage for processing
          hidden(
            -name	=> "NEXTPAGE",
            -value	=> "search_progs",
            -override	=> 1,
          ).
          # Reverse sort value
          hidden(
            -name	=> "REVERSE",
            -value	=> 0,
            -override	=> 1,
          ).
          # Make sure we go to the correct next page no.
          hidden(
            -name	=> "PAGE",
            -value	=> "1",
            -override	=> 1,
          ).
          # INFO for page info if clicked
          hidden(
            -name	=> "INFO",
            -value	=> 0,
            -override	=> 1,
          ).
          end_form()
        );

	return 0;
}



# Build page trail
sub pagetrail {
	my ( $page, $pagesize, $count, $trailsize ) = ( @_ );

	my $first = $pagesize * ($page - 1);
	my $last = $first + $pagesize;
	$last = $count if $last > $count;
	# How many pages
	my $pages = int( $count / $pagesize ) + 1;
	# Page trail
	my @pagetrail;
	push @pagetrail, td( { -class=>'pagetrail' }, label( {
		-title		=> "Previous Page",
		-class		=> 'pagetrail',
		-onClick	=> "form.NEXTPAGE.value='search_progs'; form.PAGE.value=$page-1; submit()",},
		"<<",
	)) if $page > 1;
	push @pagetrail, td( { -class=>'pagetrail' }, label( {
		-title		=> "Page 1",
		-class		=> 'pagetrail',
		-onClick	=> "form.NEXTPAGE.value='search_progs'; form.PAGE.value=1; submit()",},
		"1",
	)) if $page > 1;
	push @pagetrail, td( { -class=>'pagetrail' }, '...' ) if $page > $trailsize+2;
 	for (my $pn=$page-$trailsize; $pn <= $page+$trailsize; $pn++) {
		push @pagetrail, td( { -class=>'pagetrail' }, label( {
			-title		=> "Page $pn",
			-class		=> 'pagetrail',
			-onClick	=> "form.NEXTPAGE.value='search_progs'; form.PAGE.value='$pn'; submit()",},
			"$pn",
		)) if $pn > 1 && $pn != $page && $pn < $pages;
		push @pagetrail, td( { -class=>'pagetrail' }, label( {
			-title          => "Current Page",
			-class          => 'pagetrail-current', },
		"$page",
		)) if $pn == $page;
	}
	push @pagetrail, td( { -class=>'pagetrail' }, '...' ) if $page < $pages-$trailsize-1;
	push @pagetrail, td( { -class=>'pagetrail' }, label( {
		-title		=> "Page ".$pages,
		-class		=> 'pagetrail',
		-onClick	=> "form.NEXTPAGE.value='search_progs'; form.PAGE.value=$pages; submit()",},
		"$pages",
	)) if $page < $pages;
	push @pagetrail, td( { -class=>'pagetrail' }, label( {
		-title		=> "Next Page",
		-class		=> 'pagetrail',
		-onClick	=> "form.NEXTPAGE.value='search_progs'; form.PAGE.value=$page+1; submit()",},
		">>",
	)) if $page < $pages;
	my @html = table( { -id=>'centered', -class=>'pagetrail' }, Tr( { -class=>'pagetrail' }, @pagetrail ));
	return ($first, $last, @html);
}



sub get_progs {
	my $types = shift;
	my $search = shift;
	my $searchfields = shift;
	my $hide = shift;
	my $since = shift;
	
	my $fields;
	$fields .= "|<$_>" for @headings;
	my $options = '';
	$options .= " --since $since" if $since;
	$options .= " --hide" if $hide;
	my $cmd = "$get_iplayer_cmd $options --nocopyright --nopurge --type $types --listformat 'ENTRY${fields}' --fields $searchfields -- $search";
	print "DEBUG: Command: $cmd\n" if $DEBUG;
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

	print $fh $cgi->header(-type=>'text/html', -charset=>'utf-8' );
	print $fh "<html>";
	print $fh "<HEAD><TITLE>get_iplayer Manager</TITLE>\n";
	insert_stylesheet();
	print $fh "</HEAD>\n";
	insert_javascript();
	print $fh "<body>\n";
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
	
	print $fh  table( { -id=>'centered', -class=>'title' }, Tr( { -class=>'title' }, td( { -class=>'title' },
		a( { -class=>'title', -href => "http://linuxcentre.net/getiplayer/" }, 
			img({
				-class=>'title',
				-src=>"$icons_base_url/logo_white_131x28.gif",
				-alt=>'get_iplayer Manager',
			} )
		)
	)));

	print $fh table({ -class=>'icons' },
		Tr( { -class=>'icons' }, td( { -class=>'icons' }, [
			img({
				-class => 'icons',
				-alt => 'Back',
				-title => 'Back',
				-src => "$icons_base_url/back.png",
				-onClick  => "history.back()",
			}),
			# go to search page
			#image_button(-name=>'button_name', -src=>image URL, -align=>alignment, -alt=>text, -value=>text)
			image_button({
				-class => 'icons',
				-alt => 'Search',
				-title => 'Programme Search',
				-src => "$icons_base_url/index.png",
				-onClick  => "formheader.NEXTPAGE.value='search_progs'; submit()",
			}),
			# go back to parent page - set no params
			image_button({
				-class => 'icons',
				-alt => 'PVR Searches',
				-title => 'PVR Searches',
				-src => "$icons_base_url/pie2.png",
				-onClick  => "formheader.NEXTPAGE.value='pvr_list'; submit()",
			}),
			# Open the help page in a different window
			img({
				-class => 'icons',
				-alt => 'Help',
				-title => 'Help',
				-src => "$icons_base_url/unknown.png",
				-onClick  => "parent.location='http://linuxcentre.net/getiplayer/documentation'",
			}),
		] )	
	) );
	
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
		"Note: Changes cannot be undone".
		br()."&copy;2009 Phil Lewis - Licensed under GPLv3"
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


#############################################
#
# Javascript Functions here
#
#############################################
sub insert_javascript {

	print $fh <<EOF;

	<script type="text/javascript">
	
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
	
	BODY			{ color: #000; background: white; font-size: 90%; font-family: verdana, sans-serif;}
	IMG			{ border: 0; }

	TABLE.title 		{ font-size: 130%; border-spacing: 0px; padding: 0px; }
	A.title			{ color: #F55; text-decoration: none; }
	
	TABLE.icons		{ font-size: 100%; border-spacing: 10px 0px; padding: 0px; }
	IMG.icons		{ font-size: 100%; }
	INPUT.icons		{ font-size: 100%; }
	TD.icons		{ border: 1px solid #666666; background: #DDD; }
	TD.icons:hover		{ background: #BBB; }
	
	TABLE.header		{ font-size: 80%; border-spacing: 1px; padding: 0; }
	INPUT.header		{ font-size: 80%; } 
	SELECT.header		{ font-size: 80%; } 

	TABLE.types		{ font-size: 70%; text-align: left; border-spacing: 0px; padding: 0; }
	TR.types		{ white-space: nowrap; }
	TD.types		{ width: 20px }
	
	TABLE.options		{ font-size: 70%; text-align: left; border-spacing: 0px; padding: 0; white-space: nowrap; }
	TR.options		{ white-space: nowrap; }
	TH.options		{ width: 20px }
	TD.options		{ width: 20px }
	INPUT.options		{ font-size: 100%; } 
	SELECT.options		{ font-size: 100%; } 
	
	TABLE.pagetrail		{ font-size: 80%; text-align: center; font-weight: bold; border-spacing: 10px 0; padding: 0px; }
	TD.pagetrail:hover	{ background: #CCC; }
	#centered		{ height:20px; margin:0px auto 0; position: relative; }
	LABEL.pagetrail		{ Color: #009; }
	LABEL.pagetrail-current	{ Color: #900; }

	TABLE.colselect		{ font-size: 70%; padding: 0; border-spacing: 0px; }
	TR.colselect		{ text-align: left; }
	TH.colselect		{ font-weight: bold; }
	INPUT.colselect		{ font-size: 70%; }
	LABEL.colselect		{ font-size: 70%; }
	
	TABLE.search		{ font-size: 70%; border-spacing: 2px; padding: 0; width: 100%; }
	TABLE.searchhead	{ font-size: 110%; border-spacing: 0px; padding: 0; width: 100%; }
	TR.search		{ background: #EEE; }
	TR.search:hover		{ background: #CCC; }
	TH.search		{ Color: white; text-align: center; background: #999; text-align: center; }
	TD.search		{ text-align: left; }
	INPUT.search		{ font-size: 70%; background: #EEE; }
	LABEL.sorted            { Color: #cfc; }
	LABEL.unsorted          { Color: #fff; }
	LABEL.sorted_reverse    { Color: #fcc; }

	TABLE.info		{ font-size: 70%; border-spacing: 2px; padding: 0; width: 100%; }
	TR.info			{ background: #EEE; }
	TH.info			{ Color: white; text-align: center; background: #999; text-align: center; }
	TD.info			{ text-align: left; }

	B.footer		{ font-size: 70%; color: #777; font-weight: normal; }
	</STYLE>
EOF

}
