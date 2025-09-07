import re

def bin_data_to_hex_data(bin_data):
    if bin_data == "":
        return "00"
    bin_data = re.sub(r'[ .]', '0', bin_data)
    bin_data = re.sub(r'[^0]', '1', bin_data)
    bin_data += "0" * ((8 - len(bin_data) % 8) % 8)
    hex_len = int(len(bin_data) / 4)
    dec_data = int(bin_data, 2)
    hex_data = "%0*X" % (hex_len, dec_data)
    return hex_data

def hex_data_to_bin_data(hex_data):
    if hex_data == "":
        return "00000000"
    hex_data += "0" * ((2 - len(hex_data) % 2) % 2)
    dec_data = int(hex_data, 16)
    bin_len = len(hex_data) * 4
    bin_data = bin(dec_data)[2:]
    bin_data = "0" * ((8 - len(bin_data) % 8) % 8) + bin_data
    return bin_data

def bdf_escape(value):
    if value is None:
        return ""
    if type(value) != str:
        value = str(value)
    print(">>" + value + "<<")
    if not re.search(r'[\s"]', value):
        return value
    return '"' + value.replace('"', '""') + '"'
