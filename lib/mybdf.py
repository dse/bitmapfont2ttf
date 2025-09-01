from bdf import BDF
from mybdfchar import MyBDFChar

class MyBDF(BDF):
    def newChar(self, name, font):
        return MyBDFChar(name = name, font = font)

    def getSwidthX(self):
        if self.scalableWidthX != None:
            return self.scalableWidthX
        if self.devicePixelWidthX != None:
            return self.devicePixelWidthX / 72000.0 * self.getResolutionX() * self.getPointSize()
        raise Exception('cannot determine swidthX')

    def getSwidthY(self):
        return 0

    def getDwidthX(self):
        if self.devicePixelWidthX != None:
            return self.devicePixelWidthX
        if self.scalableWidthX != None:
            return int(round(self.scalableWidthX * 72000.0 / self.getResolutionX() / self.getPointSize()))
        raise Exception('cannot determine dwidthX')

    def getDwidthY(self):
        return 0

    def getPointSize(self):
        pt10 = self.properties["POINT_SIZE"]
        if pt10 != None:
            return pt10 / 10.0
        raise Exception('font does not have a POINT_SIZE property')
        # if self.pointSize != None:
        #     return self.pointSize * 1.0
        # px = self.properties["PIXEL_SIZE"]
        # if px != None:
        #     return 72.0 * px / self.getResolutionY()
        # raise Exception('cannot determine pointSize')

    def setPixelSize(self, px):
        self.properties["PIXEL_SIZE"] = px
        self.properties["POINT_SIZE"] = int(round(px * 720.0 / self.getResolutionY()))
        self.pointSize = int(round(px * 72.0 / self.getResolutionY()))

    def getPixelSize(self):
        px = self.properties["PIXEL_SIZE"]
        if px != None:
            return px
        raise Exception('font does not specify pixel size')
        # pt10 = self.properties["POINT_SIZE"]
        # if pt10 != None:
        #     return pt10 / 720.0 * self.getResolutionY()
        # raise Exception('cannot determine pixelSize')

    def getResolutionX(self):
        r = self.properties["RESOLUTION_X"]
        if r != None:
            return r
        raise Exception('cannot determine resolutionX')

    def getResolutionY(self):
        r = self.properties["RESOLUTION_Y"]
        if r != None:
            return r
        raise Exception('cannot determine resolutionY')

    def ascentPx(self):
        ascent = self.properties["FONT_ASCENT"]
        if ascent != None:
            return ascent
        raise Exception('cannot determine ascentPx')

    def descentPx(self):
        descent = self.properties["FONT_DESCENT"]
        if descent != None:
            return descent
        raise Exception('cannot determine descentPx')

    def scalableToPixels(self, scalable):
        return 1.0 * scalable * self.properties["PIXEL_SIZE"] / 1000.0
    def scalableToPixelsX(self, scalable):
        return 1.0 * scalable * self.properties["PIXEL_SIZE"] / 1000.0 / self.aspectRatioXtoY()

    def pixelsToScalable(self, pixels):
        return 1.0 * pixels * 1000.0 / self.properties["PIXEL_SIZE"]
    def pixelsToScalableX(self, pixels):
        return 1.0 * pixels * 1000.0 / self.properties["PIXEL_SIZE"] * self.aspectRatioXtoY()

    # less than 1 means taller than wide; greater than 1 means wider than tall
    def aspectRatioXtoY(self):
        return 1.0 * self.properties["RESOLUTION_Y"] / self.properties["RESOLUTION_X"]
