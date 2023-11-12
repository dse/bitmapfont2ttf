from mybdf import MyBDF

import fontforge
import os
import re
import sys

MACSTYLE_BOLD    = 0x01
MACSTYLE_ITALIC  = 0x02

# https://docs.microsoft.com/ja-jp/typography/opentype/spec/os2#fss
STYLEMAP_ITALIC  = 0x01
STYLEMAP_BOLD    = 0x20
STYLEMAP_REGULAR = 0x40

THAT_CIRCLE_BEZIER_CONSTANT = 0.5519150244935105707435627

class BitmapFont2TTF:
    def __init__(self, args):
        self.setArgs(args)
        self.fixFilenames()

    def setArgs(self, args):
        self.args                  = args
        self.filename              = args.filename
        self.destfilenames         = args.destfilenames
        self.monospaceConfidence   = 75
        self.dotWidth              = args.dot_width
        self.dotHeight             = args.dot_height
        self.newAscent             = args.new_ascent
        self.newDescent            = args.new_descent
        self.resX                  = args.res_x # default 96
        self.resY                  = args.res_y # default 96

    def fixFilenames(self):
        if self.filename == os.path.basename(self.filename):
            # Work around an issue where importBitmaps segfaults if you only
            # specify a filename 'foo.pcf'.  Yes, './foo.pcf' works pefectly
            # fine whereas 'foo.pcf' does not.
            self.filename = os.path.join('.', self.filename)
        if self.destfilenames == None or len(self.destfilenames) == 0:
            (rootdestfilename, junk) = os.path.splitext(self.filename)
            self.destfilenames = [rootdestfilename + '.ttf']

    def loadBDF(self):
        if not re.search(r'\.bdf$', self.filename):
            raise Exception("only bdfs are supported")
        self.bdf = MyBDF(self.filename)

    def setPropertiesFromBDF(self):
        self.isMonospaceFlagged = self.bdf.properties["spacing"] == 'M' or self.bdf.properties["spacing"] == 'C'

    def setNewMetrics(self):
        if self.args.new_pixel_size is None and self.newAscent is None and self.newDescent is None:
            return
        if self.args.new_pixel_size != None:
            self.bdf.setPixelSize(self.args.new_pixel_size)
        if self.newAscent != None:
            self.bdf.properties['ascent'] = newAscent
        if self.newDescent != None:
            self.bdf.properties['descent'] = newDescent
        # sys.stderr.write("setNewMetrics: before: em = %d; ascent = %d; descent = %d\n" % (self.font.em, self.font.ascent, self.font.descent))
        emFloat = self.font.em * 1.0
        pixelSizeFloat = self.bdf.getPixelSize() * 1.0
        ascentEm  = emFloat / pixelSizeFloat * self.bdf.ascentPx()
        descentEm = emFloat / pixelSizeFloat * self.bdf.descentPx()
        fix       = emFloat - ascentEm + descentEm
        newAscent  = int(round(ascentEm + fix / 2.0))
        newDescent = self.font.em - newAscent
        self.font.ascent  = newAscent
        self.font.descent = newDescent
        # sys.stderr.write("setNewMetrics: after:  em = %d; ascent = %d; descent = %d\n" % (self.font.em, self.font.ascent, self.font.descent))

    def setSwidth(self):
        if self.isMonospaceFlagged:
            self.swidthPx = self.bdf.boundingBoxX
            self.swidthEm = 1.0 * self.swidthPx / self.bdf.getPixelSize()
        else:
            self.swidthPx = None
            self.swidthEm = None

    def setInitialAscentDescent(self):
        # sys.stderr.write("setInitialAscentDescent: before: em = %d; ascent = %d; descent = %d\n" % (self.font.em, self.font.ascent, self.font.descent))
        descentPx = self.bdf.descentPx()
        ascentPx  = self.bdf.ascentPx()
        total     = descentPx + ascentPx
        descentEm = 1.0 * descentPx / total
        ascentEm  = 1.0 * ascentPx  / total
        origFontAscent  = self.font.ascent
        origFontDescent = self.font.descent
        ascent  = int(round(ascentEm * self.font.em))
        descent = self.font.em - ascent # in case ascent + descent != 1000 due to rounding
        self.font.ascent  = ascent
        self.font.descent = descent
        # sys.stderr.write("setInitialAscentDescent: after:  em = %d; ascent = %d; descent = %d\n" % (self.font.em, self.font.ascent, self.font.descent))

    def setItalic(self):
        self.isItalic = (
            (self.args.italic_angle != None and self.args.italic_angle != 0) or
            re.search(r'\b(italic|oblique)\b', self.font.fontname, flags = re.IGNORECASE) or
            re.search(r'\b(italic|oblique)\b', self.font.fullname, flags = re.IGNORECASE) or
            (self.args.font_name   != None and re.search(r'\b(italic|oblique)\b', self.args.font_name,   flags = re.IGNORECASE)) or
            (self.args.family_name != None and re.search(r'\b(italic|oblique)\b', self.args.family_name, flags = re.IGNORECASE))
        )
        if self.isItalic:
            if self.args.italic_angle != None:
                self.font.italicangle = self.args.italic_angle
            else:
                self.font.italicangle = 15 # arbitrary
        else:
            self.font.italicangle = 0

    def setWeight(self):
        if self.font.weight == 'Regular' or self.font.weight == 'Medium' or self.font.weight == 'Book':
            self.isBold = False
            self.font.weight = 'Book'
            self.font.os2_weight = 400
        elif self.font.weight == 'Bold':
            self.isBold = True
            self.font.weight = 'Bold'
            self.font.os2_weight = 700

    def setStyleMapBits(self):
        bits = 0
        if self.isItalic:
            bits |= STYLEMAP_ITALIC
        if self.isBold:
            bits |= STYLEMAP_BOLD
        if not self.isItalic and not self.isBold:
            bits |= STYLEMAP_REGULAR
        self.font.os2_stylemap = bits

    def setMacStyleBits(self):
        bits = 0
        if self.isItalic:
            bits |= MACSTYLE_ITALIC
        if self.isBold:
            bits |= MACSTYLE_BOLD
        self.font.macstyle = bits

    def setFontMetas(self):
        if self.args != None:
            if self.args.copyright != None:
                self.font.copyright = self.args.copyright
            if self.args.comment != None:
                self.font.comment = self.args.comment
            if self.args.font_name != None:
                self.font.fontname = self.args.font_name
            if self.args.family_name != None:
                self.font.familyname = self.args.family_name
            if self.args.full_name != None:
                self.font.fullname = self.args.full_name
            if self.args.version != None:
                self.font.version = self.args.version
            if self.args.weight != None:
                self.font.weight = self.args.weight

    def traceGlyph(self, glyph, bdfChar):
        y = bdfChar.boundingBoxYOffset + bdfChar.boundingBoxY
        pixY = 1.0 * self.font.em / self.bdf.getPixelSize()
        pixX = 1.0 * self.font.em / self.bdf.getPixelSize() * self.bdf.aspectRatioXtoY() * self.args.aspect_ratio
        deltaX = pixX * (1.0 - self.dotWidth) / 2
        deltaY = pixY * (1.0 - self.dotHeight) / 2
        for line in bdfChar.bitmapData:
            y = y - 1
            if self.args.circular_dots:
                x = bdfChar.boundingBoxXOffset
                for pixel in line:
                    if pixel == '1':
                        xh = round(pixX * self.dotWidth * 0.5)
                        yh = round(pixY * self.dotHeight * 0.5)
                        r = max(xh, yh)
                        xc = round(pixX * (x + 0.5))
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
            elif self.dotWidth != 1:
                x = bdfChar.boundingBoxXOffset
                for pixel in line:
                    if pixel == '1':
                        x1 = pixX * x       + deltaX
                        x2 = pixX * (x + 1) - deltaX
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
                if self.args.bottom != None:
                    y1unit = self.args.bottom
                if self.args.top != None:
                    y2unit = self.args.top
                # Draw contiguous horizontal sequences of pixels.
                # This saves considerable disk space.
                pixelBlocks = []
                pixelBlock = None
                x = bdfChar.boundingBoxXOffset
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
                    xa = pixelBlock[0]
                    xb = pixelBlock[1]
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
        # sys.stderr.write("traceGlyph: before: glyph.width = %d\n" % glyph.width)
        glyph.width = int(round(bdfChar.dwidthX() * pixX))
        # sys.stderr.write("traceGlyph: after:  glyph.width = %d\n" % glyph.width)

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
        pixY = 1.0 * self.font.em / self.bdf.getPixelSize()
        pixX = 1.0 * self.font.em / self.bdf.getPixelSize() * self.bdf.aspectRatioXtoY()

    # If all glyph widths aren't the same, many Windows terminals and
    # other applications where you want monospace fonts won't show it
    # in menus.
    def fixMonospace(self, checkOnly=False):
        widthCounts = {}
        glyphsByWidth = {}
        totalGlyphCount = 0
        for glyph in self.font.glyphs():
            totalGlyphCount += 1
            width = glyph.width
            count = widthCounts.get(width)
            widthCounts[width] = count = 1 if count is None else count + 1
            glyphsByWidth[width] = [] if glyphsByWidth.get(width) is None else glyphsByWidth[width]
            glyphsByWidth[width].append(glyph)
        keys = list(widthCounts.keys())
        if len(keys) == 1:
            return True
        keys.sort(key = lambda width: widthCounts[width], reverse = True)
        if checkOnly:
            sys.stderr.write("-------------------------------------------------------------------------------\n")
            sys.stderr.write("WARNING: font will probably not be detected as monospace!\n")
            for width in keys[:5]:
                count = widthCounts[width]
                percentage = 100.0 * count / totalGlyphCount
                sys.stderr.write("%6d glyphs (%5.1f%%) have width %6.1f\n" % (count, percentage, width))
                if count < 20:
                    glyphs = glyphsByWidth[width]
                    for glyph in glyphs:
                        hexEncoding = ('U+%04X' % glyph.encoding) if glyph.encoding >= 0 else glyph.encoding
                        sys.stderr.write("        %-8s %s\n" % (hexEncoding, glyph.glyphname))
            sys.stderr.write("-------------------------------------------------------------------------------\n")
            return
        mostCommonWidth = keys[0]
        mostCommonWidthPercentage = 100.0 * widthCounts[mostCommonWidth] / totalGlyphCount
        if mostCommonWidthPercentage < float(self.monospaceConfidence):
            return
        for glyph in self.font.glyphs():
            debug = glyph.encoding == 0xab
            glyph.width = mostCommonWidth

    def setFinalMetrics(self):
        ascent  = self.font.ascent
        descent = self.font.descent
        self.font.hhea_ascent_add     = 0
        self.font.hhea_descent_add    = 0
        self.font.os2_typoascent_add  = 0
        self.font.os2_typodescent_add = 0
        self.font.os2_winascent_add   = 0
        self.font.os2_windescent_add  = 0
        self.font.ascent          = ascent
        self.font.descent         = descent
        self.font.hhea_ascent     = ascent
        self.font.hhea_descent    = -descent
        self.font.hhea_linegap    = 0
        self.font.os2_typoascent  = ascent
        self.font.os2_typodescent = -descent
        self.font.os2_typolinegap = 0
        self.font.os2_winascent   = ascent
        self.font.os2_windescent  = descent
        self.font.vhea_linegap    = 0
        if self.resX != None:
            self.font.xRes = self.resX
        if self.resY != None:
            self.font.yRes = self.resY

    def save(self):
        for dest in self.destfilenames:
            if re.search(r'\.sfd$', dest):
                self.font.save(dest)
            else:
                self.font.generate(dest)

    def checkMonospace(self):
        self.fixMonospace(checkOnly=True)

    def bitmapfont2ttf(self):
        self.loadBDF()
        if not self.args.no_guess:
            self.setPropertiesFromBDF()
        self.font = fontforge.font()
        if not self.args.no_guess:
            self.setNewMetrics()
            self.setSwidth()
            self.setInitialAscentDescent()
        self.font.importBitmaps(self.filename, True) # we do this to import everything BUT the bitmaps
        # sys.stderr.write("loadBDF: ascent = %d; descent = %d; em = %d; space width = %d; H width is %d\n" % (self.font.ascent,
        #                                                                                                      self.font.descent,
        #                                                                                                      self.font.em,
        #                                                                                                      self.font[32].width,
        #                                                                                                      self.font[72].width,
        #                                                                                                      ))
        if self.args.no_guess or self.args.autotrace:
            for glyph in self.font.glyphs():
                glyph.autoTrace()

        if not self.args.no_guess:
            self.font.os2_vendor = 'PfEd'
            self.font.encoding = 'iso10646-1'
            self.setItalic()
            self.setWeight()
            self.setStyleMapBits()
            self.setMacStyleBits()
            self.setFontMetas()

        if self.args.no_guess or self.args.no_trace or self.args.autotrace:
            pass
        else:
            self.trace()

        if not self.args.no_guess:
            if self.args.monospace:
                self.fixMonospace()
            self.setFinalMetrics()
            if self.args.panose2 != None:
                panose = list(self.font.os2_panose)
                panose[2] = self.args.panose2
                self.font.os2_panose = tuple(panose)
            if self.args.os2_weight != None:
                self.font.os2_weight = self.args.os2_weight
        if not self.args.no_save:
            self.save()
