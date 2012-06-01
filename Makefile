dummy:
	@echo No need to make anything.

ifdef VERSION
tag:
	@git update-index --refresh --unmerged
	@if git diff-index --name-only HEAD | grep ^ ; then \
		echo Uncommitted changes in above files; exit 1; fi
	sed 's/^\(my $$version = \).*/\1$(VERSION);/' -i get_iplayer
	sed 's/^\(my $$VERSION = \).*/\1$(VERSION);/' -i get_iplayer.cgi
	@./get_iplayer --manpage get_iplayer.1
	git diff --exit-code get_iplayer.1 > /dev/null || \
		sed 's/\(\.TH GET_IPLAYER "1" "\)[^"]*"/\1$(shell date +"%B %Y")\"/' -i get_iplayer get_iplayer.1
	sed 's/\(The latest version is v\)[0-9]\{1,\}\.[0-9]\{1,\}/\1$(VERSION)/' -i html/get_iplayer.html
	@git log --format='%aN' |sort -u > CONTRIBUTORS; git add CONTRIBUTORS
	@git commit -m "Tag version $(VERSION)" get_iplayer get_iplayer.1 html/get_iplayer.html CONTRIBUTORS get_iplayer.cgi
	@git tag v$(VERSION)

tarball:
	@git update-index --refresh --unmerged
	@if git diff-index --name-only v$(VERSION) | grep ^ ; then \
		echo Uncommitted changes in above files; exit 1; fi
	git archive --format=tar --prefix=get_iplayer-$(VERSION)/ v$(VERSION) | gzip -9 > get_iplayer-$(VERSION).tar.gz
endif
