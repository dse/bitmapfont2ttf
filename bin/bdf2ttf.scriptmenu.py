# This version of the script is interactively executed from the
# FontForge script menu.  The importBitmaps() function appears to
# cause a segfault when executed from a regular (non-interactive)
# FontForge script.

import fontforge
import psMat
import os

bdf_font = fontforge.activeFont()

bdf_filename = bdf_font.path
font_basename, font_ext = os.path.splitext(bdf_filename)
sfd_filename = font_basename + ".sfd"
ttf_filename = font_basename + ".ttf"

new_font = fontforge.font()

new_font.fontname    = bdf_font.fontname
new_font.familyname  = bdf_font.familyname
new_font.fullname    = bdf_font.fullname
new_font.weight      = bdf_font.weight
new_font.italicangle = bdf_font.italicangle
new_font.ascent      = bdf_font.ascent
new_font.descent     = bdf_font.descent

new_font.importBitmaps(bdf_filename, 1)
glyphs = [
    glyph for glyph in new_font if new_font[glyph].isWorthOutputting()
]

new_font.selection.select(*glyphs)
new_font.autoTrace()
new_font.save(sfd_filename)
new_font.generate(ttf_filename)

