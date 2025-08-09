import os, sys, re
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))

DEFAULT_WEIGHT_NAME = "Medium"
DEFAULT_SLANT       = "R"
DEFAULT_SETWIDTH_NAME = "Normal"
DEFAULT_ADD_STYLE_NAME = None

class BDFFont:
    def __init__(self):
        self.line_number = 0
        self.lines = []
        self.glyphs = []
        self.prop_lines = []

        self.comments = []
        self.raw_props = {}

        self.startfont             = None
        self.contentversion        = None
        self.font                  = None
        self.point_size            = None
        self.x_res                 = None
        self.y_res                 = None
        self.bbx_x                 = None
        self.bbx_y                 = None
        self.bbx_ofs_x             = None
        self.bbx_ofs_y             = None
        self.metricsset            = None
        self.swidth_x              = None
        self.swidth_y              = None
        self.dwidth_x              = None
        self.dwidth_y              = None
        self.swidth1_x             = None
        self.swidth1_y             = None
        self.dwidth1_x             = None
        self.dwidth1_y             = None
        self.vvector_x             = None
        self.vvector_y             = None
        self.startproperties_count = None
        self.chars_count           = None

        self.prop_foundry             = None
        self.prop_family_name         = None
        self.prop_weight_name         = None
        self.prop_slant               = None
        self.prop_setwidth_name       = None
        self.prop_add_style_name      = None
        self.prop_pixel_size          = None
        self.prop_point_size          = None
        self.prop_resolution_x        = None
        self.prop_resolution_y        = None
        self.prop_spacing             = None
        self.prop_average_width       = None
        self.prop_charset_registry    = None
        self.prop_charset_encoding    = None
        self.prop_min_space           = None
        self.prop_norm_space          = None
        self.prop_max_space           = None
        self.prop_end_space           = None
        self.prop_avg_capital_width   = None
        self.prop_avg_lowercase_width = None
        self.prop_quad_width          = None
        self.prop_figure_width        = None
        self.prop_superscript_x       = None
        self.prop_superscript_y       = None
        self.prop_subscript_x         = None
        self.prop_subscript_y         = None
        self.prop_superscript_size    = None
        self.prop_subscript_size      = None
        self.prop_small_cap_size      = None
        self.prop_underline_position  = None
        self.prop_underline_thickness = None
        self.prop_strikeout_ascent    = None
        self.prop_strikeout_descent   = None
        self.prop_italic_angle        = None
        self.prop_cap_height          = None
        self.prop_x_height            = None
        self.prop_relative_setwidth   = None
        self.prop_relative_weight     = None
        self.prop_weight              = None
        self.prop_resolution          = None
        self.prop_font                = None
        self.prop_face_name           = None
        self.prop_full_name           = None
        self.prop_copyright           = None
        self.prop_notice              = None
        self.prop_destination         = None
        self.prop_font_type           = None
        self.prop_font_version        = None
        self.prop_rasterizer_name     = None
        self.prop_rasterizer_version  = None
        self.prop_raw_ascent          = None
        self.prop_raw_descent         = None

        self.xlfd_foundry          = None # misc
        self.xlfd_family_name      = None # fixed
        self.xlfd_weight_name      = None # medium
        self.xlfd_slant            = None # r
        self.xlfd_setwidth_name    = None # normal
        self.xlfd_add_style_name   = None # 
        self.xlfd_pixel_size       = None # 13
        self.xlfd_point_size       = None # 120
        self.xlfd_resolution_x     = None # 75
        self.xlfd_resolution_y     = None # 75
        self.xlfd_spacing          = None # c
        self.xlfd_average_width    = None # 60
        self.xlfd_charset_registry = None # iso10646
        self.xlfd_charset_encoding = None # 1

    def __str__(self):
        s = ""
        for line in self.lines:
            s += line["text"] + "\n"
            if "keyword" not in line:
                continue
            if line["keyword"] == "STARTPROPERTIES":
                for line2 in self.prop_lines:
                    s += line2["text"] + "\n"
            if line["keyword"] == "CHARS":
                for glyph in self.glyphs:
                    s += str(glyph)
        return s

    def get_lines_matching_keyword(self, keyword, property=False):
        line_list = self.prop_lines if property else self.lines
        if type(keyword) == list:
            return [line for line in line_list if "keyword" in line and line["keyword"] in keyword]
        return [line for line in line_list if "keyword" in line and line["keyword"] == keyword]

    def get_line_indexes_matching_keyword(self, keyword, property=False):
        line_list = self.prop_lines if property else self.lines
        if type(keyword) == list:
            return [i for i in range(0, len(line_list))
                    if "keyword" in line_list[i] and line_list[i]["keyword"] in keyword]
        return [i for i in range(0, len(line_list))
                if "keyword" in line_list[i] and line_list[i]["keyword"] == keyword]

    def get_first_line_index_matching_keyword(self, keyword, property=False):
        line_list = self.prop_lines if property else self.lines
        for i in range(0, len(line_list)):
            line = line_list[i]
            if "keyword" not in line:
                continue
            if type(keyword) == str and line["keyword"] == keyword:
                return i
            if type(keyword) == list and line["keyword"] in keyword:
                return i
        return -1

    def remove_lines_matching_keyword(self, keyword, keep_last=False, property=False):

        # line_list = [{A}, {B}, {C}, {D}, {E}, {F}, {G}, {H}, {I}, {J}, {K}, {L}]
        # indexes = [2, 4, 8, 10]
        # orig_index_count = 4
        # i = 3
        # last_idx = 10
        # i = 2
        #   line_list.remove(8)
        # i is 2:
        #   indexes[i] = 8
        #   line_list = [{A}, {B}, {C}, {D}, {E}, {F}, {G}, {H}, {J}, {K}, {L}]
        # i = 1:
        #   indexes[i] = 4
        #   line_list = [{A}, {B}, {C}, {D}, {F}, {G}, {H}, {J}, {K}, {L}]
        # i = 0:
        #   indexes[i] = 2
        #   line_list = [{A}, {B}, {D}, {F}, {G}, {H}, {J}, {K}, {L}]

        line_list = self.prop_lines if property else self.lines
        indexes = self.get_line_indexes_matching_keyword(keyword, property)
        if len(indexes) == 0:
            return
        orig_index_count = len(indexes)
        i = len(indexes) - 1
        if keep_last:
            last_idx = indexes[-1]
            i = len(indexes) - 2
        while i >= 0:
            line_list[indexes[i]:indexes[i]+1] = []
            i -= 1
        if keep_last:
            return line_list[last_idx - (orig_index_count - len(indexes))]

    def set_startfont(self, value):
        self.remove_lines_matching_keyword("STARTFONT")
        self.lines.insert(0, {
            "keyword": "STARTFONT",
            "words": [str(value)],
            "params": [float(value)],
            "text": "STARTFONT %s" % self.escape(value)
        })

    def append_comment(self, value):
        comment_line = {
            "keyword": "COMMENT",
            "words": [str(value)],
            "params": [str(value)],
            "text": "COMMENT %s" % self.escape(value)
        }
        indexes = self.get_line_indexes_matching_keyword("COMMENT")
        if len(indexes) == 0:
            self.lines.insert(1, comment_line)
        else:
            index = indexes[-1]
            self.lines.insert(index + 1, comment_line)

    def update_line(self, keyword, value, property=False):
        line_list = self.prop_lines if property else self.lines
        keyword = keyword.upper()
        line = self.remove_lines_matching_keyword(keyword, keep_last=True, property=property)
        if line:
            line["params"] = [value]
            line["orig_words"] = None
            line["orig_text"] = None
            line["words"] = None
            line["text"] = "%s %s" % (keyword, self.escape(value))
        else:
            keywords = ["CHARS", "STARTPROPERTIES"]
            idx = self.get_first_line_index_matching_keyword(keywords, property=property)
            line = {
                "keyword": keyword,
                "params": [value],
                "text": "%s %s" % (keyword, self.escape(value)),
            }
            if idx == -1:
                if not property:
                    raise Exception("no %s line found" % " or ".join(keywords))
                line_list.insert(len(line_list) - 1, line)
            else:
                if property:
                    line_list.insert(idx - 1, line)
                else:
                    line_list.insert(idx, line)

    def set_contentversion(self, value):
        self.contentversion = int(value)
        self.update_line("CONTENTVERSION", value)
    def set_font(self, value):
        self.font = str(value)
        self.update_line("FONT", value)

        xlfd = self.parse_xlfd(value)
        if xlfd != None:
            self.xlfd_foundry          = xlfd["foundry"]
            self.xlfd_family_name      = xlfd["family_name"]
            self.xlfd_weight_name      = xlfd["weight_name"]
            self.xlfd_slant            = xlfd["slant"]
            self.xlfd_setwidth_name    = xlfd["setwidth_name"]
            self.xlfd_add_style_name   = xlfd["add_style_name"]
            self.xlfd_pixel_size       = xlfd["pixel_size"]
            self.xlfd_point_size       = xlfd["point_size"]
            self.xlfd_resolution_x     = xlfd["resolution_x"]
            self.xlfd_resolution_y     = xlfd["resolution_y"]
            self.xlfd_spacing          = xlfd["spacing"]
            self.xlfd_average_width    = xlfd["average_width"]
            self.xlfd_charset_registry = xlfd["charset_registry"]
            self.xlfd_charset_encoding = xlfd["charset_encoding"]
        else:
            self.xlfd_foundry          = None
            self.xlfd_family_name      = None
            self.xlfd_weight_name      = None
            self.xlfd_slant            = None
            self.xlfd_setwidth_name    = None
            self.xlfd_add_style_name   = None
            self.xlfd_pixel_size       = None
            self.xlfd_point_size       = None
            self.xlfd_resolution_x     = None
            self.xlfd_resolution_y     = None
            self.xlfd_spacing          = None
            self.xlfd_average_width    = None
            self.xlfd_charset_registry = None
            self.xlfd_charset_encoding = None
            
    def set_point_size(self, value):
        self.point_size = int(value)
        self.update_line("SIZE", [self.point_size, self.x_res, self.y_res])
    def set_x_res(self, value):
        self.x_res = int(value)
        self.update_line("SIZE", [self.point_size, self.x_res, self.y_res])
    def set_y_res(self, value):
        self.y_res = int(value)
        self.update_line("SIZE", [self.point_size, self.x_res, self.y_res])
    def set_bbx_x(self, value):
        self.bbx_x = value
        self.update_line("FONTBOUNDINGBOX", [self.bbx_x, self.bbx_y, self.bbx_ofs_x, self.bbx_ofs_y])
    def set_bbx_y(self, value):
        self.bbx_y = value
        self.update_line("FONTBOUNDINGBOX", [self.bbx_x, self.bbx_y, self.bbx_ofs_x, self.bbx_ofs_y])
    def set_bbx_ofs_x(self, value):
        self.bbx_ofs_x = value
        self.update_line("FONTBOUNDINGBOX", [self.bbx_x, self.bbx_y, self.bbx_ofs_x, self.bbx_ofs_y])
    def set_bbx_ofs_y(self, value):
        self.bbx_ofs_y = value
        self.update_line("FONTBOUNDINGBOX", [self.bbx_x, self.bbx_y, self.bbx_ofs_x, self.bbx_ofs_y])
    def set_metricsset(self, value):
        self.metricsset = value
        self.update_line("METRICSSET", value)

    def set_swidth_x(self, value):
        self.swidth_x = value
        self.update_line("SWIDTH", [self.swidth_x, self.swidth_y])
    def set_swidth_y(self, value):
        self.swidth_y = value
        self.update_line("SWIDTH", [self.swidth_x, self.swidth_y])

    def set_dwidth_x(self, value):
        self.dwidth_x = value
        self.update_line("DWIDTH", [self.dwidth_x, self.dwidth_y])
    def set_dwidth_y(self, value):
        self.dwidth_y = value
        self.update_line("DWIDTH", [self.dwidth_x, self.dwidth_y])

    def set_swidth1_x(self, value):
        self.swidth1_x = value
        self.update_line("SWIDTH1", [self.swidth1_x, self.swidth1_y])
    def set_swidth1_y(self, value):
        self.swidth1_y = value
        self.update_line("SWIDTH1", [self.swidth1_x, self.swidth1_y])

    def set_dwidth1_x(self, value):
        self.dwidth1_x = value
        self.update_line("DWIDTH1", [self.swidth1_x, self.swidth1_y])
    def set_dwidth1_y(self, value):
        self.dwidth1_y = value
        self.update_line("DWIDTH1", [self.swidth1_x, self.swidth1_y])

    def set_vvector_x(self, value):
        self.vvector_x = value
        self.update_line("VVECTOR", [self.vvector_x, self.vvector_y])
    def set_vvector_y(self, value):
        self.vvector_y = value
        self.update_line("VVECTOR", [self.vvector_x, self.vvector_y])

    def set_prop(self, keyword, value):
        self.update_line(keyword, value, property=True)

    def escape(self, value):
        if type(value) == int:
            return str(value)
        if type(value) == float:
            return str(value)
        if type(value) == str:
            if '"' in value or ' ' in value:
                value = value.replace('"', '""')
                return '"%s"' % value
            return value
        if type(value) == list:
            items = []
            for i in range(0, len(value)):
                items.append(self.escape(value[i]))
            return " ".join(items)
        raise Exception("invalid value type: %s" % repr(type(value)))

    def sanity_check(self):

        has_inconsistencies = False

        # string properties
        #------------------

        fy2 = self.prop_foundry
        fy3 = self.xlfd_foundry
        if fy2 != None and fy3 != None and fy2 != fy3:
            has_inconsistencies = True
            sys.stderr.write("WARNING: inconsistent FOUNDRY values: %s and %s\n" % (repr(fy2), repr(fy3)))

        fn2 = self.prop_family_name
        fn3 = self.xlfd_family_name
        if fn2 != None and fn3 != None and fn2 != fn3:
            has_inconsistencies = True
            sys.stderr.write("WARNING: inconsistent FAMILY_NAME values: %s and %s\n" % (repr(fn2), repr(fn3)))

        wt2 = self.prop_weight_name
        wt3 = self.xlfd_weight_name
        if wt2 != None and wt3 != None and wt2 != wt3:
            has_inconsistencies = True
            sys.stderr.write("WARNING: inconsistent WEIGHT_NAME values: %s and %s\n" % (repr(wt2), repr(wt3)))

        sl2 = self.prop_slant
        sl3 = self.xlfd_slant
        if sl2 != None and sl3 != None and sl2 != sl3:
            has_inconsistencies = True
            sys.stderr.write("WARNING: inconsistent SLANT values: %s and %s\n" % (repr(sl2), repr(sl3)))

        sw2 = self.prop_setwidth_name
        sw3 = self.xlfd_setwidth_name
        if sw2 != None and sw3 != None and sw2 != sw3:
            has_inconsistencies = True
            sys.stderr.write("WARNING: inconsistent SETWIDTH_NAME values: %s and %s\n" % (repr(sw2), repr(sw3)))

        as2 = self.prop_add_style_name
        as3 = self.xlfd_add_style_name
        if as2 != None and as3 != None and as2 != as3:
            has_inconsistencies = True
            sys.stderr.write("WARNING: inconsistent ADD_STYLE_NAME values: %s and %s\n" % (repr(as2), repr(as3)))

        sp2 = self.prop_spacing
        sp3 = self.xlfd_spacing
        if sp2 != None and sp3 != None and sp2 != sp3:
            has_inconsistencies = True
            sys.stderr.write("WARNING: inconsistent SPACING values: %s and %s\n" % (repr(sp2), repr(sp3)))

        cr2 = self.prop_charset_registry
        cr3 = self.xlfd_charset_registry
        if cr2 != None and cr3 != None and cr2 != cr3:
            has_inconsistencies = True
            sys.stderr.write("WARNING: inconsistent CHARSET_REGISTRY values: %s and %s\n" % (repr(cr2), repr(cr3)))

        ce2 = self.prop_charset_encoding
        ce3 = self.xlfd_charset_encoding
        if ce2 != None and ce3 != None and ce2 != ce3:
            has_inconsistencies = True
            sys.stderr.write("WARNING: inconsistent CHARSET_ENCODING values: %s and %s\n" % (repr(ce2), repr(ce3)))

        # int properties
        #---------------

        inconsistent_pixel_size_values = False
        inconsistent_point_size_values = False
        inconsistent_x_resolution_values = False
        inconsistent_y_resolution_values = False

        px2 = self.prop_pixel_size
        px3 = self.xlfd_pixel_size
        px  = px2
        if px2 != None and px3 != None and px2 != px3:
            has_inconsistencies = True
            px = None
            inconsistent_pixel_size_values = True
            sys.stderr.write("WARNING: inconsistent PIXEL_SIZE sizes: (2) %s; (3) %s\n" % (px2, px3))

        pt1 = self.point_size
        pt2 = self.prop_point_size # decipoints
        pt3 = self.xlfd_point_size  # decipoints
        pt22 = round(pt2 / 10) if pt2 != None else None # points
        pt33 = round(pt3 / 10) if pt3 != None else None # points
        pt   = pt1
        if (pt1  != None and pt22 != None and pt1  != pt22) or \
           (pt1  != None and pt33 != None and pt1  != pt33) or \
           (pt22 != None and pt33 != None and pt22 != pt33):
            has_inconsistencies = True
            pt = None
            inconsistent_point_size_values = True
            sys.stderr.write("WARNING: inconsistent point sizes: (1) %s; (2) %s; (3) %s\n" %
                             (repr(pt1), repr(pt2), repr(pt3)))

        rx1 = self.x_res
        rx2 = self.prop_resolution_x
        rx3 = self.xlfd_resolution_x
        rx  = rx1
        if (rx1 != None and rx2 != None and rx1 != rx2) or \
           (rx1 != None and rx3 != None and rx1 != rx3) or \
           (rx2 != None and rx3 != None and rx2 != rx3):
            has_inconsistencies = True
            rx = None
            inconsistent_x_resolution_values = True
            sys.stderr.write("WARNING: inconsistent x resolutions: (1) %s; (2) %s; (3) %s\n" %
                             (repr(rx1), repr(rx2), repr(rx3)))

        ry1 = self.y_res
        ry2 = self.prop_resolution_y
        ry3 = self.xlfd_resolution_y
        ry  = ry1
        if (ry1 != None and ry2 != None and ry1 != ry2) or \
           (ry1 != None and ry3 != None and ry1 != ry3) or \
           (ry2 != None and ry3 != None and ry2 != ry3):
            has_inconsistencies = True
            ry = None
            inconsistent_y_resolution_values = True
            sys.stderr.write("WARNING: inconsistent y resolutions: (1) %s; (2) %s; (3) %s\n" %
                             (repr(ry1), repr(ry2), repr(ry3)))

        if (not inconsistent_pixel_size_values) and \
           (not inconsistent_point_size_values) and \
           (not inconsistent_y_resolution_values):
            if px is not None and pt is not None and ry is not None:
                px4 = round(pt / 72.27 * ry)
                if px4 != px:
                    has_inconsistencies = True
                    sys.stderr.write("WARNING: inconsistent pixel sizes: px = %s; px4 = %s\n" %
                                     (px, px4))

        # not much sanity checking
        aw2 = self.prop_average_width
        aw3 = self.xlfd_average_width
        if aw2 != None and aw3 != None and aw2 != aw3:
            has_inconsistencies = True
            sys.stderr.write("WARNING: inconsistent AVERAGE_WIDTH values: (2) %s; (3) %s\n" %
                             (repr(aw2), repr(aw3)))

        return not has_inconsistencies

    def parse_xlfd(self, xlfd_str):
        xlfd_props = []
        while True:
            if xlfd_str[0] != '-':
                break
            if len(xlfd_props) >= 14:
                # would be too many properties
                return None
            xlfd_str = xlfd_str[1:]
            while True:
                if match := re.match(r'[^-]+', xlfd_str):
                    xlfd_props.append(match[0])
                    xlfd_str = xlfd_str(match.end())
                break
        if len(xlfd_props) != 14:
            return None
        [foundry, family_name, weight_name, slant, setwidth_name, add_style_name,
         pixel_size, point_size, resolution_x, resolution_y,
         spacing, average_width, charset_registry, charset_encoding] = \
             [(None if prop == "" else prop) for prop in xlfd_props]
        pixel_size    = int(pixel_size)    if pixel_size    is not None else None
        point_size    = int(point_size)    if point_size    is not None else None
        resolution_x  = int(resolution_x)  if resolution_x  is not None else None
        resolution_y  = int(resolution_y)  if resolution_y  is not None else None
        average_width = int(average_width) if average_width is not None else None
        return {
            "foundry":          foundry,
            "family_name":      family_name,
            "weight_name":      weight_name,
            "slant":            slant,
            "setwidth_name":    setwidth_name,
            "add_style_name":   add_style_name,
            "pixel_size":       pixel_size,
            "point_size":       point_size,
            "resolution_x":     resolution_x,
            "resolution_y":     resolution_y,
            "spacing":          spacing,
            "average_width":    average_width,
            "charset_registry": charset_registry,
            "charset_encoding": charset_encoding,
        }

    # don't compute things

    def get_specified_y_resolution(self):
        if self.y_res is not None:
            return self.y_res
        if self.prop_y_resolution is not None:
            return self.prop_y_resolution
        if self.xlfd_y_resolution is not None:
            return self.xlfd_y_resolution
        return None

    def get_specified_point_size(self):
        if self.point_size is not None:
            return self.point_size
        if self.prop_point_size is not None:
            return self.prop_point_size / 10
        if self.xlfd_point_size is not None:
            return self.xlfd_point_size / 10
        return None

    def get_specified_pixel_size(self):
        if self.prop_pixel_size is not None:
            return self.prop_pixel_size
        if self.xlfd_pixel_size is not None:
            return self.xlfd_pixel_size
        return None

    # compute things from other values

    # XLFD conventions: pixel size cannot be calculated
    def compute_pixel_size(self):
        ry = self.get_specified_y_resolution()
        pt = self.get_specified_point_size()
        if rx is None or pt is None:
            return None
        return round(pt * ry / 72.27)

    # XLFD conventions: y resolution cannot be calculated
    def compute_y_resolution():
        pass

    def compute_point_size():
        ry = get_specified_x_resolution()
        if ry is None:
            return None
        return round(px / ry * 72.27)

    # get specified or computed values

    def get_pixel_size(self):
        px = self.get_specified_pixel_size()
        if px is not None:
            return px
        # XLFD conventions: PIXEL_SIZE can be approximated
        return self.compute_pixel_size()

    def get_y_resolution():
        ry = self.get_specified_y_resolution()
        if ry is not None:
            return ry
        # XLFD conventions: y resolution cannot be calculated
        if self.loose:
            return self.compute_y_resolution()
        return None

    def get_point_size(self):
        pt = self.get_specified_point_size()
        if pt is not Null:
            return pt
        # XLFD conventions: point size cannot be calculated
        if self.loose:
            return self.compute_point_size()
        return None
