import os, sys, re
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))

from bdf_font import BDFFont
from bdf_glyph import BDFGlyph
from bdf_utils import clear_previous_lines, split_line, \
    create_encoding_line

# https://adobe-type-tools.github.io/font-tech-notes/pdfs/5005.BDF_Spec.pdf
# https://www.x.org/releases/X11R7.6/doc/xorg-docs/specs/XLFD/xlfd.html

PARSE_STAGE_FONT = 0
PARSE_STAGE_PROP = 1
PARSE_STAGE_CHARS = 2
PARSE_STAGE_CHAR = 3
PARSE_STAGE_BITMAP = 4
PARSE_STAGE_JUNK = 5

class BDFParser:
    def __init__(self, loose=False):
        self.parse_stage = PARSE_STAGE_FONT
        self.font = BDFFont()
        self.glyph = None
        self.line_number = 0
        self.filename = None
        self.loose = loose

    def parse_line(self, text):
        self.line_number += 1
        orig_text = text
        text = text.strip()
        line = { "filename": self.filename, "line_number": self.line_number, "orig_text": orig_text, "text": text }
        words, orig_words = split_line(text)
        if len(words) == 0:
            self.font.lines.append(line)
            return
        if match := re.fullmatch(r'^([+^|])(.*?)[+^|]?', text):
            if not self.loose:
                raise Exception(self.error_prefix() +
                                "pixel data not valid in strict mode parsing")
            if self.parse_stage not in [PARSE_STAGE_BITMAP, PARSE_STAGE_CHAR]:
                raise Exception(self.error_prefix() +
                                "incorrect place for pixel data")
            firstchar = match[1]
            bits = match[2]
            self.parse_pixel_line(firstchar, bits)
        [keyword, *params] = words
        keyword = keyword.upper()
        line.update({ "words": words, "orig_words": orig_words, "keyword": keyword, "params": params })
        if self.loose and keyword == "INCLUDE": # at any stage
            for text in open(params[0], "r"):
                self.parse_line(text)
        elif self.parse_stage == PARSE_STAGE_FONT:
            self.parse_line_font(line)
        elif self.parse_stage == PARSE_STAGE_PROP:
            self.parse_line_prop(line)
        elif self.parse_stage == PARSE_STAGE_CHARS:
            self.parse_line_chars(line)
        elif self.parse_stage == PARSE_STAGE_CHAR:
            self.parse_line_char(line)
        elif self.parse_stage == PARSE_STAGE_BITMAP:
            self.parse_line_bitmap(line)
        elif self.parse_stage == PARSE_STAGE_JUNK:
            pass                # do nothing
        else:
            raise Exception(self.error_prefix() +
                            "invalid parse stage: %s" % (repr(self.parse_stage)))

    def parse_line_font(self, line):
        keyword = line["keyword"]
        params = line["params"]
        will_append = True
        if keyword == "STARTFONT":
            min = 0 if self.loose else None
            [self.font.startfont] = self.parse_params(keyword, params, [float], min=min)
            self.font.lines = clear_previous_lines(self.font.lines, keyword)
        elif keyword == "COMMENT":
            self.font.comments.append(" ".join(params))
        elif keyword == "CONTENTVERSION":
            [self.font.contentversion] = self.parse_params(keyword, params, [int])
            self.font.lines = clear_previous_lines(self.font.lines, keyword)
        elif keyword == "FONT":
            [self.font.font] = self.parse_params(keyword, params, [str])
            self.font.lines = clear_previous_lines(self.font.lines, keyword)
        elif keyword == "SIZE":
            [self.font.point_size, self.font.x_res, self.font.y_res] = \
                self.parse_params(keyword, params, [int, int, int])
            self.font.lines = clear_previous_lines(self.font.lines, keyword)
        elif keyword == "FONTBOUNDINGBOX":
            [self.font.bbx_x, self.font.bbx_y, self.font.bbx_ofs_x, self.font.bbx_ofs_y] = \
                self.parse_params(keyword, params, [int, int, int, int])
            self.font.lines = clear_previous_lines(self.font.lines, keyword)
        elif keyword == "METRICSSET":
            [self.font.metricsset] = self.parse_params(keyword, params, [int])
            self.font.lines = clear_previous_lines(self.font.lines, keyword)
        elif keyword == "SWIDTH":
            [self.font.swidth_x, self.font.swidth_y] = self.parse_params(keyword, params, [int, int])
            self.font.lines = clear_previous_lines(self.font.lines, keyword)
        elif keyword == "DWIDTH":
            [self.font.dwidth_x, self.font.dwidth_y] = self.parse_params(keyword, params, [int, int])
            self.font.lines = clear_previous_lines(self.font.lines, keyword)
        elif keyword == "SWIDTH1":
            [self.font.swidth1_x, self.font.swidth1_y] = self.parse_params(keyword, params, [int, int])
            self.font.lines = clear_previous_lines(self.font.lines, keyword)
        elif keyword == "DWIDTH1":
            [self.font.dwidth1_x, self.font.dwidth1_y] = self.parse_params(keyword, params, [int, int])
            self.font.lines = clear_previous_lines(self.font.lines, keyword)
        elif keyword == "VVECTOR":
            [self.font.vvector_x, self.font.vvector_y] = self.parse_params(keyword, params, [int, int])
            self.font.lines = clear_previous_lines(self.font.lines, keyword)
        elif keyword == "STARTPROPERTIES":
            min = 0 if self.loose else None
            [self.font.startproperties_count] = self.parse_params(keyword, params, [int], min=min)
            self.parse_stage = PARSE_STAGE_PROP
        elif keyword == "CHARS":
            min = 0 if self.loose else None
            [self.font.chars_count] = self.parse_params(keyword, params, [int], min=min)
            self.parse_stage = PARSE_STAGE_CHARS
        elif self.loose and keyword == "STARTCHAR":
            self.font.lines.append({
                "keyword": "CHARS",
                "params": [],
                "text": "CHARS"
            })
            self.parse_STARTCHAR_line(line)
            return # parse_STARTCHAR_line takes care of appending
        else:
            raise Exception(self.error_prefix() + "%s: invalid keyword" % (keyword))
        self.font.lines.append(line)

    def parse_line_prop(self, line):
        keyword = line["keyword"]
        params = line["params"]
        self.font.prop_lines = clear_previous_lines(self.font.prop_lines, keyword)
        if keyword == "ENDPROPERTIES":
            self.parse_stage = PARSE_STAGE_FONT
            if not self.loose:
                prop_count = len(self.font.prop_lines)
                if prop_count != self.font.startproperties_count:
                    raise Exception(self.error_prefix() +
                                    "received %d properties; expected %d" %
                                    (prop_count, self.font.startproperties_count))
        else:
            if len(params) != 1:
                raise Exception(self.error_prefix() + "%s: takes 1 param, no more, no fewer")
            self.font.raw_props[keyword] = params[0]
        if keyword == "FOUNDRY":
            [self.font.prop_foundry] = self.parse_params(keyword, params, [str])
        elif keyword == "FAMILY_NAME":
            [self.font.prop_family_name] = self.parse_params(keyword, params, [str])
        elif keyword == "WEIGHT_NAME":
            [self.font.prop_weight_name] = self.parse_params(keyword, params, [str])
        elif keyword == "SLANT":
            [self.font.prop_slant] = self.parse_params(keyword, params, [str])
        elif keyword == "SETWIDTH_NAME":
            [self.font.prop_setwidth_name] = self.parse_params(keyword, params, [str])
        elif keyword == "ADD_STYLE_NAME":
            [self.font.prop_add_style_name] = self.parse_params(keyword, params, [str])
        elif keyword == "PIXEL_SIZE":
            [self.font.prop_pixel_size] = self.parse_params(keyword, params, [int])
        elif keyword == "POINT_SIZE":
            [self.font.prop_point_size] = self.parse_params(keyword, params, [int])
        elif keyword == "RESOLUTION_X":
            [self.font.prop_resolution_x] = self.parse_params(keyword, params, [int])
        elif keyword == "RESOLUTION_Y":
            [self.font.prop_resolution_y] = self.parse_params(keyword, params, [int])
        elif keyword == "SPACING":
            [self.font.prop_spacing] = self.parse_params(keyword, params, [str])
        elif keyword == "AVERAGE_WIDTH":
            [self.font.prop_average_width] = self.parse_params(keyword, params, [int])
        elif keyword == "CHARSET_REGISTRY":
            [self.font.prop_charset_registry] = self.parse_params(keyword, params, [str])
        elif keyword == "CHARSET_ENCODING":
            [self.font.prop_charset_encoding] = self.parse_params(keyword, params, [str])
        elif keyword == "MIN_SPACE":
            [self.font.prop_min_space] = self.parse_params(keyword, params, [int])
        elif keyword == "NORM_SPACE":
            [self.font.prop_norm_space] = self.parse_params(keyword, params, [int])
        elif keyword == "MAX_SPACE":
            [self.font.prop_max_space] = self.parse_params(keyword, params, [int])
        elif keyword == "END_SPACE":
            [self.font.prop_end_space] = self.parse_params(keyword, params, [int])
        elif keyword == "AVG_CAPITAL_WIDTH":
            [self.font.prop_avg_capital_width] = self.parse_params(keyword, params, [int])
        elif keyword == "AVG_LOWERCASE_WIDTH":
            [self.font.prop_avg_lowercase_width] = self.parse_params(keyword, params, [int])
        elif keyword == "QUAD_WIDTH":
            [self.font.prop_quad_width] = self.parse_params(keyword, params, [int])
        elif keyword == "FIGURE_WIDTH":
            [self.font.prop_figure_width] = self.parse_params(keyword, params, [int])
        elif keyword == "SUPERSCRIPT_X":
            [self.font.prop_superscript_x] = self.parse_params(keyword, params, [int])
        elif keyword == "SUPERSCRIPT_Y":
            [self.font.prop_superscript_y] = self.parse_params(keyword, params, [int])
        elif keyword == "SUBSCRIPT_X":
            [self.font.prop_subscript_x] = self.parse_params(keyword, params, [int])
        elif keyword == "SUBSCRIPT_Y":
            [self.font.prop_subscript_y] = self.parse_params(keyword, params, [int])
        elif keyword == "SUPERSCRIPT_SIZE":
            [self.font.prop_superscript_size] = self.parse_params(keyword, params, [int])
        elif keyword == "SUBSCRIPT_SIZE":
            [self.font.prop_subscript_size] = self.parse_params(keyword, params, [int])
        elif keyword == "SMALL_CAP_SIZE":
            [self.font.prop_small_cap_size] = self.parse_params(keyword, params, [int])
        elif keyword == "UNDERLINE_POSITION":
            [self.font.prop_underline_position] = self.parse_params(keyword, params, [int])
        elif keyword == "UNDERLINE_THICKNESS":
            [self.font.prop_underline_thickness] = self.parse_params(keyword, params, [int])
        elif keyword == "STRIKEOUT_ASCENT":
            [self.font.prop_strikeout_ascent] = self.parse_params(keyword, params, [int])
        elif keyword == "STRIKEOUT_DESCENT":
            [self.font.prop_strikeout_descent] = self.parse_params(keyword, params, [int])
        elif keyword == "ITALIC_ANGLE":
            [self.font.prop_italic_angle] = self.parse_params(keyword, params, [int])
        elif keyword == "CAP_HEIGHT":
            [self.font.prop_cap_height] = self.parse_params(keyword, params, [int])
        elif keyword == "X_HEIGHT":
            [self.font.prop_x_height] = self.parse_params(keyword, params, [int])
        elif keyword == "RELATIVE_SETWIDTH":
            [self.font.prop_relative_setwidth] = self.parse_params(keyword, params, [int])
        elif keyword == "RELATIVE_WEIGHT":
            [self.font.prop_relative_weight] = self.parse_params(keyword, params, [int])
        elif keyword == "WEIGHT":
            [self.font.prop_weight] = self.parse_params(keyword, params, [int])
        elif keyword == "RESOLUTION":
            [self.font.prop_resolution] = self.parse_params(keyword, params, [int])
        elif keyword == "FONT":
            [self.font.prop_font] = self.parse_params(keyword, params, [str])
        elif keyword == "FACE_NAME":
            [self.font.prop_face_name] = self.parse_params(keyword, params, [str])
        elif keyword == "FULL_NAME":
            [self.font.prop_full_name] = self.parse_params(keyword, params, [str])
        elif keyword == "COPYRIGHT":
            [self.font.prop_copyright] = self.parse_params(keyword, params, [str])
        elif keyword == "NOTICE":
            [self.font.prop_notice] = self.parse_params(keyword, params, [str])
        elif keyword == "DESTINATION":
            [self.font.prop_destination] = self.parse_params(keyword, params, [str])
        elif keyword == "FONT_TYPE":
            [self.font.prop_font_type] = self.parse_params(keyword, params, [str])
        elif keyword == "FONT_VERSION":
            [self.font.prop_font_version] = self.parse_params(keyword, params, [str])
        elif keyword == "RASTERIZER_NAME":
            [self.font.prop_rasterizer_name] = self.parse_params(keyword, params, [str])
        elif keyword == "RASTERIZER_VERSION":
            [self.font.prop_rasterizer_version] = self.parse_params(keyword, params, [str])
        elif keyword == "RAW_ASCENT":
            [self.font.prop_raw_ascent] = self.parse_params(keyword, params, [int])
        elif keyword == "RAW_DESCENT":
            [self.font.prop_raw_descent] = self.parse_params(keyword, params, [int])
        elif keyword[0:4] == "RAW_":
            raise Exception(self.error_prefix() + "%s: not supported" % keyword)
        elif keyword == "AXIS_NAMES":
            raise Exception(self.error_prefix() + "AXIS_NAMES: not supported")
        elif keyword == "AXIS_LIMITS":
            raise Exception(self.error_prefix() + "AXIS_LIMITS: not supported")
        elif keyword == "AXIS_TYPES":
            raise Exception(self.error_prefix() + "AXIS_TYPES: not supported")
        self.font.prop_lines.append(line)

    def parse_line_chars(self, line):
        keyword = line["keyword"]
        params = line["params"]
        if keyword == "ENDFONT":
            self.parse_stage = PARSE_STAGE_JUNK
        elif keyword == "STARTCHAR":
            self.parse_STARTCHAR_line(line)
            return # parse_STARTCHAR_line takes care of appending
        self.font.lines.append(line)

    def parse_STARTCHAR_line(self, line):
        keyword = line["keyword"]
        params = line["params"]
        if not self.loose:
            if len(params) != 1:
                raise Exception(self.error_prefix() + "STARTCHAR: takes 1 param, no more, no fewer")
        elif len(params) < 1:
            raise Exception(self.error_prefix() + "STARTCHAR: takes at least 1 param in loose parsing mode")
        self.glyph = BDFGlyph()
        self.font.glyphs.append(self.glyph)
        self.glyph.lines.append(line)

        enc_line = create_encoding_line(params[0])
        if enc_line is not None:
            self.glyph.lines.append(enc_line)
        self.parse_stage = PARSE_STAGE_CHAR

    def parse_line_char(self, line):
        keyword = line["keyword"]
        params = line["params"]
        if keyword == "ENCODING":
            [self.glyph.encoding, self.glyph.alt_encoding] = self.parse_params(keyword, params, [int, int], min=1)
            self.glyph.lines = clear_previous_lines(self.glyph.lines, keyword)
        elif keyword == "SWIDTH":
            [self.glyph.swidth_x, self.glyph.swidth_y] = self.parse_params(keyword, params, [int, int])
            self.glyph.lines = clear_previous_lines(self.glyph.lines, keyword)
        elif keyword == "DWIDTH":
            [self.glyph.dwidth_x, self.glyph.dwidth_y] = self.parse_params(keyword, params, [int, int])
            self.glyph.lines = clear_previous_lines(self.glyph.lines, keyword)
        elif keyword == "SWIDTH1":
            [self.glyph.swidth1_x, self.glyph.swidth1_y] = self.parse_params(keyword, params, [int, int])
            self.glyph.lines = clear_previous_lines(self.glyph.lines, keyword)
        elif keyword == "DWIDTH1":
            [self.glyph.dwidth1_x, self.glyph.dwidth1_y] = self.parse_params(keyword, params, [int, int])
            self.glyph.lines = clear_previous_lines(self.glyph.lines, keyword)
        elif keyword == "VVECTOR":
            [self.glyph.vvector_x, self.glyph.vvector_y] = self.parse_params(keyword, params, [int, int])
            self.glyph.lines = clear_previous_lines(self.glyph.lines, keyword)
        elif keyword == "BBX":
            [self.glyph.bbx_x, self.glyph.bbx_y, self.glyph.bbx_ofs_x, self.glyph.bbx_ofs_y] = \
                self.parse_params(keyword, params, [int, int, int, int])
            self.glyph.lines = clear_previous_lines(self.glyph.lines, keyword)
        elif keyword == "BITMAP":
            self.parse_stage = PARSE_STAGE_BITMAP
        elif self.loose and keyword == "ENDFONT":
            self.glyph.lines = self.glyph.lines[0:-1]
            self.font.lines.append(line)
            self.parse_stage = PARSE_STAGE_JUNK
            return
        elif self.loose and keyword == "STARTCHAR":
            self.glyph.lines = self.glyph.lines[0:-1]
            self.parse_STARTCHAR_line(line)
            return
        else:
            raise Exception(self.error_prefix() + "%s: invalid keyword" % keyword)
        self.glyph.lines.append(line)

    def parse_line_bitmap(self, line):
        keyword = line["keyword"]
        params = line["params"]
        if re.fullmatch('[0-9A-Fa-f]+', keyword):
            self.glyph.bitmap_lines.append(line)
        elif keyword == "ENDCHAR":
            self.glyph.lines.append(line)
            self.parse_stage = PARSE_STAGE_CHARS
        elif self.loose and keyword == "STARTCHAR":
            self.glyph.lines.append({ "text": "ENDCHAR", "keyword": "ENDCHAR", "params": [] })
            self.parse_STARTCHAR_line(line)
        elif self.loose and keyword == "ENDFONT":
            self.glyph.lines.append({ "text": "ENDCHAR", "keyword": "ENDCHAR", "params": [] })
            self.font.lines.append(line)
            self.parse_stage = PARSE_STAGE_JUNK
        else:
            raise Exception(self.error_prefix() + "%s: invalid keyword" % keyword)

    def parse_pixel_line(self, firstchar, bits):
        # firstchar is either "^" or "|" or "+"
        #     "|" means nothing special
        #     "^" means cap height
        #     "+" means baseline at the bottom of this line of pixels
        # even out to 4 bits
        bits += " " * (8 - len(bits) % 8) % 8
        bytes = len(bits) / 8
        nybbles = len(bits) / 4
        bits = re.replace(r'[^ ]', '1', bits)
        bits = bits.replace(' ', '0')
        hex_line = ""
        for byte in range(0, bytes):
            byte = int(bits[byte*8,byte*8+8], base=2)
            hex_byte = ("%02X" % byte)[-2:]
            hex_line += hex_byte
        if self.parse_stage == PARSE_STAGE_CHAR:
            self.glyph.lines.append({ "keyword": "BITMAP", "text": "BITMAP", "params": [] })
        self.glyph.bitmap_lines.append({ "text": hex_line, "keyword": hex_line, "params": [] })
        self.parse_stage = PARSE_STAGE_BITMAP

    def parse_params(self, keyword, params, param_types, min=None):
        values = []
        if min is None:
            if len(params) < len(param_types):
                raise Exception(self.error_prefix() + "%s: too few params (expected %d; got %d)" %
                                (keyword, len(param_types), len(params)))
        else:
            if len(params) < min:
                raise Exception(self.error_prefix() + "%s: too few params (expected %d to %d; got %d)" %
                                (keyword, min, len(param_types), len(params)))
        if len(params) > len(param_types):
            raise Exception(self.error_prefix() + "%s: too many params (expected %d; got %d)" %
                            (keyword, len(param_types), len(params)))
        for i in range(0, len(params)):
            param_type = param_types[i]
            param = params[i]
            values.append(self.parse_param(keyword, param, param_type))
        for i in range(len(params), len(param_types)):
            values.append(None)
        return values

    def parse_param(self, keyword, param, param_type):
        filename = self.filename
        line_number = self.line_number
        if param_type == str:
            return param
        elif param_type == float:
            return float(param.replace('~', '-'))
        elif param_type == int:
            return int(param.replace('~', '-'))
        raise Exception(self.error_prefix() + "%s: invalid type for param: %s" % (keyword, repr(param_type), i))

    def error_prefix(self):
        return "%s:%d: " % (self.filename, self.line_number)
