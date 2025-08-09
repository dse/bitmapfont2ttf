import os, sys, re
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))

from bdf_font import BDFFont
from bdf_glyph import BDFGlyph

# https://adobe-type-tools.github.io/font-tech-notes/pdfs/5005.BDF_Spec.pdf
# https://www.x.org/releases/X11R7.6/doc/xorg-docs/specs/XLFD/xlfd.html

PARSE_STAGE_FONT = 0
PARSE_STAGE_PROP = 1
PARSE_STAGE_CHARS = 2
PARSE_STAGE_CHAR = 3
PARSE_STAGE_BITMAP = 4
PARSE_STAGE_JUNK = 5

class BDFParser:
    def __init__(self):
        self.parse_stage = PARSE_STAGE_FONT
        self.font = BDFFont()
        self.glyph = None
        self.line_number = 0
        self.filename = None

    def parse_line(self, text):
        self.line_number += 1
        orig_text = text
        text = text.strip()
        line = { "filename": self.filename, "line_number": self.line_number, "orig_text": orig_text, "text": text }
        words, orig_words = self.split_line(text)
        if len(words) == 0:
            self.font.lines.append(line)
            return
        [keyword, *params] = words
        keyword = keyword.upper()
        line.update({ "words": words, "orig_words": orig_words, "keyword": keyword, "params": params })
        if self.parse_stage == PARSE_STAGE_FONT:
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
            raise Exception(self.error_prefix() + "invalid parse stage: %s" % (repr(self.parse_stage)))
    def parse_line_font(self, line):
        keyword = line["keyword"]
        params = line["params"]
        self.font.lines.append(line)
        if keyword == "STARTFONT":
            [self.font.startfont] = self.parse_params(keyword, params, [float])
            self.font.lines = self.clear_previous_lines(self.font.lines, keyword, last=True)
        elif keyword == "COMMENT":
            self.font.comments.append(" ".join(params))
        elif keyword == "CONTENTVERSION":
            [self.font.contentversion] = self.parse_params(keyword, params, [int])
            self.font.lines = self.clear_previous_lines(self.font.lines, keyword, last=True)
        elif keyword == "FONT":
            [self.font.font] = self.parse_params(keyword, params, [str])
            self.font.lines = self.clear_previous_lines(self.font.lines, keyword, last=True)
        elif keyword == "SIZE":
            [self.font.point_size, self.font.x_res, self.font.y_res] = \
                self.parse_params(keyword, params, [int, int, int])
            self.font.lines = self.clear_previous_lines(self.font.lines, keyword, last=True)
        elif keyword == "FONTBOUNDINGBOX":
            [self.font.bbx_x, self.font.bbx_y, self.font.bbx_ofs_x, self.font.bbx_ofs_y] = \
                self.parse_params(keyword, params, [int, int, int, int])
            self.font.lines = self.clear_previous_lines(self.font.lines, keyword, last=True)
        elif keyword == "METRICSSET":
            [self.font.metricsset] = self.parse_params(keyword, params, [int])
            self.font.lines = self.clear_previous_lines(self.font.lines, keyword, last=True)
        elif keyword == "SWIDTH":
            [self.font.swidth_x, self.font.swidth_y] = self.parse_params(keyword, params, [int, int])
            self.font.lines = self.clear_previous_lines(self.font.lines, keyword, last=True)
        elif keyword == "DWIDTH":
            [self.font.dwidth_x, self.font.dwidth_y] = self.parse_params(keyword, params, [int, int])
            self.font.lines = self.clear_previous_lines(self.font.lines, keyword, last=True)
        elif keyword == "SWIDTH1":
            [self.font.swidth1_x, self.font.swidth1_y] = self.parse_params(keyword, params, [int, int])
            self.font.lines = self.clear_previous_lines(self.font.lines, keyword, last=True)
        elif keyword == "DWIDTH1":
            [self.font.dwidth1_x, self.font.dwidth1_y] = self.parse_params(keyword, params, [int, int])
            self.font.lines = self.clear_previous_lines(self.font.lines, keyword, last=True)
        elif keyword == "VVECTOR":
            [self.font.vvector_x, self.font.vvector_y] = self.parse_params(keyword, params, [int, int])
            self.font.lines = self.clear_previous_lines(self.font.lines, keyword, last=True)
        elif keyword == "STARTPROPERTIES":
            [self.font.startproperties_count] = self.parse_params(keyword, params, [int], min=0)
            self.parse_stage = PARSE_STAGE_PROP
        elif keyword == "CHARS":
            [self.font.chars_count] = self.parse_params(keyword, params, [int], min=0)
            self.parse_stage = PARSE_STAGE_CHARS
        else:
            raise Exception(self.error_prefix() + "%s: invalid keyword" % (self.filename, self.line_number, keyword))
    def parse_line_prop(self, line):
        keyword = line["keyword"]
        params = line["params"]
        self.font.prop_lines = self.clear_previous_lines(self.font.prop_lines, keyword)
        self.font.prop_lines.append(line)
        if keyword == "ENDPROPERTIES":
            self.parse_stage = PARSE_STAGE_FONT
            return
        if len(params) != 1:
            raise Exception(self.error_prefix() + "%s: takes 1 param, no more, no fewer" % (self.filename, self.line_number))
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
            raise Exception(self.error_prefix() + "%s: not supported" % (self.filename, self.line_number, keyword))
        elif keyword == "AXIS_NAMES":
            raise Exception(self.error_prefix() + "AXIS_NAMES: not supported" % (self.filename, self.line_number))
        elif keyword == "AXIS_LIMITS":
            raise Exception(self.error_prefix() + "AXIS_LIMITS: not supported" % (self.filename, self.line_number))
        elif keyword == "AXIS_TYPES":
            raise Exception(self.error_prefix() + "AXIS_TYPES: not supported" % (self.filename, self.line_number))
    def parse_line_chars(self, line):
        keyword = line["keyword"]
        params = line["params"]
        if keyword == "ENDFONT":
            self.font.lines.append(line)
            self.parse_stage = PARSE_STAGE_JUNK
        elif keyword == "STARTCHAR":
            if len(params) != 1:
                raise Exception(self.error_prefix() + "STARTCHAR: takes 1 param, no more, no fewer" % (self.filename, self.line_number))
            self.glyph = BDFGlyph()
            self.font.glyphs.append(self.glyph)
            self.glyph.lines.append(line)
            self.parse_stage = PARSE_STAGE_CHAR
    def parse_line_char(self, line):
        keyword = line["keyword"]
        params = line["params"]
        self.glyph.lines.append(line)
        if keyword == "ENCODING":
            [self.glyph.encoding, self.glyph.alt_encoding] = self.parse_params(keyword, params, [int, int], min=1)
        elif keyword == "SWIDTH":
            [self.glyph.swidth_x, self.glyph.swidth_y] = self.parse_params(keyword, params, [int, int])
        elif keyword == "DWIDTH":
            [self.glyph.dwidth_x, self.glyph.dwidth_y] = self.parse_params(keyword, params, [int, int])
        elif keyword == "SWIDTH1":
            [self.glyph.swidth1_x, self.glyph.swidth1_y] = self.parse_params(keyword, params, [int, int])
        elif keyword == "DWIDTH1":
            [self.glyph.dwidth1_x, self.glyph.dwidth1_y] = self.parse_params(keyword, params, [int, int])
        elif keyword == "VVECTOR":
            [self.glyph.vvector_x, self.glyph.vvector_y] = self.parse_params(keyword, params, [int, int])
        elif keyword == "BBX":
            [self.glyph.bbx_x, self.glyph.bbx_y, self.glyph.bbx_ofs_x, self.glyph.bbx_ofs_y] = \
                self.parse_params(keyword, params, [int, int, int, int])
        elif keyword == "BITMAP":
            self.parse_stage = PARSE_STAGE_BITMAP
        else:
            raise Exception(self.error_prefix() + "%s: invalid keyword" % (self.filename, self.line_number))

    def parse_line_bitmap(self, line):
        keyword = line["keyword"]
        params = line["params"]
        self.glyph.lines.append(line)
        if keyword == "ENDCHAR":
            self.parse_stage = PARSE_STAGE_CHARS

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

    def split_line(self, text):
        orig_words = []
        words = []
        while True:
            text = re.sub(r'^\s+', '', text)
            if text == "":
                break
            orig_word = ""
            word = ""
            while True:
                if match := re.match(r'[^" ]+', text):
                    text = text[len(match[0]):]
                    orig_word += match[0]
                    word += match[0]
                elif match := re.match(r'"((""|[^"])*)', text):
                    text = text[len(match[0]):]
                    orig_word += match[0]
                    word += match[1].replace('""', '"')
                    if match := re.match(r'"', text):
                        orig_word += '"'
                else:
                    break
            words.append(word)
            orig_words.append(orig_word)
        return words, orig_words

    def clear_previous_lines(self, lines, keyword, last=False):
        matches = [line for line in lines if "keyword" in line and line["keyword"] == keyword]
        if len(matches) == 0:
            return lines
        if last:
            kept_last_line = matches[-1]
            matches = matches[0:-1]
            lines = lines[0:-1]
        lines = [line for line in lines if line not in matches]
        if last:
            return lines + [kept_last_line]
        return lines

    def error_prefix(self):
        return "%s:%d: " % (self.filename, self.line_number)
