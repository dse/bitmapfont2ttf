import os, sys, re
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
