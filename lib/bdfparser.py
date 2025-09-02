import re
from bdf import BDF
from bdfchar import BDFChar

PARSE_STAGE_MAIN = 0
PARSE_STAGE_PROPERTIES = 1
PARSE_STAGE_CHARS = 2
PARSE_STAGE_CHAR = 3
PARSE_STAGE_BITMAP = 4
PARSE_STAGE_ENDFONT = 5

class BDFParser():
    def __init__(self, filename=None, args=None):
        self.filename = filename
        self.font = BDF()
        self.parseStage = PARSE_STAGE_MAIN
        self.args = args
        if filename is not None:
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
            self.font.setBdfVersion(args[0])
        elif cmd == "CONTENTVERSION":
            if len(args) < 1:
                raise Exception("%s: not enough arguments")
            self.font.setContentVersion(args[0])
        elif cmd == "FONT":
            if len(args) < 1:
                raise Exception("%s: not enough arguments")
            self.font.setFontName(args[0])
        elif cmd == "SIZE":
            if len(args) < 3:
                raise Exception("%s: not enough arguments")
            self.font.setSize(*args[0:3])
        elif cmd == "FONTBOUNDINGBOX":
            if len(args) < 4:
                raise Exception("%s: not enough arguments")
            self.font.setBoundingBox(*args[0:4])
        elif cmd == "SWIDTH":
            if len(args) < 2:
                raise Exception("%s: not enough arguments")
            self.font.setSwidth(*args[0:2])
        elif cmd == "DWIDTH":
            if len(args) < 2:
                raise Exception("%s: not enough arguments")
            self.font.setDwidth(*args[0:2])
        elif cmd == "SWIDTH1":
            raise Exception("%s: not supported" % cmd)
        elif cmd == "DWIDTH1":
            raise Exception("%s: not supported" % cmd)
        elif cmd == "VVECTOR":
            raise Exception("%s: not supported" % cmd)
        elif cmd == "METRICSSET":
            if len(args) < 1:
                raise Exception("%s: not enough arguments")
            self.font.setMetricsSet(args[0])
        else:
            raise Exception("%s: not supported in main section" % cmd)

    def parseLineAtStageProperties(self, line, cmd, args):
        if cmd == "ENDPROPERTIES":
            self.parseStage = PARSE_STAGE_MAIN
        else:
            propName = cmd
            if len(args) == 0:
                self.font.deleteProperty(propName)
            else:
                propValue = args[0]
                self.font.setProperty(propName, propValue)

    def parseLineAtStageChars(self, line, cmd, args):
        if cmd == "STARTCHAR":
            self.font.startChar(args[0] if len(args) else None)
            self.parseStage = PARSE_STAGE_CHAR
        elif cmd == "ENDFONT":
            self.parseStage = PARSE_STAGE_ENDFONT
        else:
            raise Exception("%s: not supported in chars section" % cmd)

    def parseLineAtStageChar(self, line, cmd, args):
        if cmd == "BITMAP":
            self.font.startBitmap()
            self.parseStage = PARSE_STAGE_BITMAP
        elif cmd == "ENDCHAR":
            self.font.endChar()
            self.parseStage = PARSE_STAGE_CHARS
        elif cmd == "ENDFONT":
            self.font.endChar()
            self.parseStage = PARSE_STAGE_ENDFONT
        elif cmd == "STARTCHAR":
            self.font.endChar()
            self.font.startChar(args[0] if len(args) else None)
            self.parseStage = PARSE_STAGE_CHAR
        elif cmd == "BBX":
            if len(args) < 4:
                raise Exception("%s: not enough arguments")
            self.font.setCharBoundingBox(*args[0:4])
        elif cmd == "SWIDTH":
            if len(args) < 2:
                raise Exception("%s: not enough arguments")
            self.font.setCharSwidth(*args[0:2])
        elif cmd == "DWIDTH":
            if len(args) < 2:
                raise Exception("%s: not enough arguments")
            self.font.setCharDwidth(*args[0:2])
        elif cmd == "SWIDTH1":
            raise Exception("%s: not supported" % cmd)
        elif cmd == "DWIDTH1":
            raise Exception("%s: not supported" % cmd)
        elif cmd == "VVECTOR":
            raise Exception("%s: not supported" % cmd)
        elif cmd == "ENCODING":
            if len(args) < 1:
                raise Exception("%s: not enough arguments")
            self.font.setCharEncoding(args[0], args[1] if len(args) >= 2 else None)
        else:
            raise Exception("%s: not supported in main section" % cmd)

    def parseLineAtStageBitmap(self, line, cmd, args):
        if cmd == "ENDCHAR":
            self.font.endCharBitmap()
            self.font.endChar()
            self.parseStage = PARSE_STAGE_CHARS
        elif cmd == "ENDFONT":
            self.font.endChar()
            self.parseStage = PARSE_STAGE_ENDFONT
        else:
            self.font.appendCharBitmapData(line)

    def parseLineAtStageEndFont(self, line, cmd, args):
        pass


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
