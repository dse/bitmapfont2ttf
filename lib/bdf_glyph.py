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
        self.bdf_line_order = []
    def set_name(self, value):
        self.name = value
    def set_encoding(self, value):
        self.encoding = value
        self.update_encoding_line()
    def set_alt_encoding(self, value):
        self.alt_encoding = value
        self.update_encoding_line()
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
    def update_lines():
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
