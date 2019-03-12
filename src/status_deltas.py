import json
import os
from typing import Dict, List

import matplotlib.pyplot as plt

HISTOGRAM_VALUES_FILE = "histogram_values.json"


class StatusDelta:
    def __init__(self, name: str, values: List[int]):
        self.name = name.split("-")[3]
        self.values = [value / 1000 for value in values]


class StatusDeltasHistograms:

    def __init__(self, nodeName, nodeNameDir):
        self.nodeName = nodeName
        with open(os.path.join(nodeNameDir, HISTOGRAM_VALUES_FILE)) as f:
            jsonDict: Dict[str, List[int]] = json.load(f)
            self.statusDeltas = []
            for k, v in jsonDict.items():
                if k.startswith("eng-status-delta"):
                    self.statusDeltas.append(StatusDelta(k, v))

    def plotStatusDeltas(self):
        print("\n\nStatus deltas for %s" % self.nodeName)
        data = [statusDelta.values for statusDelta in self.statusDeltas]
        labels = [statusDelta.name for statusDelta in self.statusDeltas]
        plt.title("Player Status Deltas for %s" % self.nodeName)
        plt.hist(data, label=labels)
        plt.xlabel("Distance (Game World Units)")
        plt.ylabel("Frequency")
        plt.legend()
        plt.show()
