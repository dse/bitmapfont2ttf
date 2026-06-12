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

    def bitmapfont2ttf(self, font=None):
        if (os.path.splitext(self.filename))[1].lower() != '.bdf':
            raise Exception("only bdf bitmap fonts are supported")
        if font is None:
            self.bdf = BDFFont()
            self.bdf.use_properties = self.args.use_properties
        else:
            self.bdf = font
            self.bdf.use_properties = self.args.use_properties

        self.font = fontforge.font()

        self.ascent_px = self.bdf.ascent_px()
        self.descent_px = self.bdf.descent_px()
        self.pixel_size = self.ascent_px + self.descent_px

        # if self.args.add_pixel_size section adds one pixel to descent, let self.args.windows section add one pixel to ascent.
        favor_descent = True

        if self.args.add_pixel_size:
            self.pixel_size += self.args.add_pixel_size
            self.ascent_px += int(self.args.add_pixel_size / 2)
            self.descent_px = self.pixel_size - self.ascent_px
            # may add one more pixel to descent than to ascent
            if self.args.add_pixel_size % 2 == 1:
                favor_descent = False
        if self.args.windows:
            if self.pixel_size % 4 == 2:
                self.pixel_size += 1
                if favor_descent:
                    self.descent_px += 1
                else:
                    self.ascent_px += 1

        self.bdf.set_ascent_px(self.ascent_px)
        self.bdf.set_descent_px(self.descent_px)
        self.bdf.set_pixel_size(self.pixel_size)

        self.em_per_pixel_y = round(self.font.em / self.pixel_size)
        self.em_per_pixel_x = round(self.font.em * self.bdf.get_aspect_ratio() * self.args.aspect_ratio / self.pixel_size)
        self.delta_x = self.em_per_pixel_x * (1.0 - self.args.dot_width) / 2
        self.delta_y = self.em_per_pixel_y * (1.0 - self.args.dot_height) / 2

        self.font.ascent  = self.ascent_px * self.em_per_pixel_y
        self.font.descent = self.descent_px * self.em_per_pixel_y
        self.upos_px   = self.bdf.get_underline_position_px()
        self.uthick_px = self.bdf.get_underline_thickness_px()
        if self.upos_px is not None and self.uthick_px is not None:
            self.font.upos   = self.upos_px * self.em_per_pixel_y
            self.font.uthick = self.uthick_px * self.em_per_pixel_y

        self.font.version     = self.bdf.get_font_version("")
        self.font.encoding    = "UnicodeBMP"

        if self.args.font_name is not None:
            fontname = self.args.font_name
        else:
            fontname = self.bdf.get_font_name()
        if self.args.full_name is not None:
            fullname = self.args.full_name
        else:
            fullname = self.bdf.get_full_name()
        if self.args.family_name is not None:
            familyname = self.args.family_name
        else:
            familyname  = self.bdf.get_family_name()
        if self.args.weight_name is not None:
            weight = self.args.weight_name
        else:
            weight = self.bdf.get_weight_name()

        format_args = {
            "familyname": familyname,
            "fontname": fontname,
            "fullname": fullname,
            "weight": weight,
            "pixel_size": self.bdf.get_pixel_size(),
        }

        self.font.fontname   = self.format(fontname, format_args)
        self.font.fullname   = self.format(fullname, format_args)
        self.font.familyname = self.format(familyname, format_args)
        self.font.weight     = self.format(weight, format_args)
        self.font.weight     = self.format(weight, format_args)

        self.font.copyright = self.bdf.get_copyright()
        if self.args.copyright is not None:
            self.font.copyright = self.args.copyright

        self.italicize_slant = 0.0
        self.italicize_angle = 0.0
        self.italicize_center_y = 0
        if self.args.italicize_angle is not None or self.args.italicize_slant is not None:
            if self.args.italicize_angle is not None:
                self.italicize_angle = self.args.italicize_angle
                self.italicize_slant = math.tan(self.args.italicize_angle * math.pi / 180) * self.em_per_pixel_y / self.em_per_pixel_x
            elif self.args.italicize_slant is not None:
                self.italicize_slant = self.args.italicize_slant
                self.italicize_angle = math.atan(self.args.italicize_slant * self.em_per_pixel_x / self.em_per_pixel_y) * 180 / math.pi
            self.italicize_center_y = self.args.italicize_center if self.args.italicize_center is not None else 0
            self.font.italicangle = self.italicize_angle
        elif self.args.italic_angle is not None:
            self.font.italicangle = self.args.italic_angle
        else:
            self.font.italicangle = self.bdf.get_ttf_italic_angle()

        if self.bdf.properties.get("WEIGHT_NAME") is not None:
            self.font.weight = self.bdf.properties["WEIGHT_NAME"]

        self.trace()

        if self.args.monospace:
            self.make_font_monospace()

        if self.args.panose is not None:
            self.font.os2_panose = tuple(self.args.panose)
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

        if not self.args.no_sfnt_names:
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

        if self.args.set_ttf_os2_weight is not None:
            self.font.os2_weight = self.args.set_ttf_os2_weight
        if self.args.macstyle is not None:
            self.font.macstyle = self.args.macstyle
        if self.args.stylemap is not None:
            self.font.os2_stylemap = self.args.stylemap
        if self.args.fstype is not None:
            self.font.os2_fstype = self.args.fstype
        if self.args.use_typo_metrics is not None:
            self.font.os2_use_typo_metrics = self.args.use_typo_metrics
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

        comment = "%s:\n" % self.filename
        comment += "    pixel size:    %d\n" % self.bdf.get_pixel_size()
        comment += "    pixel ascent:  %d\n" % self.bdf.get_ascent_px()
        comment += "    pixel descent: %d\n" % self.bdf.get_descent_px()
        comment += "    em:            %d\n" % self.font.em
        comment += "    em ascent:     %d\n" % self.font.ascent
        comment += "    em descent:    %d\n" % self.font.descent
        comment += "    weight:        %s\n" % self.font.weight
        comment += "    TTF weight:    %d\n" % self.font.os2_weight

        print(comment)

        # if you don't set font weight before this point it doesn't work
        if self.args.remove_ttf_ascent_add:                         # Do we ever NOT use this?
            self.font.hhea_ascent_add     = 0
            self.font.hhea_descent_add    = 0
            self.font.os2_typoascent_add  = 0
            self.font.os2_typodescent_add = 0
            self.font.os2_winascent_add   = 0
            self.font.os2_windescent_add  = 0

        if self.args.set_ttf_all_ascent_descent:                        # Do we ever NOT use this?
            self.font.hhea_ascent     = self.font.ascent
            self.font.hhea_descent    = -self.font.descent
            self.font.os2_typoascent  = self.font.ascent
            self.font.os2_typodescent = -self.font.descent
            self.font.os2_winascent   = self.font.ascent
            self.font.os2_windescent  = self.font.descent

        if self.args.remove_ttf_line_gap:                           # Do we ever NOT use this?
            self.font.hhea_linegap    = 0
            self.font.os2_typolinegap = 0
            self.font.vhea_linegap    = 0

        return self.font

    # make sure all glyphs are the same width.  otherwise font may not be detected as monospace.  TODO: handle dual-width fonts
    def make_font_monospace(self):
        panose = list(self.font.os2_panose)
        panose[3] = 9
        self.font.os2_panose = tuple(panose)

        glyphs = list([glyph for glyph in self.font.glyphs()
                       if glyph.glyphname not in [".null",              # zero width
                                                  "nonmarkingreturn"]]) # non-zero width?
        if len(glyphs) == 0:
            return
        super_narrow_glyphs = [glyph for glyph in glyphs if glyph.width < MIN_GLYPH_WIDTH_EM * glyph.font.em]
        substantive_glyphs = [glyph for glyph in glyphs if glyph.width >= MIN_GLYPH_WIDTH_EM * glyph.font.em]
        for glyph in super_narrow_glyphs:
            glyph.width = 0
        if len(substantive_glyphs) == 0:
            raise Exception("while detecting monospacedness, did not find any worthy glyphs")

        if self.args.force_monospace:
            # basically don't try to cluster
            new_glyph_width = statistics.mean(statistics.multimode([glyph.width for glyph in substantive_glyphs]))
        else:
            clusters = get_clusters(substantive_glyphs, fn=lambda g:g.width)
            if len(clusters) > 1:
                raise Exception("font is dualspace; dualspace fonts not supported yet")
            widths = [glyph.width for glyph in clusters[0]]
            new_glyph_width = statistics.mean(statistics.multimode(widths))

        for glyph in substantive_glyphs:
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
        def key_fn(char):
            if char.encoding is not None and char.encoding >= 0:
                return (0, char.encoding)
            if char.base_encoding is not None and char.base_encoding >= 0:
                return (1, char.base_encoding)
            return (2, char.name)
        chars = list(self.bdf.chars)
        chars.sort(key=key_fn)
        for char in chars:
            try:
                glyph = self.font.createChar(char.encoding, char.name)
            except:
                sys.stderr.write('\nERROR: cannot createChar(%s, %s)\n' % (repr(char.encoding), repr(char.name)))
                raise
            self.trace_glyph(glyph, char)
            glyph.addExtrema()
            glyph.simplify()

    def trace_glyph(self, glyph, bdf_char):
        ofs_y = bdf_char.get_bbx_ofs_y()
        ofs_x = bdf_char.get_bbx_ofs_x()
        height = bdf_char.get_bbx_y()
        width = bdf_char.get_bbx_x()

        y = ofs_y + height

        for hex_data in bdf_char.bitmap_data:
            line = hex_data_to_bin_data(hex_data)
            y = y - 1
            if self.args.circular_dots:
                x = ofs_x
                for pixel in line:
                    if pixel == '1':
                        xh = round(self.em_per_pixel_x * self.args.dot_width * 0.5)
                        yh = round(self.em_per_pixel_y * self.args.dot_height * 0.5)
                        r = max(xh, yh)
                        xc = round(self.em_per_pixel_x * (x + 0.5 - self.italicize_slant * (y - self.italicize_center_y)))
                        yc = round(self.em_per_pixel_y * (y + 0.5))
                        x1 = xc - r
                        x2 = xc + r
                        y1 = yc - r
                        y2 = yc + r
                        xcp = round(self.em_per_pixel_x * self.args.dot_width * 0.5 * THAT_CIRCLE_BEZIER_CONSTANT)
                        ycp = round(self.em_per_pixel_y * self.args.dot_height * 0.5 * THAT_CIRCLE_BEZIER_CONSTANT)
                        contour = fontforge.contour();
                        contour.moveTo(xc, y1)
                        contour.cubicTo((xc + xcp, y1), (x2, yc - ycp), (x2, yc))
                        contour.cubicTo((x2, yc + ycp), (xc + xcp, y2), (xc, y2))
                        contour.cubicTo((xc - xcp, y2), (x1, yc + ycp), (x1, yc))
                        contour.cubicTo((x1, yc - ycp), (xc - xcp, y1), (xc, y1))
                        contour.closed = True
                        glyph.layers['Fore'] += contour
                    x = x + 1
            elif self.args.dot_width < 1:                       # rectangular dots
                x = ofs_x
                for pixel in line:
                    if pixel == '1':
                        xx = x - self.italicize_slant * (y - self.italicize_center_y)
                        x1 = self.em_per_pixel_x * xx       + self.delta_x
                        x2 = self.em_per_pixel_x * (xx + 1) - self.delta_x
                        y1 = self.em_per_pixel_y * y       + self.delta_y
                        y2 = self.em_per_pixel_y * (y + 1) - self.delta_y
                        contour = fontforge.contour()
                        contour.moveTo(round(x1), round(y1))
                        contour.lineTo(round(x1), round(y2))
                        contour.lineTo(round(x2), round(y2))
                        contour.lineTo(round(x2), round(y1))
                        contour.closed = True
                        glyph.layers['Fore'] += contour
                    x = x + 1
            else:                                               # solid horizontal lines
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
                    xa = pixel_block[0] - self.italicize_slant * (y - self.italicize_center_y)
                    xb = pixel_block[1] - self.italicize_slant * (y - self.italicize_center_y)
                    x1 = self.em_per_pixel_x * xa       + self.delta_x
                    x2 = self.em_per_pixel_x * (xb + 1) - self.delta_x
                    y1 = self.em_per_pixel_y * y        + self.delta_y
                    y2 = self.em_per_pixel_y * (y + 1)  - self.delta_y
                    if y1unit != 0.0 or y2unit != 1.0:
                        [y1, y2] = [y1 + (y2 - y1) * y1unit,
                                    y1 + (y2 - y1) * y2unit]
                    if self.args.draw_crt:
                        yc  = (y1 + y2) / 2
                        yc1 = yc + (y1 - yc) * THAT_CIRCLE_BEZIER_CONSTANT
                        yc2 = yc + (y2 - yc) * THAT_CIRCLE_BEZIER_CONSTANT

                        xp1 = x1 + self.em_per_pixel_x * 0.5
                        xp2 = x2 - self.em_per_pixel_x * 0.5

                        x1 = xp1 - self.em_per_pixel_x * 2 / math.pi
                        x2 = xp2 + self.em_per_pixel_x * 2 / math.pi

                        if xp1 > xp2:
                            delta = (xp2 - xp1) / 2
                            xp1 = (x1 + x2) / 2
                            xp2 = (x1 + x2) / 2
                            x1 = x1 - delta
                            x2 = x2 + delta

                        xc1 = xp1 + (x1 - xp1) * THAT_CIRCLE_BEZIER_CONSTANT
                        xc2 = xp2 + (x2 - xp2) * THAT_CIRCLE_BEZIER_CONSTANT
                        x1 = round(x1)
                        x2 = round(x2)
                        xc1 = round(xc1)
                        xc2 = round(xc2)
                        xp1 = round(xp1)
                        xp2 = round(xp2)
                        y1 = round(y1)
                        y2 = round(y2)
                        yc1 = round(yc1)
                        yc2 = round(yc2)
                        contour = fontforge.contour()
                        contour.moveTo(x1, yc)
                        contour.cubicTo((x1, yc1), (xc1, y1), (xp1, y1))
                        if xp1 != xp2:
                            contour.lineTo(xp2, y1)
                        contour.cubicTo((xc2, y1), (x2, yc1), (x2, yc))
                        contour.cubicTo((x2, yc2), (xc2, y2), (xp2, y2))
                        if xp1 != xp2:
                            contour.lineTo(xp1, y2)
                        contour.cubicTo((xc1, y2), (x1, yc2), (x1, yc))
                        contour.closed = True
                        glyph.layers['Fore'] += contour
                    else:
                        contour = fontforge.contour()
                        contour.moveTo(round(x1), round(y1))
                        contour.lineTo(round(x1), round(y2))
                        contour.lineTo(round(x2), round(y2))
                        contour.lineTo(round(x2), round(y1))
                        contour.closed = True
                        glyph.layers['Fore'] += contour
        glyph.width = int(round(bdf_char.get_dwidth_x() * self.em_per_pixel_x))

    def format(self, str, format_args):
        """
        replace %{...} sequences in the string with appropriate values
        and return the result.

        if a %{...} is immediately preceded by a space, that space is
        removed from the string if there is no value to replace the
        %{...} sequence with.
        """
        def replacer(match):
            space = match[1]
            varname = match[2]
            replacement = ""
            if varname in ["family", "familyname"] and "familyname" in format_args:
                replacement = format_args["familyname"]
            elif varname in ["font", "fontname"] and "fontname" in format_args:
                replacement = format_args["fontname"]
            elif varname in ["weight", "weightname"] and "weight" in format_args:
                replacement = format_args["weight"]
            elif varname in ["full", "fullname"] and "fullname" in format_args:
                replacement = format_args["fullname"]
            elif varname in ["px", "pixelsize"] and "pixel_size" in format_args:
                replacement = str(format_args["pixel_size"])
            if replacement == "":
                return ""
            return space + replacement
        return re.sub(r'(\s?)%\{([^%{}]+)\}', replacer, str)

def close(a, b):
    return (a <= (b * FUDGE_FACTOR)) and (b <= (a * FUDGE_FACTOR))

def get_clusters(items, fn=lambda i:i):
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
