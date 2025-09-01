import os, sys
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))

def parse_params(params, param_types, is_rest_params=False, is_opt_params=False, allow_fewer=True):
    values = []
    rest_params = None
    rest_param_types = None
    opt_params = None
    opt_param_types = None
    lengths_must_match = not is_rest_params and not is_opt_params
    rest_indices = []
    opt_indices = []
    if not is_rest_params and not is_opt_params:
        rest_indices = [i for i in range(0, len(param_types)) if param_types[i] == Ellipsis]
        opt_indices  = [i for i in range(0, len(param_types)) if type(param_types[i]) == list]
    has_rest_params = len(rest_indices) == 1
    has_opt_params = len(opt_indices) == 1
    if len(rest_indices) and len(opt_indices):
        raise Exception("cannot mix rest params [Ellipsis] and optional params")
    if len(rest_indices) > 1:
        raise Exception("cannot specify more than one set of rest params")
    if len(opt_indices) > 1:
        raise Exception("cannot specify more than one set of optional params")
    if is_rest_params:
        return values + params
    if is_opt_params:
        for i in range(0, len(params)):
            values.append(parse_param(params[i], param_types[i]))
        return values
    if has_rest_params:
        _ = param_types.pop(-1) # Ellipsis
        rest_params = params[len(param_types):]
        params = params[0:len(param_types)]
    elif has_opt_params:
        opt_param_types = param_types.pop(-1) # an array
        opt_params = params[len(param_types):]
        params = params[0:len(param_types)]
    if len(params) < len(param_types) and lengths_must_match:
        raise Exception(("too few parameters:\n" +
                         "    expected parameter types %s;\n" +
                         "    got %s") % (repr(param_types), repr(params)))
    elif len(params) > len(param_types) and (lengths_must_match or is_opt_params):
        raise Exception(("too many parameters:\n" +
                         "    expected parameter types %s;\n" +
                         "    got %s") % (repr(param_types), repr(params)))
    for i in range(0, len(params)):
        values.append(parse_param(params[i], param_types[i]));
    if has_rest_params:
        return values + parse_params(rest_params, None, is_rest_params=True, allow_fewer=True)
    if has_opt_params:
        return values + parse_params(opt_params, opt_param_types, is_opt_params=True, allow_fewer=True)
    return values

def parse_param(param, param_type=None):
    if param_type == str:
        return str(param)
    elif param_type == int:
        param = param.replace('~', '-') # in case coming from XLFD
        return int(param)
    elif param_type == float:
        param = param.replace('~', '-') # in case coming from XLFD
        return float(param)
    elif param_type is None:
        return param
    else:
        raise Exception("invalid parameter type: %s" % repr(param_type))
