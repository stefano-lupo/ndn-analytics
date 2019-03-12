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

    def printRates(self):
        print("\n\nInterest rates for %s" % self.nodeName)
        for type, rate in self.interestRatesByType.items():
            rate.print(type)


class Rate:

    def __init__(self, time, count, meanRate):
        self.time: int = time
        self.count: int = count
        self.meanRate: float = meanRate

    def print(self, type):
        print(rateFormatString.format(type=type, count=self.count, meanRate=self.meanRate))

