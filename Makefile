dummy:
	@echo No need to make anything.

ifdef VERSION
release:
	@git update-index --refresh --unmerged
	@if git diff-index --name-only HEAD | grep ^ ; then \
		echo Uncommitted changes in above files; exit 1; fi
	@sed -i.bak -e 's/^\(my $$version = \).*/\1$(VERSION);/' -e 's/^\(my $$version_text\) = .*/\1;/' get_iplayer
	@sed -i.bak -e 's/^\(my $$VERSION = \).*/\1$(VERSION);/' -e 's/^\(my $$VERSION_TEXT\) = .*/\1;/' get_iplayer.cgi
	@rm -f get_iplayer.bak get_iplayer.cgi.bak
	@./get_iplayer --nocopyright --manpage get_iplayer.1
	@git diff --exit-code get_iplayer.1 > /dev/null || \
		sed -i.bak -e 's/\(\.TH GET_IPLAYER "1" "\)[^"]*"/\1$(shell date +"%B %Y")\"/' get_iplayer get_iplayer.1
	@rm -f get_iplayer.bak get_iplayer.1.bak
	@git log --format='%aN' | sort -u > CONTRIBUTORS; git add CONTRIBUTORS
	@git commit -m "Release $(VERSION)" get_iplayer get_iplayer.cgi get_iplayer.1 CONTRIBUTORS
	@git tag v$(VERSION)

tarball:
	@git update-index --refresh --unmerged
	@if git diff-index --name-only v$(VERSION) | grep ^ ; then \
		echo Uncommitted changes in above files; exit 1; fi
	git archive --format=tar --prefix=get_iplayer-$(VERSION)/ v$(VERSION) | gzip -9 > get_iplayer-$(VERSION).tar.gz
endif
