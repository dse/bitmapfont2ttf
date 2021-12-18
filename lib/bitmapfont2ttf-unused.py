class BitmapFont2TTF:
    # NOT IN USE
    def fixMissingGlyphs(self):
        sys.stderr.write('>>>>>>> fixMissingGlyphs() NOT IN USE <<<<<<<\n')
        return

        self.fixMissingGlyph(39, 8217) # U+0027 APOSTROPHE;   U+2019 RIGHT SINGLE QUOTATION MARK
        self.fixMissingGlyph(45, 8722) # U+002D HYPHEN-MINUS; U+2212 MINUS SIGN
        self.fixMissingGlyph(96, 8216) # U+0060 GRAVE;        U+2018 LEFT SINGLE QUOTATION MARK

    # NOT IN USE
    def fixMissingGlyph(self, destUni, sourceUni):
        sys.stderr.write('>>>>>>> fixMissingGlyph() NOT IN USE <<<<<<<\n')
        return

        hasSource = False
        hasDest = False
        sourceGlyph = None
        destGlyph = None
        self.font.selection.select(('unicode', None), sourceUni)
        for glyph in self.font.selection.byGlyphs:
            sourceGlyph = glyph
            hasSource = True
            break
        self.font.selection.select(('unicode', None), destUni)
        for glyph in self.font.selection.byGlyphs:
            hasDest = True
            break
        if hasSource and not hasDest:
            destGlyph = self.font.createChar(destUni)
            self.font.selection.select(sourceGlyph)
            self.font.copy()
            self.font.selection.select(destGlyph)
            self.font.paste()

    # NOT IN USE
    def autoTrace(self):
        sys.stderr.write('>>>>>>> autoTrace() NOT IN USE <<<<<<<\n')
        return

        glyphCount = self.getGlyphCount()

        sys.stderr.write("bitmapfont2ttf: %s: tracing %d glyphs...\n" % (self.args.full_name, glyphCount))

        glyphIndex = 0
        for glyph in self.font.glyphs():
            glyphIndex += 1
            if self.verbose >= 2:
                sys.stderr.write("bitmapfont2ttf: %s: [%d/%d] %s\r" % (self.args.full_name, glyphIndex, glyphCount, glyph))
            elif self.verbose >= 1:
                sys.stderr.write("bitmapfont2ttf: %s: [%d/%d]\r" % (self.args.full_name, glyphIndex, glyphCount))
            glyph.autoTrace()
            glyph.addExtrema()
            glyph.simplify()

            # this is not true for lucida typewriter fonts
            # if glyph.swidth:
            #     glyph.width = glyph.swidth
            # elif self.swidth:
            #     glyph.width = self.swidth

            bdfChar = None
            if glyph.encoding in self.bdf.charsByEncoding:
                bdfChar = self.bdf.charsByEncoding[glyph.encoding]

            oldWidth = glyph.width
            newWidth = None
            if bdfChar:
                if bdfChar.devicePixelWidthX:
                    newWidth = round(
                        self.bdf.pixelsToScalableX(bdfChar.devicePixelWidthX) / 1000.0 * self.font.em
                    )
                elif bdfChar.scalableWidthX:
                    newWidth = round(
                        bdfChar.scalableWidthX / 1000.0 * self.font.em
                    )

            if newWidth != None and abs(newWidth - oldWidth) > 1:
                glyph.width = newWidth

    # NOT IN USE
    def adjustGlyphSizes(self):
        sys.stderr.write('>>>>>>> adjustGlyphSizes() NOT IN USE <<<<<<<\n')
        return

        if self.bdf.fillBoundingBoxWidth:
            for glyph in self.font.glyphs():
                oldWidth = glyph.width
                if self.bdf.properties["resolutionX"] and self.bdf.properties["resolutionY"]:
                    newWidth = 1.0 * self.font.em / self.bdf.properties["pixelSize"] * self.bdf.boundingBoxX * self.bdf.aspectRatioXtoY()
                else:
                    newWidth = 1.0 * self.font.em / self.bdf.properties["pixelSize"] * self.bdf.boundingBoxX
                    raise Exception("neither resolutionX nor resolutionY defined")
                print("oldWidth = %f; newWidth = %f" % (oldWidth, newWidth))
                glyph.transform(psMat.translate((newWidth - oldWidth) / 2, 0))
                glyph.width = newWidth
        if self.finalPixelSize != self.pixelSize:
            sys.stderr.write("bitmapfont2ttf: %s: adjusting pixel size from %d to %d\n" % (self.args.full_name, self.pixelSize, self.finalPixelSize))
            for glyph in self.font.glyphs():
                glyph.transform(psMat.scale(1.0 * self.pixelSize / self.finalPixelSize))

    # NOT IN USE
    def getGlyphCount(self):
        sys.stderr.write('>>>>>>> getGlyphCount() NOT IN USE <<<<<<<\n')
        return

        glyphCount = 0
        for glyph in self.font.glyphs():
            glyphCount += 1
        return glyphCount

    # NOT IN USE
    def useFinalPixelSize(self):
        sys.stderr.write('>>>>>>> useFinalPixelSize() NOT IN USE <<<<<<<\n')
        return

        if self.finalPixelSize != self.pixelSize:
            if self.finalPixelSize > self.pixelSize:
                diff = self.finalPixelSize - self.pixelSize # 1, 2, 3, ...
                diff1 = int(diff) / 2 # 1 => 0, 2 => 1, 3 => 1, 4 => 2, ...
                diff2 = diff - diff1  # 1 => 1, 2 => 1, 3 => 2, 4 => 2, ...
                self.ascentPx += diff2
                self.descentPx += diff1
            else:
                diff = self.pixelSize - self.finalPixelSize # 1, 2, 3, ...
                diff1 = int(diff) / 2 # 1 => 0, 2 => 1, 3 => 1, 4 => 2, ...
                diff2 = diff - diff1  # 1 => 1, 2 => 1, 3 => 2, 4 => 2, ...
                self.ascentPx -= diff2
                self.descentPx -= diff1
            em = self.font.em
            self.font.ascent  = int(0.5 + 1.0 * em * self.ascentPx  / self.finalPixelSize)
            self.font.descent = int(0.5 + 1.0 * em * self.descentPx / self.finalPixelSize)


    # def traceGlyph(self, glyph):
    #     if not(glyph.encoding in self.bdf.charsByEncoding):
    #         return
    #     bdfChar = self.bdf.charsByEncoding[glyph.encoding]
    #     y = bdfChar.boundingBoxYOffset + bdfChar.boundingBoxY

    #     pixY = 1000.0 / self.bdf.properties["pixelSize"]
    #     pixX = 1000.0 / self.bdf.properties["pixelSize"] * self.bdf.aspectRatioXtoY()

    #     for line in bdfChar.bitmapData:
    #         y = y - 1
    #         x = bdfChar.boundingBoxXOffset
    #         deltaX = pixX * (1 - self.dotWidth) / 2
    #         deltaY = pixY * (1 - self.dotHeight) / 2
    #         for pixel in line:
    #             if pixel == '1':
    #                 x1 = pixX * x       + deltaX
    #                 x2 = pixX * (x + 1) - deltaX
    #                 y1 = pixY * y       + deltaY
    #                 y2 = pixY * (y + 1) - deltaY
    #                 contour = fontforge.contour()
    #                 contour.moveTo(x1, y1)
    #                 contour.lineTo(x1, y2)
    #                 contour.lineTo(x2, y2)
    #                 contour.lineTo(x2, y1)
    #                 contour.closed = True
    #                 glyph.layers['Fore'] += contour
    #             x = x + 1
