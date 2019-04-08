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
matplotlib.rcParams['legend.framealpha'] = None
# matplotlib.rcParams['axes.labelsize'] = 20


FIGURE_DIR = "figures"
ROUTERS = {
    "tree": ["nodeE", "nodeF", "nodeG"],
    "dumbbell": ["nodeE", "nodeF"],
    "scalability": ["nodeQ", "nodeR", "nodeS", "nodeT"]
}

nodesToSkip = []

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
        self.figureDir = os.path.join(dataDir, FIGURE_DIR, self.mainDir)
        if os.path.exists(self.figureDir):
            shutil.rmtree(self.figureDir)
        os.makedirs(self.figureDir, exist_ok=True)

    def saveFig(self, fig, plotName: str):
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
        # f, ax = self.getAxis()
        f = plt.figure()
        f.suptitle("Round trip times for %s" % objectType)
        gridSpecs = gridspec.GridSpec(nrows=2, ncols=2, figure=f)
        ax = [f.add_subplot(gs) for gs in gridSpecs]
        # ax = ax.flatten()

        for i, node in enumerate(nodes):
            packetTimeHistograms: PacketTimeHistograms = PacketTimeHistograms(self.getNodeDir(node), node)
            packetTimeHistograms.showHistograms(ax[i], objectType=objectType, metricType=metricType)
        gridSpecs.tight_layout(f)
        self.saveFig(f, "rtt")

    def plotStatusDeltas(self, nodes=None):
        f = plt.figure()
        f.suptitle("Position Delta")
        gridSpecs = gridspec.GridSpec(nrows=2, ncols=2, figure=f)
        ax = [f.add_subplot(gs) for gs in gridSpecs]

        # f, ax = self.getAxis()
        # f.suptitle("PlayerStatus deltas")
        # ax = ax.flatten()
        nodes = self.gameNodes if nodes is None else nodes
        for i, node in enumerate(nodes):
            statusDeltaHistograms: StatusDeltasHistograms = StatusDeltasHistograms(node, self.getNodeDir(node))
            statusDeltaHistograms.plotStatusDeltas(ax[i])
        gridSpecs.tight_layout(f)
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
        plotMulticategoryBar(ax, ratesByDir)
        ax.set_ylabel("Interests Received per Second")
        ax.legend(loc='lower center', framealpha=0.5)
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
            interests["Interests Seen"][node] = pubInterests
            interests["Interests Expressed"][node] = subInterests
            print("Node %s: IAF = %.2d" % (node, 100 * pubInterests / subInterests))
        plotMulticategoryBar(ax, interests)
        ax.set_ylabel("Number of Interests")
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

    def plotDeadReckoningPie(self, nodes: List[str] = None):
        nodes = self.gameNodes if nodes is None else nodes
        drAnalyzers = [DeadReckoningAnalyzer(n, self.getNodeDir(n)) for n in nodes]
        f, ax = self.getAxis()
        ax = ax.flatten()
        for i, analyzer in enumerate(drAnalyzers):
            analyzer.plotPieChart(ax[i])
            # analyzer.plotDonut(ax[i])
        f.suptitle("DR Publisher Throttling")
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
    analysisByNode.plotDeadReckoningPie()
    # plt.show()


if __name__ == "__main__":
    dataDir = sys.argv[1]
    topology = sys.argv[2]
    subDirs = os.listdir(dataDir)
    if FIGURE_DIR in subDirs:
        subDirs.remove(FIGURE_DIR)
    for mainDir in subDirs:
        otherDirs = [otherDir for otherDir in subDirs if otherDir != mainDir]
        print("\n\nMain dir: %s, otherDirs: %s\n" % (mainDir, otherDirs))
        runAnalysisByNode(dataDir, topology, mainDir, otherDirs)


