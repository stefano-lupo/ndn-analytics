import os
import sys

from typing import List

import matplotlib.pyplot as plt
import numpy as np

from interest_rate import InterestRatesForNode
from packet_time_histograms import PacketTimeHistograms
from status_deltas import StatusDeltasHistograms


class AnalysisByNode:

    def __init__(self, dir, nodes: List[str] = None):
        self.dir = dir
        if nodes is None:
            self.nodes = os.listdir(dir)

    def getNodeDir(self, nodeName: str) -> str:
        return os.path.join(self.dir, nodeName)

    def printInterestRates(self, nodes=None):
        nodes = self.nodes if nodes is None else nodes
        for node in nodes:
            interestRate = InterestRatesForNode(self.getNodeDir(node), node)
            interestRate.printRates()

    def plotPacketTimes(self, nodes=None, objectType="status", metricType="rtt"):
        nodes = self.nodes if nodes is None else nodes
        nodes.sort()
        f, ax = plt.subplots(2, 2)
        ax = ax.flatten()
        f.suptitle("%s - %s" % (objectType, metricType))
        for i, node in enumerate(nodes):
            packetTimeHistograms: PacketTimeHistograms = PacketTimeHistograms(self.getNodeDir(node), node)
            packetTimeHistograms.showHistograms(ax[i], objectType=objectType, metricType=metricType)
        plt.show()

    def plotStatusDeltas(self, nodes=None):
        nodes = self.nodes if nodes is None else nodes
        for node in nodes:
            statusDeltaHistograms: StatusDeltasHistograms = StatusDeltasHistograms(node, self.getNodeDir(node))
            statusDeltaHistograms.plotStatusDeltas()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        dir = "./data/local/no_dr"
        print("No dir given as CLA, defaulting to %s" % dir)
    else:
        dir = sys.argv[1]

    analysisByNode = AnalysisByNode(dir)
    analysisByNode.printInterestRates()
    analysisByNode.plotStatusDeltas()
    analysisByNode.plotPacketTimes()
