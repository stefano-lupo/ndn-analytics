import os
from typing import List, Dict

from interest_rate import InterestRatesForNode
from reading_utils import readCsvSafe

fileNameFormat = "sub-{objectType}-interestscounter-{nodeName}.csv"

class InterestAggregation:

    def __init__(self, myNode: str, myNodeDir: str, nodes: List[str], dataDir: str, routers: List[str] = None, objectType: str = 'status'):
        self.myNode = myNode
        self.pubInterestRate = InterestRatesForNode(myNodeDir, myNode)
        self.subInterestsCounterByNode: Dict[str, int] = dict()
        self.objectType = objectType
        for node in [n for n in nodes if n != myNode and n not in ([] if routers == None else routers)]:
            fileName = fileNameFormat.format(objectType=objectType, nodeName=myNode)
            fullFile = os.path.join(dataDir, node, fileName)
            csvData = readCsvSafe(fullFile)
            if csvData == None:
                self.subInterestsCounterByNode[node] = 0
            else:
                self.subInterestsCounterByNode[node] = int(csvData[-1][1])

    def getDifference(self) -> (int, int):
        totalInterestsExpressed: int = sum(self.subInterestsCounterByNode.values())
        return (self.pubInterestRate.getInterestRateForType(self.objectType).totalInterestsSeen, totalInterestsExpressed)
