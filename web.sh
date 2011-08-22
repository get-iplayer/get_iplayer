#!/bin/sh

BASEURL=http://www.infradead.org/get_iplayer

git pull -q

TAGS="`git tag -l 'v*' | sort -r`"

THISTAG=
for NEWTAG in $TAGS; do
    OLDTAG=$THISTAG
    THISTAG=$NEWTAG

    if [ "$OLDTAG" = "" ]; then
	echo ${THISTAG##v} > VERSION.new
	LATESTTAG=$THISTAG
	continue;
    fi
    # Compare $OLDTAG with $THISTAG
    git show --format=%aD $OLDTAG -- | head -1 | sed "s/^\(.*\)..:..:.. [+-]..../Version ${OLDTAG##v} -- \1/"
    git log $THISTAG..$OLDTAG --pretty=oneline | sed 's/[0-9a-f]*/ \*/' | grep -v 'Tag version '
    echo
    if [ ! -d $OLDTAG ]; then
	git archive --format=tar $OLDTAG --prefix=$OLDTAG/ | tar xf -
	echo "bin $BASEURL/$OLDTAG/get_iplayer" > MANIFEST.$OLDTAG
	for a in $OLDTAG/plugins/*.plugin ; do 
	    echo "plugins $BASEURL/$a" >> MANIFEST.$OLDTAG
	done
    fi
done > CHANGELOG.new

mv CHANGELOG.new CHANGELOG-get_iplayer
mv VERSION.new VERSION-get_iplayer
ln -sfn $LATESTTAG latest
