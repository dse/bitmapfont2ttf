from mybdf import MyBDF

import fontforge
import os
import re
import sys
import math

# https://stackoverflow.com/questions/1734745/how-to-create-circle-with-b%C3%A9zier-curves
# https://spencermortensen.com/articles/bezier-circle/
THAT_CIRCLE_BEZIER_CONSTANT = 0.5519150244935105707435627

class BitmapFont2TTF:
    def __init__(self, args):
        self.setArgs(args)
        self.fixFilenames()

    def bitmapfont2ttf(self):
        if (os.path.splitext(self.filename))[1].lower() != '.bdf':
            raise Exception("only bdf bitmap fonts are supported")
        self.bdf = MyBDF(self.filename)
        if self.args.bdf_ascent_descent_2:
            if self.args.windows:
                if self.bdf.properties["pixelSize"] % 4 == 2:
                    self.bdf.properties["pixelSize"] += 1
                    self.bdf.properties["descent"]   += 1
            else:
                self.bdf.properties["pixelSize"] += self.args.add_pixel_size
                self.bdf.properties["descent"]   += self.args.add_pixel_size
        self.font = fontforge.font()
        self.font.importBitmaps(self.filename, True) # imports everything EXCEPT the bitmaps
        self.trace()
        if self.bdfAscentDescent:
            ascentPx = self.bdf.ascentPx()
            descentPx = self.bdf.descentPx()
            pixelSize = self.bdf.getPixelSize()
            emUnitsPerPixel = 1.0 * self.font.em / (ascentPx + descentPx)
            self.font.ascent  = int(round(ascentPx * emUnitsPerPixel))
            self.font.descent = int(round(descentPx * emUnitsPerPixel))
        if self.removeAscentAdd:
            self.font.hhea_ascent_add     = 0
            self.font.hhea_descent_add    = 0
            self.font.os2_typoascent_add  = 0
            self.font.os2_typodescent_add = 0
            self.font.os2_winascent_add   = 0
            self.font.os2_windescent_add  = 0
        if self.allAscentDescent:
            self.font.hhea_ascent     = self.font.ascent
            self.font.hhea_descent    = -self.font.descent
            self.font.os2_typoascent  = self.font.ascent
            self.font.os2_typodescent = -self.font.descent
            self.font.os2_winascent   = self.font.ascent
            self.font.os2_windescent  = self.font.descent
        if self.removeLineGap:
            self.font.hhea_linegap    = 0
            self.font.os2_typolinegap = 0
            self.font.vhea_linegap    = 0
        if self.monospace:
            self.fixForMonospaceDetection()
        if self.modifyPanose:
            panose = list(self.font.os2_panose)
            if self.setPanose0 is not None: panose[0] = self.setPanose0
            if self.setPanose1 is not None: panose[1] = self.setPanose1
            if self.setPanose2 is not None: panose[2] = self.setPanose2
            if self.setPanose3 is not None: panose[3] = self.setPanose3
            if self.setPanose4 is not None: panose[4] = self.setPanose4
            if self.setPanose5 is not None: panose[5] = self.setPanose5
            if self.setPanose6 is not None: panose[6] = self.setPanose6
            if self.setPanose7 is not None: panose[7] = self.setPanose7
            if self.setPanose8 is not None: panose[8] = self.setPanose8
            if self.setPanose9 is not None: panose[9] = self.setPanose9
            self.font.os2_panose = tuple(panose)

        if self.setPSFontName != None:
            self.font.fontname = self.setPSFontName
        elif self.bdf.psFontName != None:
            self.font.fontname = self.bdf.psFontName

        if self.setFullName != None:
            self.font.fullname = self.setFullName
        elif self.bdf.properties["fullName"] != None:
            self.font.fullname = self.bdf.properties["fullName"]

        if self.setFamilyName != None:
            self.font.familyname = self.setFamilyName
        elif self.bdf.properties["familyName"] != None:
            self.font.familyname = self.bdf.properties["familyName"]

        if self.setWeightName != None:
            # BDF weight names are "Ultra Light", "Extra Light", "Light",
            # and "Semi Light".  Weight Names would be "Medium" for the
            # normal weight, or "Extra-Light" for all the others.
            #
            # Removing the spaces from the BDF weight names does not solve
            # this.  Setting self.font.weight doesn't fix it either.
            # --os2-weight fixes this.
            self.font.weight = self.setWeightName
        elif self.bdf.properties["weightName"] != None:
            self.font.weight = self.bdf.properties["weightName"]

        if self.setOS2Weight != None:
            self.font.os2_weight = self.setOS2Weight
        if self.italicAngle != None:
            self.font.italicangle = self.italicAngle
        elif self.italicizeAngle != None:
            self.font.italicangle = self.italicizeAngle
        if self.copyright != None:
            self.font.copyright = self.copyright

        if not self.noSfntNames:
            self.font.sfntRevision = 0x00010000
            self.font.appendSFNTName("English (US)", "Copyright", self.font.copyright) # [0]
            self.font.appendSFNTName("English (US)", "Family", self.font.familyname) # [1]
            if self.subfamily != None:
                self.font.appendSFNTName("English (US)", "SubFamily", self.subfamily) # [2] FIXME: else autogenerate
            if self.uniqueId != None:
                self.font.appendSFNTName("English (US)", "UniqueID", self.uniqueId) # [3]
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
    def fixForMonospaceDetection(self):
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

    def setArgs(self, args):
        self.args = args

        self.filename              = args.filename
        self.destfilenames         = args.destfilenames
        self.dotWidth              = args.dot_width
        self.dotHeight             = args.dot_height
        self.aspectRatio           = args.aspect_ratio
        self.circularDots          = args.circular_dots
        self.bottom                = args.bottom
        self.top                   = args.top
        self.monospace             = args.monospace
        self.bdfAscentDescent      = args.bdf_ascent_descent
        self.removeLineGap         = args.remove_line_gap
        self.removeAscentAdd       = args.remove_ascent_add
        self.allAscentDescent      = args.all_ascent_descent
        self.setPanose0            = args.panose_0
        self.setPanose1            = args.panose_1
        self.setPanose2            = args.panose_2
        self.setPanose3            = args.panose_3
        self.setPanose4            = args.panose_4
        self.setPanose5            = args.panose_5
        self.setPanose6            = args.panose_6
        self.setPanose7            = args.panose_7
        self.setPanose8            = args.panose_8
        self.setPanose9            = args.panose_9
        self.modifyPanose          = (args.panose_0 is not None or
                                      args.panose_1 is not None or
                                      args.panose_2 is not None or
                                      args.panose_3 is not None or
                                      args.panose_4 is not None or
                                      args.panose_5 is not None or
                                      args.panose_6 is not None or
                                      args.panose_7 is not None or
                                      args.panose_8 is not None or
                                      args.panose_9 is not None)
        self.setWeightName         = args.weight_name
        self.setPSFontName         = args.ps_font_name
        self.setFullName           = args.full_name
        self.setFamilyName         = args.family_name
        self.setOS2Weight          = args.os2_weight

        self.italicizeAngle           = args.italicize_angle
        self.italicizeCenterY         = args.italicize_center
        self.italicizeSlant           = args.italicize_slant
        self.italicAngle              = args.italic_angle

        self.copyright               = args.copyright
        self.noSfntNames             = args.no_sfnt_names
        self.subfamily               = args.subfamily
        self.uniqueId                = args.unique_id

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

    def fixFilenames(self):
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
            self.traceGlyph(glyph, char)
            glyph.addExtrema()
            glyph.simplify()

    def traceGlyph(self, glyph, bdfChar):
        yOffset = bdfChar.boundingBoxYOffset
        if yOffset == None:
            yOffset = self.bdf.boundingBoxYOffset
        if yOffset == None:
            raise Exception("cannot find bounding box y offset: %s" % glyph)
        xOffset = bdfChar.boundingBoxXOffset
        if xOffset == None:
            xOffset = self.bdf.boundingBoxXOffset
        if xOffset == None:
            raise Exception("cannot find bounding box x offset: %s" % glyph)
        height = bdfChar.boundingBoxY
        if height == None:
            height = self.bdf.boundingBoxY
        if height == None:
            raise Exception("cannot find bounding box height: %s" % glyph)
        width = bdfChar.boundingBoxX
        if width == None:
            width = self.bdf.boundingBoxX
        if width == None:
            raise Exception("cannot find bounding box width: %s" % glyph)

        y = yOffset + height
        pixY = 1.0 * self.font.em / self.bdf.getPixelSize()
        pixX = 1.0 * self.font.em / self.bdf.getPixelSize() * self.bdf.aspectRatioXtoY() * self.aspectRatio
        deltaX = pixX * (1.0 - self.dotWidth) / 2
        deltaY = pixY * (1.0 - self.dotHeight) / 2

        italicizeSlant = 0.0
        italicizeAngle = 0.0
        if self.italicizeAngle is not None:
            italicizeAngle = self.italicizeAngle
            italicizeSlant = math.tan(self.italicizeAngle * math.pi / 180) * pixY / pixX
            self.italicizeSlant = italicizeSlant
        elif self.italicizeSlant is not None:
            italicizeSlant = self.italicizeSlant
            italicizeAngle = math.atan(self.italicizeSlant * pixX / pixY) * 180 / math.pi
            self.italicizeAngle = italicizeAngle
            print("italicizeAngle = %f" % self.italicizeAngle)
        italicizeCenterY = self.italicizeCenterY if self.italicizeCenterY is not None else 0

        for line in bdfChar.bitmapData:
            y = y - 1
            if self.circularDots:
                x = xOffset
                for pixel in line:
                    if pixel == '1':
                        xh = round(pixX * self.dotWidth * 0.5)
                        yh = round(pixY * self.dotHeight * 0.5)
                        r = max(xh, yh)
                        xc = round(pixX * (x + 0.5 - italicizeSlant * (y - italicizeCenterY)))
                        yc = round(pixY * (y + 0.5))
                        x1 = xc - r
                        x2 = xc + r
                        y1 = yc - r
                        y2 = yc + r
                        xcp = round(pixX * self.dotWidth * 0.5 * THAT_CIRCLE_BEZIER_CONSTANT)
                        ycp = round(pixY * self.dotHeight * 0.5 * THAT_CIRCLE_BEZIER_CONSTANT)
                        contour = fontforge.contour();
                        contour.moveTo(xc, y1)
                        contour.cubicTo((xc + xcp, y1), (x2, yc - ycp), (x2, yc))
                        contour.cubicTo((x2, yc + ycp), (xc + xcp, y2), (xc, y2))
                        contour.cubicTo((xc - xcp, y2), (x1, yc + ycp), (x1, yc))
                        contour.cubicTo((x1, yc - ycp), (xc - xcp, y1), (xc, y1))
                        contour.closed = True
                        glyph.layers['Fore'] += contour
                    x = x + 1
            elif self.dotWidth < 1:
                x = xOffset
                for pixel in line:
                    if pixel == '1':
                        xx = x - italicizeSlant * (y - italicizeCenterY)
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
                pixelBlocks = []
                pixelBlock = None
                x = xOffset
                bottom = 0
                top = 1
                for pixel in line:
                    if pixel == '1':
                        if pixelBlock == None:
                            pixelBlock = [x, x]
                            pixelBlocks.append(pixelBlock)
                        else:
                            pixelBlock[1] = x;
                    else:
                        pixelBlock = None
                    x = x + 1
                for pixelBlock in pixelBlocks:
                    xa = pixelBlock[0] - italicizeSlant * (y - italicizeCenterY)
                    xb = pixelBlock[1] - italicizeSlant * (y - italicizeCenterY)
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
        glyph.width = int(round(bdfChar.dwidthX() * pixX))

    # def f800(self):
    #     """add private use characters for testing varying simulated "scan line" heights."""
    #     print("f800()")
    #     for codepoint in range(0xf800,0xf900):
    #         milliems = 1 + codepoint - 0xf800
    #         if codepoint not in self.font:
    #             continue
    #         glyph = self.font[codepoint]
    #         for y in [250, 375, 500, 625, 750, 875]:
    #             contour = fontforge.contour()
    #             contour.moveTo(0, y)
    #             contour.lineTo(glyph.width, y)
    #             contour.lineTo(glyph.width, y - milliems)
    #             contour.lineTo(0, y - milliems)
    #             contour.closed = True
    #             glyph.layers['Fore'] += contour
