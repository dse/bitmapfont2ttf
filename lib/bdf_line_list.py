from bdf_utils import bdf_escape

from bdf_line import BDFLine

class BDFLineList:
    def __init__(self, is_bdf_main=False, is_bdf_prop=False, is_glyph=False, is_bitmap_data=False):
        self.lines = []
        self.is_bdf_main = is_bdf_main
        self.is_bdf_prop = is_bdf_prop
        self.is_glyph    = is_glyph
        self.is_bitmap_data = is_bitmap_data

    def get_lines_matching_keyword(self, keyword):
        return [line for line in self.lines if line.matches(keyword)]

    def get_line_indexes_matching_keyword(self, keyword):
        return [i for i in range(0, len(self.lines)) if self.lines[i].matches(keyword)]

    def get_first_line_index_matching_keyword(self, keyword):
        for i in range(0, len(self.lines)):
            line = self.lines[i]
            if line.matches(keyword):
                return i
        return -1

    def remove_lines_matching_keyword(self, keyword, keep_last=False):
        indexes = self.get_line_indexes_matching_keyword(keyword)
        if len(indexes) == 0:
            return
        orig_index_count = len(indexes)
        i = len(indexes) - 1
        if keep_last:
            last_idx = indexes[-1]
            i = len(indexes) - 2
        while i >= 0:
            self.lines[indexes[i]:indexes[i]+1] = []
            i -= 1
        if keep_last:
            return self.lines[last_idx - (orig_index_count - len(indexes))]

    def append_comment(self, value):
        comment_line = {
            "keyword": "COMMENT",
            "words": [str(value)],
            "params": [str(value)],
            "text": "COMMENT %s" % bdf_escape(value)
        }
        indexes = self.get_line_indexes_matching_keyword("COMMENT")
        if len(indexes) == 0:
            self.lines.insert(1, comment_line)
        else:
            index = indexes[-1]
            self.lines.insert(index + 1, comment_line)

    def update_line(self, keyword, value):
        keyword = keyword.upper()
        line = self.remove_lines_matching_keyword(keyword, keep_last=True)
        if line:
            line.params = [value]
            line.orig_words = None
            line.orig_text = None
            line.words = None
            line.text = "%s %s" % (keyword, self.escape(value))
        else:
            new_line = BDFLine()
            new_line.keyword = keyword
            new_line.params = [value]
            new_line.text = "%s %s" % (keyword, bdf_escape(value))
            if self.is_bdf_main:
                keywords = ["CHARS", "STARTPROPERTIES"]
                idx = self.get_first_line_index_matching_keyword(keywords)
                if idx < 0:
                    self.lines.insert(len(self.lines) - 1, new_line)
                else:
                    self.lines.insert(idx, new_line)
            elif self.is_bdf_prop:
                keywords = ["ENDPROPERTIES"]
                idx = self.get_first_line_index_matching_keyword(keywords)
                if idx < 0:
                    self.lines.insert(len(self.lines) - 1, new_line)
                else:
                    self.lines.insert(idx, new_line)
            elif self.is_glyph:
                keywords = ["BITMAP"]
                idx = self.get_first_line_index_matching_keyword(keywords)
                if idx < 0:
                    self.lines.insert(len(self.lines) - 1, new_line)
                else:
                    self.lines.insert(idx, new_line)
            else:
                self.lines.append(new_line)
