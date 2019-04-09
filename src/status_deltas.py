import json
import os
from typing import Dict, List

import numpy as np

HISTOGRAM_VALUES_FILE = "histogram_values.json"
DISTANCE_SCALE_FACTOR = 100

def rejectOutliers(data, m=2):
    return data[abs(data - np.mean(data)) < m * np.std(data)]

class StatusDelta:
    def __init__(self, name: str, values: List[int]):
        self.name = name.split("-")[3]
        self.values = [value / DISTANCE_SCALE_FACTOR for value in values]

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
        data = [statusDelta.values for statusDelta in self.statusDeltas]
        labels = [statusDelta.name for statusDelta in self.statusDeltas]
        ax.set_title("%s" % self.nodeName)
        weights = [100 * np.ones_like(v) / len(v) for v in data]
        ax.hist(data, weights=weights, label=labels)
        ax.set_xlabel("Distance (GWUs)")
        ax.set_ylabel("Frequency (%)")
        ax.legend()

    def get95th(self):
        # item for sublist in l for item in sublist
        allData = self.getAllData()
        percentile = np.percentile(allData, 95)
        print(percentile)

    def getAllData(self):
        # item for sublist in l for item in sublist
        return [item for sublist in [sd.values for sd in self.statusDeltas] for item in sublist]
