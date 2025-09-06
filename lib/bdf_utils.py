def binDataToHexData(binData):
    if binData == "":
        return "00"
    binData = re.sub(r'[ .]', '0', binData)
    binData = re.sub(r'[^0]', '1', binData)
    binData += "0" * ((8 - len(binData) % 8) % 8)
    hexLen = int(len(binData) / 4)
    decData = int(binData, 2)
    hexData = "%0*X" % (hexLen, decData)
    return hexData

def hexDataToBinData(hexData):
    if hexData == "":
        return "00000000"
    hexData += "0" * ((2 - len(hexData) % 2) % 2)
    decData = int(hexData, 16)
    binLen = len(hexData) * 4
    binData = bin(decData)[2:]
    binData = "0" * ((8 - len(binData) % 8) % 8) + binData
    return binData
