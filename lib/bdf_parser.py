import re
import os
from bdf_font import BDFFont
from bdf_char import BDFChar

PARSE_STAGE_MAIN = 0
PARSE_STAGE_PROPERTIES = 1
PARSE_STAGE_CHARS = 2
PARSE_STAGE_CHAR = 3
PARSE_STAGE_BITMAP = 4
PARSE_STAGE_ENDFONT = 5

RX_PIXEL_LINE = r'^\s*([+|^])([^+|^]*)(?:[+|^]\s*)?$'

class BDFParser():
    def __init__(self, filename=None, args=None):
        self.filename = filename
        self.font = BDFFont()
        self.parse_stage = PARSE_STAGE_MAIN
        self.args = args
        if filename is not None:
            self.read(filename)

    def read(self, filename):
        line_number = 0
        for line in open(filename, "r"):
            line_number += 1
            self.parse_line(line, filename, line_number)

    def parse_line(self, line, filename, line_number):
        args = bdf_parse_line(line)
        if len(args) == 0:
            return
        if re.match(r'^ *#', line):
            return
        (cmd, args) = (args[0].upper(), args[1:])
        if cmd == "INCLUDE":                                    # not strictly BDF
            dirname = os.path.dirname(filename)
            # path arguments are relative to directory containing parent file
            for include_filename in args:
                include_filename = os.path.join(dirname, include_filename)
                self.read(include_filename)
        elif self.parse_stage == PARSE_STAGE_MAIN:
            self.parse_line_at_stage_main(line, filename, line_number, cmd, args)
        elif self.parse_stage == PARSE_STAGE_PROPERTIES:
            self.parse_line_at_stage_properties(line, filename, line_number, cmd, args)
        elif self.parse_stage == PARSE_STAGE_CHARS:
            self.parse_line_at_stage_chars(line, filename, line_number, cmd, args)
        elif self.parse_stage == PARSE_STAGE_CHAR:
            self.parse_line_at_stage_char(line, filename, line_number, cmd, args)
        elif self.parse_stage == PARSE_STAGE_BITMAP:
            self.parse_line_at_stage_bitmap(line, filename, line_number, cmd, args)
        elif self.parse_stage == PARSE_STAGE_ENDFONT:
            self.parse_line_at_stage_end_font(line, filename, line_number, cmd, args)

    def parse_line_at_stage_main(self, line, filename, line_number, cmd, args):
        dirname = os.path.dirname(filename)
        if cmd == "STARTPROPERTIES":
            self.parse_stage = PARSE_STAGE_PROPERTIES
        elif cmd == "CHARS":
            self.parse_stage = PARSE_STAGE_CHARS
        elif cmd == "STARTCHAR":                                # not strictly BDF
            self.font.start_char(args[0] if len(args) else None)
            self.parse_stage = PARSE_STAGE_CHAR
        elif cmd == "ENDFONT":                                  # not strictly BDF
            self.parse_stage = PARSE_STAGE_ENDFONT
        elif cmd == "STARTFONT":
            if len(args) < 1:
                raise Exception("%s: not enough arguments")
            self.font.set_bdf_version(args[0])
        elif cmd == "CONTENTVERSION":
            if len(args) < 1:
                raise Exception("%s: not enough arguments")
            self.font.set_content_version(args[0])
        elif cmd == "FONT":
            if len(args) < 1:
                raise Exception("%s: not enough arguments")
            self.font.set_font_name(args[0])
        elif cmd == "SIZE":
            if len(args) < 3:
                raise Exception("%s: not enough arguments")
            self.font.set_size(*args[0:3])
        elif cmd == "FONTBOUNDINGBOX":
            if len(args) < 4:
                raise Exception("%s: not enough arguments")
            self.font.set_bbx(*args[0:4])
        elif cmd == "SWIDTH":
            if len(args) < 2:
                raise Exception("%s: not enough arguments")
            self.font.set_swidth(*args[0:2])
        elif cmd == "DWIDTH":
            if len(args) < 2:
                raise Exception("%s: not enough arguments")
            self.font.set_dwidth(*args[0:2])
        elif cmd == "SWIDTH1":
            raise Exception("%s: not supported" % cmd)
        elif cmd == "DWIDTH1":
            raise Exception("%s: not supported" % cmd)
        elif cmd == "VVECTOR":
            raise Exception("%s: not supported" % cmd)
        elif cmd == "METRICSSET":
            if len(args) < 1:
                raise Exception("%s: not enough arguments")
            self.font.set_metrics_set(args[0])
        elif cmd == "COMMENT":
            comment = re.sub(r'^\s*comment\s?', '', line, flags=re.IGNORECASE).rstrip()
            self.font.append_comment(comment)
        else:
            raise Exception("%s: not supported in main section" % cmd)

    def parse_line_at_stage_properties(self, line, filename, line_number, cmd, args):
        if cmd == "ENDPROPERTIES":
            self.parse_stage = PARSE_STAGE_MAIN
        else:
            prop_name = cmd
            if len(args) == 0:
                self.font.delete_property(prop_name)
            else:
                prop_value = args[0]
                self.font.set_property(prop_name, prop_value)

    def parse_line_at_stage_chars(self, line, filename, line_number, cmd, args):
        if cmd == "STARTCHAR":
            self.font.start_char(args[0] if len(args) else None)
            self.parse_stage = PARSE_STAGE_CHAR
        elif cmd == "ENDFONT":
            self.parse_stage = PARSE_STAGE_ENDFONT
        else:
            raise Exception("%s: not supported in chars section" % cmd)

    def parse_line_at_stage_char(self, line, filename, line_number, cmd, args):
        if cmd == "BITMAP":
            self.font.start_char_bitmap()
            self.parse_stage = PARSE_STAGE_BITMAP
        elif cmd == "ENDCHAR":
            self.font.end_char()
            self.parse_stage = PARSE_STAGE_CHARS
        elif cmd == "ENDFONT":                                  # not strictly BDF
            self.font.end_char()
            self.parse_stage = PARSE_STAGE_ENDFONT
        elif cmd == "STARTCHAR":                                # not strictly BDF
            self.font.end_char()
            self.font.start_char(args[0] if len(args) else None)
            self.parse_stage = PARSE_STAGE_CHAR
        elif cmd == "BBX":
            if len(args) < 4:
                raise Exception("%s: not enough arguments")
            self.font.set_char_bbx(*args[0:4])
        elif cmd == "SWIDTH":
            if len(args) < 2:
                raise Exception("%s: not enough arguments")
            self.font.set_char_swidth(*args[0:2])
        elif cmd == "DWIDTH":
            if len(args) < 2:
                raise Exception("%s: not enough arguments")
            self.font.set_char_dwidth(*args[0:2])
        elif cmd == "SWIDTH1":
            raise Exception("%s: not supported" % cmd)
        elif cmd == "DWIDTH1":
            raise Exception("%s: not supported" % cmd)
        elif cmd == "VVECTOR":
            raise Exception("%s: not supported" % cmd)
        elif cmd == "ENCODING":
            if len(args) < 1:
                raise Exception("%s: not enough arguments")
            self.font.set_char_encoding(args[0], args[1] if len(args) >= 2 else None)
        elif match := re.fullmatch(RX_PIXEL_LINE, line):
            self.font.start_char_bitmap()
            self.font.append_char_bitmap_pixel_data(match[1], match[2])
            self.parse_stage = PARSE_STAGE_BITMAP
        else:
            raise Exception("%s: not supported in main section" % cmd)

    def parse_line_at_stage_bitmap(self, line, filename, line_number, cmd, args):
        if cmd == "ENDCHAR":
            self.font.end_char_bitmap()
            self.font.end_char()
            self.parse_stage = PARSE_STAGE_CHARS
        elif cmd == "ENDFONT":                                  # not strictly BDF
            self.font.end_char_bitmap()
            self.font.end_char()
            self.parse_stage = PARSE_STAGE_ENDFONT
        elif cmd == "STARTCHAR":
            self.font.end_char_bitmap()
            self.font.end_char()
            self.font.start_char(args[0] if len(args) else None)
            self.parse_stage = PARSE_STAGE_CHAR
        elif match := re.fullmatch(RX_PIXEL_LINE, line):
            self.font.append_char_bitmap_pixel_data(match[1], match[2])
        else:
            self.font.append_char_bitmap_data(line)

    def parse_line_at_stage_end_font(self, line, filename, line_number, cmd, args):
        pass

def bdf_parse_line(line):
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
