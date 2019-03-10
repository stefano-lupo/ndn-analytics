# from enum import Enum
#
#
# class ObjectType(Enum):
#     STATUS = 'status',
#     PROJECTILE = 'projectile',
#     BLOCK = 'block'
#
#
# class MetricType(Enum):
#     LATENCY = 'latency',
#     RTT = 'rtt'
from typing import List


HistogramValues = List[int]


# Format of metric names is : sub-<object-type>-<latency|rtt>-<player_name>
class Metric:
    def __init__(self, name: str, histogramValues: list):
        pieces = name.split("-")
        # self.objectType: ObjectType = ObjectType(pieces[1])
        # self.metricType: MetricType = MetricType(pieces[2])
        # self.playerName: str = pieces[3]
        self.objectType: str = pieces[1]
        self.metricType: str = pieces[2]
        self.playerName: str = pieces[3]
        self.histogramValues: HistogramValues = histogramValues

