from bdfchar import BDFChar

class MyBDFChar(BDFChar):

    def swidthX(self):
        if self.scalableWidthX != None:
            return self.scalableWidthX
        if self.devicePixelWidthX != None:
            return self.devicePixelWidthX / 72000.0 * self.resolutionX() * self.font.getPointSize()
        return self.font.swidthX()

    def swidthY(self):
        if self.scalableWidthY != None:
            return self.scalableWidthY
        if self.devicePixelWidthY != None:
            return self.devicePixelWidthY / 72000.0 * self.resolutionY() * self.font.getPointSize()
        return self.font.swidthY()

    def dwidthX(self):
        if self.devicePixelWidthX != None:
            return self.devicePixelWidthX
        if self.scalableWidthX != None:
            return int(round(self.scalableWidthX * 72000.0 / self.resolutionX() / self.font.getPointSize()))
        return self.font.dwidthX()

    def dwidthY(self):
        if self.devicePixelWidthY != None:
            return self.devicePixelWidthY
        if self.scalableWidthY != None:
            return int(round(self.scalableWidthY * 72000.0 / self.resolutionY() / self.font.getPointSize()))
        return self.font.dwidthY()

    def resolutionX(self):
        return self.font.resolutionX()

    def resolutionY(self):
        return self.font.resolutionY()

    # row =  0 for pixel row just above baseline
    # row = -1 for pixel row just below baseline
    def pixelCountByRow(self, row):
        row = int(round(row))
        yTop = self.boundingBoxYOffset + self.boundingBoxY - 1
        rowIndex = yTop - row   # into bitmapData
        if rowIndex < 0 or rowIndex >= len(self.bitmapData):
            return 0
        return self.bitmapData[rowIndex].count('1')
