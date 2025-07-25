import re

# https://adobe-type-tools.github.io/font-tech-notes/pdfs/5005.BDF_Spec.pdf
# https://www.x.org/releases/X11R7.6/doc/xorg-docs/specs/XLFD/xlfd.html

BDF_LINE_TYPE_BLANK = 0

BDF_PARSE_STAGE_FONT = 0
BDF_PARSE_STAGE_PROPERTIES = 1
BDF_PARSE_STAGE_GLYPH_DATA_SECTION = 2
BDF_PARSE_STAGE_GLYPH_DATA = 3
BDF_PARSE_STAGE_BITMAP = 4
BDF_PARSE_STAGE_END_OF_FONT = 5

class BDFParser:
    def __init__(self, loose=False):
        self.loose = loose
        self.parse_stage = BDF_PARSE_STAGE_FONT
        self.line_number = 0
        self.lines_data = []
        self.glyphs = []
        self.init_attributes()
        self.init_properties()

    def parse_line(self, line):
        line = re.sub('(?:\r\n?|\n\r?)$', '', line)
        self.line_number += 1
        self.line_data = { "line_number": line_number, "text": line }
        self.lines_data.push(self.line_data)
        split_line = split_bdf_line(line)
        if len(split_line) == 0:
            self.line_data.update({ "type": BDF_LINE_TYPE_BLANK })
            return
        [keyword, *params] = split_bdf_line(line)
        keyword = keyword.upper()
        self.line_data.update({ "keyword": keyword, "params": params })
        if self.parse_stage == BDF_PARSE_STAGE_FONT:
            return self.parse_line_stage_font(keyword, params)
        elif self.parse_stage == BDF_PARSE_STAGE_PROPERTIES:
            return self.parse_line_stage_properties(keyword, params)
        elif self.parse_stage == BDF_PARSE_STAGE_GLYPH_DATA_SECTION:
            return self.parse_line_stage_glyph_data_section(keyword, params)
        elif self.parse_stage == BDF_PARSE_STAGE_GLYPH_DATA:
            return self.parse_line_stage_glyph_data(keyword, params)
        elif self.parse_stage == BDF_PARSE_STAGE_BITMAP:
            return self.parse_line_stage_bitmap(keyword, params)
        elif self.parse_stage == BDF_PARSE_STAGE_END_OF_FONT:
            return

    def parse_line_stage_bitmap(keyword, params): # params ignored
        if keyword == "ENDCHAR":
            self.parse_stage = BDF_PARSE_STAGE_GLYPH_DATA_SECTION
        elif match := re.fullmatch('[0-9A-Fa-f]+', keyword):
            self.glyph["bitmap_data"].append(keyword)

    def init_attributes(self):
        self.bdf_version = None
        self.comments = []
        self.content_version = None
        self.font_name = None
        self.point_size = None
        self.res_x = None
        self.res_y = None
        self.bb_x = None
        self.bb_y = None
        self.bb_ofs_x = None
        self.bb_ofs_y = None
        self.metrics_set = None
        self.swidth_x = None
        self.swidth_y = None
        self.dwidth_x = None
        self.dwidth_y = None
        self.swidth1_x = None
        self.swidth1_y = None
        self.dwidth1_x = None
        self.dwidth1_y = None
        self.nominal_glyph_count = None    # saith the "CHARS" line
        self.nominal_property_count = None # saith the "STARTPROPERTIES" line

    def parse_line_stage_font(keyword, params):
        if keyword == "STARTFONT":
            [self.bdf_version] = parse_params(params, [float])
        elif keyword == "COMMENT":
            self.comments.append(" ".join(params))
        elif keyword == "CONTENTVERSION":
            [self.content_version] = parse_params(params, [int])
        elif keyword == "FONT":
            [self.font_name] = parse_params(params, [str])
        elif keyword == "SIZE":
            [self.point_size, self.res_x, self.res_y] = \
                parse_params(params, [int, int, int])
        elif keyword == "FONTBOUNDINGBOX":
            [self.bb_x, self.bb_y, self.bb_ofs_x, self.bb_ofs_y] = \
                parse_params(params, [int, int, int, int])
        elif keyword == "METRICSSET":
            [self.metrics_set] = parse_params(params, [int])
            if self.metrics_set not in [0, 1, 2]:
                raise Exception("invalid METRICSSET value on line %d" % self.line_number)
        elif keyword == "SWIDTH":
            [self.swidth_x, self.swidth_y] = parse_params(params, [float, float])
        elif keyword == "DWIDTH":
            [self.dwidth_x, self.dwidth_y] = parse_params(params, [int, int])
        elif keyword == "SWIDTH1":
            [self.swidth1_x, self.swidth1_y] = parse_params(params, [float, float])
        elif keyword == "DWIDTH1":
            [self.dwidth1_x, self.dwidth1_y] = parse_params(params, [int, int])
        elif keyword == "VVECTOR":
            [self.vvector_x, self.vvector_y] = parse_params(params, [int, int])
        elif keyword == "STARTPROPERTIES":
            [self.nominal_property_count] = parse_params(params, [int])
            self.parse_stage = BDF_PARSE_STAGE_PROPERTIES
        elif keyword == "CHARS":
            [self.nominal_glyph_count] = parse_params(params, [int])
            self.parse_stage = BDF_PARSE_STAGE_GLYPH_DATA_SECTION
        else:
            raise Exception("invalid keyword at line %d: %s" % (self.line_number, keyword))

    def parse_line_stage_glyph_data_section(keyword, params):
        if keyword == "STARTCHAR":
            self.parse_stage = BDF_PARSE_STAGE_GLYPH_DATA
            return self.parse_line_stage_glyph_data(keyword, params)
        elif keyword == "ENDFONT":
            self.parse_stage = BDF_PARSE_STAGE_END_OF_FONT
        else:
            raise Exception("invalid keyword at line %d: %s" % (self.line_number, keyword))

    def parse_line_stage_glyph_data(keyword, params):
        if keyword == "STARTCHAR":
            [glyph_name] = parse_params(params, [str])
            self.glyph = { "name": glyph_name }
            self.glyphs.push(self.glyph)
        elif keyword == "ENCODING":
            [encoding, alt_encoding] = parse_params(params, [int, int], optional=True)
            if encoding is None:
                raise Exception("not enough parameters for ENCODING on line %d" % self.line_number)
            self.glyph.update({ "encoding": encoding, "alt_encoding": alt_encoding })
        elif keyword == "SWIDTH":
            [swidth_x, swidth_y] = parse_params(params, [float, float])
            self.glyph.update({ "swidth_x": swidth_x })
            self.glyph.update({ "swidth_y": swidth_y })
        elif keyword == "DWIDTH":
            [dwidth_x, dwidth_y] = parse_params(params, [int, int])
            self.glyph.update({ "dwidth_x": dwidth_x })
            self.glyph.update({ "dwidth_y": dwidth_y })
        elif keyword == "SWIDTH1":
            [swidth1_x, swidth1_y] = parse_params(params, [float, float])
            self.glyph.update({ "swidth1_x": swidth1_x })
            self.glyph.update({ "swidth1_y": swidth1_y })
        elif keyword == "DWIDTH1":
            [dwidth1_x, dwidth1_y] = parse_params(params, [int, int])
            self.glyph.update({ "dwidth1_x": dwidth1_x })
            self.glyph.update({ "dwidth1_y": dwidth1_y })
        elif keyword == "VVECTOR":
            [vvector_x, vvector_y] = parse_params(params, [int, int])
            self.glyph.update({ "vvector_x": vvector_x })
            self.glyph.update({ "vvector_y": vvector_y })
        elif keyword == "BBX":
            [bb_x, bb_y, bb_ofs_x, bb_ofs_y] = \
                parse_params(params, [int, int, int, int])
            self.glyph.update({ "bb_x": bb_x })
            self.glyph.update({ "bb_y": bb_y })
            self.glyph.update({ "bb_ofs_x": bb_ofs_x })
            self.glyph.update({ "bb_ofs_y": bb_ofs_y })
        elif keyword == "BITMAP":
            self.glyph["bitmap_data"] = []
            self.parse_stage = BDF_PARSE_STAGE_BITMAP
        else:
            raise Exception("invalid keyword on line %d: %s" % (self.line_number, keyword))

    def init_properties(self):
        self.prop_foundry = None
        self.prop_family_name = None
        self.prop_weight_name = None
        self.prop_slant = None
        self.prop_setwidth_name = None
        self.prop_add_style_name = None
        self.prop_pixel_size = None
        self.prop_point_size = None
        self.prop_resolution_x = None
        self.prop_resolution_y = None
        self.prop_spacing = None
        self.prop_average_width = None
        self.prop_charset_registry = None
        self.prop_charset_encoding = None
        self.prop_min_space = None
        self.prop_norm_space = None
        self.prop_max_space = None
        self.prop_end_space = None
        self.prop_avg_capital_width = None
        self.prop_avg_lowercase_width = None
        self.prop_quad_width = None
        self.prop_figure_width = None
        self.prop_superscript_x = None
        self.prop_superscript_y = None
        self.prop_subscript_x = None
        self.prop_subscript_y = None
        self.prop_superscript_size = None
        self.prop_subscript_size = None
        self.prop_small_cap_size = None
        self.prop_underline_position = None
        self.prop_underline_thickness = None
        self.prop_strikeout_ascent = None
        self.prop_strikeout_descent = None
        self.prop_italic_angle = None
        self.prop_cap_height = None
        self.prop_x_height = None
        self.prop_relative_setwidth = None
        self.prop_relative_weight = None
        self.prop_resolution = None # deprecated
        self.prop_resolution_x = None
        self.prop_resolution_y = None
        self.prop_font = None
        self.prop_face_name = None
        self.prop_full_name = None # deprecated
        self.prop_copyright = None
        self.prop_notice = None
        self.prop_destination = None
        self.prop_font_type = None
        self.prop_font_version = None
        self.prop_rasterizer_name = None
        self.prop_rasterizer_version = None
        self.prop_raw_ascent = None
        self.prop_raw_descent = None
        self.prop_font_ascent = None
        self.prop_font_descent = None
        self.prop_default_char = None

    def parse_line_stage_properties(keyword, params):
        if keyword == "ENDPROPERTIES":
            self.parse_stage = BDF_PARSE_STAGE_FONT
            return
        property_value = { "list": params, "scalar": params[0] if len(params) else None }
        self.properties[keyword] = property_value
        if keyword == "FOUNDRY":
            [self.prop_foundry] = parse_params(params, [str])
            property_value.update({ "value": self.prop_foundry })
        elif keyword == "FAMILY_NAME":
            [self.prop_family_name] = parse_params(params, [str])
            property_value.update({ "value": self.prop_family_name })
        elif keyword == "WEIGHT_NAME":
            [self.prop_weight_name] = parse_params(params, [str])
            property_value.update({ "value": self.prop_weight_name })
        elif keyword == "SLANT":
            [self.prop_slant] = parse_params(params, [str])
            self.prop_slant = self.prop_slant.upper()
            if self.prop_slant not in ["R", "I", "O", "RI", "RO", "OT"]:
                raise Exception("invalid SLANT property value at line %d" % self.line_number)
            property_value.update({ "value": self.prop_slant })
        elif keyword == "SETWIDTH_NAME":
            [self.prop_setwidth_name] = parse_params(params, [str])
            property_value.update({ "value": self.prop_setwidth_name })
        elif keyword == "ADD_STYLE_NAME":
            [self.prop_add_style_name] = parse_params(params, [str])
            property_value.update({ "value": self.prop_add_style_name })
        elif keyword == "PIXEL_SIZE":
            [self.prop_pixel_size] = parse_params(params, [int])
            property_value.update({ "value": self.prop_pixel_size })
        elif keyword == "POINT_SIZE":
            [self.prop_point_size] = parse_params(params, [int])
            property_value.update({ "value": self.prop_point_size })
        elif keyword == "RESOLUTION_X":
            [self.prop_resolution_x] = parse_params(params, [int])
            property_value.update({ "value": self.prop_resolution_x })
        elif keyword == "RESOLUTION_Y":
            [self.prop_resolution_y] = parse_params(params, [int])
            property_value.update({ "value": self.prop_resolution_y })
        elif keyword == "SPACING":
            [self.prop_spacing] = parse_params(params, [int])
            self.prop_spacing = self.prop_spacing.upper()
            if self.prop_spacing not in ["P", "M", "C"]:
                raise Exception("invalid SPACING property value at line %d" % self.line_number)
            property_value.update({ "value": self.prop_spacing })
        elif keyword == "AVERAGE_WIDTH":
            [self.prop_average_width] = parse_params(params, [int])
            property_value.update({ "value": self.prop_average_width })
        elif keyword == "CHARSET_REGISTRY":
            [self.prop_charset_registry] = parse_params(params, [str])
            property_value.update({ "value": self.prop_charset_registry })
        elif keyword == "CHARSET_ENCODING":
            [self.prop_charset_encoding] = parse_params(params, [str])
            property_value.update({ "value": self.prop_charset_encoding })
        elif keyword == "MIN_SPACE":
            [self.prop_min_space] = parse_params(params, [int])
            property_value.update({ "value": self.prop_min_space })
        elif keyword == "NORM_SPACE":
            [self.prop_norm_space] = parse_params(params, [int])
            property_value.update({ "value": self.prop_norm_space })
        elif keyword == "MAX_SPACE":
            [self.prop_max_space] = parse_params(params, [int])
            property_value.update({ "value": self.prop_max_space })
        elif keyword == "END_SPACE":
            [self.prop_end_space] = parse_params(params, [int])
            property_value.update({ "value": self.prop_end_space })
        elif keyword == "AVG_CAPITAL_WIDTH":
            [self.prop_avg_capital_width] = parse_params(params, [int])
            property_value.update({ "value": self.prop_avg_capital_width })
        elif keyword == "AVG_LOWERCASE_WIDTH":
            [self.prop_avg_lowercase_width] = parse_params(params, [int])
            property_value.update({ "value": self.prop_avg_lowercase_width })
        elif keyword == "QUAD_WIDTH":
            [self.prop_quad_width] = parse_params(params, [int])
            property_value.update({ "value": self.prop_quad_width })
        elif keyword == "FIGURE_WIDTH":
            [self.prop_figure_width] = parse_params(params, [int])
            property_value.update({ "value": self.prop_figure_width })
        elif keyword == "SUPERSCRIPT_X":
            [self.prop_superscript_x] = parse_params(params, [int])
            property_value.update({ "value": self.prop_superscript_x })
        elif keyword == "SUPERSCRIPT_Y":
            [self.prop_superscript_y] = parse_params(params, [int])
            property_value.update({ "value": self.prop_superscript_y })
        elif keyword == "SUBSCRIPT_X":
            [self.prop_subscript_x] = parse_params(params, [int])
            property_value.update({ "value": self.prop_subscript_x })
        elif keyword == "SUBSCRIPT_Y":
            [self.prop_subscript_y] = parse_params(params, [int])
            property_value.update({ "value": self.prop_subscript_y })
        elif keyword == "SUPERSCRIPT_SIZE":
            [self.prop_superscript_size] = parse_params(params, [int])
            property_value.update({ "value": self.prop_superscript_size })
        elif keyword == "SUBSCRIPT_SIZE":
            [self.prop_subscript_size] = parse_params(params, [int])
            property_value.update({ "value": self.prop_subscript_size })
        elif keyword == "SMALL_CAP_SIZE":
            [self.prop_small_cap_size] = parse_params(params, [int])
            property_value.update({ "value": self.prop_small_cap_size })
        elif keyword == "UNDERLINE_POSITION":
            [self.prop_underline_position] = parse_params(params, [int])
            property_value.update({ "value": self.prop_underline_position })
        elif keyword == "UNDERLINE_THICKNESS":
            [self.prop_underline_thickness] = parse_params(params, [int])
            property_value.update({ "value": self.prop_underline_thickness })
        elif keyword == "STRIKEOUT_ASCENT":
            [self.prop_strikeout_ascent] = parse_params(params, [int])
            property_value.update({ "value": self.prop_strikeout_ascent })
        elif keyword == "STRIKEOUT_DESCENT":
            [self.prop_strikeout_descent] = parse_params(params, [int])
            property_value.update({ "value": self.prop_strikeout_descent })
        elif keyword == "ITALIC_ANGLE":
            [self.prop_italic_angle] = parse_params(params, [int])
            property_value.update({ "value": self.prop_italic_angle })
        elif keyword == "CAP_HEIGHT":
            [self.prop_cap_height] = parse_params(params, [int])
            property_value.update({ "value": self.prop_cap_height })
        elif keyword == "X_HEIGHT":
            [self.prop_x_height] = parse_params(params, [int])
            property_value.update({ "value": self.prop_x_height })
        elif keyword == "RELATIVE_SETWIDTH":
            [self.prop_relative_setwidth] = parse_params(params, [int])
            property_value.update({ "value": self.prop_relative_setwidth })
        elif keyword == "RELATIVE_WEIGHT":
            [self.prop_relative_weight] = parse_params(params, [int])
            property_value.update({ "value": self.prop_relative_weight })
        elif keyword == "RESOLUTION":
            [self.prop_resolution] = parse_params(params, [int]) # deprecated; use _X and _Y
            property_value.update({ "value": self.prop_resolution })
        elif keyword == "RESOLUTION_X":
            [self.prop_resolution_x] = parse_params(params, [int])
            property_value.update({ "value": self.prop_resolution_x })
        elif keyword == "RESOLUTION_Y":
            [self.prop_resolution_y] = parse_params(params, [int])
            property_value.update({ "value": self.prop_resolution_y })
        elif keyword == "FONT":
            [self.prop_font] = parse_params(params, [str])
            property_value.update({ "value": self.prop_font })
        elif keyword == "FACE_NAME":
            [self.prop_face_name] = parse_params(params, [str])
            property_value.update({ "value": self.prop_face_name })
        elif keyword == "FULL_NAME":
            [self.prop_full_name] = parse_params(params, [str]) # deprecated; use FACE_NAME
            property_value.update({ "value": self.prop_full_name })
        elif keyword == "COPYRIGHT":
            [self.prop_copyright] = parse_params(params, [str])
            property_value.update({ "value": self.prop_copyright })
        elif keyword == "NOTICE":
            [self.prop_notice] = parse_params(params, [str])
            property_value.update({ "value": self.prop_notice })
        elif keyword == "DESTINATION":
            [self.prop_destination] = parse_params(params, [int])
            property_value.update({ "value": self.prop_destination })
        elif keyword == "FONT_TYPE":
            [self.prop_font_type] = parse_params(params, [str])
            property_value.update({ "value": self.prop_font_type })
        elif keyword == "FONT_VERSION":
            [self.prop_font_version] = parse_params(params, [str])
            property_value.update({ "value": self.prop_font_version })
        elif keyword == "RASTERIZER_NAME":
            [self.prop_rasterizer_name] = parse_params(params, [str])
            property_value.update({ "value": self.prop_rasterizer_name })
        elif keyword == "RASTERIZER_VERSION":
            [self.prop_rasterizer_version] = parse_params(params, [str])
            property_value.update({ "value": self.prop_rasterizer_version })
        elif keyword == "RAW_ASCENT":
            [self.prop_raw_ascent] = parse_params(params, [int])
            property_value.update({ "value": self.prop_raw_ascent })
        elif keyword == "RAW_DESCENT":
            [self.prop_raw_descent] = parse_params(params, [int])
            property_value.update({ "value": self.prop_raw_descent })
        elif keyword == "FONT_ASCENT":
            [self.prop_font_ascent] = parse_params(params, [int])
            property_value.update({ "value": self.prop_font_ascent })
        elif keyword == "FONT_DESCENT":
            [self.prop_font_descent] = parse_params(params, [int])
            property_value.update({ "value": self.prop_font_descent })
        elif keyword == "DEFAULT_CHAR":
            [self.prop_default_char] = parse_params(params, [int])
            property_value.update({ "value": self.prop_default_char })

def split_bdf_line(line):
    words = []
    pos = 0
    while True:
        if match := re.match('\s+', line):
            line = line[match.end():]
            pos += match.end()
        if line == "":
            break
        word = ""
        while True:
            if match := re.match('[^"\s]+', line):
                line = line[match.end():]
                word += match[0]
                pos += match.end()
            elif match := re.match('"((?:[^"]|"")*)"', line):
                line = line[match.end():]
                word += match[1].replace('""', '"')
                pos += match.end()
            elif match := re.match('"', line):
                raise Exception("unterminated quote at %d: %s" % (pos, repr(line)))
            else:
                break
        words += word
    return words

def parse_params(params, param_types, optional=False):
    values = []
    if not optional:
        if len(params) < len(param_types):
            raise Exception("not enough parameters: got %d parameters; expected %d" % (len(params), len(param_types)))
        if len(params) > len(param_types):
            raise Exception("too many parameters: got %d parameters; expected %d" % (len(params), len(param_types)))
    for i in range(0, len(params)):
        param_type = param_types[i] if i < len(param_types) else None
        param      = params[i]      if i < len(params)      else None
        if param is None:
            values.append(None)
        elif param_type is None:
            values.append(param)
        elif param_type == str:
            values.append(param)
        elif param_type == float:
            param = param.replace("~", "-")
            values.append(float(param))
        elif param_type == int:
            param = param.replace("~", "-")
            values.append(int(param))
        else:
            raise Exception("unsupported parameter type: %s" % repr(param_type))
    return values

def ellipsis(str):
    if len(str) > 16:
        return str[0:13] + "..."
    return str
