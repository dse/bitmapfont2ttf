import re
import sys
from bdfchar import BDFChar
from bdfpropertytypes import BDF_PROPERTY_TYPES

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
        self.properties["PIXEL_SIZE"] = None                     # PIXEL_SIZE
        self.properties["POINT_SIZE"] = None                   # POINT_SIZE
        self.properties["RESOLUTION_X"] = None                   # RESOLUTION_X
        self.properties["RESOLUTION_Y"] = None                   # RESOLUTION_Y
        self.properties["SPACING"] = None                       # SPACING ('M' for monospace or 'C' for character-cell fonts)
        self.properties["CAP_HEIGHT"] = None                     # CAP_HEIGHT
        self.properties["X_HEIGHT"] = None                       # X_HEIGHT
        self.properties["FONT_ASCENT"] = None                        # FONT_ASCENT
        self.properties["FONT_DESCENT"] = None                       # FONT_DESCENT
        self.properties["AVERAGE_WIDTH"] = None                # AVERAGE_WIDTH
        self.properties["SETWIDTH_NAME"] = None                  # SETWIDTH_NAME
        self.properties["FAMILY_NAME"] = None                    # FAMILY_NAME (font.familyname)
        self.properties["WEIGHT_NAME"] = None                    # WEIGHT_NAME (font.weight)
        self.properties["FOUNDRY"] = None                       # FOUNDRY
        self.properties["SLANT"] = None                         # SLANT ("R" or "I" or "O") [font.italicAngle]
        self.properties["FACE_NAME"] = None                      # FACE_NAME
        self.properties["FULL_NAME"] = None                      # FULL_NAME (font.fullname)

        self.bdfProperties = {}
        self.bdfArrayProperties = {}

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
            if cmd == 'DWIDTH':
                self.devicePixelWidthX = float(args[0])
                self.devicePixelWidthY = float(args[1])
            if cmd == 'SWIDTH1':
                self.scalableWidthWritingMode1X = float(args[0])
                self.scalableWidthWritingMode1Y = float(args[1])
            if cmd == 'DWIDTH1':
                self.devicePixelWidthWritingMode1X = float(args[0])
                self.devicePixelWidthWritingMode1Y = float(args[1])
            if cmd == 'VVECTOR':
                sys.stderr.write("ERROR: bitmapfont2ttf: %s: fonts with VVECTOR not supported yet.\n" % self.args.full_name)
                exit(1)
            if cmd == 'STARTPROPERTIES':
                self.readPropertiesFp(fp)

    def readPropertiesFp(self, fp):
        for line in fp:
            args = bdfParseLine(line)
            if len(args) < 1:
                continue
            (cmd, args) = (args[0].upper(), args[1:])
            if cmd == 'ENDPROPERTIES':
                return

            propName = cmd
            propType = BDF_PROPERTY_TYPES.get(propName)
            if propType is None:
                propType = str
            self.properties[propName] = propType(args[0]);

            result = bdfParseLine2(line)
            if result:
                key = result[0]
                value = result[1]
                self.addBdfProperty(key, value)

    def addBdfProperty(self, key, value):
        self.bdfProperties[key] = value
        if self.bdfArrayProperties.get(key) == None:
            self.bdfArrayProperties[key] = []
        self.bdfArrayProperties[key].append(value)

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
            elif cmd == 'DWIDTH':
                char.devicePixelWidthX = int(args[0])
                char.devicePixelWidthY = int(args[1])
            elif cmd == 'SWIDTH1':
                char.scalableWidthWritingMode1X = float(args[0])
                char.scalableWidthWritingMode1Y = float(args[1])
            elif cmd == 'DWIDTH1':
                char.devicePixelWidthWritingMode1X = int(args[0])
                char.devicePixelWidthWritingMode1Y = int(args[1])
            elif cmd == 'VVECTOR':
                sys.stderr.write("ERROR: bitmapfont2ttf: %s: fonts with VVECTOR not supported yet.\n" % self.args.full_name)
                exit(1)

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
