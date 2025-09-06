from bdf_font import BDFFont

import fontforge
import os
import re
import sys
import math

from bdf_utils import bin_data_to_hex_data, hex_data_to_bin_data

# https://stackoverflow.com/questions/1734745/how-to-create-circle-with-b%C3%A9zier-curves
# https://spencermortensen.com/articles/bezier-circle/
THAT_CIRCLE_BEZIER_CONSTANT = 0.5519150244935105707435627

class BitmapFont2TTF:
    def __init__(self, args):
        self.set_args(args)
        self.fix_filenames()

    def bitmapfont2ttf(self, font=None):
        if (os.path.splitext(self.filename))[1].lower() != '.bdf':
            raise Exception("only bdf bitmap fonts are supported")
        if font is None:
            self.bdf = BDFFont(self.filename)
        else:
            self.bdf = font
        if self.args.bdf_ascent_descent_2:
            if self.properties.get("PIXEL_SIZE") is None:
                raise Exception("PIXEL_SIZE missing")
            if self.properties.get("FONT_DESCENT") is None:
                raise Exception("FONT_DESCENT missing")
            if self.args.windows:
                if self.bdf.properties["PIXEL_SIZE"] % 4 == 2:
                    self.bdf.properties["PIXEL_SIZE"] += 1
                    self.bdf.properties["FONT_DESCENT"] += 1
            else:
                self.bdf.properties["PIXEL_SIZE"] += self.args.add_pixel_size
                self.bdf.properties["FONT_DESCENT"] += self.args.add_pixel_size
        self.font = fontforge.font()
        self.font.importBitmaps(self.filename, True) # imports everything EXCEPT the bitmaps
        self.trace()
        if self.bdf_ascent_descent:
            ascent_px = self.bdf.ascent_px()
            descent_px = self.bdf.descent_px()
            pixelSize = self.bdf.get_pixel_size()
            em_units_per_pixel = 1.0 * self.font.em / (ascent_px + descent_px)
            self.font.ascent  = int(round(ascent_px * em_units_per_pixel))
            self.font.descent = int(round(descent_px * em_units_per_pixel))
        if self.remove_ascent_add:
            self.font.hhea_ascent_add     = 0
            self.font.hhea_descent_add    = 0
            self.font.os2_typoascent_add  = 0
            self.font.os2_typodescent_add = 0
            self.font.os2_winascent_add   = 0
            self.font.os2_windescent_add  = 0
        if self.all_ascent_descent:
            self.font.hhea_ascent     = self.font.ascent
            self.font.hhea_descent    = -self.font.descent
            self.font.os2_typoascent  = self.font.ascent
            self.font.os2_typodescent = -self.font.descent
            self.font.os2_winascent   = self.font.ascent
            self.font.os2_windescent  = self.font.descent
        if self.remove_line_gap:
            self.font.hhea_linegap    = 0
            self.font.os2_typolinegap = 0
            self.font.vhea_linegap    = 0
        if self.monospace:
            panose = list(self.font.os2_panose)
            panose[3] = 9
            self.font.os2_panose = tuple(panose)
            self.fix_for_monospace_detection()
        if self.modify_panose:
            panose = list(self.font.os2_panose)
            if self.set_panose_0 is not None: panose[0] = self.set_panose_0
            if self.set_panose_1 is not None: panose[1] = self.set_panose_1
            if self.set_panose_2 is not None: panose[2] = self.set_panose_2
            if self.set_panose_3 is not None: panose[3] = self.set_panose_3
            if self.set_panose_4 is not None: panose[4] = self.set_panose_4
            if self.set_panose_5 is not None: panose[5] = self.set_panose_5
            if self.set_panose_6 is not None: panose[6] = self.set_panose_6
            if self.set_panose_7 is not None: panose[7] = self.set_panose_7
            if self.set_panose_8 is not None: panose[8] = self.set_panose_8
            if self.set_panose_9 is not None: panose[9] = self.set_panose_9
            self.font.os2_panose = tuple(panose)

        if self.set_font_name != None:
            self.font.fontname = self.set_font_name
        elif self.bdf.font_name != None:
            self.font.fontname = self.bdf.font_name

        if self.set_full_name != None:
            self.font.fullname = self.set_full_name
        elif self.bdf.properties.get("FULL_NAME") != None:
            self.font.fullname = self.bdf.properties["FULL_NAME"]

        if self.set_family_name != None:
            self.font.familyname = self.set_family_name
        elif self.bdf.properties.get("FAMILY_NAME") != None:
            self.font.familyname = self.bdf.properties["FAMILY_NAME"]

        if self.set_weight_name != None:
            # BDF weight names are "Ultra Light", "Extra Light", "Light",
            # and "Semi Light".  Weight Names would be "Medium" for the
            # normal weight, or "Extra-Light" for all the others.
            #
            # Removing the spaces from the BDF weight names does not solve
            # this.  Setting self.font.weight doesn't fix it either.
            # --os2-weight fixes this.
            self.font.weight = self.set_weight_name
        elif self.bdf.properties.get("WEIGHT_NAME") != None:
            self.font.weight = self.bdf.properties["WEIGHT_NAME"]

        if self.set_os2_weight != None:
            self.font.os2_weight = self.set_os2_weight

        if self.italic_angle != None:
            self.font.italicangle = self.italic_angle
        elif self.italicize_angle != None:
            self.font.italicangle = self.italicize_angle
        elif self.bdf.properties.get("SLANT") != None:
            slant = self.bdf.properties["SLANT"].upper()
            if slant == "R":
                self.font.italicangle = 0
            elif slant == "O":
                self.font.italicangle = -12
            elif slant == "I":
                self.font.italicangle = -12

        if self.copyright != None:
            self.font.copyright = self.copyright

        if not self.no_sfnt_names:
            self.font.sfntRevision = 0x00010000
            self.font.appendSFNTName("English (US)", "Copyright", self.font.copyright) # [0]
            self.font.appendSFNTName("English (US)", "Family", self.font.familyname) # [1]
            if self.subfamily != None:
                self.font.appendSFNTName("English (US)", "SubFamily", self.subfamily) # [2] FIXME: else autogenerate
            if self.unique_id != None:
                self.font.appendSFNTName("English (US)", "UniqueID", self.unique_id) # [3]
            else:
                self.font.appendSFNTName("English (US)", "UniqueID", self.font.familyname + " 2024") # FIXME [3]
            self.font.appendSFNTName("English (US)", "Fullname", self.font.fullname) # [4]
            self.font.appendSFNTName("English (US)", "Version", "0.0") # FIXME [5]
            self.font.appendSFNTName("English (US)", "PostScriptName", self.font.fontname) # [6]
            print("sfnt_names: %s" % repr(self.font.sfnt_names))

        self.font.os2_fstype = 0x0040

        # os2_family_class?
        # os2_family_class?
        # os2_vendor?
        # set any bits in the stylemap?
        # set no bits?
        # fstype?

        # self.f800()
        self.save()

        count2 = 0
        for glyph in self.font.glyphs():
            count2 += 1
        print("there are %d glyphs" % count2)

    # make sure all glyphs are the same width.
    # otherwise font may not be detected as monospace.
    def fix_for_monospace_detection(self):
        count = 0
        counts = {}
        for glyph in self.font.glyphs():
            count += 1
            if glyph.width not in counts:
                counts[glyph.width] = 0
            counts[glyph.width] += 1
        widths = list(counts.keys())
        if len(widths) == 1:
            print("    all %d glyphs are %d/%d wide; is monospace" % (count, widths[0], self.font.em))
            return
        width = widths[0]
        for glyph in self.font.glyphs():
            if glyph.width != width:
                print("    U+%04X: chaning width from %d to %d" % (glyph.encoding, glyph.width, width))
            glyph.width = width

    def save(self):
        for dest in self.destfilenames:
            if (os.path.splitext(dest))[1].lower() == '.sfd':
                print("saving %s" % dest)
                self.font.save(dest)
            else:
                print("generating %s" % dest)
                self.font.generate(dest)

    def set_args(self, args):
        self.args = args

        self.filename              = args.filename
        self.destfilenames         = args.destfilenames
        self.dot_width              = args.dot_width
        self.dot_height             = args.dot_height
        self.aspect_ratio           = args.aspect_ratio
        self.circular_dots          = args.circular_dots
        self.bottom                = args.bottom
        self.top                   = args.top
        self.monospace             = args.monospace
        self.bdf_ascent_descent      = args.bdf_ascent_descent
        self.remove_line_gap         = args.remove_line_gap
        self.remove_ascent_add       = args.remove_ascent_add
        self.all_ascent_descent      = args.all_ascent_descent
        self.set_panose_0            = args.panose_0
        self.set_panose_1            = args.panose_1
        self.set_panose_2            = args.panose_2
        self.set_panose_3            = args.panose_3
        self.set_panose_4            = args.panose_4
        self.set_panose_5            = args.panose_5
        self.set_panose_6            = args.panose_6
        self.set_panose_7            = args.panose_7
        self.set_panose_8            = args.panose_8
        self.set_panose_9            = args.panose_9
        self.modify_panose          = (args.panose_0 is not None or
                                      args.panose_1 is not None or
                                      args.panose_2 is not None or
                                      args.panose_3 is not None or
                                      args.panose_4 is not None or
                                      args.panose_5 is not None or
                                      args.panose_6 is not None or
                                      args.panose_7 is not None or
                                      args.panose_8 is not None or
                                      args.panose_9 is not None)
        self.set_weight_name         = args.weight_name
        self.set_font_name         = args.font_name
        self.set_full_name           = args.full_name
        self.set_family_name         = args.family_name
        self.set_os2_weight          = args.os2_weight

        self.italicize_angle           = args.italicize_angle
        self.italicize_center_y         = args.italicize_center
        self.italicize_slant           = args.italicize_slant
        self.italic_angle              = args.italic_angle

        self.copyright               = args.copyright
        self.no_sfnt_names             = args.no_sfnt_names
        self.subfamily               = args.subfamily
        self.unique_id                = args.unique_id

        # self.newAscent             = args.new_ascent
        # self.newDescent            = args.new_descent
        # self.newPixelSize          = args.new_pixel_size
        # self.fontName              = args.font_name
        # self.comment               = args.comment
        # self.version               = args.version
        # self.weight                = args.weight
        # self.panose2               = args.panose2
        # self.os2Weight             = args.os2_weight
        # self.lineGap               = args.line_gap
        # self.fixAscentDescent      = args.fix_ascent_descent
        # self.fixWeight             = args.fix_weight
        # self.fixStyleMap           = args.fix_style_map
        # self.fixSlant              = args.fix_slant
        # self.fixMacStyle           = args.fix_mac_style

    def fix_filenames(self):
        if self.filename == os.path.basename(self.filename):
            # Work around an issue where importBitmaps segfaults if you only
            # specify a filename 'foo.pcf'.  Yes, './foo.pcf' works pefectly
            # fine whereas 'foo.pcf' does not.
            self.filename = os.path.join('.', self.filename)
        if self.destfilenames == None or len(self.destfilenames) == 0:
            (rootdestfilename, junk) = os.path.splitext(self.filename)
            self.destfilenames = [rootdestfilename + '.ttf']

    def trace(self):
        count = len(self.bdf.chars)
        index = 0
        for char in self.bdf.chars:
            index = index + 1
            encoding = char.encoding if char.encoding != None else -1
            try:
                glyph = self.font.createChar(encoding, char.name)
            except:
                sys.stderr.write('\nERROR: encoding %s; name %s\n' % (encoding, char.name))
                raise
            self.trace_glyph(glyph, char)
            glyph.addExtrema()
            glyph.simplify()

    def trace_glyph(self, glyph, bdf_char):
        ofs_y = bdf_char.bbx_ofs_y
        if ofs_y == None:
            ofs_y = self.bdf.bbx_ofs_y
        if ofs_y == None:
            raise Exception("cannot find bounding box y offset: %s" % glyph)
        ofs_x = bdf_char.bbx_ofs_x
        if ofs_x == None:
            ofs_x = self.bdf.bbx_ofs_x
        if ofs_x == None:
            raise Exception("cannot find bounding box x offset: %s" % glyph)
        height = bdf_char.bbx_y
        if height == None:
            height = self.bdf.bbx_y
        if height == None:
            raise Exception("cannot find bounding box height: %s" % glyph)
        width = bdf_char.bbx_x
        if width == None:
            width = self.bdf.bbx_x
        if width == None:
            raise Exception("cannot find bounding box width: %s" % glyph)

        y = ofs_y + height
        pixY = 1.0 * self.font.em / self.bdf.get_pixel_size()
        pixX = 1.0 * self.font.em / self.bdf.get_pixel_size() * self.bdf.get_aspect_ratio() * self.aspect_ratio
        deltaX = pixX * (1.0 - self.dot_width) / 2
        deltaY = pixY * (1.0 - self.dot_height) / 2

        italicize_slant = 0.0
        italicize_angle = 0.0
        if self.italicize_angle is not None:
            italicize_angle = self.italicize_angle
            italicize_slant = math.tan(self.italicize_angle * math.pi / 180) * pixY / pixX
            self.italicize_slant = italicize_slant
        elif self.italicize_slant is not None:
            italicize_slant = self.italicize_slant
            italicize_angle = math.atan(self.italicize_slant * pixX / pixY) * 180 / math.pi
            self.italicize_angle = italicize_angle
            print("italicize_angle = %f" % self.italicize_angle)
        italicize_center_y = self.italicize_center_y if self.italicize_center_y is not None else 0

        for line in bdf_char.bitmap_data:
            line = hex_data_to_bin_data(line)
            y = y - 1
            if self.circular_dots:
                x = ofs_x
                for pixel in line:
                    if pixel == '1':
                        xh = round(pixX * self.dot_width * 0.5)
                        yh = round(pixY * self.dot_height * 0.5)
                        r = max(xh, yh)
                        xc = round(pixX * (x + 0.5 - italicize_slant * (y - italicize_center_y)))
                        yc = round(pixY * (y + 0.5))
                        x1 = xc - r
                        x2 = xc + r
                        y1 = yc - r
                        y2 = yc + r
                        xcp = round(pixX * self.dot_width * 0.5 * THAT_CIRCLE_BEZIER_CONSTANT)
                        ycp = round(pixY * self.dot_height * 0.5 * THAT_CIRCLE_BEZIER_CONSTANT)
                        contour = fontforge.contour();
                        contour.moveTo(xc, y1)
                        contour.cubicTo((xc + xcp, y1), (x2, yc - ycp), (x2, yc))
                        contour.cubicTo((x2, yc + ycp), (xc + xcp, y2), (xc, y2))
                        contour.cubicTo((xc - xcp, y2), (x1, yc + ycp), (x1, yc))
                        contour.cubicTo((x1, yc - ycp), (xc - xcp, y1), (xc, y1))
                        contour.closed = True
                        glyph.layers['Fore'] += contour
                    x = x + 1
            elif self.dot_width < 1:
                x = ofs_x
                for pixel in line:
                    if pixel == '1':
                        xx = x - italicize_slant * (y - italicize_center_y)
                        x1 = pixX * xx       + deltaX
                        x2 = pixX * (xx + 1) - deltaX
                        y1 = pixY * y       + deltaY
                        y2 = pixY * (y + 1) - deltaY
                        contour = fontforge.contour()
                        contour.moveTo(round(x1), round(y1))
                        contour.lineTo(round(x1), round(y2))
                        contour.lineTo(round(x2), round(y2))
                        contour.lineTo(round(x2), round(y1))
                        contour.closed = True
                        glyph.layers['Fore'] += contour
                    x = x + 1
            else:
                [y1unit, y2unit] = [0, 1]
                if self.bottom != None:
                    y1unit = self.bottom
                if self.top != None:
                    y2unit = self.top
                # Draw contiguous horizontal sequences of pixels.
                # This saves considerable disk space.
                pixel_blocks = []
                pixel_block = None
                x = ofs_x
                bottom = 0
                top = 1
                for pixel in line:
                    if pixel == '1':
                        if pixel_block == None:
                            pixel_block = [x, x]
                            pixel_blocks.append(pixel_block)
                        else:
                            pixel_block[1] = x;
                    else:
                        pixel_block = None
                    x = x + 1
                for pixel_block in pixel_blocks:
                    xa = pixel_block[0] - italicize_slant * (y - italicize_center_y)
                    xb = pixel_block[1] - italicize_slant * (y - italicize_center_y)
                    x1 = pixX * xa       + deltaX
                    x2 = pixX * (xb + 1) - deltaX
                    y1 = pixY * y        + deltaY
                    y2 = pixY * (y + 1)  - deltaY
                    if y1unit != 0.0 or y2unit != 1.0:
                        [y1, y2] = [y1 + (y2 - y1) * y1unit,
                                    y1 + (y2 - y1) * y2unit]
                    contour = fontforge.contour()
                    contour.moveTo(round(x1), round(y1))
                    contour.lineTo(round(x1), round(y2))
                    contour.lineTo(round(x2), round(y2))
                    contour.lineTo(round(x2), round(y1))
                    contour.closed = True
                    glyph.layers['Fore'] += contour
        glyph.width = int(round(bdf_char.get_dwidth_x() * pixX))
