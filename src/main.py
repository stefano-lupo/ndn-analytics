from typing import List, Dict
import json
import os
from pprint import pprint

import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

from metric_name import Metric

Metrics = List[Metric]

topology = "square"
deadReckoning = False
node = "nodeB"
histogramFile = "histogram_values.json"

directory = os.path.join("data", topology, "dr" if deadReckoning else "no_dr", node)

with open(os.path.join(directory, histogramFile)) as f:
    histograms = json.load(f)

metrics : Metrics = [Metric(name, values) for name, values in histograms.items()]

MetricsByObjectType = Dict[str, Dict[str, Metrics]]
metricsByObjectType = {"status": {}, "block": {}, "projectile": {}}

for playerMetric in metrics:

    metricsForObjectType = metricsByObjectType[playerMetric.objectType]
    if playerMetric.metricType in metricsForObjectType:
        metricsForObjectType[playerMetric.metricType].append(playerMetric)
    else:
        metricsForObjectType[playerMetric.metricType] = [playerMetric]

print(metricsByObjectType)

for objectType, metricsByMetricType in metricsByObjectType.items():
    f, (ax1, ax2) = plt.subplots(1, 2)
    f.suptitle(objectType)
    rttMetrics = metricsByMetricType["rtt"]

    # TODO: Make absolutely sure iteration order is constant
    values = [m.histogramValues for m in rttMetrics]
    labels = [m.playerName for m in rttMetrics]
    ax1.hist(values, label=labels)
    ax1.set_title("Round Trip Times")
    ax1.legend()

    latencyMetrics = metricsByMetricType["latency"]
    values = [m.histogramValues for m in latencyMetrics]
    labels = [m.playerName for m in latencyMetrics]
    ax2.hist(values, label=labels)
    ax2.set_title("Latencies")
    ax2.legend()

    plt.show()
