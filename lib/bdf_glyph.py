import os, sys, fontforge
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))

class BDFGlyph():
    def __init__(self):
        self.lines = []
        self.bitmap_data = []

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

    def clear_previous_lines(self, keyword):
        matching_lines = [line for line in self.lines if line["keyword"] == keyword]
        if len(matching_lines) == 0:
            return
        lines_to_clear = matching_lines[0:-1]
        self.lines = [line for line in self.lines if line not in lines_to_clear]

    def __str__(self):
        s = ""
        for line in self.lines:
            s += line["text"] + "\n"
            if "keyword" not in line:
                continue
            if line["keyword"] == "BITMAP":
                for line2 in self.bitmap_data:
                    s += line2["text"] + "\n"
        return s
