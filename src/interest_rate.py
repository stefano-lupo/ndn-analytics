import os
from typing import Dict, List

from reading_utils import readCsvSafe

fileNameFormat = "pub-interest-rate-{nodeName}-{objectType}-sync.csv"
rateFormatString: str = "{type}\tcount: {count}\t rate: {meanRate} / sec"
objectTypes = ["status", "projectiles", "blocks"]


class InterestRatesForNode:

    def __init__(self, directory, nodeName):
        self.nodeName: str = nodeName
        self.interestRatesByType: Dict[str, Rate] = dict()

        for objectType in objectTypes:
            fileName = os.path.join(directory, fileNameFormat.format(nodeName=nodeName, objectType=objectType))
            self.interestRatesByType[objectType] = Rate(readCsvSafe(fileName), objectType)

    def getInterestRatesByType(self):
        return self.interestRatesByType

    def getInterestRateForType(self, objectType='status'):
        return self.interestRatesByType[objectType]

    def plotInterestRateForType(self, ax, objectType='status'):
        ax.bar(self.nodeName, self.interestRatesByType[objectType].finalMeanRate)

    def plotInterestRates(self, ax):
        for obj, rate in self.interestRatesByType.items():
            ax.bar(self.nodeName, rate.finalMeanRate)

    def plotInterestRateOverTime(self, ax, objectType='status'):
        self.getInterestRateForType(objectType).plotOverTime(ax, self.nodeName)

    def getMeanRateOverTime(self, objectType='status'):
        return self.interestRatesByType[objectType].getMeanRateOverTime()


class Rate:

    def __init__(self, csvData: List[List], objectType: str):
        csvData = csvData[1:]
        self.finalMeanRate: float = round(float(csvData[-1][2]), 2)
        self.totalInterestsSeen: int = int(csvData[-1][1])
        self.meanRateOverTime: Dict[int, float] = {int(row[0]): float(row[2]) for row in csvData}
        self.objectType = objectType

    def getFinalMeanRate(self, type):
        print(rateFormatString.format(type=type, meanRate=self.finalMeanRate))
        return self.finalMeanRate

    def getMeanRateOverTime(self):
        return self.meanRateOverTime

    def plotOverTime(self, ax, nodeName: str):
        ax.plot(self.meanRateOverTime.keys(), self.meanRateOverTime.values(), label=nodeName)
