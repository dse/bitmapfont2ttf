test: FORCE
	fontforge bin/bdfbdf ~/git/dse.d/fonts.d/xorg-monospace-fonts-ttf/xorg-adobe-100dpi/helvB08.bdf

test-diff: FORCE
	fontforge bin/bdfbdf ~/git/dse.d/fonts.d/xorg-monospace-fonts-ttf/xorg-adobe-100dpi/helvB08.bdf | \
		{ diff -u -w ~/git/dse.d/fonts.d/xorg-monospace-fonts-ttf/xorg-adobe-100dpi/helvB08.bdf - || true ; }

.PHONY: FORCE
