import os
import csv
from typing import Dict

fileNameFormat = "pub-interest-rate-{nodeName}-{objectType}-sync.csv"
rateFormatString: str = "{type}\tcount: {count}\t rate: {meanRate} / sec"
objectTypes = ["status", "projectiles", "blocks"]


class InterestRatesForNode:

    def __init__(self, directory, nodeName):
        self.nodeName: str = nodeName
        self.interestRatesByType: Dict[str, Rate] = dict()

        for objectType in objectTypes:
            fileName = os.path.join(directory, fileNameFormat.format(nodeName=nodeName, objectType=objectType))
            try:
                with open(fileName) as f:
                    csvData = list(csv.reader(f))
                    lastRow = csvData[-1]
                    self.interestRatesByType[objectType] = Rate(lastRow[0], lastRow[1], lastRow[2])
            except FileNotFoundError as e:
                print("Could not find file %s, skipping" % fileName)

    def getInterestRatesByType(self):
        return self.interestRatesByType

    def getInterestRateForType(self, objectType='status'):
        return self.interestRatesByType[objectType]

    def plotInterestRateForType(self, ax, objectType='status'):
        print("\n\nInterest rates for %s" % self.nodeName)
        ax.bar(self.nodeName, self.interestRatesByType[objectType].meanRate)

    def plotInterestRates(self, ax):
        for obj, rate in self.interestRatesByType.items():
            print("\n\nInterest rates for %s, %s" % (self.nodeName, obj))
            ax.bar(self.nodeName, rate.meanRate)


class Rate:

    def __init__(self, time, count, meanRate):
        self.time: int = time
        self.count: int = count
        self.meanRate: float = round(float(meanRate), 2)

    def print(self, type):
        print(rateFormatString.format(type=type, count=self.count, meanRate=self.meanRate))

