from mybdf import MyBDF

import fontforge
import os
import re
import sys

class BitmapFont2TTF:
    def __init__(self, args):
        self.setArgs(args)
        self.fixFilenames()

    def setArgs(self, args):
        self.args = args
        self.filename = args.filename
        self.destfilenames = args.destfilenames

        self.nearestMultipleOfFour = False
        self.nextMultipleOfFour = False
        self.verbose = 0
        self.dotWidth = 1
        self.dotHeight = 1

        if args.nearest_multiple_of_four:
            self.nearestMultipleOfFour = args.nearest_multiple_of_four
        if args.next_multiple_of_four:
            self.nextMultipleOfFour = args.next_multiple_of_four
        if args.verbose:
            self.verbose = args.verbose
        if args.dot_width:
            self.dotWidth = args.dot_width
        if args.dot_height:
            self.dotHeight = args.dot_height

    def fixFilenames(self):
        if self.filename == os.path.basename(self.filename):
            # Work around an issue where importBitmaps segfaults if you only
            # specify a filename 'foo.pcf'.  Yes, './foo.pcf' works pefectly
            # fine whereas 'foo.pcf' does not.
            self.filename = os.path.join('.', self.filename)

        if self.destfilenames == None or len(self.destfilenames) == 0:
            (rootdestfilename, junk) = os.path.splitext(self.filename)
            self.destfilenames = [rootdestfilename + '.ttf']

    def traceGlyph(self, glyph, bdfChar):
        y = bdfChar.boundingBoxYOffset + bdfChar.boundingBoxY
        pixY = 1.0 * self.font.em / self.bdf.getPixelSize()
        pixX = 1.0 * self.font.em / self.bdf.getPixelSize() * self.bdf.aspectRatioXtoY()
        for line in bdfChar.bitmapData:
            y = y - 1
            deltaX = pixX * (1.0 - self.dotWidth) / 2
            deltaY = pixY * (1.0 - self.dotHeight) / 2
            if self.dotWidth == 1:
                # Draw contiguous horizontal sequences of pixels.
                # This saves considerable disk space.
                pixelBlocks = []
                pixelBlock = None
                x = bdfChar.boundingBoxXOffset
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
                    contour = fontforge.contour()
                    contour.moveTo(round(x1), round(y1))
                    contour.lineTo(round(x1), round(y2))
                    contour.lineTo(round(x2), round(y2))
                    contour.lineTo(round(x2), round(y1))
                    contour.closed = True
                    glyph.layers['Fore'] += contour
            else:
                # Draw each individual pixel.
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
        glyph.width = int(round(bdfChar.dwidthX() * pixX))

    def trace(self):
        count = len(self.bdf.chars)
        index = 0
        for char in self.bdf.chars:
            index = index + 1
            sys.stderr.write('  %d/%d glyphs...\r' % (index, count))
            encoding = char.encoding if char.encoding else -1
            try:
                glyph = self.font.createChar(encoding, char.name)
            except:
                sys.stderr.write('\nencoding %s; name %s\n' % (encoding, char.name))
                raise
            self.traceGlyph(glyph, char)
            glyph.addExtrema()
            glyph.simplify()
        sys.stderr.write('  %d/%d glyphs done!\n' % (count, count))

    def loadBDF(self):
        if not re.search(r'\.bdf$', self.filename):
            raise Exception("only bdfs are supported")
        self.bdf = MyBDF(self.filename)

    def setPropertiesFromBDF(self):
        self.isMonospace = self.bdf.properties["spacing"] == 'M' or self.bdf.properties["spacing"] == 'C'
        self.pixelSize = self.bdf.properties["pixelSize"]
        print("self.pixelSize is %s" % self.pixelSize)
        if not self.pixelSize:
            if self.bdf.boundingBoxY:
                self.pixelSize = self.bdf.boundingBoxY

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
            if self.args.italic_angle != None:
                self.font.italicangle = self.args.italic_angle

    def save(self):
        for dest in self.destfilenames:
            if re.search(r'\.sfd$', dest):
                self.font.save(dest)
            else:
                self.font.generate(dest)
            sys.stderr.write("bitmapfont2ttf: %s: Wrote %s\n" % (self.args.full_name, dest))

    def setSwidth(self):
        if self.isMonospace:
            self.swidthPx = self.bdf.boundingBoxX
            self.swidthEm = 1.0 * self.swidthPx / self.pixelSize
        else:
            self.swidthPx = None
            self.swidthEm = None

    def setInitialAscentDescent(self):
        self.descentPx = self.bdf.descentPx()
        self.ascentPx  = self.bdf.ascentPx()
        print("ascent %s px; descent %s px" % (self.ascentPx, self.descentPx))
        self.descentEm = 1.0 * self.descentPx / self.pixelSize
        self.ascentEm  = 1.0 * self.ascentPx  / self.pixelSize
        print("ascent %s em; descent %s em" % (self.ascentEm, self.descentEm))
        ascent  = round(self.ascentEm * self.font.em)
        descent = round(self.descentEm * self.font.em)
        print("ascent %s; descent %s" % (ascent, descent))
        self.font.ascent  = ascent
        self.font.descent = descent

    def setItalic(self):
        self.isItalic = (re.search(r'\b(italic|oblique)\b', self.font.fontname, flags = re.IGNORECASE) or
                         re.search(r'\b(italic|oblique)\b', self.font.fullname, flags = re.IGNORECASE) or
                         (self.args.font_name   != None and re.search(r'\b(italic|oblique)\b', self.args.font_name,   flags = re.IGNORECASE)) or
                         (self.args.family_name != None and re.search(r'\b(italic|oblique)\b', self.args.family_name, flags = re.IGNORECASE)))
        if self.isItalic:
            self.font.italicangle = 15
        else:
            self.font.italicangle = 0

    def setWeight(self):
        if self.font.weight == 'Regular' or self.font.weight == 'Medium' or self.font.weight == 'Book':
            self.font.weight = 'Book'
            self.font.os2_weight = 400
            if self.isItalic:
                self.font.os2_stylemap |= 0x0201
                self.font.macstyle     |= 0x0002
            else:
                self.font.os2_stylemap |= 0x0040
                self.font.macstyle     |= 0x0000
        elif self.font.weight == 'Bold':
            self.font.weight = 'Bold'
            self.font.os2_weight = 700
            if self.isItalic:
                self.font.os2_stylemap |= 0x0221
                self.font.macstyle     |= 0x0003
            else:
                self.font.os2_stylemap |= 0x0020
                self.font.macstyle     |= 0x0001

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

    def bitmapfont2ttf(self):
        self.loadBDF()
        if self.args.nearest_multiple_of_four:
            self.bdf.alterAscentDescentMultipleFour('nearest')
        elif self.args.next_multiple_of_four:
            self.bdf.alterAscentDescentMultipleFour('next')
        self.setPropertiesFromBDF()
        self.font = fontforge.font()
        self.setSwidth()
        self.setInitialAscentDescent()
        self.font.importBitmaps(self.filename, True);
        self.font.os2_vendor = 'PfEd'
        self.font.encoding = 'iso10646-1'
        self.setItalic()
        self.setWeight()
        self.setFontMetas()
        self.trace()
        self.setFinalMetrics()
        self.save()
