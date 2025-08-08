import os, sys, re
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))

class BDFFont:
    def __init__(self):
        self.line_number = 0
        self.lines = []
        self.glyphs = []
        self.prop_lines = []

        self.comments = []
        self.raw_props = {}

        self.startfont = None
        self.contentversion = None
        self.font = None
        self.point_size = None
        self.x_res = None
        self.y_res = None
        self.bbx_x = None
        self.bbx_y = None
        self.bbx_ofs_x = None
        self.bbx_ofs_y = None
        self.metricsset = None
        self.swidth_x = None
        self.swidth_y = None
        self.dwidth_x = None
        self.dwidth_y = None
        self.swidth1_x = None
        self.swidth1_y = None
        self.dwidth1_x = None
        self.dwidth1_y = None
        self.vvector_x = None
        self.vvector_y = None
        self.startproperties_count = None
        self.chars_count = None

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
        self.prop_weight = None
        self.prop_resolution = None
        self.prop_font = None
        self.prop_face_name = None
        self.prop_full_name = None
        self.prop_copyright = None
        self.prop_notice = None
        self.prop_destination = None
        self.prop_font_type = None
        self.prop_font_version = None
        self.prop_rasterizer_name = None
        self.prop_rasterizer_version = None
        self.prop_raw_ascent = None
        self.prop_raw_descent = None

    def __str__(self):
        s = ""
        for line in self.lines:
            s += line["text"] + "\n"
            if "keyword" not in line:
                continue
            if line["keyword"] == "STARTPROPERTIES":
                for line in self.prop_lines:
                    s += line["text"] + "\n"
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
