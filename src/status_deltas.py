import json
import os
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np

HISTOGRAM_VALUES_FILE = "histogram_values.json"
DISTANCE_SCALE_FACTOR = 100

def rejectOutliers(data, m=2):
    return data[abs(data - np.mean(data)) < m * np.std(data)]

class StatusDelta:
    def __init__(self, name: str, values: List[int]):
        self.name = name.split("-")[3]
        # print(values)
        # values = np.array(values)
        # initialNumPoints = np.size(values)
        # values = rejectOutliers(values)
        # print(values)
        # print("Initial num points %d, after outlier removal %d" % (initialNumPoints, len(values)))
        self.values = [value / DISTANCE_SCALE_FACTOR for value in values]
        # print("mean %d, min %d, max %d, std dev %d" % (np.mean(self.values), np.max(self.values), np.min(self.values), np.std(self.values)))



class StatusDeltasHistograms:

    def __init__(self, nodeName, nodeNameDir):
        self.nodeName = nodeName
        with open(os.path.join(nodeNameDir, HISTOGRAM_VALUES_FILE)) as f:
            jsonDict: Dict[str, List[int]] = json.load(f)
            self.statusDeltas = []
            for k, v in jsonDict.items():
                if k.startswith("eng-status-delta"):
                    self.statusDeltas.append(StatusDelta(k, v))

    def plotStatusDeltas(self, ax):
        print("\n\nStatus deltas for %s" % self.nodeName)
        data = [statusDelta.values for statusDelta in self.statusDeltas]
        labels = [statusDelta.name for statusDelta in self.statusDeltas]
        ax.set_title("Player Status Deltas for %s" % self.nodeName)
        ax.hist(data, bins=[0,1,2,3,4], label=labels)
        ax.set_xlabel("Distance (Game World Units)")
        ax.set_ylabel("Frequency")
        ax.legend()
