#!/bin/sh

if [ ! -r perlfiles.tar.gz ]; then
    # Must be a better way of doing this, but for now just stash
    # a tarball of the files that are actually required. Perhaps
    # we should install perl separately like we do all the media
    # stuff?
    echo You need a tarball of the perl stuff
    exit 1
fi

GIPDIR=`dirname $0`
TMPDIR=`mktemp -d /tmp/gipXXXXXX`
mkdir "$TMPDIR/perlfiles"
tar xvfz perlfiles.tar.gz -C "$TMPDIR/perlfiles"
makensis -NOCD -DBUILDPATH="$TMPDIR" -DSOURCEPATH="$GIPDIR" "$GIPDIR/windows/get_iplayer_setup.nsi"
mv -v $TMPDIR/get_iplayer_setup*.exe .
rm -rf $TMPDIR
