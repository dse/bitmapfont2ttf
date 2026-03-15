from bdf_font import BDFFont

import math
import statistics
import fontforge
import os
import re
import sys
import math

FUDGE_FACTOR = 1.01
MIN_GLYPH_WIDTH_EM = 0.1

from bdf_utils import bin_data_to_hex_data, hex_data_to_bin_data

# https://stackoverflow.com/questions/1734745/how-to-create-circle-with-b%C3%A9zier-curves
# https://spencermortensen.com/articles/bezier-circle/
THAT_CIRCLE_BEZIER_CONSTANT = 0.5519150244935105707435627

class BitmapFont2TTF:
    def __init__(self, args=None):
        if args is not None:
            self.set_args(args)
        self.fix_filenames()

    def set_args(self, args):
        self.args = args

        self.filename           = args.filename
        self.destfilenames      = args.destfilenames
        self.italicize_angle    = args.italicize_angle
        self.italicize_center_y = args.italicize_center
        self.italicize_slant    = args.italicize_slant
        self.italic_angle       = args.italic_angle

    def bitmapfont2ttf(self, font=None):
        if (os.path.splitext(self.filename))[1].lower() != '.bdf':
            raise Exception("only bdf bitmap fonts are supported")
        if font is None:
            self.bdf = BDFFont(self.filename)
            self.bdf.use_properties = self.args.use_properties
        else:
            self.bdf = font
            self.bdf.use_properties = self.args.use_properties
        self.font = fontforge.font()
        self.font.importBitmaps(self.filename, True) # imports everything EXCEPT the bitmaps
        self.trace()
        if self.args.bdf_ascent_descent:
            ascent_px = self.bdf.ascent_px()
            descent_px = self.bdf.descent_px()
            pixelSize = self.bdf.get_pixel_size()
            em_units_per_pixel = 1.0 * self.font.em / (ascent_px + descent_px)
            self.font.ascent  = int(round(ascent_px * em_units_per_pixel))
            self.font.descent = int(round(descent_px * em_units_per_pixel))
        if self.args.remove_ascent_add:
            self.font.hhea_ascent_add     = 0
            self.font.hhea_descent_add    = 0
            self.font.os2_typoascent_add  = 0
            self.font.os2_typodescent_add = 0
            self.font.os2_winascent_add   = 0
            self.font.os2_windescent_add  = 0
        if self.args.all_ascent_descent:
            self.font.hhea_ascent     = self.font.ascent
            self.font.hhea_descent    = -self.font.descent
            self.font.os2_typoascent  = self.font.ascent
            self.font.os2_typodescent = -self.font.descent
            self.font.os2_winascent   = self.font.ascent
            self.font.os2_windescent  = self.font.descent
        if self.args.remove_line_gap:
            self.font.hhea_linegap    = 0
            self.font.os2_typolinegap = 0
            self.font.vhea_linegap    = 0
        if self.args.monospace:
            if not self.args.dumb:
                panose = list(self.font.os2_panose)
                panose[3] = 9
                self.font.os2_panose = tuple(panose)
            self.make_font_detect_as_monospace()

        if self.args.panose_0 is not None or self.args.panose_1 is not None or \
           self.args.panose_2 is not None or self.args.panose_3 is not None or \
           self.args.panose_4 is not None or self.args.panose_5 is not None or \
           self.args.panose_6 is not None or self.args.panose_7 is not None or \
           self.args.panose_8 is not None or self.args.panose_9 is not None:
            panose = list(self.font.os2_panose)
            if self.args.panose_0 is not None: panose[0] = self.args.panose_0
            if self.args.panose_1 is not None: panose[1] = self.args.panose_1
            if self.args.panose_2 is not None: panose[2] = self.args.panose_2
            if self.args.panose_3 is not None: panose[3] = self.args.panose_3
            if self.args.panose_4 is not None: panose[4] = self.args.panose_4
            if self.args.panose_5 is not None: panose[5] = self.args.panose_5
            if self.args.panose_6 is not None: panose[6] = self.args.panose_6
            if self.args.panose_7 is not None: panose[7] = self.args.panose_7
            if self.args.panose_8 is not None: panose[8] = self.args.panose_8
            if self.args.panose_9 is not None: panose[9] = self.args.panose_9
            self.font.os2_panose = tuple(panose)

        if not self.dumb:
            self.inherit_bdf_metas()

        if self.args.font_name is not None:
            self.font.fontname = self.args.font_name
        if self.args.full_name is not None:
            self.font.fullname = self.args.full_name
        if self.args.family_name is not None:
            self.font.familyname = self.args.family_name
        if self.args.weight_name is not None:
            # BDF weight names are "Ultra Light", "Extra Light", "Light",
            # and "Semi Light".  Weight Names would be "Medium" for the
            # normal weight, or "Extra-Light" for all the others.
            #
            # Removing the spaces from the BDF weight names does not solve
            # this.  Setting self.font.weight doesn't fix it either.
            # --os2-weight fixes this.
            self.font.weight = self.args.weight_name
        if self.args.os2_weight is not None:
            self.font.os2_weight = self.args.os2_weight
        if self.italic_angle is not None:
            # if --italic-angle and --italicize-anything are specified,
            # the nominal italic angle is set to the first one.
            # apparently setting it to -12 fixes an issue where
            # bold italic wasn't showing up
            self.font.italicangle = self.italic_angle
        elif self.italicize_angle is not None:
            self.font.italicangle = self.italicize_angle

        if self.args.copyright is not None:
            self.font.copyright = self.args.copyright

        if not (self.args.no_sfnt_names or self.dumb):
            if self.font.sfntRevision is None:
                self.font.sfntRevision = 0x00010000
            self.font.appendSFNTName("English (US)", "Copyright", self.font.copyright) # [0]
            self.font.appendSFNTName("English (US)", "Family", self.font.familyname) # [1]
            if self.args.subfamily is not None:
                self.font.appendSFNTName("English (US)", "SubFamily", self.args.subfamily) # [2] FIXME: else autogenerate
            if self.args.unique_id is not None:
                self.font.appendSFNTName("English (US)", "UniqueID", self.args.unique_id) # [3]
            else:
                self.font.appendSFNTName("English (US)", "UniqueID", self.font.familyname + " 2024") # FIXME [3]
            self.font.appendSFNTName("English (US)", "Fullname", self.font.fullname) # [4]
            self.font.appendSFNTName("English (US)", "Version", "0.0") # FIXME [5]
            self.font.appendSFNTName("English (US)", "PostScriptName", self.font.fontname) # [6]

        if self.args.macstyle is not None:
            self.font.macstyle = self.args.macstyle
        if self.args.stylemap is not None:
            self.font.os2_stylemap = self.args.stylemap
        if self.args.panose is not None:
            self.font.os2_panose = tuple(self.args.panose)
        if self.args.fstype is not None:
            self.font.os2_fstype = self.args.fstype
        if self.args.use_typo_metrics == True:
            self.font.os2_use_typo_metrics = True
        elif self.args.use_typo_metrics == False:
            self.font.os2_use_typo_metrics = False
        if self.args.family_class is not None:
            self.font.os2_family_class = self.args.family_class
        if self.args.vendor is not None:
            self.font.os2_vendor = self.args.vendor
        if self.args.os2_version is not None:
            self.font.os2_version = self.args.os2_version
        if self.args.weight_width_slope_only is not None:
            self.font.os2_weight_width_slope_only = self.args.weight_width_slope_only

        # early PostScript interpreters cannot have more than 29 (yes, twenty-nine) characters
        # https://glyphsapp.com/learn/naming
        if len(self.font.fontname) > 29:
            print("WARNING: PS font name longer than 29 characters: %s" % repr(self.font.fontname))

        return self.font

    # make sure all glyphs are the same width.  otherwise font may not be detected as monospace.  TODO: handle dual-width fonts
    def make_font_detect_as_monospace(self):
        glyphs = list([glyph for glyph in self.font.glyphs()
                       if glyph.glyphname not in [".notdef", ".null", "nonmarkingreturn"]])
        #                              widths are: nonzero,   zero,    nonzero
        if len(glyphs) == 0:
            return
        super_narrow_glyphs = [glyph for glyph in glyphs if glyph.width < MIN_GLYPH_WIDTH_EM * glyph.font.em]
        for glyph in super_narrow_glyphs:
            glyph.width = 0
        substantive_glyphs = [glyph for glyph in glyphs if glyph.width >= MIN_GLYPH_WIDTH_EM * glyph.font.em]
        if len(substantive_glyphs) == 0:
            raise Exception("while detecting monospacedness, did not find any worthy glyphs")
        clusters = get_clusters(substantive_glyphs, fn=lambda g:g.width)
        if len(clusters) > 1:
            raise Exception("font is dualspace; dualspace fonts not supported yet")

        widths = [glyph.width for glyph in clusters[0]]
        new_glyph_width = statistics.mean(statistics.multimode(widths))
        for glyph in substantive_glyphs:
            print(type(glyph.width))                            # int
            print(type(new_glyph_width))                        # int
            print(type(glyph.left_side_bearing))                # float
            print(type(glyph.right_side_bearing))               # float
            glyph.left_side_bearing = int(glyph.left_side_bearing + (new_glyph_width - glyph.width) / 2)
            glyph.width = new_glyph_width

        if "notdef" in self.font:
            notdef = self.font["notdef"]
            if notdef.width:
                notdef.width = new_glyph_width
        if "nmreturn" in self.font:
            nmreturn = self.font["nmreturn"]
            if nmreturn.width:
                nmreturn.width = new_glyph_width

    def save(self):
        for dest in self.destfilenames:
            if dest.endswith(".sfd"):
                print("Saving %s..." % dest)
                self.font.save(dest)
            else:
                print("Generating %s..." % dest)
                self.font.generate(dest)
            print("Done.");

    def fix_filenames(self):
        if self.filename == os.path.basename(self.filename):
            # Work around an issue where importBitmaps segfaults if you only
            # specify a filename 'foo.pcf'.  Yes, './foo.pcf' works pefectly
            # fine whereas 'foo.pcf' does not.
            self.filename = os.path.join('.', self.filename)
        if self.destfilenames is None or len(self.destfilenames) == 0:
            (rootdestfilename, junk) = os.path.splitext(self.filename)
            self.destfilenames = [rootdestfilename + '.ttf']

    def trace(self):
        count = len(self.bdf.chars)
        index = 0
        for char in self.bdf.chars:
            index = index + 1
            encoding = char.encoding if char.encoding is not None else -1
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
        if ofs_y is None:
            ofs_y = self.bdf.bbx_ofs_y
        if ofs_y is None:
            raise Exception("cannot find bounding box y offset: %s" % glyph)
        ofs_x = bdf_char.bbx_ofs_x
        if ofs_x is None:
            ofs_x = self.bdf.bbx_ofs_x
        if ofs_x is None:
            raise Exception("cannot find bounding box x offset: %s" % glyph)
        height = bdf_char.bbx_y
        if height is None:
            height = self.bdf.bbx_y
        if height is None:
            raise Exception("cannot find bounding box height: %s" % glyph)
        width = bdf_char.bbx_x
        if width is None:
            width = self.bdf.bbx_x
        if width is None:
            raise Exception("cannot find bounding box width: %s" % glyph)

        y = ofs_y + height
        pixY = 1.0 * self.font.em / self.bdf.get_pixel_size()
        pixX = 1.0 * self.font.em / self.bdf.get_pixel_size() * self.bdf.get_aspect_ratio() * self.args.aspect_ratio
        deltaX = pixX * (1.0 - self.args.dot_width) / 2
        deltaY = pixY * (1.0 - self.args.dot_height) / 2

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
        italicize_center_y = self.italicize_center_y if self.italicize_center_y is not None else 0

        for line in bdf_char.bitmap_data:
            line = hex_data_to_bin_data(line)
            y = y - 1
            if self.args.circular_dots:
                x = ofs_x
                for pixel in line:
                    if pixel == '1':
                        xh = round(pixX * self.args.dot_width * 0.5)
                        yh = round(pixY * self.args.dot_height * 0.5)
                        r = max(xh, yh)
                        xc = round(pixX * (x + 0.5 - italicize_slant * (y - italicize_center_y)))
                        yc = round(pixY * (y + 0.5))
                        x1 = xc - r
                        x2 = xc + r
                        y1 = yc - r
                        y2 = yc + r
                        xcp = round(pixX * self.args.dot_width * 0.5 * THAT_CIRCLE_BEZIER_CONSTANT)
                        ycp = round(pixY * self.args.dot_height * 0.5 * THAT_CIRCLE_BEZIER_CONSTANT)
                        contour = fontforge.contour();
                        contour.moveTo(xc, y1)
                        contour.cubicTo((xc + xcp, y1), (x2, yc - ycp), (x2, yc))
                        contour.cubicTo((x2, yc + ycp), (xc + xcp, y2), (xc, y2))
                        contour.cubicTo((xc - xcp, y2), (x1, yc + ycp), (x1, yc))
                        contour.cubicTo((x1, yc - ycp), (xc - xcp, y1), (xc, y1))
                        contour.closed = True
                        glyph.layers['Fore'] += contour
                    x = x + 1
            elif self.args.dot_width < 1:
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
                if self.args.bottom is not None:
                    y1unit = self.args.bottom
                if self.args.top is not None:
                    y2unit = self.args.top
                # Draw contiguous horizontal sequences of pixels.
                # This saves considerable disk space.
                pixel_blocks = []
                pixel_block = None
                x = ofs_x
                bottom = 0
                top = 1
                for pixel in line:
                    if pixel == '1':
                        if pixel_block is None:
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

    def inherit_bdf_metas(self):
        if self.bdf.font_name is not None:
            self.font.fontname = self.bdf.font_name
        if self.bdf.properties.get("FULL_NAME") is not None:
            self.font.fullname = self.bdf.properties["FULL_NAME"]
        if self.bdf.properties.get("FAMILY_NAME") is not None:
            self.font.familyname = self.bdf.properties["FAMILY_NAME"]
        if self.bdf.properties.get("WEIGHT_NAME") is not None:
            self.font.weight = self.bdf.properties["WEIGHT_NAME"]
        if self.bdf.properties.get("SLANT") is not None:
            slant = self.bdf.properties["SLANT"].upper()
            if slant == "R":
                self.font.italicangle = 0
            elif slant == "O":
                self.font.italicangle = -12
            elif slant == "I":
                self.font.italicangle = -12

def close(a, b):
    return (a <= (b * FUDGE_FACTOR)) and (b <= (a * FUDGE_FACTOR))

def get_clusters(items, fn=lambda i:i):
    print([fn(i) for i in items])
    A = []
    H = []
    D = []
    for item in items:
        if not len(A):
            A.append(item)
            continue

        II = fn(item)
        AA = [fn(i) for i in A]
        DD = [fn(i) for i in D]
        HH = [fn(i) for i in H]

        # is this value close to any in cluster A?
        if len([ii for ii in AA if close(II, ii)]):
            A.append(item)
            continue
        # is this value close to double of anything in cluster A?
        if len([ii for ii in AA if close(II, ii*2)]):
            if len(D):
                raise Exception("neither monospace nor dualspace: %s" % repr([II, AA, HH, DD]))
            H.append(item)
            continue
        # is this value close to any in cluster H?
        if len([ii for ii in HH if close(II, ii)]):
            if len(D):
                raise Exception("neither monospace nor dualspace: %s" % repr([II, AA, HH, DD]))
            H.append(item)
            continue
        # is this value close to half of anything in cluster A?
        if len([ii for ii in AA if close(II, ii/2)]):
            if len(H):
                raise Exception("neither monospace nor dualspace: %s" % repr([II, AA, HH, DD]))
            D.append(item)
            continue
        # is this value close to anything in cluster D?
        if len([ii for ii in DD if close(II, ii)]):
            if len(H):
                raise Exception("neither monospace nor dualspace: %s" % repr([II, AA, HH, DD]))
            D.append(item)
            continue
        raise Exception("neither monospace nor dualspace: %s" % repr([II, AA, HH, DD]))
    if len(H) and len(D):
        raise Exception("neither monospace nor dualspace: %s" % repr([II, AA, HH, DD]))
    if len(H):
        return [H, A]
    if len(D):
        return [A, D]
    return [A]
