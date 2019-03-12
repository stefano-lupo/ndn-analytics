import os
import sys

from typing import List

from interest_rate import InterestRatesForNode
from packet_time_histograms import PacketTimeHistograms
from status_deltas import StatusDeltasHistograms


class SingleNodeAnalyser:

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

    def plotPacketTimes(self, nodes=None):
        nodes = self.nodes if nodes is None else nodes
        for node in nodes:
            packetTimeHistograms: PacketTimeHistograms = PacketTimeHistograms(self.getNodeDir(node))
            packetTimeHistograms.showHistograms()

    def plotStatusDeltas(self, nodes=None):
        nodes = self.nodes if nodes is None else nodes
        for node in nodes:
            statusDeltaHistograms: StatusDeltasHistograms  = StatusDeltasHistograms(node, self.getNodeDir(node))
            statusDeltaHistograms.plotStatusDeltas()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        dir = "./data/local/no_dr"
        print("No dir given as CLA, defaulting to %s" % dir)
    else:
        dir = sys.argv[1]

    singleNodeAnalyser = SingleNodeAnalyser(dir)
    singleNodeAnalyser.printInterestRates()
    singleNodeAnalyser.plotStatusDeltas()
    singleNodeAnalyser.plotPacketTimes()
