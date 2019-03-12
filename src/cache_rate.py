import csv
import os
from typing import List, Dict

CACHE_FILE_NAME = "sub-{objectType}-cacherate-{playerName}.csv"

class CacheRates:
    def __init__(self, myDataDir, myName, otherNodes: List[str], objectType="status"):
        self.myName = myName
        self.cacheRates: Dict[str, int] = {}
        for node in otherNodes:
            filename =  CACHE_FILE_NAME.format(objectType=objectType, playerName=node)
            with open(os.path.join(myDataDir, filename)) as f:
                csvData = list(csv.reader(f))
                lastRow = csvData[-1]
                self.cacheRates[node] = round(float(lastRow[1]) * 100, 2)

        print("Cache rates for %s: %s" % (self.myName, self.cacheRates))


    def plotCacheRates(self, ax):
        ax.set_title(self.myName)

        ax.bar(self.cacheRates.keys(), self.cacheRates.values())
