from typing import List, Dict
from collections import defaultdict, OrderedDict
import re

from reading_utils import readFileSafe

NFD_LOG_FILE = "nfd.log"
GAME_PREFIX = "/com/stefanolupo/ndngame/0/({playerName})/({objectType})/sync"
CACHE_LOOKUP_LINE = "find " + GAME_PREFIX
CACHE_HIT_LINE = "matching " + GAME_PREFIX


class CacheRate:

    def __init__(self):
        self.lookups = 0
        self.hits = 0

    def addLookup(self):
        self.lookups = self.lookups + 1

    def addHitWithoutLookup(self):
        self.hits = self.hits + 1

    def mergeWithOther(self, other):
        self.lookups += other.lookups
        self.hits += other.hits

    def getCacheRate(self) -> float:
        return self.hits / self.lookups


class NfdLogParser:

    def __init__(self, nodeName: str, nodeDir: str):
        self.lines: List[str] = readFileSafe(nodeDir, NFD_LOG_FILE)
        self.nodeName = nodeName
        (cacheRates, totalLookups, totalHits) = self.buildCacheRates()
        self.cacheRates: Dict[str, Dict[str, CacheRate]] = cacheRates
        self.totalLookups = totalLookups
        self.totalHits = totalHits

    def plotCacheRate(self, ax, playerName = None, objectType = None):
        ax.bar(self.nodeName, self.getTotalCacheRate(playerName, objectType))

    def getTotalCacheRate(self, playerName: str = None, objectType: str = None) -> float:
        if playerName is None and objectType is None:
            return self.totalHits / self.totalLookups

        lookups = 0
        hits = 0
        dictToUse = self.getCacheRatesForPlayer(playerName) if playerName is not None else self.getCacheRatesForObjectType(objectType)
        for cacheRate in dictToUse.values():
            lookups += cacheRate.lookups
            hits += cacheRate.hits
        return hits / lookups


    def getCacheRatesForPlayer(self, playerName: str) -> Dict[str, CacheRate]:
        return self.cacheRates[playerName]

    def getCacheRatesForObjectType(self, objectType: str) -> Dict[str, CacheRate]:
        cacheRateByPlayer = defaultdict(CacheRate)
        for player, cacheRateByObjectType in self.cacheRates.items():
            cacheRateByPlayer[player] = cacheRateByObjectType[objectType]
        return cacheRateByPlayer

    def buildCacheRates(self, playerName: str = ".*", objectType: str = ".*") -> (CacheRate, int, int):
        cacheRates = defaultdict(lambda: defaultdict(CacheRate))
        cacheLookupLine = CACHE_LOOKUP_LINE.format(playerName=playerName, objectType=objectType)
        cacheHitLine = CACHE_HIT_LINE.format(playerName=playerName, objectType=objectType)
        numLookups: int = 0
        numCacheHits: int = 0

        for i, line in enumerate(self.lines):
            cacheLookupMatch = re.search(cacheLookupLine, line)
            if cacheLookupMatch:
                numLookups = numLookups + 1
                playerName: str = cacheLookupMatch.group(1)
                objectType: str = cacheLookupMatch.group(2)
                cacheRates[playerName][objectType].addLookup()
                continue

            cacheHitMatch = re.search(cacheHitLine, line)
            if cacheHitMatch:
                numCacheHits = numCacheHits + 1
                playerName: str = cacheHitMatch.group(1)
                objectType: str = cacheHitMatch.group(2)
                cacheRates[playerName][objectType].addHitWithoutLookup()
                continue
        print("Cache rate of %s: %f / %f = %f" % (self.nodeName, numCacheHits, numLookups, numCacheHits / numLookups))
        cacheRates = sorted(cacheRates.items(), key=lambda kv: kv[0])
        cacheRates = OrderedDict(cacheRates)

        return cacheRates, numLookups, numCacheHits
