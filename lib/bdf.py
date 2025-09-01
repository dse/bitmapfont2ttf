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

    def read(self, filename):
        self.filename = filename
        for line in open(filename, "r"):
            self.parseLine(line)

    def parseLine(self, line):
        args = bdfParseLine(line)
        if len(args) == 0:
            return
        (cmd, args) = (args[0].upper(), args[1:])
        if self.parseStage == PARSE_STAGE_MAIN:
            self.parseLineAtStageMain(line, cmd, args)
        elif self.parseStage == PARSE_STAGE_PROPERTIES:
            self.parseLineAtStageProperties(line, cmd, args)
        elif self.parseStage == PARSE_STAGE_CHARS:
            self.parseLineAtStageChars(line, cmd, args)
        elif self.parseStage == PARSE_STAGE_CHAR:
            self.parseLineAtStageChar(line, cmd, args)
        elif self.parseStage == PARSE_STAGE_BITMAP:
            self.parseLineAtStageBitmap(line, cmd, args)
        elif self.parseStage == PARSE_STAGE_ENDFONT:
            self.parseLineAtStageEndFont(line, cmd, args)

    def parseLineAtStageMain(self, line, cmd, args):
        if cmd == "STARTPROPERTIES":
            self.parseStage = PARSE_STAGE_PROPERTIES
        elif cmd == "CHARS":
            self.parseStage = PARSE_STAGE_CHARS
        elif cmd == "STARTCHAR":
            self.startChar(args[0] if len(args) else None)
            self.parseStage = PARSE_STAGE_CHAR
        elif cmd == "ENDFONT":
            self.parseStage = PARSE_STAGE_ENDFONT
        elif cmd == "STARTFONT":
            if len(args) < 1:
                raise Exception("%s: not enough arguments")
            self.bdfVersion = float(args[0])
        elif cmd == "CONTENTVERSION":
            if len(args) < 1:
                raise Exception("%s: not enough arguments")
            self.contentVersion = int(args[0])
        elif cmd == "FONT":
            if len(args) < 1:
                raise Exception("%s: not enough arguments")
            self.psFontName = args[0]
        elif cmd == "SIZE":
            if len(args) < 3:
                raise Exception("%s: not enough arguments")
            self.pointSize = float(args[0])                 # point size of the glyphs
            self.xRes      = float(args[1])                 # x resolution of the device for which the font is intended
            self.yRes      = float(args[2])                 # y resolution "  "   "      "   "     "   "    "  "
        elif cmd == "FONTBOUNDINGBOX":
            if len(args) < 4:
                raise Exception("%s: not enough arguments")
            self.hasBoundingBox = True
            self.boundingBoxX       = int(args[0])          # integer pixel values, offsets relative to origin
            self.boundingBoxY       = int(args[1])
            self.boundingBoxXOffset = int(args[2])
            self.boundingBoxYOffset = int(args[3])
        elif cmd == "SWIDTH":
            if len(args) < 2:
                raise Exception("%s: not enough arguments")
            self.scalableWidthX = float(args[0])
            self.scalableWidthY = float(args[1])
            if self.scalableWidthY != 0.0:
                raise Exception("SWIDTH with non-zero Y coordinate not supported")
        elif cmd == "DWIDTH":
            if len(args) < 2:
                raise Exception("%s: not enough arguments")
            self.devicePixelWidthX = float(args[0])
            self.devicePixelWidthY = float(args[1])
            if self.devicePixelWidthY != 0.0:
                raise Exception("DWIDTH with non-zero Y coordinate not supported")
        elif cmd == "SWIDTH1":
            raise Exception("%s: not supported" % cmd)
        elif cmd == "DWIDTH1":
            raise Exception("%s: not supported" % cmd)
        elif cmd == "VVECTOR":
            raise Exception("%s: not supported" % cmd)
        elif cmd == "METRICSSET":
            if len(args) < 1:
                raise Exception("%s: not enough arguments")
            self.metricsSet = int(args[0])
        else:
            raise Exception("%s: not supported in main section" % cmd)

    def parseLineAtStageProperties(self, line, cmd, args):
        if cmd == "ENDPROPERTIES":
            self.parseStage = PARSE_STAGE_MAIN
        else:
            propName = cmd
            if len(args) == 0:
                del self.properties[propName]
            else:
                propValue = args[0]
                propType = BDF_PROPERTY_TYPES.get(propName)
                if propType is None:
                    propType = str
                self.properties[propName] = propType(propValue)

    def parseLineAtStageChars(self, line, cmd, args):
        if cmd == "STARTCHAR":
            self.startChar(args[0] if len(args) else None)
            self.parseStage = PARSE_STAGE_CHAR
        elif cmd == "ENDFONT":
            self.parseStage = PARSE_STAGE_ENDFONT
        else:
            raise Exception("%s: not supported in chars section" % cmd)

    def parseLineAtStageChar(self, line, cmd, args):
        if cmd == "BITMAP":
            self.startBitmap()
            self.parseStage = PARSE_STAGE_BITMAP
        elif cmd == "ENDCHAR":
            self.endChar()
            self.parseStage = PARSE_STAGE_CHARS
        elif cmd == "ENDFONT":
            self.endChar()
            self.parseStage = PARSE_STAGE_ENDFONT
        elif cmd == "STARTCHAR":
            self.endChar()
            self.startChar(args[0] if len(args) else None)
            self.parseStage = PARSE_STAGE_CHAR
        elif cmd == "BBX":
            if len(args) < 4:
                raise Exception("%s: not enough arguments")
            self.char.hasBoundingBox = True
            self.char.boundingBoxX       = int(args[0])
            self.char.boundingBoxY       = int(args[1])
            self.char.boundingBoxXOffset = int(args[2])
            self.char.boundingBoxYOffset = int(args[3])
        elif cmd == "SWIDTH":
            if len(args) < 2:
                raise Exception("%s: not enough arguments")
            self.char.scalableWidthX = float(args[0])
            self.char.scalableWidthY = float(args[1])
            if self.char.scalableWidthY != 0.0:
                raise Exception("SWIDTH with non-zero Y coordinate not supported")
        elif cmd == "DWIDTH":
            if len(args) < 2:
                raise Exception("%s: not enough arguments")
            self.char.devicePixelWidthX = int(args[0])
            self.char.devicePixelWidthY = int(args[1])
            if self.char.devicePixelWidthY != 0.0:
                raise Exception("DWIDTH with non-zero Y coordinate not supported")
        elif cmd == "SWIDTH1":
            raise Exception("%s: not supported" % cmd)
        elif cmd == "DWIDTH1":
            raise Exception("%s: not supported" % cmd)
        elif cmd == "VVECTOR":
            raise Exception("%s: not supported" % cmd)
        elif cmd == "ENCODING":
            if len(args) < 1:
                raise Exception("%s: not enough arguments")
            self.char.encoding = int(args[0])
            if len(args) > 1:
                self.char.nonStandardEncoding = int(args[1])
            if self.char.encoding == -1:
                self.char.encoding = None
        else:
            raise Exception("%s: not supported in main section" % cmd)

    def parseLineAtStageBitmap(self, line, cmd, args):
        if cmd == "ENDCHAR":
            self.endBitmap()
            self.endChar()
            self.parseStage = PARSE_STAGE_CHARS
        elif cmd == "ENDFONT":
            self.endChar()
            self.parseStage = PARSE_STAGE_ENDFONT
        else:
            self.char.bitmapData.append(line.strip())

    def parseLineAtStageEndFont(self, line, cmd, args):
        pass

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

    def startBitmap(self):
        pass

    def endBitmap(self):
        numBits = max(len(s) * 4 for s in self.char.bitmapData)
        self.char.bitmapData = [bin(int(s, 16))[2:].rjust(numBits, '0') for s in self.char.bitmapData]

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

    def __str__(self):
        result = "<BDF"
        if self.filename != None:
            result += (" %s" % self.filename)
        if self.pointSize != None:
            result += (" %gpt" % self.pointSize)
        if self.xRes != None:
            result += (" %gxdpi" % self.xRes)
        if self.yRes != None:
            result += (" %gydpi" % self.yRes)
        if self.hasBoundingBox:
            result += (" [%g, %g offset %g, %g]" % (
                self.boundingBoxX, self.boundingBoxY,
                self.boundingBoxXOffset, self.boundingBoxYOffset
            ))
        result += ">"
        return result

def bdfParseLine(line):
    orig_line = line
    words = []
    line = line.rstrip()
    while True:
        line = line.lstrip()
        if line == "":
            break
        if match := re.match(r'\s*"((?:[^"]+|"")*)"($|\s+)', line):
            word = match[1]
            word = word.replace('""', '"')
            words.append(word)
            line = line[match.end():]
            continue
        if match := re.match(r'^\s*(\S+)($|\s+)', line):
            word = match[1]
            words.append(word)
            line = line[match.end():]
            continue
        raise Exception("BDF line parse error: %s" % repr(orig_line))
    return words

def bdfParseLine2(line):
    match = re.match(r'^\s*(\S+)(?:\s+)(\S.*?)\s*$', line)
    if match:
        key = match.group(1)
        value = match.group(2)
        return [key, value]
    match = re.match(r'^\s*(\S+)', line)
    if match:
        key = match.group(1);
        return [match.group(1), None]
    return None
