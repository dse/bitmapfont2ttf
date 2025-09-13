import re, fontforge

from bdf_utils import bin_data_to_hex_data, hex_data_to_bin_data, bdf_escape

unknown_charname_counter = 0

BITMAP_PIXEL_LINE_TYPE_NORMAL = 0
BITMAP_PIXEL_LINE_TYPE_BASELINE = 1
BITMAP_PIXEL_LINE_TYPE_CAP_HEIGHT = 2

DEFAULT_ORDER = [
    "ENCODING",
    "DWIDTH",
    "SWIDTH",
    "BBX",
]

class BDFChar:
    def __init__(self, name=None, font=None, order=None):
        self.name = name
        self.font = font
        self.encoding = None
        self.alt_encoding = None
        self.has_bbx = False
        self.bbx_x = None
        self.bbx_y = None
        self.bbx_ofs_x = None
        self.bbx_ofs_y = None
        self.swidth_x = None
        self.swidth_y = None
        self.dwidth_x = None
        self.dwidth_y = None
        self.bitmap_data_cap_height_idx = None
        self.bitmap_data_baseline_idx = None
        self.bitmap_data_hex_line_count = 0
        self.bitmap_data_pixel_line_count = 0
        self.normalize_char_names = False

        self.order = order
        if type(self.order) == str:
            self.order = self.order.replace(',', ' ').strip().split()
            self.order = [upper(x) for x in self.order]

    def get_swidth_x(self):
        if self.swidth_x is not None:
            return self.swidth_x
        if self.dwidth_x is not None:
            return (
                self.dwidth_x                                   # pixels
                / self.get_resolution_x()                       # inches
                * 72.27                                         # points
                / self.get_point_size()                         # em units
                * 1000                                          # milliem units
            )
        return self.font.get_swidth_x()

    def get_swidth_y(self):
        return 0

    def get_dwidth_x(self):
        if self.dwidth_x is not None:
            return self.dwidth_x
        if self.swidth_x is not None:
            return (
                self.swidth_x                                   # milliem units
                / 1000                                          # em units
                * self.get_point_size()                         # points
                / 72.27                                         # inches
                * self.get_resolution_x()                       # pixels
            )
        return self.font.get_dwidth_x()

    def get_dwidth_y(self):
        return 0

    def get_resolution_x(self):
        return self.font.get_resolution_x()

    def get_resolution_y(self):
        return self.font.get_resolution_y()

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

    def set_encoding(self, encoding, alt_encoding):
        self.encoding = int(encoding)
        if self.encoding == -1:
            self.encoding = None
        self.alt_encoding = (None if alt_encoding is None
                                    else int(alt_encoding))

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
        flags = {}
        if self.order is not None:
            for line_type in self.order:
                if not (line_type in flags and flags[line_type]):
                    string += self.get_line(line_type)
                    flags[line_type] = True
        for line_type in DEFAULT_ORDER:
            if not (line_type in flags and flags[line_type]):
                string += self.get_line(line_type)
                flags[line_type] = True
        if len(self.bitmap_data):
            string += "BITMAP\n"
            string += self.get_bitmap_data_lines()
        string += "ENDCHAR\n"
        return string

    def get_line(self, attr_type):
        if attr_type == "ENCODING":
            return self.get_encoding_line()
        if attr_type == "BBX":
            return self.get_bbx_line()
        if attr_type == "SWIDTH":
            return self.get_swidth_line()
        if attr_type == "DWIDTH":
            return self.get_dwidth_line()

    def get_normalized_charname_encoding(self):
        if self.name is None:
            if self.encoding is None:
                return [generate_new_unknown_char_name(), -1]
            elif self.encoding < 0:
                return [generate_new_unknown_char_name(), -1]
            else:
                return [fontforge.nameFromUnicode(encoding), self.encoding]
        elif match := re.match('U\+([0-9a-f]+)', self.name, flags=re.IGNORECASE):
            encoding_from_name = int(match[1], 16)
            if self.encoding is None:
                return [fontforge.nameFromUnicode(encoding_from_name), encoding_from_name]
            elif self.encoding < 0:
                return [fontforge.nameFromUnicode(encoding_from_name) + "." + generate_new_unknown_char_name(), -1]
            elif self.encoding == encoding_from_name:
                return [fontforge.nameFromUnicode(self.encoding), self.encoding]
            else:
                # std charname based on ENCODING overrides non-std charname specified in STARTCHAR
                return [fontforge.nameFromUnicode(self.encoding), self.encoding]
        else:
            encoding_from_name = fontforge.unicodeFromName(self.name)
            if encoding_from_name < 0:                          # invalid charname
                if self.encoding is None:
                    return [self.name, -1]
                elif self.encoding < 0:
                    return [self.name, -1]
                else:
                    return [fontforge.nameFromUnicode(self.encoding), self.encoding]
            else:
                if self.encoding is None:
                    return [self.name, encoding_from_name]
                elif self.encoding < 0:
                    return [self.name + "." + generate_new_unknown_char_name(), -1]
                elif self.encoding == encoding_from_name:
                    return [self.name, encoding_from_name]
                else:
                    process.stderr.write("WARNING: STARTCHAR %s (%d) conflicts with ENCODING %d\n" %
                                         (self.name, encoding_from_name, self.encoding))
                    # ENCODING overrides STARTCHAR
                    return [fontforge.nameFromUnicode(self.encoding), self.encoding]

    def get_startchar_line(self):
        return "STARTCHAR %s\n" % self.get_normalized_charname_encoding()[0]

    def get_encoding_line(self):
        string = "ENCODING %d" % self.get_normalized_charname_encoding()[1]
        if self.alt_encoding is not None:
            string += " %d" % self.alt_encoding
        return string + "\n"

    def get_bbx_line(self):
        [x, y, ofs_x, ofs_y] = [self.get_bbx_x(),
                                self.get_bbx_y(),
                                self.get_bbx_ofs_x(),
                                self.get_bbx_ofs_y()]
        if x is None or y is None or ofs_x is None or ofs_y is None:
            return self.font.get_bbx_line(name="BBX")
        # each character must specify own bounding box for some utils to work
        return "BBX %d %d %d %d\n" % (x, y, ofs_x, ofs_y)

    def get_dwidth_line(self):
        dwidth_x = self.get_dwidth_x()
        if dwidth_x is None:
            return ""
        return "DWIDTH %d 0\n" % dwidth_x

    def get_swidth_line(self):
        swidth_x = self.get_swidth_x()
        if swidth_x is None:
            return ""
        return "SWIDTH %d 0\n" % swidth_x

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

    def get_bitmap_data_lines(self):
        string = ""
        for data in self.bitmap_data:
            string += data.strip() + "\n"
        return string

def generate_new_unknown_char_name():
    global unknown_charname_counter
    unknown_charname_counter += 1
    return "unknown%d" % unknown_charname_counter
