import reading_utils
import numpy as np
from typing import List, Dict

FILE_FORMAT = "dr-counter-{}.csv"

# counterNames: List[str] = ["null", "velocity", "threshold", "skip"]
counterNames: List[str] = ["velocity", "threshold", "skip"]

class DeadReckoningAnalyzer:

    def __init__(self, node:str, nodeDir:str):
        self.nodeDir = nodeDir
        self.node = node
        self.counters = {}
        try:
            self.counters: Dict[str, int] = {name: self.getCounter(name) for name in counterNames}
        except FileNotFoundError:
            return
        # self.nullCount = self.getCounter("null")
        # self.velCount = self.getCounter("velocity")
        # self.thresholdCount = self.getCounter("threshold")
        # self.skipCount = self.getCounter("skip")
        self.total = sum(self.counters.values())
        self.actionable = 0 if self.total is 0 else (self.total - self.counters["skip"]) / self.total

    def getCounter(self, counterName: str) -> int:
        try:
            lines = reading_utils.readCsv(reading_utils.buildFileName(self.nodeDir, FILE_FORMAT.format(counterName)))
        except FileNotFoundError:
            raise FileNotFoundError()

        return int(lines[-1][1])

    def plotPieChart(self, ax):
        if len(self.counters) == 0:
            return
        ax.pie(self.counters.values(), explode=[0.2, 0.2, 0.2], labels=self.counters.keys(), radius=3, autopct='%1.1f%%',
               shadow=True, startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        ax.set_title(self.node)
        # ax.pie(self.counters.values(), labels=self.counters.keys())

    def plotDonut(self, ax):
        wedges, texts, percentages = ax.pie(self.counters.values(), autopct='%1.1f%%' ,wedgeprops=dict(width=0.5), startangle=-40)

        bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
        kw = dict(xycoords='data', textcoords='data', arrowprops=dict(arrowstyle="-"),
                  bbox=bbox_props, zorder=0, va="center")

        for i, p in enumerate(wedges):
            ang = (p.theta2 - p.theta1) / 2. + p.theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = "angle,angleA=0,angleB={}".format(ang)
            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            ax.annotate("{} - {}".format(list(self.counters.keys())[i], percentages[i]._text), xy=(x, y), xytext=(1.35 * np.sign(x), 1.4 * y),
                        horizontalalignment=horizontalalignment, **kw)

        ax.set_title(self.node)
