import os, sys, fontforge
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))

from bdf_line_list import BDFLineList

class BDFGlyph():
    def __init__(self, font=None):
        self.font = font
        self.line_list = BDFLineList(is_glyph=True)
        self.bitmap_data_line_list = BDFLineList(is_bitmap_data=True)
        self.encoding = None
        self.alt_encoding = None
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
        self.bbx_x = None
        self.bbx_y = None
        self.bbx_ofs_x = None
        self.bbx_ofs_y = None

    def __str__(self):
        s = ""
        for line in self.line_list.lines:
            s += (line.text if line.text is not None else "") + "\n"
            if line.keyword is None:
                continue
            if line.keyword == "BITMAP":
                for line2 in self.bitmap_data_line_list.lines:
                    s += (line2.text if line2.text is not None else "") + "\n"
        return s

    def set_bbx(self, bbx_x, bbx_y, bbx_ofs_x, bbx_ofs_y):
        self.bbx_x = bbx_x
        self.bbx_y = bbx_y
        self.bbx_ofs_x = bbx_ofs_x
        self.bbx_ofs_y = bbx_ofs_y
        self.line_list.update_line("BBX", [self.bbx_x, self.bbx_y, self.bbx_ofs_x, self.bbx_ofs_y])

    def finalize(self):
        if self.bbx_x is None and self.font.bbx_x is not None:
            self.set_bbx(self.font.bbx_x, self.font.bbx_y, self.font.bbx_ofs_x, self.font.bbx_ofs_y)

        if self.swidth_x is None and self.font.swidth_x is not None:
            self.swidth_x = self.font.swidth_x
            self.swidth_y = self.font.swidth_y
            self.line_list.update_line("SWIDTH", [self.font.swidth_x, self.font.swidth_y])
        if self.dwidth_x is None and self.font.dwidth_x is not None:
            self.dwidth_x = self.font.dwidth_x
            self.dwidth_y = self.font.dwidth_y
            self.line_list.update_line("DWIDTH", [self.font.dwidth_x, self.font.dwidth_y])
        if self.swidth1_x is None and self.font.swidth1_x is not None:
            self.swidth1_x = self.font.swidth1_x
            self.swidth1_y = self.font.swidth1_y
            self.line_list.update_line("SWIDTH1", [self.font.swidth1_x, self.font.swidth1_y])
        if self.dwidth1_x is None and self.font.dwidth1_x is not None:
            self.dwidth1_x = self.font.dwidth1_x
            self.dwidth1_y = self.font.dwidth1_y
            self.line_list.update_line("DWIDTH1", [self.font.dwidth1_x, self.font.dwidth1_y])
        if self.vvector_x is None and self.font.vvector_x is not None:
            self.vvector_x = self.font.vvector_x
            self.vvector_y = self.font.vvector_y
            self.line_list.update_line("VVECTOR", [self.font.vvector_x, self.font.vvector_y])
