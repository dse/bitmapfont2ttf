from mybdf import MyBDF

import fontforge
import os
import re
import sys

MACSTYLE_BOLD      = 1 << 0
MACSTYLE_ITALIC    = 1 << 1
MACSTYLE_UNDERLINE = 1 << 2
MACSTYLE_OUTLINE   = 1 << 3
MACSTYLE_SHADOW    = 1 << 4
MACSTYLE_CONDENSED = 1 << 5
MACSTYLE_EXPANDED  = 1 << 6

# https://docs.microsoft.com/ja-jp/typography/opentype/spec/os2#fss
STYLEMAP_ITALIC           = 1 << 0
STYLEMAP_UNDERSCORE       = 1 << 1
STYLEMAP_NEGATIVE         = 1 << 2
STYLEMAP_OUTLINED         = 1 << 3
STYLEMAP_STRIKEOUT        = 1 << 4
STYLEMAP_BOLD             = 1 << 5
STYLEMAP_REGULAR          = 1 << 6
STYLEMAP_USE_TYPO_METRICS = 1 << 7
STYLEMAP_WWS              = 1 << 8
STYLEMAP_OBLIQUE          = 1 << 9

THAT_CIRCLE_BEZIER_CONSTANT = 0.5519150244935105707435627

class BitmapFont2TTF:
    def __init__(self, args):
        self.setArgs(args)
        self.fixFilenames()

    def bitmapfont2ttf(self):
        if (os.path.splitext(self.filename))[1].lower() != '.bdf':
            raise Exception("only bdf bitmap fonts are supported")
        self.bdf = MyBDF(self.filename)
        self.font = fontforge.font()
        self.font.importBitmaps(self.filename, True) # imports everything EXCEPT the bitmaps
        self.trace()
        if self.monospace:
            self.fixForMonospaceDetection()
        if self.bdfAscentDescent:
            ascentPx = self.bdf.ascentPx()
            descentPx = self.bdf.descentPx()
            pixelSize = self.bdf.getPixelSize()
            emUnitsPerPixel = 1.0 * self.font.em / (ascentPx + descentPx)
            self.font.ascent  = int(round(ascentPx * emUnitsPerPixel))
            self.font.descent = int(round(descentPx * emUnitsPerPixel))
        if self.removeLineGap:
            self.font.hhea_linegap    = 0
            self.font.os2_typolinegap = 0
            self.font.vhea_linegap    = 0
        self.save()

    # make sure all glyphs are the same width.
    # otherwise font may not be detected as monospace.
    def fixForMonospaceDetection(self):
        widthCounts = {}
        glyphCount = 0
        for glyph in self.font.glyphs():
            glyphCount += 1
            if glyph.width not in widthCounts:
                widthCounts[glyph.width] = 0
            widthCounts[glyph.width] += 1
        keys = list(widthCounts.keys())
        if len(keys) == 1:
            # already will be detected as monospace
            return
        keys.sort(key = lambda width: widthCounts[width], reverse = True)
        width = keys[0]
        for glyph in self.font.glyphs():
            glyph.width = width

    def save(self):
        for dest in self.destfilenames:
            if (os.path.splitext(self.filename))[1].lower() == '.sfd':
                self.font.save(dest)
            else:
                self.font.generate(dest)

    def setArgs(self, args):
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

        # self.newAscent             = args.new_ascent
        # self.newDescent            = args.new_descent
        # self.newPixelSize          = args.new_pixel_size
        # self.italicAngle           = args.italic_angle
        # self.fontName              = args.font_name
        # self.familyName            = args.family_name
        # self.copyright             = args.copyright
        # self.comment               = args.comment
        # self.fullName              = args.full_name
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

###############################################################################
    def bitmapfont2ttfOld(self):
        self.loadBDF()
        self.font = fontforge.font()
        if self.guessType1:
            self.setNewMetrics()
            self.setInitialAscentDescent()
        if self.guessType2:
            self.computeAscentDescentFromBDF()
            if self.lineGap != None:
                self.doFixLineGap()
            if self.fixAscentDescent:
                self.doFixAscentDescent()
        self.font.importBitmaps(self.filename, True) # imports everything EXCEPT the bitmaps
        if self.guessType1:
            self.font.os2_vendor = 'PfEd'
            self.font.encoding = 'iso10646-1'
            self.setIsItalicAttribute()
            self.setIsBoldAttribute()
            self.updateItalicAngle()
            self.doFixWeight()
            self.updateStyleMapFlags()
            self.updateMacStyleFlags()
            self.setFontMetas()
        self.trace()
        if self.guessType2:
            if (self.monospace or ("SPACING" in self.bdf.properties and
                                   (self.bdf.properties["SPACING"] == "M" or
                                    self.bdf.properties["SPACING"] == "C"))):
                self.doFixForMonospace()
        if self.guessType1:
            if self.monospace:
                self.fixMonospace()
            self.doFixLineGap()
            self.doFixAscentDescent()
        if self.guessType2:
            self.setIsItalicAttribute()
            self.setIsBoldAttribute()
            if self.lineGap != None:
                self.doFixLineGap()
            if self.fixAscentDescent:
                self.doFixAscentDescent()
            if self.fixWeight:
                self.doFixWeight()
            if self.fixStyleMap:
                self.updateStyleMapFlags()
            if self.fixMacStyle:
                self.updateMacStyleFlags()
            if self.fixSlant:
                self.updateItalicAngle()
            self.setFontMetas()
        if self.guessType1 or self.guessType2:
            if self.panose2 != None:
                # weight
                print(self.font.os2_panose)
                panose = list(self.font.os2_panose)
                panose[2] = self.panose2
                self.font.os2_panose = tuple(panose)
                print(self.font.os2_panose)
            if self.os2Weight != None:
                self.font.os2_weight = self.os2Weight
        self.save()

    # LEGACY
    def setNewMetrics(self):
        if self.newPixelSize is None and self.newAscent is None and self.newDescent is None:
            return
        if self.newPixelSize != None:
            self.bdf.setPixelSize(self.newPixelSize)
        if self.newAscent != None:
            self.bdf.properties['ascent'] = newAscent
        if self.newDescent != None:
            self.bdf.properties['descent'] = newDescent
        emFloat = self.font.em * 1.0
        pixelSizeFloat = self.bdf.getPixelSize() * 1.0
        ascentEm  = emFloat / pixelSizeFloat * self.bdf.ascentPx()
        descentEm = emFloat / pixelSizeFloat * self.bdf.descentPx()
        fix       = emFloat - ascentEm + descentEm
        newAscent  = int(round(ascentEm + fix / 2.0))
        newDescent = self.font.em - newAscent
        self.font.ascent  = newAscent
        self.font.descent = newDescent

    # LEGACY
    # set ascent and descent from BDF data
    def setInitialAscentDescent(self):
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

    # typically these are guessed.
    def setFontMetas(self):
        if self.copyright != None:
            self.font.copyright = self.copyright
        if self.comment != None:
            self.font.comment = self.comment
        if self.fontName != None:
            self.font.fontname = self.fontName
        if self.familyName != None:
            self.font.familyname = self.familyName
        if self.fullName != None:
            self.font.fullname = self.fullName
        if self.version != None:
            self.font.version = self.version
        if self.weight != None:
            self.font.weight = self.weight

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
        for line in bdfChar.bitmapData:
            y = y - 1
            if self.circularDots:
                x = xOffset
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
                x = xOffset
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
        glyph.width = int(round(bdfChar.dwidthX() * pixX))

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

    # Set various ascent and descent metrics based on
    # main ascent and descent metrics.
    # Call this after setting self.font.ascent and
    # self.font.descent.
    def doFixAscentDescent(self):
        self.font.hhea_ascent_add     = 0
        self.font.hhea_descent_add    = 0
        self.font.os2_typoascent_add  = 0
        self.font.os2_typodescent_add = 0
        self.font.os2_winascent_add   = 0
        self.font.os2_windescent_add  = 0
        # self.font.ascent          = self.font.ascent
        # self.font.descent         = self.font.descent
        self.font.hhea_ascent     = self.font.ascent
        self.font.hhea_descent    = -self.font.descent
        self.font.os2_typoascent  = self.font.ascent
        self.font.os2_typodescent = -self.font.descent
        self.font.os2_winascent   = self.font.ascent
        self.font.os2_windescent  = self.font.descent

    # Standardize on Book/400 and Bold/700.
    def doFixWeight(self):
        if self.font.weight == 'Regular' or self.font.weight == 'Medium' or self.font.weight == 'Book':
            self.font.weight = 'Book'
            self.font.os2_weight = 400
        elif self.font.weight == 'Bold':
            self.font.weight = 'Bold'
            self.font.os2_weight = 700

    # Add isItalic and isBold attributes based on various
    # font attributes, convenience booleans used for setting
    # other flags.
    def setIsItalicAttribute(self):
        self.isItalic = (
            (self.italicAngle != None and self.italicAngle != 0) or
            re.search(r'\b(italic|oblique)\b', self.font.fontname, flags = re.IGNORECASE) or
            re.search(r'\b(italic|oblique)\b', self.font.fullname, flags = re.IGNORECASE) or
            (self.fontName   != None and re.search(r'\b(italic|oblique)\b', self.fontName,   flags = re.IGNORECASE)) or
            (self.familyName != None and re.search(r'\b(italic|oblique)\b', self.familyName, flags = re.IGNORECASE))
        )
    def setIsBoldAttribute(self):
        self.isBold = self.font.weight == 'Bold'

    # Update the stylemap flags.
    def updateStyleMapFlags(self):
        bits = 0
        if self.isItalic:
            bits |= STYLEMAP_ITALIC
        if self.isBold:
            bits |= STYLEMAP_BOLD
        if not self.isItalic and not self.isBold:
            bits |= STYLEMAP_REGULAR
        self.font.os2_stylemap = bits

    # Update the macstyle flags.
    def updateMacStyleFlags(self):
        bits = 0
        if self.isItalic:
            bits |= MACSTYLE_ITALIC
        if self.isBold:
            bits |= MACSTYLE_BOLD
        self.font.macstyle = bits

    # Update the italic angle.
    def updateItalicAngle(self):
        if self.isItalic:
            if self.italicAngle != None:
                self.font.italicangle = self.italicAngle
            else:
                self.font.italicangle = 15 # arbitrary
        else:
            self.font.italicangle = 0
