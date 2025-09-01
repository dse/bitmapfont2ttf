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
