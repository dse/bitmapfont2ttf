import re
import sys
from bdfchar import BDFChar
from bdfpropertytypes import BDF_PROPERTY_TYPES

PARSE_STAGE_MAIN = 0
PARSE_STAGE_PROPERTIES = 1
PARSE_STAGE_CHARS = 2
PARSE_STAGE_CHAR = 3
PARSE_STAGE_BITMAP = 4
PARSE_STAGE_ENDFONT = 5

class BDF:
    def __init__(self, filename = None):
        self.bdfVersion = None
        self.contentVersion = None
        self.psFontName = None                                  # FONT (font.fontname)
        self.pointSize = None
        self.xRes = None
        self.yRes = None
        self.hasBoundingBox = False
        self.boundingBoxX = None
        self.boundingBoxY = None
        self.boundingBoxXOffset = None
        self.boundingBoxYOffset = None
        self.metricsSet = None
        self.scalableWidthX = None
        self.scalableWidthY = None
        self.devicePixelWidthX = None
        self.devicePixelWidthY = None
        self.scalableWidthWritingMode1X = None
        self.scalableWidthWritingMode1Y = None
        self.devicePixelWidthWritingMode1X = None
        self.devicePixelWidthWritingMode1Y = None
        self.properties = {}
        self.filename = None
        self.chars = []
        self.charsByEncoding = {}
        self.charsByNonStandardEncoding = {}
        self.charsByName = {}
        self.parseStage = PARSE_STAGE_MAIN

        if filename != None:
            self.read(filename)

    def startChar(self, name):
        self.char = BDFChar(name=name, font=self)
        self.chars.append(self.char)
        self.char.bitmapData = []

    def endChar(self):
        if self.char.encoding != None:
            self.charsByEncoding[self.char.encoding] = self.char
        if self.char.nonStandardEncoding != None:
            self.charsByEncoding[self.char.nonStandardEncoding] = self.char
        if self.char.name != None:
            self.charsByName[self.char.name] = self.char

    def startCharBitmap(self):
        self.char.startBitmap()

    def endCharBitmap(self):
        self.char.endBitmap()

    def newChar(self, name, font):
        return BDFChar(name = name, font = font)

    def getSwidthX(self):
        if self.scalableWidthX != None:
            return self.scalableWidthX
        if self.devicePixelWidthX != None:
            return self.devicePixelWidthX / 72000.0 * self.getResolutionX() * self.getPointSize()
        raise Exception('cannot determine swidthX')

    def getSwidthY(self):
        return 0

    def getDwidthX(self):
        if self.devicePixelWidthX != None:
            return self.devicePixelWidthX
        if self.scalableWidthX != None:
            return int(round(self.scalableWidthX * 72000.0 / self.getResolutionX() / self.getPointSize()))
        raise Exception('cannot determine dwidthX')

    def getDwidthY(self):
        return 0

    def getPointSize(self):
        pt10 = self.properties["POINT_SIZE"]
        if pt10 != None:
            return pt10 / 10.0
        raise Exception('font does not have a POINT_SIZE property')

    def setPixelSize(self, px):
        self.properties["PIXEL_SIZE"] = px
        self.properties["POINT_SIZE"] = int(round(px * 720.0 / self.getResolutionY()))
        self.pointSize = int(round(px * 72.0 / self.getResolutionY()))

    def getPixelSize(self):
        px = self.properties["PIXEL_SIZE"]
        if px != None:
            return px
        raise Exception('font does not specify pixel size')

    def getResolutionX(self):
        r = self.properties["RESOLUTION_X"]
        if r != None:
            return r
        raise Exception('cannot determine resolutionX')

    def getResolutionY(self):
        r = self.properties["RESOLUTION_Y"]
        if r != None:
            return r
        raise Exception('cannot determine resolutionY')

    def ascentPx(self):
        ascent = self.properties["FONT_ASCENT"]
        if ascent != None:
            return ascent
        raise Exception('cannot determine ascentPx')

    def descentPx(self):
        descent = self.properties["FONT_DESCENT"]
        if descent != None:
            return descent
        raise Exception('cannot determine descentPx')

    def scalableToPixels(self, scalable):
        return 1.0 * scalable * self.properties["PIXEL_SIZE"] / 1000.0
    def scalableToPixelsX(self, scalable):
        return 1.0 * scalable * self.properties["PIXEL_SIZE"] / 1000.0 / self.aspectRatioXtoY()

    def pixelsToScalable(self, pixels):
        return 1.0 * pixels * 1000.0 / self.properties["PIXEL_SIZE"]
    def pixelsToScalableX(self, pixels):
        return 1.0 * pixels * 1000.0 / self.properties["PIXEL_SIZE"] * self.aspectRatioXtoY()

    # less than 1 means taller than wide; greater than 1 means wider than tall
    def aspectRatioXtoY(self):
        return 1.0 * self.properties["RESOLUTION_Y"] / self.properties["RESOLUTION_X"]

    def setBdfVersion(self, value):
        self.bdfVersion = float(value)

    def setContentVersion(self, value):
        self.contentVersion = int(value)

    def setFontName(self, value):
        self.psFontName = str(value)

    def setSize(self, pointSize, xRes, yRes):
        self.pointSize = int(pointSize)
        self.xRes = int(xRes)
        self.yRes = int(yRes)

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

    def setMetricsSet(self, value):
        self.metricsSet = int(value)

    def setProperty(self, name, value):
        propType = self.getPropertyType(name)
        self.properties[name] = propType(value)

    def deleteProperty(self, name):
        del self.properties[name]

    def getPropertyType(self, name):
        propType = BDF_PROPERTY_TYPES.get(name)
        if propType is None:
            propType = str
        return propType

    def endCharBitmap(self):
        self.char.endBitmap()

    def setCharBoundingBox(self, *args):
        self.char.setBoundingBox(*args)

    def setCharSwidth(self, *args):
        self.char.setSwidth(*args)

    def setCharDwidth(self, *args):
        self.char.setDwidth(*args)

    def setCharEncoding(self, *args):
        self.char.setEncoding(*args)

    def appendCharBitmapData(self, *args):
        self.char.appendBitmapData(*args)

    def appendCharBitmapPixelData(self, start, binData):
        self.char.appendBitmapPixelData(start, binData)

    def __str__(self):
        string = ""
        string += self.getStartFontLine()
        string += self.getContentVersionLine()
        string += self.getFontNameLine()
        string += self.getSizeLine()
        string += self.getBoundingBoxLine()
        string += self.getMetricsSetLine()
        string += self.getDwidthLine()
        string += self.getSwidthLine()
        string += self.getPropertiesLines()
        string += self.getCharsLines()
        string += "ENDFONT\n"
        return string

    def getStartFontLine(self):
        if self.bdfVersion is None:
            return "STARTFONT 2.2\n"
        return "STARTFONT %s\n" % str(self.bdfVersion)

    def getContentVersionLine(self):
        if self.contentVersion is None:
            return ""
        return "CONTENTVERSION %d\n" % self.contentVersion

    def getFontNameLine(self):
        if self.psFontName is None:
            return ""
        return "FONT %s\n" % bdfEscape(self.psFontName)

    def getSizeLine(self):
        if self.pointSize is None or self.xRes is None or self.yRes is None:
            return ""
        return "SIZE %d %d %d\n" % (self.pointSize, self.xRes, self.yRes)

    def getBoundingBoxLine(self):
        if not self.hasBoundingBox:
            return ""
        return "FONTBOUNDINGBOX %d %d %d %d\n" % (self.boundingBoxX,
                                                  self.boundingBoxY,
                                                  self.boundingBoxXOffset,
                                                  self.boundingBoxYOffset)

    def getMetricsSetLine(self):
        if self.metricsSet is None:
            return ""
        return "METRICSSET %d\n" % self.metricsSet

    def getDwidthLine(self):
        if self.devicePixelWidthX is None:
            return ""
        return "DWIDTH %d 0\n" % self.devicePixelWidthX

    def getSwidthLine(self):
        if self.scalableWidthX is None:
            return ""
        return "SWIDTH %d 0\n" % self.scalableWidthX

    def getPropertiesLines(self):
        keys = self.properties.keys()
        if len(keys) == 0:
            return ""
        string = "STARTPROPERTIES %d\n" % len(keys)
        for key in self.properties.keys():
            string += "%s %s\n" % (key, bdfEscape(self.properties[key]))
        string += "ENDPROPERTIES\n"
        return string

    def getCharsLines(self):
        string = "CHARS %d\n" % len(self.chars)
        for char in self.chars:
            string += str(char)
        return string

def bdfEscape(str):
    if not re.match(r'[\s"]', str):
        return str
    return '"' + str.replace('"', '""') + '"'
