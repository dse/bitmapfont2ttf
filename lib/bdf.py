import re
import sys
from bdfchar import BDFChar
from bdfpropertytypes import BDF_PROPERTY_TYPES

PARSE_STAGE_MAIN = 0
PARSE_STAGE_PROPERTIES = 1
PARSE_STAGE_CHARS = 2
PARSE_STAGE_GLYPH = 3
PARSE_STAGE_BITMAP = 4
PARSE_STAGE_ENDFONT = 5

class BDF:
    def __init__(self, filename = None):
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

        if filename != None:
            self.read(filename)

    def newChar(self, name, font):
        return BDFChar(name = name, font = font)

    def read(self, filename):
        with open(filename) as fp:
            self.filename = filename
            self.readFp(fp)

    def readFp(self, fp):
        for line in fp:
            args = bdfParseLine(line)
            if len(args) < 1:
                continue
            (cmd, args) = (args[0].upper(), args[1:])
            if cmd == 'CHARS':
                self.readCharsFp(fp)
            if cmd == 'SIZE' and len(args) >= 3:
                self.pointSize = float(args[0])                 # point size of the glyphs
                self.xRes      = float(args[1])                 # x resolution of the device for which the font is intended
                self.yRes      = float(args[2])                 # y resolution "  "   "      "   "     "   "    "  "
                continue
            if cmd == 'FONTBOUNDINGBOX' and len(args) >= 4:
                self.hasBoundingBox = True
                self.boundingBoxX       = int(args[0])          # integer pixel values, offsets relative to origin
                self.boundingBoxY       = int(args[1])
                self.boundingBoxXOffset = int(args[2])
                self.boundingBoxYOffset = int(args[3])
                continue
            if cmd == 'FONT' and len(args) >= 1:
                self.psFontName = args[0]
            if cmd == 'METRICSSET' and len(args) >= 1:
                self.metricsSet = int(args[0])
            if cmd == 'SWIDTH':
                self.scalableWidthX = float(args[0])
                self.scalableWidthY = float(args[1])
                if self.scalableWidthY != 0.0:
                    raise Exception("SWIDTH with non-zero Y coordinate not supported")
            if cmd == 'DWIDTH':
                self.devicePixelWidthX = float(args[0])
                self.devicePixelWidthY = float(args[1])
                if self.devicePixelWidthY != 0.0:
                    raise Exception("DWIDTH with non-zero Y coordinate not supported")
            if cmd == 'SWIDTH1':
                raise Exception("SWIDTH1 not supported")
            if cmd == 'DWIDTH1':
                raise Exception("DWIDTH1 not supported")
            if cmd == 'VVECTOR':
                raise Exception("VVECTOR not supported")
            if cmd == 'STARTPROPERTIES':
                self.readPropertiesFp(fp)

    def readPropertiesFp(self, fp):
        for line in fp:
            args = bdfParseLine(line)
            if len(args) == 0:                                  # blank line
                continue
            propName = args[0].upper()
            if len(args) == 1:                                  # empty property
                del self.properties[propName]
                continue
            propValue = args[1]
            if cmd == 'ENDPROPERTIES':
                return
            propType = BDF_PROPERTY_TYPES.get(propName)
            if propType is None:
                propType = str
            self.properties[propName] = propType(args[0]);

    def readCharsFp(self, fp):
        for line in fp:
            args = bdfParseLine(line)
            if len(args) < 1:
                continue
            (cmd, args) = (args[0].upper(), args[1:])
            if cmd == 'STARTCHAR':
                char = self.readCharFp(fp, args[0])
                self.chars.append(char)
                if char.encoding != None:
                    self.charsByEncoding[char.encoding] = char
                if char.nonStandardEncoding != None:
                    self.charsByEncoding[char.nonStandardEncoding] = char
                if char.name != None:
                    self.charsByName[char.name] = char

    def readBitmapDataFp(self, fp, char):
        bitmapData = []
        for line in fp:
            if re.match(r'^\s*ENDCHAR\s*$', line, flags = re.IGNORECASE):
                break
            bitmapData.append(line.strip())
        if len(bitmapData) < 1:
            raise Exception("No bitmap data for %s in %s" % (char.name, self.filename))
        # sys.stderr.write("--- %s ---\n" % char)
        # for s in bitmapData:
            # sys.stderr.write("[%s]\n" % s)
        numBits = max(len(s) * 4 for s in bitmapData)
        # print(s)
        bitmapData = [bin(int(s, 16))[2:].rjust(numBits, '0') for s in bitmapData]
        return bitmapData

    def readCharFp(self, fp, name):
        char = self.newChar(name = name, font = self)
        for line in fp:
            args = bdfParseLine(line)
            if len(args) < 1:
                continue
            (cmd, args) = (args[0].upper(), args[1:])
            if cmd == 'BITMAP':
                char.bitmapData = self.readBitmapDataFp(fp, char)
                return char
            elif cmd == 'ENDCHAR':
                return char
            elif cmd == 'ENCODING':
                char.encoding = int(args[0])
                if len(args) > 1:
                    char.nonStandardEncoding = int(args[1])
                if char.encoding == -1:
                    char.encoding = None
            elif cmd == 'BBX':
                char.hasBoundingBox = True
                char.boundingBoxX       = int(args[0])
                char.boundingBoxY       = int(args[1])
                char.boundingBoxXOffset = int(args[2])
                char.boundingBoxYOffset = int(args[3])
            elif cmd == 'SWIDTH':
                char.scalableWidthX = float(args[0])
                char.scalableWidthY = float(args[1])
                if char.scalableWidthY != 0.0:
                    raise Exception("SWIDTH with non-zero Y coordinate not supported")
            elif cmd == 'DWIDTH':
                char.devicePixelWidthX = int(args[0])
                char.devicePixelWidthY = int(args[1])
                if char.devicePixelWidthY != 0.0:
                    raise Exception("DWIDTH with non-zero Y coordinate not supported")
            elif cmd == 'SWIDTH1':
                raise Exception("SWIDTH1 not supported")
            elif cmd == 'DWIDTH1':
                raise Exception("DWIDTH1 not supported")
            elif cmd == 'VVECTOR':
                raise Exception("VVECTOR not supported")

    def __str__(self):
        result = "<MyBDF"
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
