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
