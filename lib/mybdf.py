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
        if self.scalableWidthY != None:
            return self.scalableWidthY
        if self.devicePixelWidthY != None:
            return self.devicePixelWidthY / 72000.0 * self.getResolutionY() * self.getPointSize()
        raise Exception('cannot determine swidthY')

    def getDwidthX(self):
        if self.devicePixelWidthX != None:
            return self.devicePixelWidthX
        if self.scalableWidthX != None:
            return int(round(self.scalableWidthX * 72000.0 / self.getResolutionX() / self.getPointSize()))
        raise Exception('cannot determine dwidthX')

    def getDwidthY(self):
        if self.devicePixelWidthY != None:
            return self.devicePixelWidthY
        if self.scalableWidthY != None:
            return int(round(self.scalableWidthY * 72000.0 / self.getResolutionY() / self.getPointSize()))
        raise Exception('cannot determine dwidthY')

    def getPointSize(self):
        pt10 = self.properties['pointSize10']
        if pt10 != None:
            return pt10 / 10.0
        raise Exception('font does not have a POINT_SIZE property')
        # if self.pointSize != None:
        #     return self.pointSize * 1.0
        # px = self.properties['pixelSize']
        # if px != None:
        #     return 72.0 * px / self.getResolutionY()
        # raise Exception('cannot determine pointSize')

    def setPixelSize(self, px):
        self.properties['pixelSize']   = px
        self.properties['pointSize10'] = int(round(px * 720.0 / self.getResolutionY()))
        self.pointSize                 = int(round(px * 72.0 / self.getResolutionY()))

    def getPixelSize(self):
        px = self.properties['pixelSize']
        if px != None:
            return px
        raise Exception('font does not specify pixel size')
        # pt10 = self.properties['pointSize10']
        # if pt10 != None:
        #     return pt10 / 720.0 * self.getResolutionY()
        # raise Exception('cannot determine pixelSize')

    def getResolutionX(self):
        r = self.properties['resolutionX']
        if r != None:
            return r
        raise Exception('cannot determine resolutionX')

    def getResolutionY(self):
        r = self.properties['resolutionY']
        if r != None:
            return r
        raise Exception('cannot determine resolutionY')

    def ascentPx(self):
        ascent = self.properties['ascent']
        if ascent != None:
            return ascent
        raise Exception('cannot determine ascentPx')

    def descentPx(self):
        descent = self.properties['descent']
        if descent != None:
            return descent
        raise Exception('cannot determine descentPx')

    def scalableToPixels(self, scalable):
        return 1.0 * scalable * self.properties["pixelSize"] / 1000.0
    def scalableToPixelsX(self, scalable):
        return 1.0 * scalable * self.properties["pixelSize"] / 1000.0 / self.aspectRatioXtoY()

    def pixelsToScalable(self, pixels):
        return 1.0 * pixels * 1000.0 / self.properties["pixelSize"]
    def pixelsToScalableX(self, pixels):
        return 1.0 * pixels * 1000.0 / self.properties["pixelSize"] * self.aspectRatioXtoY()

    # less than 1 means taller than wide; greater than 1 means wider than tall
    def aspectRatioXtoY(self):
        return 1.0 * self.properties["resolutionY"] / self.properties["resolutionX"]
