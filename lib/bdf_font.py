import re
import sys
from bdf_char import BDFChar
from bdf_property_types import BDF_PROPERTY_TYPES
from bdf_utils import bdf_escape

DEFAULT_ORDER = [
    "FONT",
    "SIZE",
    "FONTBOUNDINGBOX",
    "COMMENT",
    "CONTENTVERSION",
    "METRICSSET",
    "DWIDTH",
    "SWIDTH",
    "PROPERTIES",
]

class BDFFont:
    def __init__(self, filename=None, order=None):
        self.bdf_version = None
        self.content_version = None
        self.font_name = None                                  # FONT (font.fontname)
        self.point_size = None
        self.res_x = None
        self.res_y = None
        self.has_bbx = False
        self.bbx_x = None
        self.bbx_y = None
        self.bbx_ofs_x = None
        self.bbx_ofs_y = None
        self.metrics_set = None
        self.swidth_x = None
        self.swidth_y = None
        self.dwidth_x = None
        self.dwidth_y = None
        self.properties = {}
        self.filename = None
        self.chars = []
        self.chars_by_encoding = {}
        self.charsByNonStandardEncoding = {}
        self.chars_by_name = {}
        self.comments = []

        self.order = order
        if type(self.order) == str:
            self.order = self.order.replace(',', ' ').strip().split()
            self.order = [upper(x) for x in self.order]

        if filename is not None:
            self.read(filename)

    def start_char(self, name):
        self.char = BDFChar(name=name, font=self)
        self.chars.append(self.char)
        self.char.bitmap_data = []

    def end_char(self):
        if self.char.encoding is not None:
            self.chars_by_encoding[self.char.encoding] = self.char
        if self.char.alt_encoding is not None:
            self.chars_by_encoding[self.char.alt_encoding] = self.char
        if self.char.name is not None:
            self.chars_by_name[self.char.name] = self.char

    def start_char_bitmap(self):
        self.char.start_bitmap()

    def end_char_bitmap(self):
        self.char.end_bitmap()

    def newChar(self, name, font):
        return BDFChar(name = name, font = font)

    def get_swidth_x(self):
        if self.swidth_x is not None:
            return self.swidth_x
        if self.dwidth_x is not None:
            return self.dwidth_x / 72000.0 * self.get_resolution_x() * self.get_point_size()
        raise Exception('cannot determine swidthX')

    def get_swidth_y(self):
        return 0

    def get_dwidth_x(self):
        if self.dwidth_x is not None:
            return self.dwidth_x
        if self.swidth_x is not None:
            return int(round(self.swidth_x * 72000.0 / self.get_resolution_x() / self.get_point_size()))
        raise Exception('cannot determine dwidthX')

    def get_dwidth_y(self):
        return 0

    def get_point_size(self):
        pt10 = self.properties["POINT_SIZE"]
        if pt10 is not None:
            return pt10 / 10.0
        raise Exception('font does not have a POINT_SIZE property')

    def setPixelSize(self, px):
        self.properties["PIXEL_SIZE"] = px
        self.properties["POINT_SIZE"] = int(round(px * 720.0 / self.get_resolution_y()))
        self.point_size = int(round(px * 72.0 / self.get_resolution_y()))

    def get_pixel_size(self):
        px = self.properties["PIXEL_SIZE"]
        if px is not None:
            return px
        raise Exception('font does not specify pixel size')

    def get_resolution_x(self):
        r = self.properties["RESOLUTION_X"]
        if r is not None:
            return r
        raise Exception('cannot determine resolutionX')

    def get_resolution_y(self):
        r = self.properties["RESOLUTION_Y"]
        if r is not None:
            return r
        raise Exception('cannot determine resolutionY')

    def ascent_px(self):
        ascent = self.properties["FONT_ASCENT"]
        if ascent is not None:
            return ascent
        raise Exception('cannot determine ascent_px')

    def descent_px(self):
        descent = self.properties["FONT_DESCENT"]
        if descent is not None:
            return descent
        raise Exception('cannot determine descent_px')

    def scalableToPixels(self, scalable):
        return 1.0 * scalable * self.properties["PIXEL_SIZE"] / 1000.0
    def scalableToPixelsX(self, scalable):
        return 1.0 * scalable * self.properties["PIXEL_SIZE"] / 1000.0 / self.get_aspect_ratio()

    def pixelsToScalable(self, pixels):
        return 1.0 * pixels * 1000.0 / self.properties["PIXEL_SIZE"]
    def pixelsToScalableX(self, pixels):
        return 1.0 * pixels * 1000.0 / self.properties["PIXEL_SIZE"] * self.get_aspect_ratio()

    # less than 1 means taller than wide; greater than 1 means wider than tall
    def get_aspect_ratio(self):
        return 1.0 * self.properties["RESOLUTION_Y"] / self.properties["RESOLUTION_X"]

    def set_bdf_version(self, value):
        self.bdf_version = float(value)

    def set_content_version(self, value):
        self.content_version = int(value)

    def set_font_name(self, value):
        self.font_name = str(value)

    def set_size(self, point_size, res_x, res_y):
        self.point_size = int(point_size)
        self.res_x = int(res_x)
        self.res_y = int(res_y)

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

    def set_metrics_set(self, value):
        self.metrics_set = int(value)

    def set_property(self, name, value):
        prop_type = self.get_property_type(name)
        self.properties[name] = prop_type(value)

    def delete_property(self, name):
        del self.properties[name]

    def get_property_type(self, name):
        prop_type = BDF_PROPERTY_TYPES.get(name)
        if prop_type is None:
            prop_type = str
        return prop_type

    def end_char_bitmap(self):
        self.char.end_bitmap()

    def set_char_bbx(self, *args):
        self.char.set_bbx(*args)

    def set_char_swidth(self, *args):
        self.char.set_swidth(*args)

    def set_char_dwidth(self, *args):
        self.char.set_dwidth(*args)

    def set_char_encoding(self, *args):
        self.char.set_encoding(*args)

    def append_char_bitmap_data(self, *args):
        self.char.append_bitmap_data(*args)

    def append_char_bitmap_pixel_data(self, start, bin_data):
        self.char.append_bitmap_pixel_data(start, bin_data)

    def __str__(self):
        string = ""
        string += self.get_startfont_line()
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
        string += self.get_chars_lines()
        string += "ENDFONT\n"
        return string

    def get_line(self, line_type):
        if line_type == "COMMENT":
            return self.get_comment_lines()
        if line_type == "STARTFONT":
            return self.get_startfont_line()
        if line_type == "CONTENTVERSION":
            return self.get_content_version_line()
        if line_type == "FONT":
            return self.get_font_name_line()
        if line_type == "SIZE":
            return self.get_size_line()
        if line_type == "FONTBOUNDINGBOX":
            return self.get_bbx_line()
        if line_type == "METRICSSET":
            return self.get_metrics_set_line()
        if line_type == "DWIDTH":
            return self.get_dwidth_line()
        if line_type == "SWIDTH":
            return self.get_swidth_line()
        if line_type == "PROPERTIES":
            return self.get_properties_lines()

    def get_comment_lines(self):
        string = ""
        for line in self.comments:
            string += "COMMENT " + line + "\n"
        return string

    def get_startfont_line(self):
        if self.bdf_version is None:
            return "STARTFONT 2.2\n"
        return "STARTFONT %s\n" % str(self.bdf_version)

    def get_content_version_line(self):
        if self.content_version is None:
            return ""
        return "CONTENTVERSION %d\n" % self.content_version

    def get_font_name_line(self):
        if self.font_name is None:
            return ""
        return "FONT %s\n" % bdf_escape(self.font_name)

    def get_size_line(self):
        if self.point_size is None or self.res_x is None or self.res_y is None:
            return ""
        return "SIZE %d %d %d\n" % (self.point_size, self.res_x, self.res_y)

    def get_bbx_line(self):
        if not self.has_bbx:
            return ""
        return "FONTBOUNDINGBOX %d %d %d %d\n" % (self.bbx_x,
                                                  self.bbx_y,
                                                  self.bbx_ofs_x,
                                                  self.bbx_ofs_y)

    def get_metrics_set_line(self):
        if self.metrics_set is None:
            return ""
        return "METRICSSET %d\n" % self.metrics_set

    def get_dwidth_line(self):
        if self.dwidth_x is None:
            return ""
        return "DWIDTH %d 0\n" % self.dwidth_x

    def get_swidth_line(self):
        if self.swidth_x is None:
            return ""
        return "SWIDTH %d 0\n" % self.swidth_x

    def get_properties_lines(self):
        keys = self.properties.keys()
        if len(keys) == 0:
            return ""
        string = "STARTPROPERTIES %d\n" % len(keys)
        for key in self.properties.keys():
            string += "%s %s\n" % (key, bdf_escape(self.properties[key]))
        string += "ENDPROPERTIES\n"
        return string

    def get_chars_lines(self):
        string = "CHARS %d\n" % len(self.chars)
        for char in self.chars:
            string += str(char)
        return string

    def append_comment(self, comment):
        self.comments.append(comment)
