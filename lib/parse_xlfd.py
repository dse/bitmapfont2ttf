import re

def is_xlfd(xlfd):
    """Return True or False depending on whether the supplied xlfd is valid.

Shorthand for parse_xlfd(xlfd, as_type=bool, throw=False)

    """
    return parse_xlfd(xlfd, as_type=bool, throw=False)

def parse_xlfd(xlfd, as_type=list, throw=False):
    """Parse the supplied string as an X Logical Font Description.

If the as_type parameter is bool, return True or False depending on whether it's a valid XLFD.

If the throw parameter is truthy, raise an error if the supplied XLFD is invalid.

The as_type parameter can also be list, tuple, or dict.

    """
    def get_next_field(field_type=str):
        nonlocal xlfd
        nonlocal as_type
        if len(xlfd) == 0:
            raise Exception("empty or insufficiently long xlfd")
        if xlfd[0] != "-":
            raise Exception("invalid xlfd")
        if match := re.match(r'-\[\s*([^\-\]]*?)\s*\]', xlfd):
            xlfd = xlfd[match.end():]
            if field_type == "int_or_matrix":
                matrix_str = match[1]                           # "1 1 1 1"
                matrix_strs = match[1].split()                  # ["1", "1", "1", "1"]
                if len(matrix_strs) != 4:
                    raise Exception("incorrect transformation matrix size: %s" % repr(matrix_str))
                matrix = []
                for num_str in matrix_strs:
                    if match := re.fullmatch(r'[+~]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+~]?[0-9]+)?', num_str):
                        matrix.append(float(match[0].replace("~", "-")))
                    else:
                        raise Exception("invalid floating-point number: %s" % repr(num_str))
                if as_type == tuple:
                    return tuple(matrix)                        # (1, 1, 1, 1)
                return matrix                                   # [1, 1, 1, 1]
            else:
                raise Exception("transformation matrix not valid here")
        elif match := re.match(r'-([^-]*)', xlfd):
            xlfd = xlfd[match.end():]
            if match[1] == "":
                return None
            if field_type == int or field_type == "int_or_matrix":
                return int(match[1])
            if field_type == float:
                return float(match[1])
            if field_type == str or field_type is None:
                return match[1]
            raise Exception("invalid field_type parameter: %s" % repr(field_type))
        raise Exception("invalid xlfd")
    if as_type not in [tuple, list, dict, bool]:
        raise Exception("as_type must be list, tuple, dict, or bool")
    try:
        foundry          = get_next_field()                     # 0
        family_name      = get_next_field()                     # 1
        weight_name      = get_next_field()                     # 2
        slant            = get_next_field()                     # 3
        setwidth_name    = get_next_field()                     # 4
        add_style_name   = get_next_field()                     # 5
        pixel_size       = get_next_field("int_or_matrix")      # 6
        point_size       = get_next_field("int_or_matrix")      # 7
        resolution_x     = get_next_field(int)                  # 8
        resolution_y     = get_next_field(int)                  # 9
        spacing          = get_next_field()                     # 10
        average_width    = get_next_field(int)                  # 11
        charset_registry = get_next_field()                     # 12
        charset_encoding = get_next_field()                     # 13
        if as_type == bool:
            return True
        if as_type in [list, tuple]:
            result = [foundry,                                  # 0
                      family_name,                              # 1
                      weight_name,                              # 2
                      slant,                                    # 3
                      setwidth_name,                            # 4
                      add_style_name,                           # 5
                      pixel_size,                               # 6
                      point_size,                               # 7
                      resolution_x,                             # 8
                      resolution_y,                             # 9
                      spacing,                                  # 10
                      average_width,                            # 11
                      charset_registry,                         # 12
                      charset_encoding]                         # 13
            if as_type == tuple:
                return tuple(result)
            return result
        if as_type == dict:
            return { "foundry":          foundry,               # 0
                     "family_name":      family_name,           # 1
                     "weight_name":      weight_name,           # 2
                     "slant":            slant,                 # 3
                     "setwidth_name":    setwidth_name,         # 4
                     "add_style_name":   add_style_name,        # 5
                     "pixel_size":       pixel_size,            # 6
                     "point_size":       point_size,            # 7
                     "resolution_x":     resolution_x,          # 8
                     "resolution_y":     resolution_y,          # 9
                     "spacing":          spacing,               # 10
                     "average_width":    average_width,         # 11
                     "charset_registry": charset_registry,      # 12
                     "charset_encoding": charset_encoding }     # 13
    except Exception as e:
        if as_type == bool:
            return False
        if not throw:
            return None
        raise e

if __name__ == "__main__":
    def test(xlfd, as_type=list, throw=True):
        result = parse_xlfd(xlfd, as_type=as_type, throw=throw)
        print(result)
    test("-misc-fixed-medium-r-normal--13-130-75-75-c-60-iso8859-1", as_type=list)
    test("-misc-fixed-medium-r-normal--13-130-75-75-c-60-iso8859-1", as_type=dict)
    test("-misc-fixed-medium-r-normal--13-130-75-75-c-60-iso8859-1", as_type=bool)
    test("-misc-fixed-medium-r-normal--13-[1 1 1 1]-75-75-c-60-iso8859-1", as_type=bool)
    test("-misc-fixed-medium-r-normal--[1 1 1 1]-[1 1 1 1]-75-75-c-60-iso8859-1", as_type=tuple)
