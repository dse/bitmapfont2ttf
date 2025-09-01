import os, sys
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))

def ellipsis(str):
    if len(str) > 16:
        return str[0:13] + "..."
    return str
