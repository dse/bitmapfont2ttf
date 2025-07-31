import os, sys
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))

def parse_params(params, param_types, is_rest_params=False):
    values = []
    rest_params = None
    rest_param_types = None
    rest_indices = [i for i in range(0, len(param_types)) if type(param_types[i]) == list]
    if is_rest_params:
        if len(rest_indices):
            raise Exception("rest params cannot nest")
    else:
        if len(rest_indices) > 1:
            raise Exception("too many sets of rest params")
        elif len(rest_indices) == 1:
            if type(param_types[-1]) != list:
                raise Exception("rest params must occur last")
            rest_param_types = param_types.pop(-1)
            rest_params = params[len(param_types):]
    if len(params) < len(param_types) and not is_rest_params:
        raise Exception("too few parameters")
    elif len(param_types) < len(params):
        raise Exception("too many parameters")
    for i in range(0, len(params)):
        values.append(parse_param(params[i], param_types[i]))
    if rest_param_types is not None:
        return values + parse_params(rest_params, res_param_types, is_rest_params=True)
    return values

def parse_param(param, param_type):
    if param_type == str:
        return str(param)
    elif param_type == int:
        param = param.replace('~', '-') # in case coming from XLFD
        return int(param)
    elif param_type == float:
        param = param.replace('~', '-') # in case coming from XLFD
        return float(param)
    else:
        raise Exception("invalid parameter type: %s" % repr(param_type))
