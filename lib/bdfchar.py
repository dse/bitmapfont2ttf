class BDFChar:
    def __init__(self, name = None, font = None):
        self.name = name
        self.font = font
        self.encoding = None
        self.nonStandardEncoding = None
        self.hasBoundingBox = False
        self.boundingBoxX = None
        self.boundingBoxY = None
        self.boundingBoxXOffset = None
        self.boundingBoxYOffset = None
        self.scalableWidthX = None
        self.scalableWidthY = None
        self.devicePixelWidthX = None
        self.devicePixelWidthY = None
        self.scalableWidthWritingMode1X = None
        self.scalableWidthWritingMode1Y = None
        self.devicePixelWidthWritingMode1X = None
        self.devicePixelWidthWritingMode1Y = None

    def getSwidthX(self):
        if self.scalableWidthX != None:
            return self.scalableWidthX
        if self.devicePixelWidthX != None:
            return self.devicePixelWidthX / 72000.0 * self.getResolutionX() * self.font.getPointSize()
        return self.font.getSwidthX()

    def getSwidthY(self):
        return 0

    def getDwidthX(self):
        if self.devicePixelWidthX != None:
            return self.devicePixelWidthX
        if self.scalableWidthX != None:
            return int(round(self.scalableWidthX * 72000.0 / self.getResolutionX() / self.font.getPointSize()))
        return self.font.getDwidthX()

    def getDwidthY(self):
        return 0

    def getResolutionX(self):
        return self.font.getResolutionX()

    def getResolutionY(self):
        return self.font.getResolutionY()

    # row =  0 for pixel row just above baseline
    # row = -1 for pixel row just below baseline
    def pixelCountByRow(self, row):
        row = int(round(row))
        yTop = self.boundingBoxYOffset + self.boundingBoxY - 1
        rowIndex = yTop - row   # into bitmapData
        if rowIndex < 0 or rowIndex >= len(self.bitmapData):
            return 0
        return self.bitmapData[rowIndex].count('1')

    def setBoundingBox(self, x, y, xOfs, yOfs):
        self.hasBoundingBox = True
        self.boundingBoxX       = int(x)          # integer pixel values, offsets relative to origin
        self.boundingBoxY       = int(y)
        self.boundingBoxXOffset = int(xOfs)
        self.boundingBoxYOffset = int(yOfs)

    def setSwidth(self, x, y):
        self.scalableWidthX = float(x)
        self.scalableWidthY = float(y)
        if self.scalableWidthY != 0.0:
            raise Exception("SWIDTH with non-zero Y coordinate not supported")

    def setDwidth(self, x, y):
        self.devicePixelWidthX = float(x)
        self.devicePixelWidthY = float(y)
        if self.devicePixelWidthY != 0.0:
            raise Exception("DWIDTH with non-zero Y coordinate not supported")

    def setEncoding(self, encoding, nonStandardEncoding):
        self.encoding = int(encoding)
        if self.encoding == -1:
            self.encoding = None
        self.nonStandardEncoding = (None if nonStandardEncoding is None
                                    else int(nonStandardEncoding))

    def appendBitmapData(self, data):
        self.bitmapData.append(str(data).strip())

    def endBitmap(self):
        numBits = max(len(s) * 4 for s in self.bitmapData)
        self.bitmapData = [bin(int(s, 16))[2:].rjust(numBits, '0')
                           for s in self.bitmapData]

    def __str__(self):
        result = "<BDFChar"
        if self.name != None:
            result += (" %s" % self.name)
        if self.encoding != None:
            result += (" @%d" % self.encoding)
        if self.nonStandardEncoding != None:
            result += (" @[%d]" % self.nonStandardEncoding)
        if self.hasBoundingBox:
            result += (" [%g, %g offset %g, %g]" % (
                self.boundingBoxX, self.boundingBoxY,
                self.boundingBoxXOffset, self.boundingBoxYOffset
            ))
        result += ">"
        return result
