import reading_utils
from typing import List, Dict

FILE_FORMAT = "dr-counter-%s"

counterNames: List[str] = ["null", "velocity", "threshold", "skip"]

class DeadReckoningAnalyzer:

    def __init__(self, node:str, nodeDir:str):
        self.nodeDir = nodeDir
        self.node = node
        self.counters: Dict[str, int] = {name:self.getCounter(name) for name in counterNames}
        # self.nullCount = self.getCounter("null")
        # self.velCount = self.getCounter("velocity")
        # self.thresholdCount = self.getCounter("threshold")
        # self.skipCount = self.getCounter("skip")
        self.total = sum(self.counters.values())
        self.actionable = (self.total - self.counters["skip"]) / self.total

    def getCounter(self, counterName: str) -> int:
        lines = reading_utils.readFileSafe(self.nodeDir, FILE_FORMAT.format(counterName))
        return int(lines[-1])

    def plotPieChart(self, ax):
        ax.pie(self.counters.values(), labels=self.counters.keys())
