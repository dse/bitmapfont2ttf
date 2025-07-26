def ellipsis(str):
    if len(str) > 16:
        return str[0:13] + "..."
    return str
