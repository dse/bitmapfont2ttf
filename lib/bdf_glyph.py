import os, sys, fontforge
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))

from bdf_utils import bdf_quote

class BDFGlyph:
    def __init__(self):
        self.name = None
        self.encoding = None
        self.alt_encoding = None
        self.bb_x = None
        self.bb_y = None
        self.bb_ofs_x = None
        self.bb_ofs_y = None
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
        self.bitmap_data = []
        self.lines_in_order = []
        self.unknown_name_counter = 0
        self.printed = {}
    def set_name(self, value):
        self.name = value
    def set_encoding(self, value):
        self.encoding = value
        # self.update_encoding_line()
    def set_alt_encoding(self, value):
        self.alt_encoding = value
        # self.update_encoding_line()
    def set_bounding_box(self, bb_x, bb_y, bb_ofs_x, bb_ofs_y):
        self.bb_x = bb_x
        self.bb_y = bb_y
        self.bb_ofs_x = bb_ofs_x
        self.bb_ofs_y = bb_ofs_y
    def set_swidth(self, x, y):
        self.swidth_x = x
        self.swidth_y = y
    def set_dwidth(self, x, y):
        self.dwidth_x = x
        self.dwidth_y = y
        self.dwidth_line = "DWIDTH %d %d" % (x, y)
    def set_swidth1(self, x, y):
        self.swidth1_x = x
        self.swidth1_y = y
        self.swidth1_line = "SWIDTH1 %d %d" % (x, y)
    def set_dwidth1(self, x, y):
        self.dwidth1_x = x
        self.dwidth1_y = y
        self.dwidth1_line = "DWIDTH1 %d %d" % (x, y)
    def set_vvector(self, x, y):
        self.vvector_x = x
        self.vvector_y = y
        self.vvector_line = "VVECTOR %d %d" % (x, y)
    def append_bitmap_data(self, data):
        self.bitmap_data.append(data)
    def get_bounding_box_x(self):
        return self.bb_x if self.bb_x is not None else self.font.bb_x
    def get_bounding_box_y(self):
        return self.bb_y if self.bb_y is not None else self.font.bb_y
    def get_bounding_box_offset_x(self):
        return self.bb_ofs_x if self.bb_ofs_x is not None else self.font.bb_ofs_x
    def get_bounding_box_offset_y(self):
        return self.bb_ofs_y if self.bb_ofs_y is not None else self.font.bb_ofs_y
    def get_bounding_box(self):
        return [self.get_bounding_box_x(), self.get_bounding_box_y(),
                self.get_bounding_box_offset_x(), self.get_bounding_box_offset_y()]
    def get_swidth_x(self):
        return self.swidth_x if self.swidth_x is not None else self.font.swidth_x
    def get_swidth_y(self):
        return self.swidth_y if self.swidth_y is not None else self.font.swidth_y
    def get_dwidth_x(self):
        return self.dwidth_x if self.dwidth_x is not None else self.font.dwidth_x
    def get_dwidth_y(self):
        return self.dwidth_y if self.dwidth_y is not None else self.font.dwidth_y
    def get_swidth1_x(self):
        return self.swidth1_x if self.swidth1_x is not None else self.font.swidth1_x
    def get_swidth1_y(self):
        return self.swidth1_y if self.swidth1_y is not None else self.font.swidth1_y
    def get_dwidth1_x(self):
        return self.dwidth1_x if self.dwidth1_x is not None else self.font.dwidth1_x
    def get_dwidth1_y(self):
        return self.dwidth1_y if self.dwidth1_y is not None else self.font.dwidth1_y
    def get_vvector_x(self):
        return self.vvector_x if self.vvector_x is not None else self.font.vvector_x
    def get_vvector_y(self):
        return self.vvector_y if self.vvector_y is not None else self.font.vvector_y
    def get_encoding(self):
        return self.encoding
    def get_alt_encoding(self):
        return self.alt_encoding if self.encoding < 0 else -1
    def update_lines(self):
        if self.encoding is not None:
            if self.alt_encoding is None or self.alt_encoding < 0:
                self.encoding_line = "ENCODING %d" % self.encoding
            else:
                self.encoding_line = "ENCODING %d %d" % (self.encoding, self.alt_encoding)
        if self.name is not None:
            self.startchar_line = "STARTCHAR %s" % self.name
        if self.bb_x is not None:
            self.bbx_line = "BBX %d %d %d %d" % (self.bb_x, self.bb_y, self.bb_ofs_x, self.bb_ofs_y)
        if self.swidth_x is not None:
            self.swidth_line = "SWIDTH %d %d" % (self.swidth_x, self.swidth_y)
        if self.dwidth_x is not None:
            self.dwidth_line = "DWIDTH %d %d" % (self.dwidth_x, self.dwidth_y)
        if self.swidth1_x is not None:
            self.swidth1_line = "SWIDTH1 %d %d" % (self.swidth1_x, self.swidth1_y)
        if self.dwidth1_x is not None:
            self.dwidth1_line = "DWIDTH1 %d %d" % (self.dwidth1_x, self.dwidth1_y)
        if self.vvector_x is not None:
            self.vvector_line = "VVECTOR %d %d" % (self.vvector_x, self.vvector_y)
    def get_pixel_count(row):
        raw_row = self.y_to_raw_row(row)
        if raw_row not in range(0, len(self.bitmap_data)):
            return 0
        return self.get_bitmap_row_pixel_count(self.bitmap_data[raw_row])
    def get_bitmap_row_pixel_count(hex_data):
        count = 0
        for char in hex_data:
            char = char.lower()
            if char == '0':
                count += 0
            elif char in '1248':
                count += 1
            elif char in '3569ac':
                count += 2
            elif char in 'edb7':
                count += 3
            elif char == 'f':
                count += 4
            else:
                raise Exception('invalid character in bitmap data')
        return count
    def get_total_pixel_count(self):
        count = 0
        for hex_data in self.bitmap_data:
            count += self.get_bitmap_row_pixel_count(hex_data)
        return count
    def get_max_pixel_row(self):
        ...
    def get_min_pixel_row(self):
        ...
    def trace_to_fontforge_glyph(glyph):
        ...
    def y_to_raw_row(y):
        return (self.get_bounding_box_y() -
                self.get_bounding_box_offset_y() - 1 - y)
    def raw_row_to_y(raw_row):
        return (self.get_bounding_box_y() -
                self.get_bounding_box_offset_y() - 1 - raw_row)
    def as_string(self):
        s = ""
        s += self.startchar_line()
        s += self.get_lines_in_order()
        s += self.encoding_line()
        s += self.bbx_line()
        s += self.swidth_line()
        s += self.dwidth_line()
        s += self.swidth1_line()
        s += self.dwidth1_line()
        s += self.vvector_line()
        s += self.bitmap_lines() # always at the end
        s += self.endchar_line() # always at the end
        return s
    def startchar_line(self):
        if self.name is not None:
            return "STARTCHAR %s\n" % bdf_quote(self.name)
        if self.encoding >= 0:
            return "STARTCHAR %s\n" % fontforge.nameFromUnicode(self.encoding)
        self.unknown_name_counter += 1
        return "STARTCHAR unk%d" % self.unknown_name_counter
    def encoding_line(self):
        if self.was_printed("ENCODING"):
            return ""
        if self.alt_encoding is None:
            return "ENCODING %d\n" % self.encoding
        else:
            return "ENCODING %d %d\n" % (self.encoding, self.alt_encoding)
    def bbx_line(self):
        if self.was_printed("BBX"):
            return ""
        if None not in [self.bb_x, self.bb_y, self.bb_ofs_x, self.bb_ofs_y]:
            return "BBX %d %d %d %d\n" % (self.bb_x, self.bb_y, self.bb_ofs_x, self.bb_ofs_y)
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
    def bitmap_lines(self):
        if self.was_printed("BITMAP"):
            return ""
        s = ""
        if len(self.bitmap_data):
            s += "BITMAP\n"
            for data in self.bitmap_data:
                s += data + "\n"
        return s
    def endchar_line(self):
        return "ENDCHAR\n"
    def was_printed(self, type):
        if self.printed[type]:
            return True
        self.printed[type] = True
        return False
    def append_line_type(self, line_type, fn):
        self.lines_in_order.append([line_type, fn])
    def get_lines_in_order(self):
        s = ""
        for [line_type, fn] in self.lines_in_order:
            s += fn()
        return s
