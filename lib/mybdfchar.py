class MyBDFChar:
    def __init__(self, name = None, font = None):
        self.name = name

        # ENCODING
        self.encoding = None
        self.nonStandardEncoding = None

        # BBX
        self.hasBoundingBox = False
        self.boundingBoxX = None
        self.boundingBoxY = None
        self.boundingBoxXOffset = None
        self.boundingBoxYOffset = None

        # SWIDTH
        self.scalableWidthX = None
        self.scalableWidthY = None

        # DWIDTH
        self.devicePixelWidthX = None
        self.devicePixelWidthY = None

        # SWIDTH1
        self.scalableWidthWritingMode1X = None
        self.scalableWidthWritingMode1Y = None

        # DWIDTH1
        self.devicePixelWidthWritingMode1X = None
        self.devicePixelWidthWritingMode1Y = None

    def __str__(self):
        result = "<MyBDFChar"
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

    def swidthX(self):
        if self.scalableWidthX != None:
            return self.scalableWidthX
        if self.devicePixelWidthX != None:
            return self.devicePixelWidthX / 72000.0 * self.resolutionX() * self.font.getPointSize()
        return self.font.swidthX()

    def swidthY(self):
        if self.scalableWidthY != None:
            return self.scalableWidthY
        if self.devicePixelWidthY != None:
            return self.devicePixelWidthY / 72000.0 * self.resolutionY() * self.font.getPointSize()
        return self.font.swidthY()

    def dwidthX(self):
        if self.devicePixelWidthX != None:
            return self.devicePixelWidthX
        if self.scalableWidthX != None:
            return int(round(self.scalableWidthX * 72000.0 / self.resolutionX() / self.font.getPointSize()))
        return self.font.dwidthX()

    def dwidthY(self):
        if self.devicePixelWidthY != None:
            return self.devicePixelWidthY
        if self.scalableWidthY != None:
            return int(round(self.scalableWidthY * 72000.0 / self.resolutionY() / self.font.getPointSize()))
        return self.font.dwidthY()

    def resolutionX(self):
        return self.font.resolutionX()

    def resolutionY(self):
        return self.font.resolutionY()
