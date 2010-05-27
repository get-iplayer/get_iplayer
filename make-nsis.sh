#!/bin/sh

if [ ! -r perlfiles.tar.gz ]; then
    # Must be a better way of doing this, but for now just stash
    # a tarball of the files that are actually required. Perhaps
    # we should install perl separately like we do all the media
    # stuff?
    echo You need a tarball of the perl stuff
    exit 1
fi

NSISDIR=`mktemp -d /tmp/gipXXXXXX`

cp -av windows/get_iplayer windows/installer_files $NSISDIR
tar xvfz perlfiles.tar.gz -C $NSISDIR/get_iplayer
mkdir -p $NSISDIR/get_iplayer/Downloads
cd $NSISDIR
makensis -NOCD get_iplayer/get_iplayer_setup.nsi
cd -
mv -v $NSISDIR/get_iplayer_setup_*.exe .
rm -rf $NSISDIR
