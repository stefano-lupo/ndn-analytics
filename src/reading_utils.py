import csv
import os
from typing import List


def readCsvSafe(fileName: str, keepHeader = False):
    try:
        with open(fileName) as f:
            csvData = list(csv.reader(x.replace('\0', '') for x in f))
            return csvData if keepHeader else csvData[1:]
    except FileNotFoundError as e:
        print("Could not find file %s" % fileName)


def readFileSafe(*args: str) -> List[str]:
    fileName: str = buildFileName(*args)
    try:
        with open(fileName) as f:
            return f.readlines()
    except FileNotFoundError as e:
        print("Could not find file %s " % fileName)


def buildFileName(*arg):
    return os.path.join(*arg)
