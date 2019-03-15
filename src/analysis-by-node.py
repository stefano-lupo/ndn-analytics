import os
import sys
from typing import List, Dict
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np

from interest_rate import InterestRatesForNode
from packet_time_histograms import PacketTimeHistograms
from status_deltas import StatusDeltasHistograms
from interest_aggregation import InterestAggregation
from nfd_log_parser import NfdLogParser, CacheRate

ROUTERS = {
    "tree": ["nodeE", "nodeF", "nodeG"],
    "dumbbell": ["nodeE", "nodeF"]
}

# TODO: Find out enums
STATUS = "status"
BLOCKS = "blocks"
PROJECTILES = "projectiles"

def plotMulticategoryBar(ax, valuesDict: Dict[str, Dict[str, float]]):
    xCategories = next(iter(valuesDict.values())).keys()
    ind = np.arange(len(xCategories))
    delWidth = 0.5 / len(valuesDict.keys())
    width = 0
    for legendCategory, values in valuesDict.items():
        ax.bar(ind + width, values.values(), delWidth, label=legendCategory, align="edge")
        width = width + delWidth

    ax.legend()
    ax.autoscale_view()
    ax.set_xticks(ind + width / 2)
    ax.set_xticklabels(xCategories)


class AnalysisByNode:

    def __init__(self, dataDir, topology: str, subDirs: List[str], nodes: List[str] = None):
        self.dataDir = dataDir
        self.subDirs = subDirs
        self.nodes = os.listdir(self.getSubDir(subDirs[0])) if nodes is None else nodes
        self.nodes.sort()
        self.gameNodes = self.nodes if topology not in ROUTERS.keys() else [node for node in self.nodes if node not in ROUTERS[topology]]
        self.routerNodes = [node for node in self.nodes if node not in self.gameNodes]
        self.topology = topology

    def getSubDir(self, subDir: str = None) -> str:
        subDir = self.subDirs[0] if subDir is None else subDir
        return os.path.join(self.dataDir, subDir)

    def getNodeDir(self, nodeName: str, subDir: str = None) -> str:
        fullSubDirPath = self.getSubDir(subDir)
        return os.path.join(fullSubDirPath, nodeName)

    def plotInterestRates(self, nodes=None, objectType=STATUS):
        nodes = self.gameNodes if nodes is None else nodes
        f, ax = plt.subplots(1)
        f.suptitle("Interest Rates- %s" % objectType)
        ax.set_xlabel("Node")
        ax.set_ylabel("Interests received per second")
        for node in nodes:
            interestRate = InterestRatesForNode(self.getNodeDir(node), node)
            interestRate.plotInterestRateForType(ax, objectType)

    def plotPacketTimes(self, nodes=None, objectType=STATUS, metricType="rtt"):
        nodes = self.gameNodes if nodes is None else nodes
        nodes.sort()
        f, ax = plt.subplots(2, 2)
        ax = ax.flatten()
        f.suptitle("%s - %s" % (objectType, metricType))
        for i, node in enumerate(nodes):
            packetTimeHistograms: PacketTimeHistograms = PacketTimeHistograms(self.getNodeDir(node), node)
            packetTimeHistograms.showHistograms(ax[i], objectType=objectType, metricType=metricType)

    def plotStatusDeltas(self, nodes=None):
        f, ax = plt.subplots(2, 2)
        ax = ax.flatten()
        nodes = self.gameNodes if nodes is None else nodes
        for i, node in enumerate(nodes):
            statusDeltaHistograms: StatusDeltasHistograms = StatusDeltasHistograms(node, self.getNodeDir(node))
            statusDeltaHistograms.plotStatusDeltas(ax[i])
    #
    # def plotCacheRates(self, nodes=None, objectType="status"):
    #     nodes = self.nodes if nodes is None else nodes
    #     f, ax = plt.subplots(2, 2)
    #     f.suptitle("%s Cache Rates" % objectType)
    #     ax = ax.flatten()
    #     for a in ax:
    #          # a.set_xlabel("Node")
    #          a.set_ylabel("Hit Rate (%)")
    #
    #     for i, myNode in enumerate(nodes):
    #         otherNodes = [node for node in nodes if node != myNode]
    #         cacheRates: CacheRates = CacheRates(self.getNodeDir(myNode), myNode, otherNodes)
    #         cacheRates.plotCacheRates(ax[i])

    def compareProducerRates(self, objectType=STATUS):

        RatesByNode = Dict[str, float]
        ratesByDir: Dict[str, RatesByNode] = {}

        for subDir in self.subDirs:
            ratesByNode: RatesByNode = {}
            for node in self.gameNodes:
                nodeDir = self.getNodeDir(node, subDir)
                print(nodeDir)
                interestRateForNode = InterestRatesForNode(nodeDir, node)
                ratesByNode[node] = interestRateForNode.getInterestRateForType(objectType).finalMeanRate
            ratesByDir[subDir] = ratesByNode

        fig, ax = plt.subplots()
        plotMulticategoryBar(ax, ratesByDir)
        ax.set_ylabel("Interests Received per Second")
        fig.suptitle("Impact on Interest Rates")

    def plotInterestRatesOverTime(self, objectType=STATUS):
        f, ax = plt.subplots()
        f.suptitle("Interest rates over time for %s" % objectType)
        for node in self.gameNodes:
            InterestRatesForNode(self.getNodeDir(node), node).plotInterestRateOverTime(ax)
        ax.legend()
        ax.set_xlabel("Elapsed Time (s)")
        ax.set_ylabel("Interests received per second")

    def plotInterestAggregations(self, objectType=STATUS):
        f, ax = plt.subplots()
        interests: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for node in self.gameNodes:
            interestAgg = InterestAggregation(node, self.getNodeDir(node), self.nodes, self.getSubDir(), self.routerNodes, objectType)
            pubInterests, subInterests = interestAgg.getDifference()
            interests["pub"][node] = pubInterests
            interests["sub"][node] = subInterests
        plotMulticategoryBar(ax, interests)
        ax.set_ylabel("Number of Interests")
        f.suptitle("Publisher Interests seen vs total subscriber interests expressed")

    def analyseCaches(self, objectType=STATUS):
        nfdParsers = [NfdLogParser(node, self.getNodeDir(node)) for node in self.nodes]
        nfdParsers.sort(key=lambda nfdP: nfdP.nodeName)
        self.getRouterCacheRates(nfdParsers, objectType=objectType)
        self.getTotalCacheRateByNode(nfdParsers)

    def getTotalCacheRateByNode(self, nfdParsers):
        f, ax = plt.subplots()
        f.suptitle("Total Cache Hit Rate by Node")
        ax.set_ylabel("Hit Rate")
        for nfdParser in nfdParsers:
            nfdParser.plotCacheRate(ax)

    def getRouterCacheRates(self, nfdParsers: List[NfdLogParser], objectType=STATUS):
        print(self.routerNodes)
        nfdParsers = nfdParsers if len(self.routerNodes) == 0 else  [nfdP for nfdP in nfdParsers if nfdP.nodeName in self.routerNodes]
        f, ax = plt.subplots()
        routerCacheRateForNodes: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for i, routerNodeParser in enumerate(nfdParsers):
            statusCacheRatesByPlayer: Dict[str, CacheRate] = routerNodeParser.getCacheRatesForObjectType(objectType=objectType)
            for player, cacheRate in statusCacheRatesByPlayer.items():
                routerCacheRateForNodes[player][routerNodeParser.nodeName] = cacheRate.getCacheRate()
        plotMulticategoryBar(ax, routerCacheRateForNodes)
        ax.set_ylabel("Cache Rate %")
        f.suptitle("Router Cache Rates by Node")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        dataDir = "./data/local"
        topology = dataDir
        subDirs = ["no_dr"]
        print("No dir given as CLA, defaulting to %s" % dataDir)
    else:
        dataDir = sys.argv[1]
        topology = sys.argv[2]
        subDirs = sys.argv[3:]

    analysisByNode = AnalysisByNode(dataDir, topology, subDirs)
    objectType = STATUS
    analysisByNode.plotInterestRates(objectType=objectType)
    analysisByNode.plotStatusDeltas()
    analysisByNode.plotPacketTimes(objectType=objectType)
    analysisByNode.compareProducerRates(objectType=objectType)
    analysisByNode.plotInterestRatesOverTime(objectType=objectType)
    analysisByNode.plotInterestAggregations(objectType=objectType)
    analysisByNode.analyseCaches(objectType=objectType)
    plt.show()
