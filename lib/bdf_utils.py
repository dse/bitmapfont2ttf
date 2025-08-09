import os, sys, re, fontforge
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))

def bdf_quote(value):
    if type(value) == str:
        if value.find('"') >= 0 or re.match(r'\s', value):
            return '"' + value.replace('"', '""') + '"'
    return str(value)

def ellipsis(value):
    if type(value) == str:
        if len(value) > 16:
            return value[0:13] + "..."
    return value

def clear_previous_lines(lines, keyword, last=False):
    matches = [line for line in lines if "keyword" in line and line["keyword"] == keyword]
    if len(matches) == 0:
        return lines
    if last:
        kept_last_line = matches[-1]
        matches = matches[0:-1]
        lines = lines[0:-1]
    lines = [line for line in lines if line not in matches]
    if last:
        return lines + [kept_last_line]
    return lines

def split_line(text):
    orig_words = []
    words = []
    while True:
        text = re.sub(r'^\s+', '', text)
        if text == "":
            break
        orig_word = ""
        word = ""
        while True:
            if match := re.match(r'[^" ]+', text):
                text = text[len(match[0]):]
                orig_word += match[0]
                word += match[0]
            elif match := re.match(r'"((""|[^"])*)', text):
                text = text[len(match[0]):]
                orig_word += match[0]
                word += match[1].replace('""', '"')
                if match := re.match(r'"', text):
                    orig_word += '"'
            else:
                break
        words.append(word)
        orig_words.append(orig_word)
    return words, orig_words

def create_encoding_line(charname, loose=False):
    # in loose parsing mode, we accept additional parameter
    # formats for STARTCHAR.

    # find any ".slash" type suffix and let, e.g., "zero" be the
    # base_charname
    invalid = False
    base_charname = charname
    idx = charname.find('.')
    suffix = None
    encoding = None
    alt_encoding = None
    if idx >= 1:            # charname does not start with "."
        base_charname = charname[0:idx]
        suffix = charname[idx:]

    # check for charnames like U+1F4A9 U1F4A9 0x1f4a9 x1f4a9 or
    # for Adobe glyph names
    if match := re.match('(?:u\+?|0?x)([A-Fa-f0-9]+)$', base_charname, flags=re.IGNORECASE):
        if loose:
            encoding = int(match[1], base=16)
        else:
            raise Exception("invalid base charname: %s" % base_charname)
    else:
        encoding = fontforge.unicodeFromName(base_charname)

    if encoding < 0:
        invalid = True
        sys.stderr.write("WARN: invalid base charname: %s; continuing\n" % base_charname)
        encoding = -1
        alt_encoding = -1
    else:
        alt_encoding = None

    if invalid:
        return None

    if alt_encoding is None or alt_encoding == -1:
        return {
            "keyword": "ENCODING",
            "params": [encoding],
            "text": "ENCODING %d" % encoding,
        }
    return {
        "keyword": "ENCODING",
        "params": [encoding, alt_encoding],
        "text": "ENCODING %d %d" % (encoding, alt_encoding),
    }
