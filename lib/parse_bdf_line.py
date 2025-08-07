import os, sys, re
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))

def parse_bdf_line(line):
    orig_words = []
    words = []
    pos = 0
    while True:
        # remove leading whitespace
        if match := re.match('\s+', line):
            line = line[match.end():]
            pos += match.end()
        # if line empty, then done
        if line == "":
            break
        # start new word
        orig_word = ""
        word = ""
        while True:
            if match := re.match('[^"\s]+', line):
                line = line[match.end():]
                word += match[0]
                orig_word += match[0]
                pos += match.end()
            elif match := re.match('"((?:[^"]+|"")*)"', line):
                line = line[match.end():]
                orig_word += match[0]
                word += match[1].replace('""', '"')
                pos += match.end()
            elif match := re.match('"', line):
                raise Exception("unterminated quote at %d: %s" % (pos, repr(line)))
            else:
                break
        words.append(word)
        orig_words.append(orig_word)
    return words, orig_words
