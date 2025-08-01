import os, sys, re
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))

from bdf_font import BDFFont
from bdf_glyph import BDFGlyph
from parse_bdf_line import parse_bdf_line
from bdf_utils import ellipsis
from parse_params import parse_params

# https://adobe-type-tools.github.io/font-tech-notes/pdfs/5005.BDF_Spec.pdf
# https://www.x.org/releases/X11R7.6/doc/xorg-docs/specs/XLFD/xlfd.html

BDF_PARSE_STAGE_FONT = 0
BDF_PARSE_STAGE_PROPERTIES = 1
BDF_PARSE_STAGE_GLYPH_DATA_SECTION = 2
BDF_PARSE_STAGE_GLYPH_DATA = 3
BDF_PARSE_STAGE_BITMAP = 4
BDF_PARSE_STAGE_END_OF_FONT = 5

BDF_ATTRIBUTE_TYPES = {
    "STARTFONT":           [float],
    # "COMMENT":             [...],
    "CONTENTVERSION":      [int],
    "FONT":                [str],
    "SIZE":                [int, int, int],
    "FONTBOUNDINGBOX":     [int, int, int, int],
    "METRICSSET":          [int],
    "SWIDTH":              [int, int],
    "DWIDTH":              [int, int],
    "SWIDTH1":             [int, int],
    "DWIDTH1":             [int, int],
    "VVECTOR":             [int, int],
    "STARTPROPERTIES":     [int],
    "CHARS":               [int],
    "STARTCHAR":           [str],
}

BDF_GLYPH_ATTRIBUTE_TYPES = {
    "ENCODING":            [int, [int]],
    "SWIDTH":              [int, int],
    "DWIDTH":              [int, int],
    "SWIDTH1":             [int, int],
    "DWIDTH1":             [int, int],
    "VVECTOR":             [int, int],
    "BBX":                 [int, int, int, int],
}

BDF_PROPERTY_TYPES = {
    "FOUNDRY":             [str],
    "FAMILY_NAME":         [str],
    "WEIGHT_NAME":         [str],
    "SLANT":               [str],
    "SETWIDTH_NAME":       [str],
    "ADD_STYLE_NAME":      [str],
    "PIXEL_SIZE":          [int],
    "POINT_SIZE":          [int],
    "RESOLUTION_X":        [int],
    "RESOLUTION_Y":        [int],
    "SPACING":             [str],
    "AVERAGE_WIDTH":       [int],
    "CHARSET_REGISTRY":    [str],
    "CHARSET_ENCODING":    [str],
    "MIN_SPACE":           [int],
    "NORM_SPACE":          [int],
    "MAX_SPACE":           [int],
    "END_SPACE":           [int],
    "AVG_CAPITAL_WIDTH":   [int],
    "AVG_LOWERCASE_WIDTH": [int],
    "QUAD_WIDTH":          [int],
    "FIGURE_WIDTH":        [int],
    "SUPERSCRIPT_X":       [int],
    "SUPERSCRIPT_Y":       [int],
    "SUBSCRIPT_X":         [int],
    "SUBSCRIPT_Y":         [int],
    "SUPERSCRIPT_SIZE":    [int],
    "SUBSCRIPT_SIZE":      [int],
    "SMALL_CAP_SIZE":      [int],
    "UNDERLINE_POSITION":  [int],
    "UNDERLINE_THICKNESS": [int],
    "STRIKEOUT_ASCENT":    [int],
    "STRIKEOUT_DESCENT":   [int],
    "ITALIC_ANGLE":        [int],
    "CAP_HEIGHT":          [int],
    "X_HEIGHT":            [int],
    "RELATIVE_SETWIDTH":   [int],
    "RELATIVE_WEIGHT":     [int],
    "WEIGHT":              [int],
    "RESOLUTION":          [int], # deprecated; use _X and _Y
    "RESOLUTION_X":        [int],
    "RESOLUTION_Y":        [int],
    "FONT":                [str],
    "FACE_NAME":           [str],
    "FULL_NAME":           [str], # deprecated; use FACE_NAME
    "COPYRIGHT":           [str],
    "NOTICE":              [str],
    "DESTINATION":         [int],
    "FONT_TYPE":           [str],
    "FONT_VERSION":        [str],
    "RASTERIZER_NAME":     [str],
    "RASTERIZER_VERSION":  [str],
    "RAW_ASCENT":          [int],
    "RAW_DESCENT":         [int],
    "FONT_ASCENT":         [int],
    "FONT_DESCENT":        [int],
    "DEFAULT_CHAR":        [int],
}

class BDFParser:
    def __init__(self):
        self.parse_stage = BDF_PARSE_STAGE_FONT
        self.font = BDFFont()

    def parse_line(self, line):
        line = re.sub('(?:\r\n?|\n\r?)$', '', line) # à la chomp
        split_line = parse_bdf_line(line)
        if len(split_line) == 0:
            return
        [keyword, *params] = split_line
        keyword = keyword.upper()
        # print(keyword)
        if self.parse_stage == BDF_PARSE_STAGE_FONT:
            self.parse_line_stage_font(keyword, params)
        elif self.parse_stage == BDF_PARSE_STAGE_PROPERTIES:
            self.parse_line_stage_properties(keyword, params)
        elif self.parse_stage == BDF_PARSE_STAGE_GLYPH_DATA_SECTION:
            self.parse_line_stage_glyph_data_section(keyword, params)
        elif self.parse_stage == BDF_PARSE_STAGE_GLYPH_DATA:
            self.parse_line_stage_glyph_data(keyword, params)
        elif self.parse_stage == BDF_PARSE_STAGE_BITMAP:
            self.parse_line_stage_bitmap(keyword, params)
        elif self.parse_stage == BDF_PARSE_STAGE_END_OF_FONT:
            return
        # invalid parse stage; not handling at this time

    def parse_line_stage_bitmap(self, keyword, params): # params ignored
        if keyword == "ENDCHAR":
            self.parse_stage = BDF_PARSE_STAGE_GLYPH_DATA_SECTION
        elif match := re.fullmatch('[0-9A-Fa-f]+', keyword):
            self.glyph.append_bitmap_data(keyword)
        else:
            raise Exception("invalid bitmap data")

    def parse_line_stage_font(self, keyword, params):
        values = None
        value = None
        if keyword in BDF_ATTRIBUTE_TYPES:
            values = parse_params(params, BDF_ATTRIBUTE_TYPES[keyword])
        else:
            values = parse_params(params, [...])
        if keyword == "STARTFONT":
            self.font.set_bdf_version(*values)
        elif keyword == "COMMENT":
            self.font.append_comment(" ".join(values))
        elif keyword == "CONTENTVERSION":
            self.font.set_content_version(*values)
        elif keyword == "FONT":
            self.font.set_font_name(*values)
        elif keyword == "SIZE":
            self.font.set_size(*values)
        elif keyword == "FONTBOUNDINGBOX":
            self.font.set_bounding_box(*values)
        elif keyword == "METRICSSET":
            self.font.set_metrics_set(*values)
        elif keyword == "SWIDTH":
            self.font.set_swidth(*values)
        elif keyword == "DWIDTH":
            self.font.set_dwidth(*values)
        elif keyword == "SWIDTH1":
            self.font.set_swidth1(*values)
        elif keyword == "DWIDTH1":
            self.font.set_dwidth1(*values)
        elif keyword == "VVECTOR":
            self.font.set_vvector(*values)
        elif keyword == "STARTPROPERTIES":
            self.font.set_nominal_property_count(*values)
            self.parse_stage = BDF_PARSE_STAGE_PROPERTIES
        elif keyword == "CHARS":
            self.font.set_nominal_glyph_count(*values)
            self.parse_stage = BDF_PARSE_STAGE_GLYPH_DATA_SECTION
        else:
            raise Exception("invalid keyword at line %d: %s" %
                            (self.line_number, keyword))

    def parse_line_stage_glyph_data_section(self, keyword, params):
        if keyword == "STARTCHAR":
            self.parse_stage = BDF_PARSE_STAGE_GLYPH_DATA
            self.parse_line_stage_glyph_data(keyword, params)
        elif keyword == "ENDFONT":
            self.parse_stage = BDF_PARSE_STAGE_END_OF_FONT
            return
        else:
            raise Exception("invalid keyword at line %d: %s" %
                            (self.line_number, keyword))

    def parse_line_stage_glyph_data(self, keyword, params):
        values = None
        if keyword in BDF_GLYPH_ATTRIBUTE_TYPES:
            values = parse_params(params, BDF_GLYPH_ATTRIBUTE_TYPES[keyword])
        else:
            values = params
        if keyword == "STARTCHAR":
            self.glyph = BDFGlyph()
            self.font.append_glyph(self.glyph)
            self.glyph.set_name(*values)
        elif keyword == "ENCODING":
            if len(values) == 2:
                [encoding, alt_encoding] = values
            else:
                [encoding] = values
                alt_encoding = None
            self.glyph.set_encoding(encoding)
            self.glyph.set_alt_encoding(alt_encoding)
        elif keyword == "SWIDTH":
            self.glyph.set_swidth(*values)
        elif keyword == "DWIDTH":
            self.glyph.set_dwidth(*values)
        elif keyword == "SWIDTH1":
            self.glyph.set_swidth1(*values)
        elif keyword == "DWIDTH1":
            self.glyph.set_dwidth1(*values)
        elif keyword == "VVECTOR":
            self.glyph.set_vvector(*values)
        elif keyword == "BBX":
            self.glyph.set_bounding_box(*values)
        elif keyword == "BITMAP":
            self.parse_stage = BDF_PARSE_STAGE_BITMAP
        else:
            raise Exception("invalid keyword on line %d: %s" %
                            (self.line_number, keyword))

    def parse_line_stage_properties(self, keyword, params):
        if keyword in BDF_PROPERTY_TYPES:
            values = parse_params(params, BDF_PROPERTY_TYPES[keyword])
        else:
            values = params
            # print(values)
        if keyword == "ENDPROPERTIES":
            self.parse_stage = BDF_PARSE_STAGE_FONT
            return
        # print(keyword, *values)
        self.font.set_property(keyword, *values)

def parse_param(param, param_type):
    if param is None:
        return None
    if param_type is None:
        return param
    if param_type is str:
        return str(param)
    if param_type is float:
        param = param.replace("~", "-")
        return float(param)
    if param_type is int:
        param = param.replace("~", "-")
        return int(param)
    raise Exception("unsupported parameter type: %s" % repr(param_type))
