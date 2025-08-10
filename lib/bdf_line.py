class BDFLine:
    def __init__(self,
                 keyword=None,
                 words=None,
                 orig_words=None,
                 params=None,
                 is_blank=False,
                 is_comment=False,
                 no_print=False,
                 text=None):
        self.keyword = keyword
        self.words = words
        self.orig_words = orig_words
        self.params = params
        self.is_blank = is_blank
        self.is_comment = is_comment
        self.no_print = no_print
        self.text = text
    def matches(self, keyword):
        if self.keyword == None:
            return None
        if type(keyword) == str:
            return self.keyword == keyword
        if type(keyword) == list:
            return self.keyword in keyword
