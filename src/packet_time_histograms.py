import json
import os
from typing import List, Dict

import numpy as np

HISTOGRAM_VALUES_FILE = "histogram_values.json"

HistogramValues = List[int]


# Format of metric names is : sub-<object-type>-<latency|rtt>-<player_name>
class PacketTimeMetric:
    def __init__(self, name: str, histogramValues: list):
        pieces = name.split("-")
        self.objectType: str = pieces[1]
        self.metricType: str = pieces[2]
        self.playerName: str = pieces[3]
        self.histogramValues: HistogramValues = histogramValues


Metrics = List[PacketTimeMetric]
MetricsByObjectType = Dict[str, Dict[str, Metrics]]


class PacketTimeHistograms:

    def __init__(self, dir, nodeName):
        self.nodeName = nodeName
        histogramsFile = os.path.join(dir, HISTOGRAM_VALUES_FILE)
        with open(histogramsFile) as f:
            histograms = json.load(f)
            metrics = []
            for name, val in histograms.items():
                if "rtt" not in name:
                    continue
                metrics.append(PacketTimeMetric(name, val))

        self.metricsByObjectType: MetricsByObjectType = {"status": {}, "blocks": {}, "projectiles": {}}
        for playerMetric in metrics:
            metricsForObjectType = self.metricsByObjectType[playerMetric.objectType]
            if playerMetric.metricType in metricsForObjectType:
                metricsForObjectType[playerMetric.metricType].append(playerMetric)
            else:
                metricsForObjectType[playerMetric.metricType] = [playerMetric]

    def showHistograms(self, ax, objectType='status', metricType="rtt"):
            metricsByMetricType = self.metricsByObjectType[objectType]
            ax.set_title("%s" % self.nodeName)

            # TODO: Make absolutely sure iteration order is constant
            if metricType not in metricsByMetricType.keys():
                print("Skipping for %s" % self.nodeName)
                return
            metrics: Metrics = metricsByMetricType[metricType]
            values = [m.histogramValues for m in metrics]
            labels = [m.playerName for m in metrics]
            weights = [100 * np.ones_like(v) / len(v) for v in values]
            ax.hist(values, weights=weights, label=labels, bins=np.linspace(0, 100, 6))
            ax.set_ylabel("Frequency (%)")
            ax.set_xlabel("Time (ms)")
            ax.legend(loc='upper right')

    def getAllData(self):
        listByPlayer = [ptm.histogramValues for ptm in self.metricsByObjectType["status"]["rtt"]]
        agg = [val for sublist in listByPlayer for val in sublist]
        return agg


