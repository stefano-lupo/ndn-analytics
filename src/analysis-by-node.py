import os
import shutil
import sys
from collections import defaultdict
from typing import List, Dict

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

from interest_aggregation import InterestAggregation
from interest_rate import InterestRatesForNode
from log_reader import LogReader
from nfd_log_parser import NfdLogParser, CacheRate
from packet_time_histograms import PacketTimeHistograms
from status_deltas import StatusDeltasHistograms
from dead_reckoning_analyzer import DeadReckoningAnalyzer

matplotlib.rcParams['figure.figsize'] = (15.0, 10.0)
matplotlib.rcParams['axes.labelsize'] = 20
matplotlib.rcParams['savefig.dpi'] = 100
matplotlib.rcParams['font.size'] = 16
matplotlib.rcParams['legend.fontsize'] = 'large'
matplotlib.rcParams['figure.titlesize'] = 'large'
matplotlib.rcParams['legend.framealpha'] = 0.5
# matplotlib.rcParams['axes.labelsize'] = 20


FIGURE_DIR = "figures"
ROUTERS = {
    "tree": ["nodeE", "nodeF", "nodeG"],
    "dumbbell": ["nodeE", "nodeF"],
    "scalability": ["nodeQ", "nodeR", "nodeS", "nodeT"]
}

dirsToSkip = ["aws-1", "aws-1-again", "aws-1-again2"]
nodesToSkip = []

# TODO: Find out enums
STATUS = "status"
BLOCKS = "blocks"
PROJECTILES = "projectiles"

def cleanName(name: str):
    if name == "nodeNN":
        return "N"
    else:
        return name[4:]

def cleanNames(names: List[str]):
    return [cleanName(n) for n in names]

def plotMulticategoryBar(ax, valuesDict: Dict[str, Dict[str, float]]):
    xCategories = next(iter(valuesDict.values())).keys()
    ind = np.arange(len(xCategories))
    delWidth = 0.5 / len(valuesDict.keys())
    width = 0
    for legendCategory, values in valuesDict.items():
        ax.bar(ind + width, values.values(), delWidth, label=legendCategory, align="edge")
        width = width + delWidth

    ax.legend(framealpha=0.5)
    ax.autoscale_view()
    ax.set_xticks(ind + width / 2)
    ax.set_xticklabels(xCategories)


class AnalysisByNode:

    def __init__(self, dataDir, topology: str, mainDir:str, subDirs: List[str], nodes: List[str] = None):
        self.dataDir = dataDir
        self.mainDir = mainDir
        self.subDirs = subDirs
        self.nodes = os.listdir(self.getSubDir(self.mainDir)) if nodes is None else nodes

        self.nodes.sort()
        for remove in nodesToSkip: self.nodes.remove(remove)
        self.gameNodes = self.nodes if topology not in ROUTERS.keys() else [node for node in self.nodes if node not in ROUTERS[topology]]
        self.routerNodes = [node for node in self.nodes if node not in self.gameNodes]
        self.topology = topology
        self.plotDims = (2, 2)
        self.plotDims = (4, 4)
        self.figureDir = os.path.join(dataDir, FIGURE_DIR, self.mainDir)
        if os.path.exists(self.figureDir):
            shutil.rmtree(self.figureDir)
        os.makedirs(self.figureDir, exist_ok=True)

    def saveFig(self, fig, plotName: str):
        # pass
        fig.savefig(os.path.join(self.figureDir, plotName) + ".png", bbox_inches='tight')
        plt.clf()
        plt.close('all')

    def getSubDir(self, subDir: str = None) -> str:
        subDir = self.mainDir if subDir is None else subDir
        return os.path.join(self.dataDir, subDir)

    def getNodeDir(self, nodeName: str, subDir: str = None) -> str:
        fullSubDirPath = self.getSubDir(subDir)
        return os.path.join(fullSubDirPath, nodeName)

    def checkForExceptions(self, nodes=None):
        nodes = self.gameNodes if nodes is None else nodes
        for node in nodes:
            logReader = LogReader(node, self.getNodeDir(node))

    def getAxis(self):
        return plt.subplots(*self.plotDims)

    def plotInterestRates(self, nodes=None, objectType=STATUS):
        nodes = self.gameNodes if nodes is None else nodes
        f, ax = plt.subplots(1)
        f.suptitle("Interest Rates for %s" % objectType)
        ax.set_xlabel("Node")
        ax.set_ylabel("Interests received per second")
        for node in nodes:
            interestRate = InterestRatesForNode(self.getNodeDir(node), node)
            interestRate.plotInterestRateForType(ax, objectType)
        self.saveFig(f, "interest-rates-over-time")

    def plotPacketTimes(self, nodes=None, objectType=STATUS, metricType="rtt"):
        nodes = self.gameNodes if nodes is None else nodes
        nodes.sort()

        packetTimeHistograms = [PacketTimeHistograms(self.getNodeDir(node), node) for node in nodes]

        # self.plotDetailedPacketTimes(packetTimeHistograms, objectType, metricType)
        self.plotAggregatedPacketTimes(packetTimeHistograms)

    def plotAggregatedPacketTimes(self, packetTimeHistograms: List[PacketTimeHistograms]):
        f, ax = plt.subplots()
        playerHists = [pth.getAllData() for pth in packetTimeHistograms]
        weights = [100 * np.ones_like(v) / len(v) for v in playerHists]
        ax.hist(playerHists, label=cleanNames([pth.nodeName for pth in packetTimeHistograms]), bins=np.linspace(0, 300, 11), weights=weights)
        ax.set_xlabel("RTT (ms)")
        ax.set_ylabel("%")
        f.suptitle("RTT of status packets in the scalability test")
        ax.legend()

        self.saveFig(f, "aggregated-packet-times")
        #
        # allData = [val for sublist in playerHists for val in sublist]
        # f, ax = plt.subplots()
        # ax.boxplot(allData)


    def plotDetailedPacketTimes(self, packetTimeHistograms: List[PacketTimeHistograms], objectType=STATUS, metricType="rtt"):
        f = plt.figure()
        f.suptitle("Round trip times for %s" % objectType)
        gridSpecs = gridspec.GridSpec(nrows=self.plotDims[0], ncols=self.plotDims[1], figure=f)
        ax = [f.add_subplot(gs) for gs in gridSpecs]
        # ax = ax.flatten()
        for i, packetTimeHistogram in enumerate(packetTimeHistograms):
            packetTimeHistograms[i].showHistograms(ax[i], objectType=objectType, metricType=metricType)
        gridSpecs.tight_layout(f)
        self.saveFig(f, "rtt")

    def plotStatusDeltas(self, nodes=None):
        nodes = self.gameNodes if nodes is None else nodes
        statusDeltaHistograms: List[StatusDeltasHistograms] = [StatusDeltasHistograms(n, self.getNodeDir(n)) for n in nodes]

        # self.plotStatusDeltaDetailedHistograms(nodes, statusDeltaHistograms)
        self.plotAggregatedStatusDeltas(nodes, statusDeltaHistograms)

    def plotAggregatedStatusDeltas(self, nodes: List[str], sdHistograms: List[StatusDeltasHistograms]):
        sdHists = [sdHist.getAllData() for sdHist in sdHistograms]
        weights = [100 * np.ones_like(v) / len(v) for v in sdHists]

        f, ax = plt.subplots()
        ax.hist(sdHists, label=cleanNames([sdh.nodeName for sdh in sdHistograms]), weights=weights, bins=np.linspace(0,5,11))
        ax.set_xlabel("Position Delta (GWU)")
        ax.set_ylabel("%")
        f.suptitle("Position Deltas of status packets in the scalability test")
        ax.legend()

        self.saveFig(f, "aggregated-position-deltas")

    def plotStatusDeltaDetailedHistograms(self, nodes, statusDeltaHistograms: List[StatusDeltasHistograms]):
        f, ax = self.getAxis()
        ax = ax.flatten()
        for i, sdh in enumerate(statusDeltaHistograms):
            sdh.plotStatusDeltas(ax[i])
        plt.show()
        self.saveFig(f, "status-deltas")

    def compareProducerRates(self, objectType=STATUS):

        RatesByNode = Dict[str, float]
        ratesByDir: Dict[str, RatesByNode] = {}

        allDirs: List[str] = [self.mainDir] + self.subDirs
        for subDir in allDirs:
            ratesByNode: RatesByNode = {}
            for node in self.gameNodes:
                nodeDir = self.getNodeDir(node, subDir)
                interestRateForNode = InterestRatesForNode(nodeDir, node)
                rate = interestRateForNode.getInterestRateForType(objectType).finalMeanRate
                ratesByNode[node] = rate
                print("Interest Rates: %s %s: %d" % (subDir, node, rate))
            ratesByDir[subDir] = ratesByNode

        f, ax = plt.subplots()
        ratesByDir = {k: {cleanName(p): val for p, val in v.items()} for k, v in ratesByDir.items()}
        plotMulticategoryBar(ax, ratesByDir)
        ax.set_ylabel("Interests Received per Second")
        ax.set_xlabel("Node")
        ax.legend(loc='upper right', framealpha=0.5)
        f.suptitle("Impact on Interest rates")
        self.saveFig(f, "interest-rate-impacts")

    def plotInterestRatesOverTime(self, objectType=STATUS):
        f, ax = plt.subplots()
        f.suptitle("Interest rates over time for %s" % objectType)
        for node in self.gameNodes:
            InterestRatesForNode(self.getNodeDir(node), node).plotInterestRateOverTime(ax)
        ax.legend()
        ax.set_xlabel("Elapsed Time (s)")
        ax.set_ylabel("Interests received per second")
        self.saveFig(f, "interest-rates-over-time")

    def plotInterestAggregations(self, objectType=STATUS):
        f, ax = plt.subplots()
        interests: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for node in self.gameNodes:
            interestAgg = InterestAggregation(node, self.getNodeDir(node), self.nodes, self.getSubDir(), self.routerNodes, objectType)
            pubInterests, subInterests = interestAgg.getDifference()
            interests["Interests Seen"][cleanName(node)] = pubInterests
            interests["Interests Expressed"][cleanName(node)] = subInterests
            print("Node %s: IAF = %.2d" % (node, 100 * pubInterests / subInterests))
        plotMulticategoryBar(ax, interests)
        ax.set_ylabel("Number of Interests")
        ax.set_xlabel("Node")
        f.suptitle("Interests seen by Publishers vs Interests expressed by Subscribers")
        self.saveFig(f, "interest-aggregations")

    def analyseCaches(self, objectType=STATUS):
        nfdParsers = [NfdLogParser(node, self.getNodeDir(node)) for node in self.nodes]
        nfdParsers.sort(key=lambda nfdP: nfdP.nodeName)
        self.getRouterCacheRates(nfdParsers, objectType=objectType)
        self.getTotalCacheRateByNode(nfdParsers)

    def getTotalCacheRateByNode(self, nfdParsers):
        # if self.topology in ROUTERS.keys():
        #     routers = ROUTERS[self.topology]
        #     nfdParsers = [n for n in nfdParsers if n.nodeName in routers]
        f, ax = plt.subplots()
        f.suptitle("Total cache hit rate by node")
        ax.set_ylabel("Hit Rate %")
        for nfdParser in nfdParsers:
            nfdParser.plotCacheRate(ax)
        self.saveFig(f, "cache-rates-by-node")

    def getRouterCacheRates(self, nfdParsers: List[NfdLogParser], objectType=STATUS):
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
        self.saveFig(f, "router-cache-rates")

    def plotDeadReckoningStack(self, nodes: List[str] = None):
        nodes = self.gameNodes if nodes is None else nodes
        drAnalyzers = [DeadReckoningAnalyzer(n, self.getNodeDir(n)) for n in nodes]
        byType: Dict[str, Dict[str, float]] = defaultdict(lambda : defaultdict(float))


        for i, analyzer in enumerate(drAnalyzers):
            byTypeForPlayer = analyzer.getPercentages()
            for type, perc in byTypeForPlayer.items():
                byType[type][analyzer.node] = perc

        N = len(drAnalyzers)

        keys = cleanNames(byType["velocity"].keys())
        nulls = list(byType["null"].values())
        velocity = list(byType["velocity"].values())
        threshold = list(byType["threshold"].values())
        skips = list(byType["skip"].values())

        if len(velocity) == 0:
            return

        f, ax = plt.subplots()
        bottom = np.zeros(N)

        ax.bar(keys, velocity, bottom=bottom)
        bottom = bottom + velocity

        ax.bar(keys, skips, bottom=bottom)
        bottom = bottom + skips

        ax.bar(keys, threshold, bottom=bottom)
        bottom = bottom + threshold

        ax.bar(keys, nulls, bottom=bottom)
        bottom = bottom + nulls

        ax.set_ylabel('%')
        f.suptitle('DR Publisher Throttling Update Results')
        ax.set_yticks(np.arange(0, 101, 10))
        ax.legend(["Velocity", "Skips", "Threshold", "Null"])
        ax.set_xlabel("Node")
        self.saveFig(f, "dr-pub-throt")


def runAnalysisByNode(dataDir: str, topology: str, mainDir: str, subDirs: List[str]):
    analysisByNode = AnalysisByNode(dataDir, topology, mainDir, subDirs)
    analysisByNode.checkForExceptions()
    objectType = STATUS
    analysisByNode.plotInterestRates(objectType=objectType)
    analysisByNode.plotStatusDeltas()
    analysisByNode.plotPacketTimes(objectType=objectType)
    analysisByNode.compareProducerRates(objectType=objectType)
    analysisByNode.plotInterestRatesOverTime(objectType=objectType)
    analysisByNode.plotInterestAggregations(objectType=objectType)
    analysisByNode.analyseCaches(objectType=objectType)
    analysisByNode.plotDeadReckoningStack()
    # plt.show()


if __name__ == "__main__":
    dataDir = sys.argv[1]
    topology = sys.argv[2]
    if len(sys.argv) > 3:
        subDirs = sys.argv[3:]
    else:
        subDirs = os.listdir(dataDir)
        subDirs = [sd for sd in subDirs if sd not in dirsToSkip]
    if FIGURE_DIR in subDirs:
        subDirs.remove(FIGURE_DIR)
    for mainDir in subDirs:
        otherDirs = [otherDir for otherDir in subDirs if otherDir != mainDir]
        print("\n\nMain dir: %s, otherDirs: %s\n" % (mainDir, otherDirs))
        runAnalysisByNode(dataDir, topology, mainDir, otherDirs)


