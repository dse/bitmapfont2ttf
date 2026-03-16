import re
import os
import sys

from bdf_font import BDFFont
from bdf_char import BDFChar

PARSE_STAGE_MAIN = 0
PARSE_STAGE_PROPERTIES = 1
PARSE_STAGE_CHARS = 2
PARSE_STAGE_CHAR = 3
PARSE_STAGE_BITMAP = 4
PARSE_STAGE_ENDFONT = 5

RX_PIXEL_LINE = r'^\s*([+|^])([^+|^]*)(?:[+|^]\s*)?$'
# U+0041 LATIN CAPITAL LETTER A
# ^   #   ^   This code parses BDFs with one important extenstion that allows
# |  # #  |   us to edit bitmap fonts more easily.  In place of a BITMAP line
# | #   # |   and a bunch of hexadecimal data, a series of lines starting with
# | #   # |   a pipe ("|") can be used to visually specify each glyph's pixels.
# | ##### |   A line can also start with a plus ("+") to indicate the glyph's
# | #   # |   baseline; the default baseline will simply be the last line.  A
# + #   # +   circumflex ("^") can also be used for the start character for any
# |       |   visual purpose, but it has no effect.
# |       |
# U+0079 LATIN SMALL LETTER Y
# ^       ^
# |       |
# | #   # |
# | #   # |
# |  # #  |
# |  # #  |
# +   #   +
# |   #   |
# | ##    |

class BDFParser():
    def __init__(self, filename=None, args=None):
        self.filename = filename
        self.font = BDFFont()
        self.parse_stage = PARSE_STAGE_MAIN
        self.args = args
        if self.args is not None:
            self.font.use_properties = self.args.use_properties
        if filename is not None:
            sys.stderr.write("Reading %s\n" % filename)
            self.read(filename)
            self.font.issue_warnings()
            self.font.end_char()
            self.font.end_font()
            sys.stderr.write("Finished reading %s\n" % filename)

    def read(self, filename):
        line_number = 0
        for line in open(filename, "r"):
            line_number += 1
            self.parse_line(line, filename, line_number)

    def parse_line(self, line, filename, line_number):
        self.line = line
        self.line_filename = filename
        self.line_number = line_number
        self.line_cmd = None
        self.line_args = None
        if re.match(r'^[ \t]*#', line):
            return
        args = bdf_parse_line(line)
        if len(args) == 0:
            return
        (cmd, args) = (args[0].upper(), args[1:])
        self.line_cmd = cmd
        self.line_args = args
        if cmd == "INCLUDE":                                    # not strictly BDF
            dirname = os.path.dirname(filename)
            for include_filename in args:
                include_filename = os.path.join(dirname, include_filename) # rel. to directory of file containing include stmt
                self.read(include_filename)
        elif self.parse_stage == PARSE_STAGE_MAIN:
            self.parse_line_at_stage_main()
        elif self.parse_stage == PARSE_STAGE_PROPERTIES:
            self.parse_line_at_stage_properties()
        elif self.parse_stage == PARSE_STAGE_CHARS:
            self.parse_line_at_stage_chars()
        elif self.parse_stage == PARSE_STAGE_CHAR:
            self.parse_line_at_stage_char()
        elif self.parse_stage == PARSE_STAGE_BITMAP:
            self.parse_line_at_stage_bitmap()
        elif self.parse_stage == PARSE_STAGE_ENDFONT:
            self.parse_line_at_stage_end_font()

    def parse_line_at_stage_main(self):
        [filename, line_number, line, cmd, args] = [self.line_filename,
                                                    self.line_number,
                                                    self.line,
                                                    self.cmd,
                                                    self.args]
        if cmd == "STARTPROPERTIES":
            self.start_properties()
        elif cmd == "CHARS":
            self.start_chars()
        elif cmd == "STARTCHAR":                                # not strictly BDF
            self.start_char()
        elif cmd == "ENDFONT":                                  # not strictly BDF
            self.end_font()
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

    def parse_line_at_stage_properties(self):
        [filename, line_number, line, cmd, args] = [self.line_filename,
                                                    self.line_number,
                                                    self.line,
                                                    self.cmd,
                                                    self.args]
        if cmd == "ENDPROPERTIES":
            self.end_properties()
        else:
            prop_name = cmd
            if len(args) == 0:
                self.font.delete_property(prop_name)
            else:
                prop_value = args[0]
                self.font.set_property(prop_name, prop_value)

    def parse_line_at_stage_chars(self):
        [filename, line_number, line, cmd, args] = [self.line_filename,
                                                    self.line_number,
                                                    self.line,
                                                    self.cmd,
                                                    self.args]
        if cmd == "STARTCHAR":
            self.start_char()
        elif cmd == "ENDFONT":
            self.end_font()
        else:
            raise Exception("%s: not supported in chars section" % cmd)

    def parse_line_at_stage_char(self):
        [filename, line_number, line, cmd, args] = [self.line_filename,
                                                    self.line_number,
                                                    self.line,
                                                    self.cmd,
                                                    self.args]
        if cmd == "BITMAP":
            self.start_bitmap()
        elif cmd == "ENDCHAR":
            self.end_char()
        elif cmd == "ENDFONT":                                  # not strictly BDF
            self.end_font()
        elif cmd == "STARTCHAR":                                # not strictly BDF
            self.start_char()
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
            self.start_bitmap()
            self.font.append_char_bitmap_pixel_data(match[1], match[2])
        else:
            raise Exception("%s: not supported in char section" % cmd)

    def parse_line_at_stage_bitmap(self):
        [filename, line_number, line, cmd, args] = [self.line_filename,
                                                    self.line_number,
                                                    self.line,
                                                    self.cmd,
                                                    self.args]
        if cmd == "ENDCHAR":
            self.end_char()
        elif cmd == "ENDFONT":                                  # not strictly BDF
            self.end_font()
        elif cmd == "STARTCHAR":
            self.start_char()
        elif match := re.fullmatch(RX_PIXEL_LINE, line):
            self.font.append_char_bitmap_pixel_data(match[1], match[2])
        else:
            self.font.append_char_bitmap_data(line)

    def parse_line_at_stage_end_font(self):
        pass

    def end_font(self):
        if self.parse_stage == PARSE_STAGE_BITMAP:
            self.font.end_char_bitmap()
            self.font.end_char()
        elif self.parse_stage == PARSE_STAGE_CHAR:
            self.font.end_char()
        self.font.end_font()
        self.parse_stage = PARSE_STAGE_ENDFONT

    def end_char(self):
        if self.parse_stage == PARSE_STAGE_BITMAP:
            self.font.end_char_bitmap()
            self.font.end_char()
        elif self.parse_stage == PARSE_STAGE_CHAR:
            self.font.end_char()
        self.parse_stage = PARSE_STAGE_CHARS

    def start_char(self):
        if self.parse_stage == PARSE_STAGE_CHAR:
            self.font.end_char()
        elif self.parse_stage == PARSE_STAGE_BITMAP:
            self.font.end_char_bitmap()
            self.font.end_char()
        self.font.start_char(self.args[0] if len(self.args) else None, self.line_filename, self.line_number)
        self.parse_stage = PARSE_STAGE_CHAR

    def start_properties(self):
        self.parse_stage = PARSE_STAGE_PROPERTIES

    def end_properties(self):
        self.parse_stage = PARSE_STAGE_MAIN

    def start_chars(self):
        self.parse_stage = PARSE_STAGE_CHARS

    def start_bitmap(self):
        self.font.start_char_bitmap()
        self.parse_stage = PARSE_STAGE_BITMAP

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
