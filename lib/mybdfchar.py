from bdfchar import BDFChar

class MyBDFChar(BDFChar):

    def getSwidthX(self):
        if self.scalableWidthX != None:
            return self.scalableWidthX
        if self.devicePixelWidthX != None:
            return self.devicePixelWidthX / 72000.0 * self.getResolutionX() * self.font.getPointSize()
        return self.font.getSwidthX()

    def getSwidthY(self):
        if self.scalableWidthY != None:
            return self.scalableWidthY
        if self.devicePixelWidthY != None:
            return self.devicePixelWidthY / 72000.0 * self.getResolutionY() * self.font.getPointSize()
        return self.font.getSwidthY()

    def getDwidthX(self):
        if self.devicePixelWidthX != None:
            return self.devicePixelWidthX
        if self.scalableWidthX != None:
            return int(round(self.scalableWidthX * 72000.0 / self.getResolutionX() / self.font.getPointSize()))
        return self.font.getDwidthX()

    def getDwidthY(self):
        if self.devicePixelWidthY != None:
            return self.devicePixelWidthY
        if self.scalableWidthY != None:
            return int(round(self.scalableWidthY * 72000.0 / self.getResolutionY() / self.font.getPointSize()))
        return self.font.getDwidthY()

    def getResolutionX(self):
        return self.font.getResolutionX()

    def getResolutionY(self):
        return self.font.getResolutionY()

    # row =  0 for pixel row just above baseline
    # row = -1 for pixel row just below baseline
    def pixelCountByRow(self, row):
        row = int(round(row))
        yTop = self.boundingBoxYOffset + self.boundingBoxY - 1
        rowIndex = yTop - row   # into bitmapData
        if rowIndex < 0 or rowIndex >= len(self.bitmapData):
            return 0
        return self.bitmapData[rowIndex].count('1')
