import re
import sys
from bdfchar import BDFChar

class BDF:
    def __init__(self, filename = None):
        # SIZE
        self.pointSize = None
        self.xRes = None
        self.yRes = None

        # FONTBOUNDINGBOX
        self.hasBoundingBox = False
        self.boundingBoxX = None
        self.boundingBoxY = None
        self.boundingBoxXOffset = None
        self.boundingBoxYOffset = None

        # METRICSSET
        self.metricsSet = None

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

        # STARTPROPERTIES .. ENDPROPERTIES
        self.properties = {}
        self.properties["pixelSize"] = None      # PIXEL_SIZE
        self.properties["pointSize10"] = None    # POINT_SIZE
        self.properties["resolutionX"] = None    # RESOLUTION_X
        self.properties["resolutionY"] = None    # RESOLUTION_Y
        self.properties["spacing"] = None        # SPACING ('M' for monospace or 'C' for character-cell fonts)
        self.properties["capHeight"] = None      # CAP_HEIGHT
        self.properties["xHeight"] = None        # X_HEIGHT
        self.properties["ascent"] = None         # FONT_ASCENT
        self.properties["descent"] = None        # FONT_DESCENT
        self.properties["averageWidth10"] = None # AVERAGE_WIDTH

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
                self.pointSize = float(args[0]) # point size of the glyphs
                self.xRes      = float(args[1]) # x resolution of the device for which the font is intended
                self.yRes      = float(args[2]) # y resolution "  "   "      "   "     "   "    "  "
                continue
            if cmd == 'FONTBOUNDINGBOX' and len(args) >= 4:
                self.hasBoundingBox = True
                self.boundingBoxX       = int(args[0]) # integer pixel values, offsets relative to origin
                self.boundingBoxY       = int(args[1])
                self.boundingBoxXOffset = int(args[2])
                self.boundingBoxYOffset = int(args[3])
                continue
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
            if cmd == 'PIXEL_SIZE' and len(args) >= 1:
                self.properties["pixelSize"] = float(args[0])
            if cmd == 'POINT_SIZE' and len(args) >= 1:
                self.properties["pointSize10"] = float(args[0])
            if cmd == 'RESOLUTION_X' and len(args) >= 1:
                self.properties["resolutionX"] = float(args[0])
            if cmd == 'RESOLUTION_Y' and len(args) >= 1:
                self.properties["resolutionY"] = float(args[0])
            if cmd == 'SPACING' and len(args) >= 1:
                self.properties["spacing"] = args[0].upper()
            if cmd == 'CAP_HEIGHT' and len(args) >= 1:
                self.properties["capHeight"] = float(args[0])
            if cmd == 'X_HEIGHT' and len(args) >= 1:
                self.properties["xHeight"] = float(args[0])
            if cmd == 'FONT_ASCENT' and len(args) >= 1:
                self.properties["ascent"] = float(args[0])
            if cmd == 'FONT_DESCENT' and len(args) >= 1:
                self.properties["descent"] = float(args[0])
            if cmd == 'AVERAGE_WIDTH' and len(args) >= 1:
                self.properties["averageWidth10"] = float(args[0])

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
    words = []
    line = line.strip()
    while True:
        match = re.match(r'^\s*"((?:[^"]+|"")*)"($|\s+)', line)
        if match:
            word = match.group(1) # $1
            word = re.sub(r'""', '"', word)
            words.append(word)
            line = line[len(match.group(0)):] # $'
            continue
        match = re.match(r'^\s*(\S+)($|\s+)', line)
        if match:
            word = match.group(1) # $1
            words.append(word)
            line = line[len(match.group(0)):] # $'
            continue
        break
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
