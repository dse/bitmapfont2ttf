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

FORCE_QUOTE = {
    "SPACING": True,
    "FOUNDRY": True,
    "WEIGHT_NAME": True,
    "SETWIDTH_NAME": True,
    "FAMILY_NAME": True,
    "SLANT": True,
}

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
        self.comments = []
        self.use_properties = False
        self.char = None
        self.finalized = False

        self.order = order
        if type(self.order) == str:
            self.order = self.order.replace(',', ' ').strip().split()
            self.order = [upper(x) for x in self.order]

        if filename is not None:
            self.read(filename)

    def start_char(self, name):
        self.char = BDFChar(name=name, font=self)

        encoding = self.char.encoding
        charname = self.char.name

        self.chars.append(self.char)
        self.char.bitmap_data = []

    def end_char(self):
        # make sure this is idempotent.
        if self.char is None:
            return
        self.char.end_bitmap()
        self.char.end_char()
        self.char = None

    def start_char_bitmap(self):
        self.char.start_bitmap()

    def end_char_bitmap(self):
        # make sure this is idempotent.
        self.char.end_bitmap()

    def newChar(self, name, font):
        return BDFChar(name = name, font = font)

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
        raise Exception('cannot determine swidthX')

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
        raise Exception('cannot determine dwidthX')

    def get_dwidth_y(self):
        return 0

    def get_point_size(self):
        if self.point_size is not None:
            return self.point_size
        pt10 = self.properties.get("POINT_SIZE")
        if pt10 is not None:
            return pt10 / 10.0
        raise Exception("cannot find font's point size")

    def get_pixel_size(self):
        px = self.properties.get("PIXEL_SIZE")
        if px is not None:
            return px
        raise Exception('font does not specify pixel size')

    def get_resolution_x(self):
        if self.res_x is not None:
            return self.res_x
        r = self.properties.get("RESOLUTION_X")
        if r is not None:
            return r
        raise Exception('cannot determine resolutionX')

    def get_resolution_y(self):
        if self.res_y is not None:
            return self.res_y
        r = self.properties.get("RESOLUTION_Y")
        if r is not None:
            return r
        raise Exception('cannot determine resolutionY')

    def ascent_px(self):
        ascent = self.properties.get("FONT_ASCENT")
        if ascent is not None:
            return ascent
        raise Exception('cannot determine ascent_px')

    def descent_px(self):
        descent = self.properties.get("FONT_DESCENT")
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
        return 1.0 * self.get_resolution_y() / self.get_resolution_x()

    def set_bdf_version(self, value):
        self.bdf_version = float(value)

    def set_content_version(self, value):
        self.content_version = int(value)

    def set_font_name(self, value):
        self.font_name = str(value)
        if self.use_properties:
            self.fix_font_name()

    def set_size(self, point_size, res_x, res_y):
        self.point_size = int(point_size)
        self.res_x = int(res_x)
        self.res_y = int(res_y)
        if self.use_properties:
            self.fix_point_size()
            self.fix_resolution_x()
            self.fix_resolution_y()

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
        # make sure this is idempotent.
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
        return "FONT %s\n" % bdf_escape(self.font_name, forcequote=True)

    def get_size_line(self):
        if self.point_size is None or self.res_x is None or self.res_y is None:
            return ""
        return "SIZE %d %d %d\n" % (self.point_size, self.res_x, self.res_y)

    def get_bbx_line(self, name="FONTBOUNDINGBOX"):
        if not self.has_bbx:
            return ""
        return "%s %d %d %d %d\n" % (name,
                                     self.bbx_x,
                                     self.bbx_y,
                                     self.bbx_ofs_x,
                                     self.bbx_ofs_y)

    def get_metrics_set_line(self):
        if self.metrics_set is None:
            return ""
        return "METRICSSET %d\n" % self.metrics_set

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

    def get_properties_lines(self):
        keys = self.properties.keys()
        if len(keys) == 0:
            return ""
        string = "STARTPROPERTIES %d\n" % len(keys)
        for key in self.properties.keys():
            string += "%s %s\n" % (key, bdf_escape(self.properties[key], forcequote=FORCE_QUOTE.get(key, False)))
        string += "ENDPROPERTIES\n"
        return string

    def get_chars_lines(self):
        string = "CHARS %d\n" % len(self.chars)
        for char in self.chars:
            string += str(char)
        return string

    def append_comment(self, comment):
        self.comments.append(comment)

    def issue_warnings(self):
        self.issue_resolution_x_warning()
        self.issue_resolution_y_warning()
        self.issue_font_name_warning()
        self.issue_point_size_warning()

    # TODO: allow XLFD FONT in main section and normal FONT property?
    def issue_font_name_warning(self):
        if self.font_name is not None and self.properties.get("FONT") is not None:
            if self.font_name != self.properties.get("FONT"):
                sys.stderr.write("WARNING: FONT in main section and properties do not match\n")

    def issue_point_size_warning(self):
        if self.point_size is not None and self.properties.get("POINT_SIZE") is not None:
            if self.point_size != int(round(self.properties["POINT_SIZE"] / 10)):
                sys.stderr.write("WARNING: inconsistent point sizes\n")

    def issue_resolution_x_warning(self):
        rx1 = self.res_x
        rx2 = self.properties.get("RESOLUTION_X")
        if rx1 is not None and rx2 is not None and rx1 != rx2:
            sys.stderr.write("WARNING: x-resolution specified in properties and SIZE line are different\n")

    def issue_resolution_y_warning(self):
        ry1 = self.res_y
        ry2 = self.properties.get("RESOLUTION_Y")
        if ry1 is not None and ry2 is not None and ry1 != ry2:
            sys.stderr.write("WARNING: y-resolution specified in properties and SIZE line are different\n")

    def end_font(self):
        if self.use_properties:
            self.fix_properties()
        self.finalize()

    def fix_properties(self):
        # make sure this is idempotent.
        self.fix_resolution_x()
        self.fix_resolution_y()
        self.fix_font_name()
        self.fix_point_size()
        self.fix_charset()

    def fix_charset(self):
        if self.properties.get("CHARSET_REGISTRY") is None and self.properties.get("CHARSET_ENCODING") is None:
            self.properties["CHARSET_REGISTRY"] = "ISO10646"
            self.properties["CHARSET_ENCODING"] = "1"

    def fix_resolution_x(self):
        if self.res_x is None and self.properties.get("RESOLUTION_X") is not None:
            self.res_x = self.properties.get("RESOLUTION_X")
        elif self.res_x is not None and self.properties.get("RESOLUTION_X") is None:
            self.properties["RESOLUTION_X"] = self.res_x

    def fix_resolution_y(self):
        if self.res_y is None and self.properties.get("RESOLUTION_Y") is not None:
            self.res_y = self.properties.get("RESOLUTION_Y")
        elif self.res_y is not None and self.properties.get("RESOLUTION_Y") is None:
            self.properties["RESOLUTION_Y"] = self.res_y

    def fix_font_name(self):
        if self.font_name is None and self.properties.get("FONT") is not None:
            self.font_name = self.properties["FONT"]
        elif self.font_name is not None and self.properties.get("FONT") is None:
            self.properties["FONT"] = self.font_name

    def fix_point_size(self):
        if self.point_size is None and self.properties.get("POINT_SIZE") is not None:
            self.point_size = int(round(self.properties["POINT_SIZE"] / 10))
        elif self.point_size is not None and self.properties.get("POINT_SIZE") is None:
            self.properties["POINT_SIZE"] = self.point_size * 10

    def set_full_name(self, value):
        self.properties["FACE_NAME"] = str(value)
        if "FULL_NAME" in self.properties:
            self.properties["FULL_NAME"] = str(value)

    def set_family_name(self, value):
        self.properties["FAMILY_NAME"] = str(value)

    def set_add_style_name(self, value):
        self.properties["ADD_STYLE_NAME"] = str(value)

    def set_setwidth_name(self, value):
        self.properties["SETWIDTH_NAME"] = str(value)

    def set_weight_name(self, value):
        self.properties["WEIGHT_NAME"] = str(value)

    def set_resolution_x(self, value):
        self.res_x = int(value)
        if "RESOLUTION_X" in self.properties:
            self.properties["RESOLUTION_X"] = int(value)

    def set_resolution_y(self, value):
        self.res_y = int(value)
        if "RESOLUTION_Y" in self.properties:
            self.properties["RESOLUTION_Y"] = int(value)

    def finalize(self):
        if self.finalized:
            return

        chars = []
        chars_by_encoding = {}
        chars_by_name = {}

        for char in self.chars:
            if char.name not in chars_by_name and char.encoding not in chars_by_encoding:
                if char.encoding >= 0:
                    chars_by_encoding[char.encoding] = char
                chars_by_name[char.name] = char
                chars.append(char)
            else:
                if char.encoding in chars_by_encoding and char.encoding >= 0:
                    sys.stderr.write("WARNING: duplicate characters with encoding %d\n" % char.encoding)
                if char.encoding in chars_by_name:
                    sys.stderr.write("WARNING: duplicate characters named %s\n" % char.name)

        self.chars = chars
        self.finalized = True
