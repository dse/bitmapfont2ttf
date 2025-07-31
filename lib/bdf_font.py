import os, sys
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))

from bdf_utils import bdf_quote

class BDFFont:
    def __init__(self):
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
        self.properties = {}
        self.bdf_glyphs = []
        self.init_properties()
        self.lines_in_order = []
    def set_bdf_version(self, value):
        self.bdf_version = value
    def append_comment(self, value):
        self.comments.append(value)
    def set_content_version(self, value):
        self.content_version = value
    def set_font_name(self, value):
        self.font_name = value
    def set_size(self, point_size, res_x, res_y):
        [self.point_size, self.res_x, self.res_y] = [point_size, res_x, res_y]
    def set_point_size(self, value):
        self.point_size = value
    def set_res_x(self, value):
        self.res_x = value
    def set_res_y(self, value):
        self.res_y = value
    def set_bounding_box(self, bb_x, bb_y, bb_ofs_x, bb_ofs_y):
        self.bb_x = bb_x
        self.bb_y = bb_y
        self.bb_ofs_x = bb_ofs_x
        self.bb_ofs_y = bb_ofs_y
    def set_metrics_set(self, value):
        self.metrics_set = value
    def set_swidth(self, x, y):
        self.swidth_x = x
        self.swidth_y = y
    def set_dwidth(self, x, y):
        self.dwidth_x = x
        self.dwidth_y = y
    def set_swidth1(self, x, y):
        self.swidth1_x = x
        self.swidth1_y = y
    def set_dwidth1(self, x, y):
        self.dwidth1_x = x
        self.dwidth1_y = y
    def set_vvector(self, x, y):
        self.vvector_x = x
        self.vvector_y = y
    def set_nominal_glyph_count(self, value):
        self.nominal_glyph_count = value
    def set_nominal_property_count(self, value):
        self.nominal_property_count = value
    def set_property(self, name, value):
        self.properties[name] = value
    def append_glyph(self, glyph):
        self.bdf_glyphs.append(glyph)
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
    def set_property(self, name, value):
        name = name.upper()
        self.properties[name] = value
        if keyword == "FOUNDRY":
            self.prop_foundry = value
        elif keyword == "FAMILY_NAME":
            self.prop_family_name = value
        elif keyword == "WEIGHT_NAME":
            self.prop_weight_name = value
        elif keyword == "SLANT":
            self.prop_slant = value
            if value not in ["R", "I", "O", "RI", "RO", "OT"]:
                raise Exception("invalid SLANT property value")
        elif keyword == "SETWIDTH_NAME":
            self.prop_setwidth_name = value
        elif keyword == "ADD_STYLE_NAME":
            self.prop_add_style_name = value
        elif keyword == "PIXEL_SIZE":
            self.prop_pixel_size = value
        elif keyword == "POINT_SIZE":
            self.prop_point_size = value
        elif keyword == "RESOLUTION_X":
            self.prop_resolution_x = value
        elif keyword == "RESOLUTION_Y":
            self.prop_resolution_y = value
        elif keyword == "SPACING":
            self.prop_spacing = value
            if self.prop_spacing not in ["P", "M", "C"]:
                raise Exception("invalid SPACING property value")
        elif keyword == "AVERAGE_WIDTH":
            self.prop_average_width = value
        elif keyword == "CHARSET_REGISTRY":
            self.prop_charset_registry = value
        elif keyword == "CHARSET_ENCODING":
            self.prop_charset_encoding = value
        elif keyword == "MIN_SPACE":
            self.prop_min_space = value
        elif keyword == "NORM_SPACE":
            self.prop_norm_space = value
        elif keyword == "MAX_SPACE":
            self.prop_max_space = value
        elif keyword == "END_SPACE":
            self.prop_end_space = value
        elif keyword == "AVG_CAPITAL_WIDTH":
            self.prop_avg_capital_width = value
        elif keyword == "AVG_LOWERCASE_WIDTH":
            self.prop_avg_lowercase_width = value
        elif keyword == "QUAD_WIDTH":
            self.prop_quad_width = value
        elif keyword == "FIGURE_WIDTH":
            self.prop_figure_width = value
        elif keyword == "SUPERSCRIPT_X":
            self.prop_superscript_x = value
        elif keyword == "SUPERSCRIPT_Y":
            self.prop_superscript_y = value
        elif keyword == "SUBSCRIPT_X":
            self.prop_subscript_x = value
        elif keyword == "SUBSCRIPT_Y":
            self.prop_subscript_y = value
        elif keyword == "SUPERSCRIPT_SIZE":
            self.prop_superscript_size = value
        elif keyword == "SUBSCRIPT_SIZE":
            self.prop_subscript_size = value
        elif keyword == "SMALL_CAP_SIZE":
            self.prop_small_cap_size = value
        elif keyword == "UNDERLINE_POSITION":
            self.prop_underline_position = value
        elif keyword == "UNDERLINE_THICKNESS":
            self.prop_underline_thickness = value
        elif keyword == "STRIKEOUT_ASCENT":
            self.prop_strikeout_ascent = value
        elif keyword == "STRIKEOUT_DESCENT":
            self.prop_strikeout_descent = value
        elif keyword == "ITALIC_ANGLE":
            self.prop_italic_angle = value
        elif keyword == "CAP_HEIGHT":
            self.prop_cap_height = value
        elif keyword == "X_HEIGHT":
            self.prop_x_height = value
        elif keyword == "RELATIVE_SETWIDTH":
            self.prop_relative_setwidth = value
        elif keyword == "RELATIVE_WEIGHT":
            self.prop_relative_weight = value
        elif keyword == "RESOLUTION":
            self.prop_resolution = value
        elif keyword == "RESOLUTION_X":
            self.prop_resolution_x = value
        elif keyword == "RESOLUTION_Y":
            self.prop_resolution_y = value
        elif keyword == "FONT":
            self.prop_font = value
        elif keyword == "FACE_NAME":
            self.prop_face_name = value
        elif keyword == "FULL_NAME":
            self.prop_full_name = value
        elif keyword == "COPYRIGHT":
            self.prop_copyright = value
        elif keyword == "NOTICE":
            self.prop_notice = value
        elif keyword == "DESTINATION":
            self.prop_destination = value
        elif keyword == "FONT_TYPE":
            self.prop_font_type = value
        elif keyword == "FONT_VERSION":
            self.prop_font_version = value
        elif keyword == "RASTERIZER_NAME":
            self.prop_rasterizer_name = value
        elif keyword == "RASTERIZER_VERSION":
            self.prop_rasterizer_version = value
        elif keyword == "RAW_ASCENT":
            self.prop_raw_ascent = value
        elif keyword == "RAW_DESCENT":
            self.prop_raw_descent = value
        elif keyword == "FONT_ASCENT":
            self.prop_font_ascent = value
        elif keyword == "FONT_DESCENT":
            self.prop_font_descent = value
        elif keyword == "DEFAULT_CHAR":
            self.prop_default_char = value
    def get_ascent(self):
        if self.prop_font_ascent is not None:
            return self.prop_font_ascent
        ...
    def get_descent(self):
        if self.prop_font_descent is not None:
            return self.prop_font_descent
        ...
    def get_pixel_size(self):
        if self.prop_pixel_size is not None:
            return self.prop_pixel_size
        ...
    def get_pixel_count(row):
        count = 0
        for glyph in self.bdf_glyphs:
            count += glyph.get_pixel_count(row)
        return count
    def get_total_pixel_count(self):
        count = 0
        for glyph in self.bdf_glyphs:
            count += glyph.get_total_pixel_count()
        return count
    def get_max_pixel_row(self):
        return max(*[glyph.get_max_pixel_row() for glyph in self.bdf_glyphs])
    def get_min_pixel_row(self):
        return min(*[glyph.get_min_pixel_row() for glyph in self.bdf_glyphs])
    def get_comments(self):
        return [*self.comments] # copy
    def as_string(self):
        s = ""
        s += self.startfont_line()
        s += self.lines_in_order()
        s += self.comment_lines() # TODO: in order
        s += self.contentversion_line()
        s += self.font_line()
        s += self.size_line()
        s += self.fontboundingbox_line()
        s += self.metricsset_line()
        s += self.swidth_line()
        s += self.dwidth_line()
        s += self.swidth1_line()
        s += self.dwidth1_line()
        s += self.vvector_line()
        s += self.properties_lines() # TODO: in order
        s += self.glyphs_lines()
        s += self.endfont_line()
        return s
    def startfont_line(self):
        s = ""
        if self.bdf_version is not None:
            return "STARTFONT %f\n" % self.bdf_version
        return "STARTFONT %f\n" % 2.2
    def comment_lines(self):
        if self.was_printed("COMMENT"):
            return ""
        s = ""
        for c in self.get_comments():
            s += "CONTENT %s\n" % bdf_quote(c)
        return s
    def contentversion_line(self):
        if self.was_printed("CONTENTVERSION"):
            return ""
        if self.content_version is not None:
            return "CONTENVERSION %s\n" % self.content_version
        return ""
    def font_line(self):
        if self.was_printed("FONT"):
            return ""
        if self.font_name is not None:
            return "FONT %s\n" % self.font_name
        return ""
    def size_line(self):
        if self.was_printed("SIZE"):
            return ""
        if None not in [self.point_size, self.res_x, self.res_y]:
            return "SIZE %d %d %d\n" % (self.point_size, self.res_x, self.res_y)
        return ""
    def fontboundingbox_line(self):
        if self.was_printed("FONTBOUNDINGBOX"):
            return ""
        if None not in [self.bb_x, self.bb_y, self.bb_ofs_x, self.bb_ofs_y]:
            return "FONTBOUNDINGBOX %d %d %d %d\n" % (self.bb_x, self.bb_y, self.bb_ofs_x, self.bb_ofs_y)
        return ""
    def metricsset_line(self):
        if self.was_printed("METRICSSET"):
            return ""
        if self.metrics_set is not None:
            return "METRICSSET %d\n" % self.metrics_set
        return ""
    def swidth_line(self):
        if self.was_printed("SWIDTH"):
            return ""
        if None not in [self.swidth_x, self.swidth_y]:
            return "SWIDTH %d %d\n" % (self.swidth_x, self.swidth_y)
        return ""
    def dwidth_line(self):
        if self.was_printed("DWIDTH"):
            return ""
        if None not in [self.dwidth_x, self.dwidth_y]:
            return "DWIDTH %d %d\n" % (self.dwidth_x, self.dwidth_y)
        return ""
    def swidth1_line(self):
        if self.was_printed("SWIDTH1"):
            return ""
        if None not in [self.swidth1_x, self.swidth1_y]:
            return "SWIDTH1 %d %d\n" % (self.swidth1_x, self.swidth1_y)
        return ""
    def dwidth1_line(self):
        if self.was_printed("DWIDTH1"):
            return ""
        if None not in [self.dwidth1_x, self.dwidth1_y]:
            return "DWIDTH1 %d %d\n" % (self.dwidth1_x, self.dwidth1_y)
        return ""
    def vvector_line(self):
        if self.was_printed("VVECTOR"):
            return ""
        if None not in [self.vvector_x, self.vvector_y]:
            return "VVECTOR %d %d\n" % (self.vvector_x, self.vvector_y)
        return ""
    def properties_lines(self):
        if self.was_printed("STARTPROPERTIES"):
            return ""
        s = ""
        if len(self.properties):
            s += "STARTPROPERTIES %d\n" % len(self.properties)
            for (key, value) in self.properties:
                print("%s %s\n" % (key, bdf_quote(value)))
            s += "ENDPROPERTIES\n"
        return s
    def glyphs_lines(self):
        if self.was_printed("CHARS"):
            return ""
        s = ""
        if len(self.bdf_glyphs):
            s += "CHARS %d\n" % len(self.bdf_glyphs)
            for bdf_glyph in self.bdf_glyphs:
                s += bdf_glyph.as_string()
        return s
    def endfont_line(self):
        return "ENDFONT\n"
    def was_printed(self, line_type):
        if self.printed[line_type] = True
            return True
        self.printed[line_type] = True
        return False
    def append_line_type(self, line_type, fn):
        self.lines_in_order.append([line_type, fn])
    def lines_in_order(self):
        s = ""
        for [line_type, fn] in self.lines_in_order:
            s += fn()
        return s
    def append_line_type(self, line_type, fn):
        self.lines_in_order.append([line_type, fn])
    def lines_in_order(self):
        s = ""
        for [line_type, fn] in self.lines_in_order:
            s += fn()
        return s
