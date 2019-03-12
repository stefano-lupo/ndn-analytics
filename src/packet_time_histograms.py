import json
import os
from typing import List, Dict

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
            metrics: Metrics = [PacketTimeMetric(name, values) for name, values in histograms.items()]

        self.metricsByObjectType: MetricsByObjectType = {"status": {}, "block": {}, "projectile": {}}
        for playerMetric in metrics:
            metricsForObjectType = self.metricsByObjectType[playerMetric.objectType]
            if playerMetric.metricType in metricsForObjectType:
                metricsForObjectType[playerMetric.metricType].append(playerMetric)
            else:
                metricsForObjectType[playerMetric.metricType] = [playerMetric]

    def showHistograms(self, ax, objectType='status', metricType="rtt"):
            metricsByMetricType = self.metricsByObjectType[objectType]
            ax.set_title("%s - RTT" % self.nodeName)

            # TODO: Make absolutely sure iteration order is constant
            metrics: Metrics = metricsByMetricType[metricType]
            values = [m.histogramValues for m in metrics]
            labels = [m.playerName for m in metrics]
            ax.hist(values, label=labels)
            ax.legend()

