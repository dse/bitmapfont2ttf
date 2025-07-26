import re

def parse_bdf_line(line):
    words = []
    pos = 0
    while True:
        if match := re.match('\s+', line):
            line = line[match.end():]
            pos += match.end()
        if line == "":
            break
        word = ""
        while True:
            if match := re.match('[^"\s]+', line):
                line = line[match:end():]
                word += match
                pos += match.end()
            elif match := re.match('"((?:[^"]+|"")*)"', line):
                line = line[match.end():]
                word += match[1].replace('""', '"')
                pos += match.end()
            elif match := re.match('"', line):
                raise Exception("unterminated quote at %d: %s" % (pos, repr(line)))
            else:
                break
        words.append(word)
    return words
