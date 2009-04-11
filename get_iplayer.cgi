#!/usr/bin/perl
#
# The Worlds most insecure web manager for get_iplayer
# ** WARNING ** Never run this in an untrusted environment or facing the internet
#
# (C) Phil Lewis, 2009
# License: GPLv3
#
my $VERSION = '0.09';

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
# * &nbsp; isn't considered good practice
# * in general, take presentation data out of the html and into css, take scripting out of the html and into the js

use strict;
use CGI ':all';
use IO::File;
use URI::Escape;
my $DEBUG = 0;
$| = 1;

# Path to get_iplayer (+ set HOME env var cos apache seems to not set it)
my $home = '/var/www';
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

# Else web version
my $cgi = new CGI();

begin_html();

my $nextpage;

# Page routing based on NEXTPAGE CGI parameter
my %nextpages = (
	'Show_Programmes'		=> \&show_progs,	# Main Programme Listings
	'pvr_queue'			=> \&pvr_queue,		# Queue Download of Selected Progs
	'pvr_list'			=> \&show_pvr_list,	# Show all current PVR searches
	'pvr_del'			=> \&pvr_del,		# Delete selected PVR searches
	'pvr_add'			=> \&pvr_add,
#	'pvr_enable'			=> \&pvr_enable,
#	'pvr_disable'			=> \&pvr_disable,
);



# Page Routing
$nextpage = $cgi->param( 'NEXTPAGE' ) || 'Show_Programmes';
form_header();
print $cgi->Dump if $DEBUG;
# Authorized
# Page Routing
if ($nextpages{$nextpage}) {
	# call the correct subroutine
	$nextpages{$nextpage}->();
}

form_footer();
html_end();
	
exit 0;



sub get_pvr_list {
	my $pvrsearch;
	my $out = `$get_iplayer_cmd --pvrlist 2>&1`;
	
	# Remove text before first pvrsearch entry
	$out =~ s/^.+?(pvrsearch\s.+)$/$1/s;
	# Parse all 'pvrsearch' elements
	for ( split /pvrsearch\s+\=\s+/, $out ) {
		my $name;
		$_ = "pvrsearch = $_";
		# Get each element
		while ( /([\w\-]+?)\s+=\s+(.+?)\n/sg ) {
			if ( $1 eq 'pvrsearch' ) {
				$name = $2;
			}
			$pvrsearch->{$name}->{$1} = $2;
			# Remove disabled entries
			delete $pvrsearch->{$name} if $pvrsearch->{$name}->{disable} == 1;
		}
	}
	return $pvrsearch;
}



sub show_pvr_list {
	my %fields;
	my $pvrsearch = get_pvr_list();
	my $sort_field = param( 'PVRSORT' ) || 'name';
	my $reverse = param( 'PVRREVERSE' ) || '0';

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
	print start_form(
		-name   => "form",
		-method => "POST",
	);

	print button(
		-class		=> 'search',
		-name		=> 'Delete Selected PVR Entries',
		-value		=> 'Delete Selected PVR Entries',
		-title		=> 'Delete Selected PVR Entries',
		-onClick 	=> "form.NEXTPAGE.value='pvr_del'; submit()",
	);

	print table( {-class=>'search'} , @html );
	# Make sure we go to the correct nextpage for processing
	print hidden(
		-name		=> "NEXTPAGE",
		-value		=> "pvr_list",
		-override	=> 1,
	);
	# Reverse sort value
	print hidden(
		-name		=> "PVRREVERSE",
		-value		=> 0,
		-override	=> 1,
	);
	print hidden(
		-name		=> "PVRSORT",
		-value		=> $sort_field,
		-override	=> 1,
	);
	print end_form();

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
	if ( $sorttype{$sort_field} eq 'numeric' ) {
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
		my $cmd = "$get_iplayer_cmd --pvrdel '$name' 2>&1";
		print p("Command: $cmd");
		my $cmdout = `$cmd`;
		return p("ERROR: ".$out) if $?;
		print p("Deleted: $name");
		$out .= $cmdout;
	}
	print p("Output: $out");
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
		my $cmd = "$get_iplayer_cmd --type $type --pid '$pid' --pvrqueue --comment '$comment (queued: ".localtime().")' 2>&1";
		print p("Command: $cmd");
		my $cmdout = `$cmd`;
		return p("ERROR: ".$out) if $?;
		print p("Queued: $type: '$name - $episode' ($pid)");
		$out .= $cmdout;
	}
	print p("Output: $out");
	return $out;
}



sub pvr_add {
	my $search = shift || param( 'SEARCH' ) || '.*';
	my $searchfields = join(",", param( 'SEARCHFIELDS' )) || 'name';
	my $typelist = join(",", param( 'PROGTYPES' )) || 'tv';
	my $out;

	# Only allow alphanumerics,_,-,. here for security reasons
	my $searchname = "${search}_${searchfields}_${typelist}";
	#$searchname =~ s/(["'&])/\\$1/g;
	$searchname =~ s/[^\w\-\. \+\(\)]/_/g;
	

	# Check how many matches first
	get_progs( $typelist, $search, $searchfields );
	my $matches = keys %prog;
	if ( $matches > 30 ) {
		print p("ERROR: Search term '$search' currently matches $matches programmes - keep below 30 current matches");
		return 1;
	} else {
		print p("Current Matches: ".(keys %prog));
	}

	my $cmd  = "$get_iplayer_cmd --pvradd '$searchname' --type $typelist --versions default --fields $searchfields -- $search";
	print p("Command: $cmd");
	my $cmdout = `$cmd`;
	return p("ERROR: ".$out) if $?;
	print p("Added PVR Search ($searchname):\n\tTypes: $typelist\n\tSearch: $search\n\tSearch Fields: $searchfields\n");
	print p("Output: $out");

	return $out;
}



sub show_progs {
	my $search = shift || param( 'SEARCH' ) || '.*';
	my $cols = join(",", param( 'COLS' )) || undef;
	my $searchfields = join(",", param( 'SEARCHFIELDS' )) || 'name';
	my $typelist = join(",", param( 'PROGTYPES' )) || 'tv';
	my $pagesize = param( 'PAGESIZE' ) || 17;
	my $pageno = param( 'PAGE' ) || 1;
	my @html;
	my %type;


	# Populate %types
	$type{$_} = 1 for split /,/, $typelist;


	# Determine which cols to display
	get_display_cols();


	# Get prog data
	my $response;
	if ( $response = get_progs( $typelist, $search, $searchfields ) ) {
		print p("ERROR: get_iplayer returned non-zero:").br().p( join '<br>', $response );
		return 1;
	}

        my $sort_field = param( 'SORT' ) || 'name';
        my $reverse = param( 'REVERSE' ) || '0';

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
			($title, $class, $onclick) = ("Sort by Reverse $heading", 'sorted', "form.NEXTPAGE.value='Show_Programmes'; form.SORT.value='$heading'; form.REVERSE.value=1; submit()");
		} else {
			($title, $class, $onclick) = ("Sort by $heading", 'unsorted', "form.NEXTPAGE.value='Show_Programmes'; form.SORT.value='$heading'; submit()");
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
								-onChange	=> "form.NEXTPAGE.value='Show_Programmes'; submit()"
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
				push @row, td( {-class=>'search'}, $prog{$pid}->{$_} );
			} else {
				push @row, td( {-class=>'search'}, a( { -class=>'search', -href=>$prog{$pid}->{web} }, img( { -class=>'search', -height=>40, -src=>$prog{$pid}->{$_} } ) ) );
			}
		}
		push @html, Tr( {-class=>'search'}, @row );
	}

	my @typeselect;
	push @typeselect, td({ -class=>'types' }, 'Programme Types:');
	for my $prog_type (keys %prog_types) {
		push @typeselect,
			td( { -class => 'types' }, [
				"&nbsp;&nbsp;&nbsp;&nbsp;$prog_types{$prog_type}",
				checkbox(
					-class		=> 'types',
					-name		=> 'PROGTYPES',
					-label		=> '',
					-value 		=> $prog_type,
					-checked	=> $type{$prog_type},
					-override	=> 1,
				)
			]
		);
	}

	# Search form
	print start_form(
		-name   => "form",
		-method => "POST",
	);

	print table( { -class=>'header' },
	  Tr( { -class=>'header' }, 
	    td( { -class=>'header' }, [
	      "Name Search",
	      textfield(
	        -class		=> 'header',
		-name		=> 'SEARCH',
		-size		=> 20,
              ),

              "in",
              popup_menu(
	        -class		=> 'header',
	        -name		=> 'SEARCHFIELDS',
                -values		=> [(@headings,'name,episode','name,episode,desc')],
		-labels		=> \%fieldname,
                -default	=> 'name',
              ),

              submit({
	        -class		=> 'header',
                -tabindex	=> '1',
                -value		=> "Search"
              }),
	
              "Programmes per Page",
              popup_menu(
	        -class		=> 'header',
	        -name		=> 'PAGESIZE',
                -values		=> ['17','50','100','200','500'],
                -default	=> $pagesize,
                -onChange	=> "form.NEXTPAGE.value='Show_Programmes'; submit()",
              ),

              "Sort",            
              popup_menu(
	        -class		=> 'header',
		-name		=> 'SORT',
		-values		=> [@headings],
		-labels		=> \%fieldname,
		-onChange 	=> "form.NEXTPAGE.value='Show_Programmes'; submit()",
              ),

            ]),
          ),
        );
	print table( { -class=>'types' }, Tr( { -class=>'types' }, @typeselect ) );
	print table( { -class=>'actions' },
		Tr( { -class=>'actions' },
			td( { -class=>'actions' }, [
				button(
					-class		=> 'actions',
					-name		=> 'Queue Selected for Download',
					-value		=> 'Queue Selected for Download',
					-title		=> 'Queue Selected for Download',
					-onClick 	=> "form.NEXTPAGE.value='pvr_queue'; submit()",
				),
				button(
					-class		=> 'actions',
					-name		=> 'Add Current Search to PVR',
					-value		=> 'Add Current Search to PVR',
					-title		=> 'Add Current Search to PVR',
					-onClick 	=> "form.NEXTPAGE.value='pvr_add'; submit()",
				),
				"Results ".($first+1)." - $last of ".($#pids+1),
			]),
		),
	);
	print div( { -id=>'centered', -class=>'pagetrail' }, @pagetrail);
	print table( {-class=>'search' }, @html );
	print div( { -id=>'centered', -class=>'pagetrail' }, @pagetrail);

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
						-onChange	=> "form.NEXTPAGE.value='Show_Programmes'; submit()",
					)
				])
			)
		);
	}
	unshift @columnselect, Tr( { -class=>'colselect' }, th( { -class=>'colselect' }, "Enable these columns:" ) ) if @columnselect;

	# Display drop down menu with multiple select for columns shown
	print (
          table( { -class => 'colselect' }, @columnselect ).
          # Make sure we go to the correct nextpage for processing
          hidden(
            -name	=> "NEXTPAGE",
            -value	=> "Show_Programmes",
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
	push @pagetrail, label( {
		-title		=> "Previous Page",
		-class		=> 'pagetrail',
		-onClick	=> "form.NEXTPAGE.value='Show_Programmes'; form.PAGE.value=$page-1; submit()",},
		"<<&nbsp;&nbsp;",
	) if $page > 1;
	push @pagetrail, label( {
		-title		=> "Page 1",
		-class		=> 'pagetrail',
		-onClick	=> "form.NEXTPAGE.value='Show_Programmes'; form.PAGE.value=1; submit()",},
		"1&nbsp;&nbsp;",
	) if $page > 1;
	push @pagetrail, "...&nbsp;&nbsp;" if $page > $trailsize+2;
 	for (my $pn=$page-$trailsize; $pn <= $page+$trailsize; $pn++) {
		push @pagetrail, label( {
			-title		=> "Page $pn",
			-class		=> 'pagetrail',
			-onClick	=> "form.NEXTPAGE.value='Show_Programmes'; form.PAGE.value='$pn'; submit()",},
			"$pn&nbsp;&nbsp;",
		) if $pn > 1 && $pn != $page && $pn < $pages;
		push @pagetrail, label( {
			-title          => "Current Page",
			-class          => 'pagetrail-current', },
		"$page&nbsp;&nbsp;",
		) if $pn == $page;
	}
	push @pagetrail, "...&nbsp;&nbsp;" if $page < $pages-$trailsize-1;
	push @pagetrail, label( {
		-title		=> "Page ".$pages,
		-class		=> 'pagetrail',
		-onClick	=> "form.NEXTPAGE.value='Show_Programmes'; form.PAGE.value=$pages; submit()",},
		"$pages&nbsp;&nbsp;",
	) if $page < $pages;
	push @pagetrail, label( {
		-title		=> "Next Page",
		-class		=> 'pagetrail',
		-onClick	=> "form.NEXTPAGE.value='Show_Programmes'; form.PAGE.value=$page+1; submit()",},
		">>&nbsp;&nbsp;",
	) if $page < $pages;
	return ($first, $last, @pagetrail);
}



sub get_progs {
	my $types = shift;
	my $search = shift;
	my $searchfields = shift;
	
	my $fields;
	$fields .= "|<$_>" for @headings;

	my @list = `$get_iplayer_cmd --nopurge --type $types --listformat 'ENTRY${fields}' --fields $searchfields -- $search`;
	return join("\n", @list) if $?;

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
        my $cols = join(",", param( 'COLS' )) || undef;

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

	print $cgi->header(-type=>'text/html', -charset=>'utf-8' );
	print "<html>";
	print "<HEAD><TITLE>get_iplayer Manager</TITLE>\n";
	insert_stylesheet();
	print "</HEAD>\n";
	insert_javascript();
	print "<body>\n";

	print $cgi->dump if $DEBUG;
}



#############################################
#
# Form Header 
#
#############################################
sub form_header {

	my $nextpage = shift || $cgi->param( 'NEXTPAGE' );
	my $advanced = shift || $cgi->param( 'ADVANCED' );
	my $menu;

	print $cgi->start_form(
			-name   => "formheader",
			-method => "POST",
		);


	print table( {-class=>'title'},
	Tr( {-class=>'title'},
		td( { -class=>'title' }, "get_iplayer Manager"),
		td( { -class=>'title', -align=>'right' -width=>'131' }, a( {-href=>"http://linuxcentre.net/get_iplayer/"}, img( { -src=>"$icons_base_url/logo_white_131x28.gif", -align=>'right' }) ) ),
	) ).

	hr({-size=>1}).

	table({ -class=>'icons' },

	Tr( { -class=>'icons' }, td( { -class=>'icons' }, [
		img({
			-alt => 'Back',
			-title => 'Back',
			-src => "$icons_base_url/back.png",
			-onClick  => "history.back()",
		}),
		# go to search page
		#image_button(-name=>'button_name', -src=>image URL, -align=>alignment, -alt=>text, -value=>text)
		image_button({
			-alt => 'Search',
			-title => 'Programme Search',
			-src => "$icons_base_url/index.png",
			-onClick  => "formheader.NEXTPAGE.value='Show_Programmes'; submit()",
		}),
		# go back to parent page - set no params
		image_button({
			-alt => 'PVR Searches',
			-title => 'PVR Searches',
			-src => "$icons_base_url/pie2.png",
			-onClick  => "formheader.NEXTPAGE.value='pvr_list'; submit()",
		}),
		# Open the help page in a different window
		img({
			-alt => 'Help',
			-title => 'Help',
			-src => "$icons_base_url/unknown.png",
			-onClick  => "parent.location='http://linuxcentre.net/getiplayer/documentation'",
		}),
		$menu,
	] )	) ).
	hidden(
		-name => "ADVANCED",
		-value => $advanced,
		-override => 1,
	).
	hidden(
		-name => "NEXTPAGE",
		-value => '',
		-override => 1,
	).

	$cgi->end_form().

	hr({-size=>1});
}



#############################################
#
# Form Footer 
#
#############################################
sub form_footer {
	print p( b({-class=>"footer"},
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
	print $cgi->dump if $DEBUG;
	print "\n</body>";
	print "\n</html>\n";
}


#############################################
#
# Javascript Functions here
#
#############################################
sub insert_javascript {

	print <<EOF;

	<script type="text/javascript">
	
	// 
	// Popup a Yes/No dialogue with param as question.
	//
	function submit_check(text) {
		if ( document.formheader.NEXTPAGE.value == "Delete") {
			var output = confirm(text);
			if (output == true) {
				document.formheader.submit();
			}
		} else {
			document.formheader.submit();
		}
	}

	//
	// Popup a message if the form contains invalid data.
	//
	function create_form_validate(f) {
		verify(f);
		submit();
	}

	//
	// A utility function that returns true if a string contains only 
	// whitespace characters
	//
	function isblank(s) {
		for(var i = 0; i < s.length; i++) {
			var c = s.charAt(i);
			if ((c != ' ') && (c != '\\n') && (c != '	')) return false;
		}
		return true;
	}


	//
	// Limit inputs to certain characters
	//
	var userid = "abcdefghijklmnopqrstuvwxyz-1234567890";
	var email = "-0123456789abcdefghijklmnopqrstuvwxyz@._";
	var numb = "0123456789";
	var fullname = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890 ',-";
	var path = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890/_-.+~";
	function res(t,v){
		var w = "";
		for (i=0; i < t.value.length; i++) {
		x = t.value.charAt(i);
		if (v.indexOf(x,0) != -1)
			w += x;
		}
		t.value = w;
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

	</SCRIPT>
EOF
}



#############################################
#
# CSS1 Styles here
#
#############################################
sub insert_stylesheet {
	print <<EOF;

	<STYLE type="text/css">
	
	BODY			{ color: #000; background: white; font-size: 90%; font-family: verdana, sans-serif;}
	IMG			{ border: 0; }

	TABLE.title		{ font-size: 120%; border-spacing: 1px; padding: 0; }
	TR.title		{ font-weight: bold; }

	TABLE.icons		{ border-spacing: 10px 0; padding: 0px; }

	TABLE.header		{ font-size: 80%; border-spacing: 1px; padding: 0; }
	INPUT.header		{ font-size: 80%; } 
	SELECT.header		{ font-size: 80%; } 

	TABLE.types		{ font-size: 70%; text-align: left; border-spacing: 0px; padding: 0; width: 35%; }
	TR.types		{ white-space: nowrap; }
	INPUT.types		{ font-size: 70%; }
	
	TABLE.actions		{ font-size: 80%; text-align: left; border-spacing: 0px; padding: 0; white-space: nowrap; }
	TD.actions		{ font-weight: bold; }
	INPUT.actions		{ font-size: 80%; }
	
	DIV.pagetrail		{ font-size: 80%; font-weight: bold; text-align: center; }
	#centered		{ width: 700px; height:20px; margin:0px auto 0; position: relative; }
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

	B.footer		{ font-size: 70%; color: #777; font-weight: normal; }
	</STYLE>
EOF

}
