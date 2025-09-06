import re, fontforge

from bdf_utils import bin_data_to_hex_data, hex_data_to_bin_data

unknown_charname_counter = 0

BITMAP_PIXEL_LINE_TYPE_NORMAL = 0
BITMAP_PIXEL_LINE_TYPE_BASELINE = 1
BITMAP_PIXEL_LINE_TYPE_CAP_HEIGHT = 2

class BDFChar:
    def __init__(self, name = None, font = None):
        self.name = name
        self.font = font
        self.encoding = None
        self.non_standard_encoding = None
        self.has_bbx = False
        self.bbx_x = None
        self.bbx_y = None
        self.bbx_ofs_x = None
        self.bbx_ofs_y = None
        self.swidth_x = None
        self.swidth_y = None
        self.dwidth_x = None
        self.dwidth_y = None
        self.swidth1_x = None
        self.swidth1_y = None
        self.dwidth1_x = None
        self.dwidth1_y = None
        self.bitmap_data_cap_height_idx = None
        self.bitmap_data_baseline_idx = None
        self.bitmap_data_hex_line_count = 0
        self.bitmap_data_pixel_line_count = 0

    def get_swidth_x(self):
        if self.swidth_x != None:
            return self.swidth_x
        if self.dwidth_x != None:
            return self.dwidth_x / 72000.0 * self.get_resolution_x() * self.font.get_point_size()
        return self.font.get_swidth_x()

    def get_swidth_y(self):
        return 0

    def get_dwidth_x(self):
        if self.dwidth_x != None:
            return self.dwidth_x
        if self.swidth_x != None:
            return int(round(self.swidth_x * 72000.0 / self.get_resolution_x() / self.font.get_point_size()))
        return self.font.get_dwidth_x()

    def get_dwidth_y(self):
        return 0

    def get_resolution_x(self):
        return self.font.get_resolution_x()

    def get_resolution_y(self):
        return self.font.get_resolution_y()

    # row =  0 for pixel row just above baseline
    # row = -1 for pixel row just below baseline
    def pixelCountByRow(self, row):
        row = int(round(row))
        top_y = self.bbx_ofs_y + self.bbx_y - 1
        row_idx = top_y - row   # into bitmap_data
        if row_idx < 0 or row_idx >= len(self.bitmap_data):
            return 0
        return self.bitmap_data[row_idx].count('1')

    def set_bbx(self, x, y, ofs_x, ofs_y):
        self.has_bbx = True
        self.bbx_x       = int(x)          # integer pixel values, offsets relative to origin
        self.bbx_y       = int(y)
        self.bbx_ofs_x = int(ofs_x)
        self.bbx_ofs_y = int(ofs_y)

    def set_swidth(self, x, y):
        self.swidth_x = int(x)
        self.swidth_y = int(y)
        if self.swidth_y != 0.0:
            raise Exception("SWIDTH with non-zero Y coordinate not supported")

    def set_dwidth(self, x, y):
        self.dwidth_x = int(x)
        self.dwidth_y = int(y)
        if self.dwidth_y != 0.0:
            raise Exception("DWIDTH with non-zero Y coordinate not supported")

    def set_encoding(self, encoding, non_standard_encoding):
        self.encoding = int(encoding)
        if self.encoding == -1:
            self.encoding = None
        self.non_standard_encoding = (None if non_standard_encoding is None
                                    else int(non_standard_encoding))

    def append_bitmap_data(self, data):
        self.bitmap_data_hex_line_count += 1
        self.bitmap_data.append(str(data).strip())

    def start_bitmap(self):
        self.bitmap_data = []
        self.bitmap_data_hex_line_count = 0
        self.bitmap_data_pixel_line_count = 0
        self.bitmap_data_cap_height_idx = None
        self.bitmap_data_baseline_idx = None

    def end_bitmap(self):
        self.bitmap_data = [s.upper() + "0" * ((2 - len(s) % 2) % 2) for s in self.bitmap_data]
        maxlen = max([len(s) for s in self.bitmap_data])
        self.bitmap_data = [s + "0" * (maxlen - len(s)) for s in self.bitmap_data]
        if self.bitmap_data_hex_line_count == 0:
            self.bbx_y = len(self.bitmap_data)
            if self.bitmap_data_baseline_idx is not None:
                self.bbx_ofs_y = self.bitmap_data_baseline_idx - len(self.bitmap_data) + 1
            else:
                self.bbx_ofs_y = 0

    def append_bitmap_pixel_data(self, start, bin_data):
        self.bitmap_data_pixel_line_count += 1
        if start == '^':
            line_type = BITMAP_PIXEL_LINE_TYPE_CAP_HEIGHT
        elif start == '+':
            line_type = BITMAP_PIXEL_LINE_TYPE_BASELINE
        else:
            line_type = BITMAP_PIXEL_LINE_TYPE_NORMAL
        if line_type == BITMAP_PIXEL_LINE_TYPE_CAP_HEIGHT:
            self.bitmap_data_cap_height_idx = len(self.bitmap_data)
        elif line_type == BITMAP_PIXEL_LINE_TYPE_BASELINE:
            self.bitmap_data_baseline_idx = len(self.bitmap_data)
        self.bitmap_data.append(bin_data_to_hex_data(bin_data))

    def __str__(self):
        string = ""
        string += self.get_startchar_line()
        string += self.get_encoding_line()
        string += self.get_bbx_line()
        string += self.get_dwidth_line()
        string += self.get_swidth_line()
        if len(self.bitmap_data):
            string += "BITMAP\n"
            string += "\n".join(self.bitmap_data) + "\n"
        string += "ENDCHAR\n"
        return string

    def get_startchar_line(self):
        if self.encoding is None or self.encoding < 0:
            if self.name is None:
                return "STARTCHAR %s\n" % generateNewUnknownCharname()
            else:
                return "STARTCHAR %s\n" % self.name
        else:
            if self.name is not None:
                return "STARTCHAR %s\n" % self.name
            else:
                return "STARTCHAR %s\n" % fontforge.nameFromUnicode(self.encoding)

    def get_encoding_line(self):
        if self.non_standard_encoding is None:
            if self.encoding is None:
                if self.name is not None:
                    encoding = fontforge.unicodeFromName(self.name)
                    return "ENCODING %d\n" % encoding
                return "ENCODING -1\n"
            return "ENCODING %d\n" % self.encoding
        return "ENCODING %d %d\n" % self.encoding, self.non_standard_encoding

    def get_bbx_line(self):
        [x, y, ofs_x, ofs_y] = [self.get_bbx_x(),
                                    self.get_bbx_y(),
                                    self.get_bbx_ofs_x(),
                                    self.get_bbx_ofs_y()]
        if x is None or y is None or ofs_x is None or ofs_y is None:
            return ""
        return "BBX %d %d %d %d\n" % (x, y, ofs_x, ofs_y)

    def get_dwidth_line(self):
        if self.dwidth_x is None:
            return ""
        return "DWIDTH %d 0\n" % self.dwidth_x

    def get_swidth_line(self):
        if self.swidth_x is None:
            return ""
        return "SWIDTH %d 0\n" % self.swidth_x

    def get_bbx_x(self):
        if self.bbx_x is not None:
            return self.bbx_x
        return self.font.bbx_x

    def get_bbx_y(self):
        if self.bbx_y is not None:
            return self.bbx_y
        return self.font.bbx_y

    def get_bbx_ofs_x(self):
        if self.bbx_ofs_x is not None:
            return self.bbx_ofs_x
        return self.font.bbx_ofs_x

    def get_bbx_ofs_y(self):
        if self.bbx_ofs_y is not None:
            return self.bbx_ofs_y
        return self.font.bbx_ofs_y

def generateNewUnknownCharName():
    unknown_charname_counter += 1
    return "unknown%d" % unknown_charname_counter
