import typing
import json
import os
from pprint import pprint

import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

from metric_name import Metric

Metrics = typing.List[Metric]

topology = "linear-three"
deadReckoning = False
node = "nodeA"
histogramFile = "histogram_values.json"

directory = os.path.join("data", topology, "dr" if deadReckoning else "no_dr", node)

with open(os.path.join(directory, histogramFile)) as f:
    histograms = json.load(f)

metrics : Metrics = [Metric(name, values) for name, values in histograms.items()]
metrics : Metrics = [m for m in metrics if m.objectType == 'status']

metricsByType = defaultdict(list)
for playerMetric in metrics:
    metricsByType[playerMetric.metricType].append(playerMetric)

print(metricsByType)

f, (ax1, ax2) = plt.subplots(1, 2)
f.suptitle("Player Status Sync")
# for metricType, metricsForType in metricsByType.items():

rttMetrics = metricsByType["rtt"]
for playerMetric in rttMetrics:
    ax1.hist(playerMetric.histogramValues, label=playerMetric.playerName)
ax1.set_title("Round Trip Times")
ax1.legend()

latencyMetrics = metricsByType["latency"]
for playerMetric in latencyMetrics:
    ax2.hist(playerMetric.histogramValues, label=playerMetric.playerName)
ax2.set_title("Latency")
ax2.legend()
plt.show()
