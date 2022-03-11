class BDFChar:
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
