import re, fontforge

from bdf_utils import binDataToHexData, hexDataToBinData

unknown_charname_counter = 0

BITMAP_PIXEL_LINE_TYPE_NORMAL = 0
BITMAP_PIXEL_LINE_TYPE_BASELINE = 1
BITMAP_PIXEL_LINE_TYPE_CAP_HEIGHT = 2

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
        self.bitmapDataCapHeightIdx = None
        self.bitmapDataBaselineIdx = None
        self.bitmapDataHexLineCount = 0
        self.bitmapDataPixelLineCount = 0

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
        self.scalableWidthX = int(x)
        self.scalableWidthY = int(y)
        if self.scalableWidthY != 0.0:
            raise Exception("SWIDTH with non-zero Y coordinate not supported")

    def setDwidth(self, x, y):
        self.devicePixelWidthX = int(x)
        self.devicePixelWidthY = int(y)
        if self.devicePixelWidthY != 0.0:
            raise Exception("DWIDTH with non-zero Y coordinate not supported")

    def setEncoding(self, encoding, nonStandardEncoding):
        self.encoding = int(encoding)
        if self.encoding == -1:
            self.encoding = None
        self.nonStandardEncoding = (None if nonStandardEncoding is None
                                    else int(nonStandardEncoding))

    def appendBitmapData(self, data):
        self.bitmapDataHexLineCount += 1
        self.bitmapData.append(str(data).strip())

    def startBitmap(self):
        self.bitmapData = []
        self.bitmapDataHexLineCount = 0
        self.bitmapDataPixelLineCount = 0
        self.bitmapDataCapHeightIdx = None
        self.bitmapDataBaselineIdx = None

    def endBitmap(self):
        self.bitmapData = [s.upper() + "0" * ((2 - len(s) % 2) % 2) for s in self.bitmapData]
        maxlen = max([len(s) for s in self.bitmapData])
        self.bitmapData = [s + "0" * (maxlen - len(s)) for s in self.bitmapData]
        if self.bitmapDataHexLineCount == 0:
            self.boundingBoxY = len(self.bitmapData)
            if self.bitmapDataBaselineIdx is not None:
                self.boundingBoxYOffset = self.bitmapDataBaselineIdx - len(self.bitmapData) + 1
            else:
                self.boundingBoxYOffset = 0

    def appendBitmapPixelData(self, start, binData):
        self.bitmapDataPixelLineCount += 1
        if start == '^':
            lineType = BITMAP_PIXEL_LINE_TYPE_CAP_HEIGHT
        elif start == '+':
            lineType = BITMAP_PIXEL_LINE_TYPE_BASELINE
        else:
            lineType = BITMAP_PIXEL_LINE_TYPE_NORMAL
        if lineType == BITMAP_PIXEL_LINE_TYPE_CAP_HEIGHT:
            self.bitmapDataCapHeightIdx = len(self.bitmapData)
        elif lineType == BITMAP_PIXEL_LINE_TYPE_BASELINE:
            self.bitmapDataBaselineIdx = len(self.bitmapData)
        self.bitmapData.append(binDataToHexData(binData))

    def __str__(self):
        string = ""
        string += self.getStartCharLine()
        string += self.getEncodingLine()
        string += self.getBoundingBoxLine()
        string += self.getDwidthLine()
        string += self.getSwidthLine()
        if len(self.bitmapData):
            string += "BITMAP\n"
            string += "\n".join(self.bitmapData) + "\n"
        string += "ENDCHAR\n"
        return string

    def getStartCharLine(self):
        if self.encoding is None or self.encoding < 0:
            if self.name is None:
                return "STARTCHAR %s\n" % generateNewUnknownCharname()
            else:
                return "STARTCHAR %s\n" % self.name
        else:
            if self.name is not None:
                return "STARTCHAR %s\n" % self.name
            else:
                return "STARTCHAR %s\n" % fontforge.nameFromUnicode(self.encoding)

    def getEncodingLine(self):
        if self.nonStandardEncoding is None:
            if self.encoding is None:
                if self.name is not None:
                    encoding = fontforge.unicodeFromName(self.name)
                    return "ENCODING %d\n" % encoding
                return "ENCODING -1\n"
            return "ENCODING %d\n" % self.encoding
        return "ENCODING %d %d\n" % self.encoding, self.nonStandardEncoding

    def getBoundingBoxLine(self):
        [x, y, xOffset, yOffset] = [self.getBoundingBoxX(),
                                    self.getBoundingBoxY(),
                                    self.getBoundingBoxXOffset(),
                                    self.getBoundingBoxYOffset()]
        if x is None or y is None or xOffset is None or yOffset is None:
            return ""
        return "BBX %d %d %d %d\n" % (x, y, xOffset, yOffset)

    def getDwidthLine(self):
        if self.devicePixelWidthX is None:
            return ""
        return "DWIDTH %d 0\n" % self.devicePixelWidthX

    def getSwidthLine(self):
        if self.scalableWidthX is None:
            return ""
        return "SWIDTH %d 0\n" % self.scalableWidthX

    def getBoundingBoxX(self):
        if self.boundingBoxX is not None:
            return self.boundingBoxX
        return self.font.boundingBoxX

    def getBoundingBoxY(self):
        if self.boundingBoxY is not None:
            return self.boundingBoxY
        return self.font.boundingBoxY

    def getBoundingBoxXOffset(self):
        if self.boundingBoxXOffset is not None:
            return self.boundingBoxXOffset
        return self.font.boundingBoxXOffset

    def getBoundingBoxYOffset(self):
        if self.boundingBoxYOffset is not None:
            return self.boundingBoxYOffset
        return self.font.boundingBoxYOffset

def generateNewUnknownCharName():
    unknown_charname_counter += 1
    return "unknown%d" % unknown_charname_counter
